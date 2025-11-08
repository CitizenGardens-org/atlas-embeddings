"""Tests for boundary_lattice module."""
import pytest
from boundary_lattice import (
    CLASSES, ANCHORS, ORBIT, COORDS_PER_CLASS,
    lin_index, inv_lin_index, boundary_fold_48x256, boundary_unfold_48x256,
    save_certificate,
)
import os
import json


def test_constants():
    """Test lattice constants."""
    assert CLASSES == 96
    assert ANCHORS == 6
    assert ORBIT == 2048
    assert COORDS_PER_CLASS == 12288
    assert COORDS_PER_CLASS == ANCHORS * ORBIT


def test_lin_index_basic():
    """Test lin_index for basic cases."""
    assert lin_index(0, 0) == 0
    assert lin_index(0, 1) == 1
    assert lin_index(1, 0) == 2048
    assert lin_index(5, 2047) == 12287


def test_lin_index_invalid():
    """Test lin_index with invalid inputs."""
    with pytest.raises(ValueError):
        lin_index(-1, 0)
    with pytest.raises(ValueError):
        lin_index(6, 0)
    with pytest.raises(ValueError):
        lin_index(0, -1)
    with pytest.raises(ValueError):
        lin_index(0, 2048)


def test_inv_lin_index_basic():
    """Test inv_lin_index for basic cases."""
    assert inv_lin_index(0) == (0, 0)
    assert inv_lin_index(1) == (0, 1)
    assert inv_lin_index(2048) == (1, 0)
    assert inv_lin_index(12287) == (5, 2047)


def test_inv_lin_index_invalid():
    """Test inv_lin_index with invalid inputs."""
    with pytest.raises(ValueError):
        inv_lin_index(-1)
    with pytest.raises(ValueError):
        inv_lin_index(12288)


def test_lin_index_roundtrip():
    """Test lin_index and inv_lin_index round-trip."""
    for a in range(ANCHORS):
        for v in [0, 1, 100, 500, 1000, 2047]:
            idx = lin_index(a, v)
            a2, v2 = inv_lin_index(idx)
            assert (a, v) == (a2, v2)


def test_boundary_fold_basic():
    """Test boundary_fold_48x256 for basic cases."""
    assert boundary_fold_48x256(0) == (0, 0)
    assert boundary_fold_48x256(255) == (0, 255)
    assert boundary_fold_48x256(256) == (1, 0)
    assert boundary_fold_48x256(12287) == (47, 255)


def test_boundary_fold_invalid():
    """Test boundary_fold_48x256 with invalid inputs."""
    with pytest.raises(ValueError):
        boundary_fold_48x256(-1)
    with pytest.raises(ValueError):
        boundary_fold_48x256(12288)


def test_boundary_unfold_basic():
    """Test boundary_unfold_48x256 for basic cases."""
    assert boundary_unfold_48x256(0, 0) == 0
    assert boundary_unfold_48x256(0, 255) == 255
    assert boundary_unfold_48x256(1, 0) == 256
    assert boundary_unfold_48x256(47, 255) == 12287


def test_boundary_unfold_invalid():
    """Test boundary_unfold_48x256 with invalid inputs."""
    with pytest.raises(ValueError):
        boundary_unfold_48x256(-1, 0)
    with pytest.raises(ValueError):
        boundary_unfold_48x256(48, 0)
    with pytest.raises(ValueError):
        boundary_unfold_48x256(0, -1)
    with pytest.raises(ValueError):
        boundary_unfold_48x256(0, 256)


def test_fold_unfold_roundtrip():
    """Test fold/unfold round-trip."""
    for idx in [0, 1, 255, 256, 1000, 5000, 12287]:
        r, c = boundary_fold_48x256(idx)
        idx2 = boundary_unfold_48x256(r, c)
        assert idx == idx2


def test_save_certificate(tmp_path):
    """Test certificate generation."""
    cert_file = tmp_path / "test_cert.json"
    save_certificate(str(cert_file))
    
    assert cert_file.exists()
    
    with open(cert_file) as f:
        cert = json.load(f)
    
    # Check structure
    assert cert["type"] == "Z2_11_subgroup_certificate"
    assert cert["version"] == "1.0"
    assert "lattice" in cert
    assert "subgroup" in cert
    assert "anchors" in cert
    assert "checksum" in cert
    
    # Check lattice info
    assert cert["lattice"]["classes"] == 96
    assert len(cert["lattice"]["anchors_per_class"]) == 6
    assert cert["lattice"]["orbit_size"] == 2048
    assert cert["lattice"]["coords_per_class"] == 12288
    
    # Check subgroup info
    assert cert["subgroup"]["order"] == 2048
    assert cert["subgroup"]["rank"] == 11
    assert len(cert["subgroup"]["generators"]) == 11
