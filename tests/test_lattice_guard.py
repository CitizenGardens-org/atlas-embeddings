"""Tests for lattice_guard module."""
import pytest
from lattice_guard import (
    Decoded, verify_address, decode, encode, guard_context,
)


def test_verify_address_valid():
    """Test verify_address with valid inputs."""
    verify_address(0, 0)
    verify_address(95, 12287)
    verify_address(50, 6000)


def test_verify_address_invalid_class():
    """Test verify_address with invalid class_id."""
    with pytest.raises(ValueError, match="class_id out of range"):
        verify_address(-1, 0)
    with pytest.raises(ValueError, match="class_id out of range"):
        verify_address(96, 0)


def test_verify_address_invalid_coord():
    """Test verify_address with invalid coord_idx."""
    with pytest.raises(ValueError, match="coord_idx out of range"):
        verify_address(0, -1)
    with pytest.raises(ValueError, match="coord_idx out of range"):
        verify_address(0, 12288)


def test_decode_basic():
    """Test decode for basic cases."""
    d = decode(0, 0)
    assert d.class_id == 0
    assert d.coord_idx == 0
    assert d.anchor == 0
    assert d.v_bits == 0
    assert d.row == 0
    assert d.col == 0


def test_decode_complex():
    """Test decode for complex case."""
    d = decode(50, 5000)
    assert d.class_id == 50
    assert d.coord_idx == 5000
    assert d.anchor == 2  # 5000 // 2048
    assert d.v_bits == 904  # 5000 % 2048
    assert d.row == 19  # 5000 // 256
    assert d.col == 136  # 5000 % 256


def test_encode_basic():
    """Test encode for basic cases."""
    assert encode(0, 0, 0) == 0
    assert encode(95, 5, 2047) == 12287


def test_encode_invalid_class():
    """Test encode with invalid class_id."""
    with pytest.raises(ValueError, match="bad class"):
        encode(-1, 0, 0)
    with pytest.raises(ValueError, match="bad class"):
        encode(96, 0, 0)


def test_encode_invalid_anchor():
    """Test encode with invalid anchor."""
    with pytest.raises(ValueError, match="bad anchor"):
        encode(0, -1, 0)
    with pytest.raises(ValueError, match="bad anchor"):
        encode(0, 6, 0)


def test_encode_invalid_v_bits():
    """Test encode with invalid v_bits."""
    with pytest.raises(ValueError, match="bad v_bits"):
        encode(0, 0, -1)
    with pytest.raises(ValueError, match="bad v_bits"):
        encode(0, 0, 2048)


def test_encode_decode_roundtrip():
    """Test encode/decode round-trip."""
    for c in [0, 10, 95]:
        for a in range(6):
            for v in [0, 100, 2047]:
                idx = encode(c, a, v)
                d = decode(c, idx)
                assert d.class_id == c
                assert d.anchor == a
                assert d.v_bits == v


def test_guard_context_with_coord():
    """Test guard_context with coord."""
    ctx = guard_context({"class": 10, "coord": 5000})
    assert ctx["class"] == 10
    assert ctx["coord"] == 5000
    assert ctx["anchor"] == 2
    assert ctx["v_bits"] == 904
    assert ctx["row"] == 19
    assert ctx["col"] == 136


def test_guard_context_with_anchor_v_bits():
    """Test guard_context with anchor and v_bits."""
    ctx = guard_context({"class": 10, "anchor": 3, "v_bits": 1500})
    assert ctx["class"] == 10
    assert ctx["anchor"] == 3
    assert ctx["v_bits"] == 1500
    assert ctx["coord"] == 7644  # 3 * 2048 + 1500


def test_guard_context_missing_class():
    """Test guard_context without class."""
    with pytest.raises(ValueError, match="missing class"):
        guard_context({"coord": 100})


def test_guard_context_missing_coords():
    """Test guard_context without coord or anchor/v_bits."""
    with pytest.raises(ValueError, match="must include either"):
        guard_context({"class": 10})
    with pytest.raises(ValueError, match="must include either"):
        guard_context({"class": 10, "anchor": 2})
    with pytest.raises(ValueError, match="must include either"):
        guard_context({"class": 10, "v_bits": 500})


def test_guard_context_boolean_class():
    """Test guard_context with boolean class value."""
    ctx = guard_context({"class": True, "coord": 100})
    assert ctx["class"] == True  # Original value preserved
    assert ctx["coord"] == 100


def test_guard_context_preserves_extra_keys():
    """Test guard_context preserves extra context keys."""
    ctx = guard_context({
        "class": 5,
        "coord": 1000,
        "extra_key": "extra_value",
        "timestamp": 12345,
    })
    assert ctx["extra_key"] == "extra_value"
    assert ctx["timestamp"] == 12345
    assert ctx["anchor"] == 0
    assert ctx["v_bits"] == 1000
