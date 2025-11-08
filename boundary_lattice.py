"""Boundary Lattice - 96×12,288 addressing and (Z/2)^11 subgroup certificate.

This module provides the canonical indexing scheme for the 96-class × 12,288-coordinate
lattice used by the Atlas boundary complex. Each class contains 12,288 coordinates
organized as 6 anchors × 2048 orbit points.

Layout:
- CLASSES = 96 (Atlas vertices)
- ANCHORS = 6 (per class)
- ORBIT = 2048 = 2^11 (Gray-coded orbit per anchor)
- COORDS_PER_CLASS = ANCHORS * ORBIT = 12,288

Linear indexing:
  coord_idx = anchor * ORBIT + v_bits
  where anchor ∈ [0,6), v_bits ∈ [0,2048)

Folding into 48×256 grid:
  The 12,288 coordinates are folded into a 48×256 rectangular layout:
  row = coord_idx // 256
  col = coord_idx % 256
"""
from __future__ import annotations
import json
import hashlib
from typing import Dict, Tuple, Any

# Constants
CLASSES = 96
ANCHORS = 6
ORBIT = 2048  # 2^11
COORDS_PER_CLASS = ANCHORS * ORBIT  # 12,288

# Folding dimensions
FOLD_ROWS = 48
FOLD_COLS = 256


def lin_index(anchor: int, v_bits: int) -> int:
    """Encode (anchor, v_bits) to linear coordinate index.
    
    Args:
        anchor: Anchor index in [0, 6)
        v_bits: Orbit index in [0, 2048)
    
    Returns:
        Linear coordinate index in [0, 12288)
    
    Raises:
        ValueError: If inputs are out of range
    """
    if not (0 <= anchor < ANCHORS):
        raise ValueError(f"anchor must be in [0, {ANCHORS})")
    if not (0 <= v_bits < ORBIT):
        raise ValueError(f"v_bits must be in [0, {ORBIT})")
    return anchor * ORBIT + v_bits


def inv_lin_index(coord_idx: int) -> Tuple[int, int]:
    """Decode linear coordinate index to (anchor, v_bits).
    
    Args:
        coord_idx: Linear coordinate index in [0, 12288)
    
    Returns:
        Tuple of (anchor, v_bits)
    
    Raises:
        ValueError: If coord_idx is out of range
    """
    if not (0 <= coord_idx < COORDS_PER_CLASS):
        raise ValueError(f"coord_idx must be in [0, {COORDS_PER_CLASS})")
    anchor = coord_idx // ORBIT
    v_bits = coord_idx % ORBIT
    return anchor, v_bits


def boundary_fold_48x256(coord_idx: int) -> Tuple[int, int]:
    """Fold linear coordinate into 48×256 grid.
    
    Maps coord_idx to (row, col) where:
      row = coord_idx // 256  (0..47)
      col = coord_idx % 256   (0..255)
    
    Args:
        coord_idx: Linear coordinate index in [0, 12288)
    
    Returns:
        Tuple of (row, col) in 48×256 grid
    
    Raises:
        ValueError: If coord_idx is out of range
    """
    if not (0 <= coord_idx < COORDS_PER_CLASS):
        raise ValueError(f"coord_idx must be in [0, {COORDS_PER_CLASS})")
    row = coord_idx // FOLD_COLS
    col = coord_idx % FOLD_COLS
    return row, col


def boundary_unfold_48x256(row: int, col: int) -> int:
    """Unfold 48×256 grid position back to linear coordinate.
    
    Args:
        row: Row index in [0, 48)
        col: Column index in [0, 256)
    
    Returns:
        Linear coordinate index in [0, 12288)
    
    Raises:
        ValueError: If row or col are out of range
    """
    if not (0 <= row < FOLD_ROWS):
        raise ValueError(f"row must be in [0, {FOLD_ROWS})")
    if not (0 <= col < FOLD_COLS):
        raise ValueError(f"col must be in [0, {FOLD_COLS})")
    coord_idx = row * FOLD_COLS + col
    return coord_idx


def save_certificate(filename: str) -> None:
    """Generate and persist (Z/2)^11 subgroup certificate.
    
    Creates a certificate documenting the (Z/2)^11 subgroup structure acting on
    the boundary lattice. The certificate includes:
    - Metadata: dimensions, parameters
    - Subgroup structure: generators, order, action description
    - Checksum for verification
    
    Args:
        filename: Output JSON filename (e.g., "subgroup_certificate.json")
    """
    from atlas12288 import ANCHORS, gray11
    from atlas12288.symmetry import Involutions
    
    # Build certificate data
    certificate: Dict[str, Any] = {
        "type": "Z2_11_subgroup_certificate",
        "version": "1.0",
        "lattice": {
            "classes": CLASSES,
            "anchors_per_class": ANCHORS,
            "orbit_size": ORBIT,
            "coords_per_class": COORDS_PER_CLASS,
            "fold_dimensions": [FOLD_ROWS, FOLD_COLS],
        },
        "subgroup": {
            "description": "(Z/2)^11 acting via bit flips on (p, b) coordinates",
            "order": 2048,  # 2^11
            "rank": 11,
            "generators": [
                {"index": i, "description": f"flip bit {i} of b (byte)"} 
                for i in range(8)
            ] + [
                {"index": i + 8, "description": f"flip bit {i} of p2 (page low bits)"}
                for i in range(3)
            ],
        },
        "anchors": [
            {"index": i, "p": p, "b": b}
            for i, (p, b) in enumerate(ANCHORS)
        ],
        "verification": {
            "orbit_example": {
                "anchor_index": 0,
                "anchor_coords": list(ANCHORS[0]),
                "orbit_sample": [
                    {
                        "gray_index": g,
                        "gray_code": gray11(g),
                        "coords": list(Involutions.orbit_from_anchor(*ANCHORS[0])[g]),
                    }
                    for g in [0, 1, 2, 3, 2047]  # First few and last
                ],
            },
        },
    }
    
    # Generate checksum
    cert_bytes = json.dumps(certificate, sort_keys=True, separators=(",", ":")).encode()
    checksum = hashlib.blake2b(cert_bytes, digest_size=32).hexdigest()
    certificate["checksum"] = checksum
    
    # Write to file
    with open(filename, "w") as f:
        json.dump(certificate, f, indent=2)
