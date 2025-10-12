from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as Q
from hashlib import sha256
from typing import Dict, Iterable, List, Optional, Set, Tuple

from core.resgraph import ResGraph, Vertex
from e8.roots import Vector, dot, generate_e8_roots
from e8.weyl import Matrix

from .uniqueness import matrix_between_embeddings, permutes_root_set

RootIndex = int


@dataclass(frozen=True)
class EmbeddingResult:
    f: Dict[Vertex, RootIndex]
    roots: List[Vector]
    matrix_cert: Optional[Matrix]
    checksum_coords: str
    log: str


def _vertex_order(V: Iterable[Vertex]) -> List[Vertex]:
    return sorted(V)


def _degree_profile(G: ResGraph, order: List[Vertex]) -> Dict[Vertex, int]:
    return {u: len(G.neighbors(u)) for u in order}


def _candidate_roots_for_vertex(
    u: Vertex,
    R: List[Vector],
    G: ResGraph,
    root_lookup: Dict[Vector, int],
    default_domain: List[int],
) -> List[int]:
    label = G.λ[u]
    if label in root_lookup:
        return [root_lookup[label]]
    return default_domain


def _independent(span: List[Vector], v: Vector) -> bool:
    if not span:
        return True

    def rank(M: List[List[Q]]) -> int:
        M = [row[:] for row in M]
        r = 0
        c = 0
        n = len(M)
        p = len(M[0]) if M else 0
        while r < n and c < p:
            pivot = None
            for i in range(r, n):
                if M[i][c] != 0:
                    pivot = i
                    break
            if pivot is None:
                c += 1
                continue
            M[r], M[pivot] = M[pivot], M[r]
            piv = M[r][c]
            for j in range(c, p):
                M[r][j] /= piv
            for i in range(n):
                if i == r:
                    continue
                factor = M[i][c]
                if factor == 0:
                    continue
                for j in range(c, p):
                    M[i][j] -= factor * M[r][j]
            r += 1
            c += 1
        return r

    A = [[span[j][i] for j in range(len(span))] for i in range(8)]
    r1 = rank([row[:] for row in A]) if span else 0
    A_aug = [row[:] for row in A]
    for i in range(8):
        A_aug[i].append(v[i])
    r2 = rank(A_aug)
    return r2 > r1


def _choose_basis(indices: List[int], R: List[Vector]) -> List[int]:
    basis: List[int] = []
    span: List[Vector] = []
    for idx in indices:
        v = R[idx]
        if _independent(span, v):
            basis.append(idx)
            span.append(v)
        if len(basis) == 8:
            break
    if len(basis) != 8:
        raise ValueError("could not find rank-8 subset")
    return basis


def _search_embedding(
    G: ResGraph,
    R: List[Vector],
    root_lookup: Dict[Vector, int],
    default_domain: List[int],
    descending: bool,
) -> Dict[Vertex, int]:
    order = _vertex_order(G.V)
    deg = _degree_profile(G, order)
    if descending:
        vars_ = sorted(order, key=lambda u: (-deg[u], u))
    else:
        vars_ = sorted(order, key=lambda u: (deg[u], u))
    domains: Dict[Vertex, List[int]] = {
        u: _candidate_roots_for_vertex(u, R, G, root_lookup, default_domain) for u in vars_
    }

    assign: Dict[Vertex, int] = {}
    used: Set[int] = set()

    def consistent(u: Vertex, r_idx: int) -> bool:
        ru = R[r_idx]
        if dot(ru, ru) != Q(2):
            return False
        for v in G.neighbors(u):
            if v in assign:
                rv = R[assign[v]]
                if G.is_adjacent(u, v) != (dot(ru, rv) == Q(-1)):
                    return False
        return True

    def backtrack(i: int) -> bool:
        if i == len(vars_):
            return True
        u = vars_[i]
        for r_idx in domains[u]:
            if r_idx in used:
                continue
            if not consistent(u, r_idx):
                continue
            assign[u] = r_idx
            used.add(r_idx)
            if backtrack(i + 1):
                return True
            used.remove(r_idx)
            del assign[u]
        return False

    if not backtrack(0):
        raise ValueError("no embedding found")
    return assign


def _pair_log(G: ResGraph, f: Dict[Vertex, int], R: List[Vector]) -> Tuple[str, str]:
    verts = sorted(G.V)
    lines: List[str] = []
    violations = 0
    for i, u in enumerate(verts):
        for j in range(i + 1, len(verts)):
            v = verts[j]
            adj = G.is_adjacent(u, v)
            ip = dot(R[f[u]], R[f[v]])
            ok = (ip == Q(-1)) == adj
            if not ok:
                violations += 1
            lines.append(f"{u},{v}: adj={int(adj)} ip={ip}")
    digest = sha256("\n".join(lines).encode()).hexdigest()
    header = f"pairs=4560 violations={violations} sha256={digest}"
    return header, "\n".join([header] + lines)


def embed_atlas_to_e8(G: ResGraph) -> EmbeddingResult:
    R = generate_e8_roots()
    root_lookup = {R[i]: i for i in range(len(R))}
    default_domain = [i for i, r in enumerate(R) if dot(r, r) == Q(2)]
    f_desc = _search_embedding(G, R, root_lookup, default_domain, descending=True)
    if len(set(f_desc.values())) != len(G.V):
        raise ValueError("embedding is not injective")

    # Second run with ascending degree order for uniqueness certificate
    f_asc = _search_embedding(G, R, root_lookup, default_domain, descending=False)
    basis_desc = _choose_basis([f_desc[v] for v in sorted(G.V)], R)
    basis_asc = _choose_basis([f_asc[v] for v in sorted(G.V)], R)
    S1 = [R[i] for i in basis_desc]
    S2 = [R[i] for i in basis_asc]
    M_candidate = matrix_between_embeddings(S1, S2)
    matrix_cert: Optional[Matrix] = M_candidate if permutes_root_set(M_candidate, R) else None

    header, log = _pair_log(G, f_desc, R)
    coords = [R[f_desc[u]] for u in sorted(G.V)]
    flat = [str(x) for row in coords for x in row]
    checksum_coords = sha256(",".join(flat).encode()).hexdigest()
    return EmbeddingResult(
        f=f_desc,
        roots=R,
        matrix_cert=matrix_cert,
        checksum_coords=checksum_coords,
        log=log,
    )
