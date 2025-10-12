from __future__ import annotations

from fractions import Fraction as Q
from typing import Dict, FrozenSet, Iterable, List, Mapping, Sequence

from e8.roots import Vector, dot

Vertex = str


class ResGraph:
    """A resonance graph with Φ adjacency defined by inner product −1."""

    def __init__(
        self,
        vertices: Iterable[Vertex],
        labels: Mapping[Vertex, Sequence[Q]],
        distinguished: Iterable[Vertex] | None = None,
    ) -> None:
        verts = list(vertices)
        if len(set(verts)) != len(verts):
            raise ValueError("vertices must be distinct")
        self.V: FrozenSet[Vertex] = frozenset(sorted(verts))
        self.U: FrozenSet[Vertex] = frozenset(distinguished or [])
        lambda_map: Dict[Vertex, Vector] = {}
        for v in self.V:
            if v not in labels:
                raise ValueError(f"missing label for vertex {v}")
            coord = tuple(Q(x) for x in labels[v])
            if len(coord) != 8:
                raise ValueError("labels must be 8-dimensional")
            lambda_map[v] = coord
        self.lambda_map: Dict[Vertex, Vector] = lambda_map
        # expose Atlas notation attributes
        self.__dict__["λ"] = self.lambda_map
        self.__dict__["Φ"] = lambda t: t == Q(-1)
        self._adj: Dict[Vertex, List[Vertex]] = {v: [] for v in self.V}
        verts_sorted = sorted(self.V)
        for i, u in enumerate(verts_sorted):
            for v in verts_sorted[i + 1 :]:
                if self.__dict__["Φ"](dot(lambda_map[u], lambda_map[v])):
                    self._adj[u].append(v)
                    self._adj[v].append(u)
        for v in self.V:
            self._adj[v].sort()

    def neighbors(self, v: Vertex) -> List[Vertex]:
        return list(self._adj[v])

    def is_adjacent(self, u: Vertex, v: Vertex) -> bool:
        return v in self._adj[u]
