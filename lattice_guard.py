"""Lattice Guard - Context validation and enrichment for 96×12,288 lattice.

Enforces canonical addressing for step contexts in the Atlas boundary lattice.
Provides decode/encode utilities and context guard functions.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

from boundary_lattice import (
    CLASSES, ANCHORS, ORBIT, COORDS_PER_CLASS,
    lin_index, inv_lin_index, boundary_fold_48x256, boundary_unfold_48x256,
)


@dataclass
class Decoded:
    """Decoded lattice address with all coordinate representations."""
    class_id: int
    coord_idx: int
    anchor: int
    v_bits: int
    row: int
    col: int


def verify_address(class_id: int, coord_idx: int) -> None:
    """Validate lattice address ranges.
    
    Args:
        class_id: Class identifier in [0, 96)
        coord_idx: Coordinate index in [0, 12288)
    
    Raises:
        ValueError: If either parameter is out of range
    """
    if not (0 <= class_id < CLASSES):
        raise ValueError(f"class_id out of range [0,{CLASSES-1}]")
    if not (0 <= coord_idx < COORDS_PER_CLASS):
        raise ValueError(f"coord_idx out of range [0,{COORDS_PER_CLASS-1}]")


def decode(class_id: int, coord_idx: int) -> Decoded:
    """Fully decode a lattice address.
    
    Args:
        class_id: Class identifier in [0, 96)
        coord_idx: Coordinate index in [0, 12288)
    
    Returns:
        Decoded object with all coordinate representations
    
    Raises:
        ValueError: If inputs are out of range
    """
    verify_address(class_id, coord_idx)
    a, v = inv_lin_index(coord_idx)
    r, c = boundary_fold_48x256(coord_idx)
    return Decoded(
        class_id=class_id,
        coord_idx=coord_idx,
        anchor=a,
        v_bits=v,
        row=r,
        col=c
    )


def encode(class_id: int, anchor: int, v_bits: int) -> int:
    """Encode (class_id, anchor, v_bits) to coordinate index.
    
    Args:
        class_id: Class identifier in [0, 96)
        anchor: Anchor index in [0, 6)
        v_bits: Orbit index in [0, 2048)
    
    Returns:
        Coordinate index in [0, 12288)
    
    Raises:
        ValueError: If any parameter is out of range
    """
    if not (0 <= class_id < CLASSES):
        raise ValueError("bad class")
    if not (0 <= anchor < ANCHORS):
        raise ValueError("bad anchor")
    if not (0 <= v_bits < ORBIT):
        raise ValueError("bad v_bits")
    return lin_index(anchor, v_bits)


def guard_context(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and enrich a step context with lattice coordinates.
    
    Expects ctx["class"] and either:
      - ctx["coord"] (linear index), or
      - ctx["anchor"] and ctx["v_bits"]
    
    Returns enriched dict with all coordinate representations:
      coord, anchor, v_bits, row, col
    
    Args:
        ctx: Step context dictionary
    
    Returns:
        Enriched context with normalized coordinates
    
    Raises:
        ValueError: If context is missing required keys or has invalid values
    """
    if "class" not in ctx:
        raise ValueError("missing class in context")
    
    # Handle boolean values for class (guard True/False)
    c = int(ctx["class"]) if not isinstance(ctx["class"], bool) else int(ctx["class"])
    
    # Determine coordinate index from available keys
    if "coord" in ctx:
        idx = int(ctx["coord"])  # linear index
    elif ("anchor" in ctx) and ("v_bits" in ctx):
        idx = encode(c, int(ctx["anchor"]), int(ctx["v_bits"]))
    else:
        raise ValueError("context must include either coord or (anchor,v_bits)")
    
    # Validate and decode
    verify_address(c, idx)
    d = decode(c, idx)
    
    # Enrich output context
    out = dict(ctx)
    out.update({
        "coord": d.coord_idx,
        "anchor": d.anchor,
        "v_bits": d.v_bits,
        "row": d.row,
        "col": d.col,
    })
    return out
