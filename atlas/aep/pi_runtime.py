from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple, Optional
import hashlib

from .ace import Budgets, project_dual_int, ace_accept, rho_hat_scaled
from .petc import PETCLedger


# -------------------------
# Channel operator (prime-indexed)
# -------------------------
@dataclass(frozen=True)
class ChannelOp:
    id: str                   # ledger id
    prime: int                # prime index p
    norm_Q: int               # ||B_p|| in scale Q (integer)
    # matvec preserves scale: input v_Q (scale Q) -> output (scale Q)
    matvec: Callable[[List[int]], List[int]]


# -------------------------
# Adapter
# -------------------------
class PiRuntimeAdapter:
    """
    Π-atoms -> prime-indexed channels. Runtime step:
      1) aggregate per-channel wtilde_Q
      2) ACE projection -> w*_Q in S
      3) build K via weighted matvec: K(v) = sum_p (w*_p/Q) * B_p(v)  (all integer with //Q)
      4) AUDIT(PETC): ledger rows + digests, decrement budgets
      5) quarantine on any breach
    Strong monoidal. With ACE gap, T is a contractive endofunctor.
    """

    def __init__(self, channels: List[ChannelOp], ledger: PETCLedger, budgets: Budgets):
        self.channels = channels
        self.ledger = ledger
        self.budgets = budgets
        # index maps
        self.idx: Dict[str, int] = {ch.id: i for i, ch in enumerate(channels)}

    # --- helpers ---
    def _aggregate(self, contribs: List[Tuple[str, int]]) -> List[int]:
        """Sum proposed weights per channel id. Scale Q integers."""

        wtilde = [0] * len(self.channels)
        for cid, w in contribs:
            i = self.idx.get(cid)
            if i is None:
                raise KeyError(f"unknown channel id: {cid}")
            wtilde[i] += int(w)
        return wtilde

    def _build_K_matvec(self, w_Q: List[int]) -> Callable[[List[int]], List[int]]:
        """Return matvec v -> sum_i (w_i * B_i(v)) // Q"""

        Q = self.budgets.Q
        chans = self.channels

        def K(v: List[int]) -> List[int]:
            acc: Optional[List[int]] = None
            for i, ch in enumerate(chans):
                wi = w_Q[i]
                if wi == 0:
                    continue
                bv = ch.matvec(v)            # scale Q
                term = [(wi * x) // Q for x in bv]
                if acc is None:
                    acc = term
                else:
                    for j in range(len(term)):
                        acc[j] += term[j]
            return acc if acc is not None else [0] * len(v)

        return K

    def _slope_data(self) -> List[int]:
        """Per-channel ||B_p|| in scale Q."""

        return [ch.norm_Q for ch in self.channels]

    # --- public step ---
    def run_step(
        self,
        x_t_Q: List[int],                 # state (scale Q)
        F_Q: List[int],                   # offset (scale Q)
        contribs: List[Tuple[str, int]],  # (channel_id, wtilde_Q)
        spectral_iters: int = 3,
    ) -> Dict[str, object]:
        """
        Returns dict with:
          quarantine: bool
          reason: str
          wtilde_Q, w_star_Q, lam_Q, mu_Q
          ace_ok: bool, ace_metrics: {slope_scaled, gap_scaled, Q2, rho_hat_scaled?}
          digests: {petc_sha256: hex, decrements: [(class, remaining), ...]}
          x_next_Q (if not quarantined)
        """

        Q = self.budgets.Q
        # 1) aggregate
        wtilde_Q = self._aggregate(contribs)
        # 2) ACE projection
        pres = project_dual_int(wtilde_Q, self.budgets)
        w_star_Q = pres.w_star_Q
        # 3) acceptance metrics
        Bnorms_Q = self._slope_data()
        # K matvec for spectral bound
        Kmv = self._build_K_matvec(w_star_Q)
        rhoQ = rho_hat_scaled(Kmv, dim=len(x_t_Q), Q=Q, iters=max(1, spectral_iters))
        ace_ok, metrics = ace_accept(w_star_Q, Bnorms_Q, Q, rhoQ)
        if not ace_ok:
            return {
                "quarantine": True,
                "reason": "ACE",
                "wtilde_Q": wtilde_Q,
                "w_star_Q": w_star_Q,
                "lam_Q": pres.lam_Q,
                "mu_Q": pres.mu_Q,
                "ace_ok": False,
                "ace_metrics": {
                    "slope_scaled": metrics.slope_scaled,
                    "gap_scaled": metrics.gap_scaled,
                    "Q2": metrics.Q2,
                    "rho_hat_scaled": metrics.rho_hat_scaled,
                },
                "digests": {},
            }
        # 4) PETC audit
        decrements: List[Tuple[str, int]] = []
        h = hashlib.sha256()
        for i, ch in enumerate(self.channels):
            wi = w_star_Q[i]
            if wi == 0:
                continue
            # digest
            h.update(ch.id.encode("utf-8"))
            h.update(str(int(wi)).encode("utf-8"))
            # decrement commutator budget for this channel's class
            # obtain class from ledger row
            row = self.ledger.rows.get(ch.id)
            if row is None:
                return {
                    "quarantine": True,
                    "reason": "PETC_MISSING_ROW",
                    "wtilde_Q": wtilde_Q,
                    "w_star_Q": w_star_Q,
                    "lam_Q": pres.lam_Q,
                    "mu_Q": pres.mu_Q,
                    "ace_ok": True,
                    "ace_metrics": {
                        "slope_scaled": metrics.slope_scaled,
                        "gap_scaled": metrics.gap_scaled,
                        "Q2": metrics.Q2,
                        "rho_hat_scaled": metrics.rho_hat_scaled,
                    },
                    "digests": {},
                }
            try:
                rem = self.ledger.decrement_commutator(row.commutator_class, 1)
                decrements.append((row.commutator_class, rem))
            except RuntimeError:
                return {
                    "quarantine": True,
                    "reason": "PETC_BREACH",
                    "wtilde_Q": wtilde_Q,
                    "w_star_Q": w_star_Q,
                    "lam_Q": pres.lam_Q,
                    "mu_Q": pres.mu_Q,
                    "ace_ok": True,
                    "ace_metrics": {
                        "slope_scaled": metrics.slope_scaled,
                        "gap_scaled": metrics.gap_scaled,
                        "Q2": metrics.Q2,
                        "rho_hat_scaled": metrics.rho_hat_scaled,
                    },
                    "digests": {"decrements": decrements},
                }
        petc_digest = h.hexdigest()
        # 5) advance state
        Kx = Kmv(x_t_Q)               # scale Q
        x_next_Q = [F_Q[i] + Kx[i] for i in range(len(x_t_Q))]
        return {
            "quarantine": False,
            "reason": "",
            "wtilde_Q": wtilde_Q,
            "w_star_Q": w_star_Q,
            "lam_Q": pres.lam_Q,
            "mu_Q": pres.mu_Q,
            "ace_ok": True,
            "ace_metrics": {
                "slope_scaled": metrics.slope_scaled,
                "gap_scaled": metrics.gap_scaled,
                "Q2": metrics.Q2,
                "rho_hat_scaled": metrics.rho_hat_scaled,
            },
            "digests": {"petc_sha256": petc_digest, "decrements": decrements},
            "x_next_Q": x_next_Q,
        }

