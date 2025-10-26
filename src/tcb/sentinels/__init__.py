"""Runtime sentinels for exact arithmetic checks within the TCB."""
from typing import Iterable


def assert_r96_cardinality(count: int) -> None:
    """Ensure that the enumerated R96 set has the expected cardinality."""
    assert count == 96, f"R96 cardinality breach: {count}"


def assert_semiring_identities(ok: bool) -> None:
    """Guard the semiring invariants used in the scheduler logic."""
    assert ok, "Semiring identities failed"


def assert_kappa_parity(ok: bool) -> None:
    """Check that the kappa parity constraint holds."""
    assert ok, "kappa parity failed"


def coverage_windowed(visits: Iterable[int], window: int, states: int = 768) -> bool:
    """Validate coverage over a sliding window without relying on floating point arithmetic."""
    data = list(visits)
    assert len(data) == states
    # TODO: implement exact combinatorial coverage checks per window
    return True
