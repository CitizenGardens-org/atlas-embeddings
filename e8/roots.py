from __future__ import annotations

from fractions import Fraction as Q
from typing import Iterable, List, Tuple, Set

Vector = Tuple[Q, ...]
RootSet = List[Vector]


def dot(x: Vector, y: Vector) -> Q:
    """Return the exact rational inner product of two E8 vectors."""
    return sum(a * b for a, b in zip(x, y))


def generate_e8_roots() -> RootSet:
    """Generate all 240 E8 roots in deterministic lexicographic order."""
    R: Set[Vector] = set()
    # 112 integer roots: two ±1's, rest 0
    for i in range(8):
        for j in range(i + 1, 8):
            for si in (-1, 1):
                for sj in (-1, 1):
                    v = [Q(0)] * 8
                    v[i] = Q(si)
                    v[j] = Q(sj)
                    R.add(tuple(v))
    # 128 half-integer roots: (±1/2,...,±1/2) with even number of + signs
    half = [Q(1, 2), Q(-1, 2)]

    def parity_plus(v: List[Q]) -> int:
        return sum(1 for x in v if x == Q(1, 2)) % 2

    def rec(k: int, cur: List[Q]) -> None:
        if k == 8:
            if parity_plus(cur) == 0:
                R.add(tuple(cur))
            return
        for h in half:
            cur.append(h)
            rec(k + 1, cur)
            cur.pop()

    rec(0, [])
    # freeze in lexicographic deterministic order
    return sorted(R)


def phi_neg_one(t: Q) -> bool:
    return t == Q(-1)


def neighbors_phi_minus_one(R: RootSet) -> List[List[int]]:
    """Return adjacency lists for the graph where ⟨x, y⟩ = −1."""
    n = len(R)
    adj = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if dot(R[i], R[j]) == Q(-1):
                adj[i].append(j)
                adj[j].append(i)
    return [sorted(xs) for xs in adj]
