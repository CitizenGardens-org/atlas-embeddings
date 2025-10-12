"""Utilities for working with the E8 root system."""

from .roots import generate_e8_roots, neighbors_phi_minus_one, dot
from .weyl import (
    Matrix,
    reflect,
    mat_from_columns,
    mat_mul,
    mat_inv,
    mat_mul_mat,
)

__all__ = [
    "generate_e8_roots",
    "neighbors_phi_minus_one",
    "dot",
    "Matrix",
    "reflect",
    "mat_from_columns",
    "mat_mul",
    "mat_inv",
    "mat_mul_mat",
]
