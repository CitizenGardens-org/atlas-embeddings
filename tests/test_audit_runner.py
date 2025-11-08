"""Tests for audit_runner module."""
import pytest
import json
import tempfile
from pathlib import Path
from audit_runner import audit, load_toml, load_ledger


def test_audit_basic():
    """Test audit with basic ledger."""
    ledger = [
        {
            "kind": "ace_step",
            "status": "committed",
            "entry_id": "ace_1",
            "context": {"class": 0, "anchor": 0},
        },
        {
            "kind": "petc",
            "context": {"ace": "ace_1"},
        },
    ]
    
    schedule = {"schedule": {"window_size": 768}}
    bundle = {
        "policy": {"class_skew_tolerance": 1, "anchor_skew_tolerance": 1},
        "intervals": {"audit_every": 768},
        "indexing": {"classes": 96, "anchors": 6},
    }
    
    report = audit(ledger, schedule, bundle)
    assert report["total_steps"] == 1
    assert report["missing_petc"] == []


def test_audit_missing_petc():
    """Test audit detects missing PETC."""
    ledger = [
        {
            "kind": "ace_step",
            "status": "committed",
            "entry_id": "ace_1",
            "context": {"class": 0, "anchor": 0},
        },
        # No PETC entry
    ]
    
    schedule = {}
    bundle = {
        "policy": {"class_skew_tolerance": 1, "anchor_skew_tolerance": 1},
        "intervals": {"audit_every": 768},
        "indexing": {"classes": 96, "anchors": 6},
    }
    
    report = audit(ledger, schedule, bundle)
    assert report["total_steps"] == 1
    assert "ace_1" in report["missing_petc"]


def test_audit_fairness_classes():
    """Test audit detects class unfairness."""
    # Create 100 steps all in class 0
    ledger = [
        {
            "kind": "ace_step",
            "status": "committed",
            "entry_id": f"ace_{i}",
            "context": {"class": 0, "anchor": 0},
        }
        for i in range(100)
    ]
    
    schedule = {}
    bundle = {
        "policy": {"class_skew_tolerance": 1, "anchor_skew_tolerance": 1},
        "intervals": {"audit_every": 768},
        "indexing": {"classes": 96, "anchors": 6},
    }
    
    report = audit(ledger, schedule, bundle)
    assert report["total_steps"] == 100
    assert not report["fair_classes_ok"]
    assert len(report["bad_classes"]) > 0


def test_audit_fairness_anchors():
    """Test audit detects anchor unfairness."""
    # Create 100 steps all with anchor 0
    ledger = [
        {
            "kind": "ace_step",
            "status": "committed",
            "entry_id": f"ace_{i}",
            "context": {"class": i % 96, "anchor": 0},
        }
        for i in range(100)
    ]
    
    schedule = {}
    bundle = {
        "policy": {"class_skew_tolerance": 10, "anchor_skew_tolerance": 1},
        "intervals": {"audit_every": 768},
        "indexing": {"classes": 96, "anchors": 6},
    }
    
    report = audit(ledger, schedule, bundle)
    assert report["total_steps"] == 100
    assert not report["fair_anchors_ok"]
    assert len(report["bad_anchors"]) > 0


def test_audit_interval_compliance():
    """Test audit checks audit interval presence."""
    ledger = []
    for i in range(1000):
        ledger.append({
            "kind": "ace_step",
            "status": "committed",
            "entry_id": f"ace_{i}",
            "context": {"class": i % 96, "anchor": i % 6},
        })
    
    # Add audit entries at correct intervals
    ledger.append({"kind": "audit", "t": 768})
    
    schedule = {}
    bundle = {
        "policy": {"class_skew_tolerance": 20, "anchor_skew_tolerance": 20},
        "intervals": {"audit_every": 768},
        "indexing": {"classes": 96, "anchors": 6},
    }
    
    report = audit(ledger, schedule, bundle)
    assert report["total_steps"] == 1000
    assert report["audit_entries"] == 1
    assert report["audit_ok"]


def test_load_ledger_list():
    """Test load_ledger with list format."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([{"kind": "test"}], f)
        temp_path = f.name
    
    try:
        ledger = load_ledger(temp_path)
        assert len(ledger) == 1
        assert ledger[0]["kind"] == "test"
    finally:
        Path(temp_path).unlink()


def test_load_ledger_dict():
    """Test load_ledger with dict format."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"entries": [{"kind": "test"}]}, f)
        temp_path = f.name
    
    try:
        ledger = load_ledger(temp_path)
        assert len(ledger) == 1
        assert ledger[0]["kind"] == "test"
    finally:
        Path(temp_path).unlink()


def test_load_toml_file():
    """Test load_toml with a basic TOML file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write('[test]\nvalue = 42\n')
        temp_path = f.name
    
    try:
        data = load_toml(temp_path)
        assert data["test"]["value"] == 42
    finally:
        Path(temp_path).unlink()
