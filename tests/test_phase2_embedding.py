from __future__ import annotations

from fractions import Fraction as Q

from atlas.atlas import make_atlas
from atlas.embedding import embed_atlas_to_e8
from e8.roots import dot, generate_e8_roots


def make_synthetic_atlas_from_e8_subset():
    R = generate_e8_roots()
    idxs = list(range(96))
    V = frozenset(f"v{i}" for i in range(96))
    labels = {f"v{i}": R[idxs[i]] for i in range(96)}
    U = frozenset({"v0"})
    return make_atlas(V, labels, U)


def test_embedding_produces_96_and_certifies_pairs():
    atlas = make_synthetic_atlas_from_e8_subset()
    result = embed_atlas_to_e8(atlas)
    assert len(result.f) == 96
    verts = sorted(atlas.V)
    for i, u in enumerate(verts):
        for v in verts[i + 1 :]:
            ip = dot(result.roots[result.f[u]], result.roots[result.f[v]])
            assert (ip == Q(-1)) == atlas.is_adjacent(u, v)
    assert len(result.log.splitlines()) == 1 + 4560
    if result.matrix_cert is not None:
        # matrix cert permutes the full root set
        images = {tuple(sum(result.matrix_cert[i][k] * r[k] for k in range(8)) for i in range(8)) for r in result.roots}
        assert len(images) == len(result.roots)
