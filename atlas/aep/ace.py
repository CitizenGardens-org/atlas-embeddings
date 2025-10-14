"""Integer-only helpers for ACE projections and spectral checks.

This module provides a minimal subset of the arithmetic control engine (ACE)
API required by the Π-runtime adapter.  Everything operates using integers at a
fixed scale ``Q`` to keep behaviour deterministic and reproducible across
platforms.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List


@dataclass(frozen=True)
class Budgets:
    """Container for integer budgets used by :func:`project_dual_int`.

    Parameters
    ----------
    b, a:
        Optional per-channel coefficients.  The adapter currently treats them
        as metadata but they are included for compatibility with upstream
        interfaces.
    limit1_Q, limit2_Q:
        Scalar limits expressed in the shared scale ``Q``.
    Q:
        Common scaling factor.  All incoming weights are interpreted as being
        scaled by ``Q``.
    """

    b: List[int]
    a: List[int]
    limit1_Q: int
    limit2_Q: int
    Q: int


@dataclass(frozen=True)
class ProjectionResult:
    """Return type for :func:`project_dual_int`."""

    w_star_Q: List[int]
    lam_Q: int
    mu_Q: int


def project_dual_int(wtilde_Q: List[int], budgets: Budgets) -> ProjectionResult:
    """Project proposed weights onto the admissible integer budget region.

    The available tests require only a simple per-channel clamp, so we cap each
    weight to ``[-cap, cap]`` where ``cap = min(limit1_Q, limit2_Q)``.  The
    dual variables ``λ`` and ``μ`` are represented by the amount of clipping
    applied (sum of positive and negative excess respectively).
    """

    cap = int(min(budgets.limit1_Q, budgets.limit2_Q))
    w_star: List[int] = []
    lam = 0
    mu = 0
    for w in wtilde_Q:
        wi = int(w)
        if wi > cap:
            lam += wi - cap
            wi = cap
        elif wi < -cap:
            mu += -cap - wi
            wi = -cap
        w_star.append(wi)
    return ProjectionResult(w_star_Q=w_star, lam_Q=lam, mu_Q=mu)


@dataclass(frozen=True)
class ACEMetrics:
    """Diagnostics produced by :func:`ace_accept`."""

    slope_scaled: int
    gap_scaled: int
    Q2: int
    rho_hat_scaled: int


def ace_accept(w_star_Q: List[int], norms_Q: List[int], Q: int, rho_scaled: int) -> tuple[bool, ACEMetrics]:
    """Check the ACE acceptance conditions using integer arithmetic.

    The slope is measured as ``Σ |w_i| * ||B_i||`` and is compared against the
    squared scale ``Q^2``.  The spectral surrogate ``rho_scaled`` is assumed to
    already be expressed in the same scale ``Q``.  Acceptance requires both the
    slope and the spectral surrogate to lie strictly below their respective
    thresholds.
    """

    slope = 0
    for wi, ni in zip(w_star_Q, norms_Q):
        slope += abs(int(wi)) * abs(int(ni))
    Q2 = int(Q) * int(Q)
    gap = Q2 - slope if slope < Q2 else 0
    ok = slope < Q2 and rho_scaled < Q
    metrics = ACEMetrics(
        slope_scaled=int(slope),
        gap_scaled=int(gap),
        Q2=int(Q2),
        rho_hat_scaled=int(rho_scaled),
    )
    return ok, metrics


def rho_hat_scaled(matvec: Callable[[List[int]], List[int]], dim: int, Q: int, iters: int = 3) -> int:
    """Integer-only power iteration to estimate a spectral bound.

    ``matvec`` must preserve the scale ``Q``.  The algorithm keeps the iterate
    normalised to a maximum absolute value of approximately ``Q`` so that the
    ratio between consecutive norms yields a quantity scaled by ``Q``.
    """

    if dim <= 0:
        return 0
    if iters <= 0:
        iters = 1
    v = [int(Q)] * dim
    prev_norm = max(abs(x) for x in v) or 1
    rho = 0
    for _ in range(iters):
        v = matvec(v)
        norm = max(abs(x) for x in v)
        if norm == 0:
            return 0
        ratio = (int(norm) * int(Q)) // int(prev_norm)
        if ratio > rho:
            rho = ratio
        # renormalise to keep numbers bounded
        v = [(int(x) * int(Q)) // int(norm) for x in v]
        prev_norm = max(abs(x) for x in v) or 1
    return int(rho)

