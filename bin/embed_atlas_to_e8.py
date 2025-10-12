#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import sys
from fractions import Fraction as Q

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from atlas.atlas import make_atlas
from atlas.embedding import embed_atlas_to_e8


def load_atlas() -> "ResGraph":
    data = json.load(open("data/atlas_min.json"))
    V = frozenset(data["V"])
    U = frozenset(data["U"])
    labels = {k: tuple(Q(n) for n in v) for k, v in data["labels"].items()}
    return make_atlas(V, labels, U)


def main() -> None:
    atlas = load_atlas()
    result = embed_atlas_to_e8(atlas)
    outdir = pathlib.Path("artifacts/phase2")
    outdir.mkdir(parents=True, exist_ok=True)
    with open(outdir / "embedding.json", "w", encoding="utf-8") as fh:
        json.dump({"f": result.f, "checksum_coords": result.checksum_coords}, fh, indent=2)
    with open(outdir / "coordinates.csv", "w", encoding="utf-8") as fh:
        for u in sorted(atlas.V):
            row = ",".join(str(x) for x in result.roots[result.f[u]])
            fh.write(f"{u},{row}\n")
    (outdir / "proof.log").write_text(result.log, encoding="utf-8")
    print("OK", result.checksum_coords)


if __name__ == "__main__":
    main()
