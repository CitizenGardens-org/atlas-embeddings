from __future__ import annotations

from fractions import Fraction as Q
from typing import Dict, Iterable, Mapping, Sequence

from core.resgraph import ResGraph, Vertex
from e8.roots import Vector


def _canonize_labels(labels: Mapping[Vertex, Sequence[int | str | Q]]) -> Dict[Vertex, Vector]:
    canon: Dict[Vertex, Vector] = {}
    for v, coords in labels.items():
        canon[v] = tuple(Q(x) for x in coords)
    return canon


def make_atlas(
    vertices: Iterable[Vertex],
    labels: Mapping[Vertex, Sequence[int | str | Q]],
    distinguished: Iterable[Vertex],
) -> ResGraph:
    """Build a :class:`ResGraph` from Atlas data."""
    canon = _canonize_labels(labels)
    return ResGraph(vertices, canon, distinguished)
