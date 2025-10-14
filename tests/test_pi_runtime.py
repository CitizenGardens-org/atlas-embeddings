from atlas.aep.pi_runtime import PiRuntimeAdapter, ChannelOp
from atlas.aep.ace import Budgets
from atlas.aep.petc import PETCLedger, ChannelRow, axis_signature


# simple identity channel: matvec returns v (scale preserved)
def id_matvec(v):
    return list(v)


def test_run_step_pass_identity():
    Q = 10**6
    # channels
    ch = ChannelOp(id="c1", prime=2, norm_Q=Q // 2, matvec=id_matvec)
    # ledger with commutator budget
    L = PETCLedger()
    L.add_channel(ChannelRow(id="c1", sigma=axis_signature(2), budget=1, commutator_class="X"))
    # budgets: allow weights up to 0.6Q
    b = [1]
    a = [1]
    L1 = int(0.6 * Q)  # no floats in code; cast in test context only
    L2 = int(0.6 * Q)
    B = Budgets(b=b, a=a, limit1_Q=L1, limit2_Q=L2, Q=Q)
    adapter = PiRuntimeAdapter([ch], L, B)
    # state and offset
    x_t = [Q, 0]
    F = [0, 0]
    # proposed weight 0.5Q
    contribs = [("c1", Q // 2)]
    out = adapter.run_step(x_t, F, contribs, spectral_iters=2)
    assert out["quarantine"] is False
    # x_next = F + (w/Q)*x = 0.5 * x
    assert out["x_next_Q"][0] == Q // 2 and out["x_next_Q"][1] == 0
    assert out["ace_ok"] is True
    assert "petc_sha256" in out["digests"]
    # budget decremented to 0
    assert L.get_budget("X") == 0


def test_petcl_breach_quarantine():
    Q = 10**6
    ch = ChannelOp(id="c1", prime=3, norm_Q=Q // 2, matvec=id_matvec)
    L = PETCLedger()
    # zero budget triggers breach
    L.add_channel(ChannelRow(id="c1", sigma=axis_signature(3), budget=0, commutator_class="Y"))
    b = [1]
    a = [1]
    B = Budgets(b=b, a=a, limit1_Q=Q, limit2_Q=Q, Q=Q)
    adapter = PiRuntimeAdapter([ch], L, B)
    out = adapter.run_step([Q], [0], [("c1", Q // 4)], spectral_iters=1)
    assert out["quarantine"] is True and out["reason"] == "PETC_BREACH"


def test_ace_quarantine_by_slope():
    Q = 10**6
    # choose huge norm to violate slope < Q^2
    ch = ChannelOp(id="c1", prime=5, norm_Q=Q * 2, matvec=id_matvec)
    L = PETCLedger()
    L.add_channel(ChannelRow(id="c1", sigma=axis_signature(5), budget=5, commutator_class="Z"))
    b = [1]
    a = [1]
    B = Budgets(b=b, a=a, limit1_Q=Q, limit2_Q=Q, Q=Q)
    adapter = PiRuntimeAdapter([ch], L, B)
    # weight Q -> slope = |w|*norm = Q*(2Q) = 2Q^2 >= Q^2
    out = adapter.run_step([Q], [0], [("c1", Q)], spectral_iters=1)
    assert out["quarantine"] is True and out["reason"] == "ACE"


def test_missing_ledger_row_quarantine():
    Q = 10**6
    ch = ChannelOp(id="cX", prime=7, norm_Q=Q // 2, matvec=id_matvec)
    L = PETCLedger()  # no rows added
    b = [1]
    a = [1]
    B = Budgets(b=b, a=a, limit1_Q=Q, limit2_Q=Q, Q=Q)
    adapter = PiRuntimeAdapter([ch], L, B)
    out = adapter.run_step([Q], [0], [("cX", Q // 4)], spectral_iters=1)
    assert out["quarantine"] is True and out["reason"] == "PETC_MISSING_ROW"

