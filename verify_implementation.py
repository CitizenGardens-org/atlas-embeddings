#!/usr/bin/env python3
"""Verification script to ensure all lattice guard components work together."""

import sys
from pathlib import Path

def verify_imports():
    """Verify all modules can be imported."""
    print("1. Verifying imports...")
    try:
        import boundary_lattice
        import lattice_guard
        import audit_runner
        print("   ✓ All modules import successfully")
        return True
    except ImportError as e:
        print(f"   ✗ Import error: {e}")
        return False

def verify_boundary_lattice():
    """Verify boundary_lattice functionality."""
    print("\n2. Verifying boundary_lattice...")
    from boundary_lattice import lin_index, inv_lin_index, boundary_fold_48x256, boundary_unfold_48x256
    
    # Test round-trip
    for a in range(6):
        for v in [0, 100, 2047]:
            idx = lin_index(a, v)
            a2, v2 = inv_lin_index(idx)
            if (a, v) != (a2, v2):
                print(f"   ✗ Round-trip failed: {a},{v} -> {idx} -> {a2},{v2}")
                return False
            
            r, c = boundary_fold_48x256(idx)
            idx2 = boundary_unfold_48x256(r, c)
            if idx != idx2:
                print(f"   ✗ Fold/unfold failed: {idx} -> {r},{c} -> {idx2}")
                return False
    
    print("   ✓ All round-trips verified")
    return True

def verify_lattice_guard():
    """Verify lattice_guard functionality."""
    print("\n3. Verifying lattice_guard...")
    from lattice_guard import guard_context, encode, decode
    
    # Test with coord
    ctx1 = guard_context({"class": 5, "coord": 1000})
    if not all(k in ctx1 for k in ["anchor", "v_bits", "row", "col"]):
        print("   ✗ guard_context missing keys")
        return False
    
    # Test with anchor/v_bits
    ctx2 = guard_context({"class": 10, "anchor": 3, "v_bits": 500})
    if ctx2["coord"] != encode(10, 3, 500):
        print("   ✗ encode/decode mismatch")
        return False
    
    print("   ✓ Context guarding works correctly")
    return True

def verify_certificate():
    """Verify certificate generation."""
    print("\n4. Verifying certificate generation...")
    from boundary_lattice import save_certificate
    import json
    
    cert_path = Path("test_verify_cert.json")
    try:
        save_certificate(str(cert_path))
        
        if not cert_path.exists():
            print("   ✗ Certificate file not created")
            return False
        
        with open(cert_path) as f:
            cert = json.load(f)
        
        if cert["type"] != "Z2_11_subgroup_certificate":
            print("   ✗ Invalid certificate type")
            return False
        
        if cert["lattice"]["classes"] != 96:
            print("   ✗ Invalid lattice classes")
            return False
        
        print("   ✓ Certificate generation successful")
        return True
    finally:
        if cert_path.exists():
            cert_path.unlink()

def verify_audit():
    """Verify audit functionality."""
    print("\n5. Verifying audit functionality...")
    from audit_runner import audit
    
    ledger = [
        {"kind": "ace_step", "status": "committed", "entry_id": "ace_1",
         "context": {"class": 0, "anchor": 0}},
        {"kind": "petc", "context": {"ace": "ace_1"}},
    ]
    
    schedule = {}
    bundle = {
        "policy": {"class_skew_tolerance": 1, "anchor_skew_tolerance": 1},
        "intervals": {"audit_every": 768},
        "indexing": {"classes": 96, "anchors": 6},
    }
    
    report = audit(ledger, schedule, bundle)
    
    if report["total_steps"] != 1:
        print("   ✗ Incorrect step count")
        return False
    
    if len(report["missing_petc"]) != 0:
        print("   ✗ False missing PETC")
        return False
    
    print("   ✓ Audit functionality works correctly")
    return True

def verify_tests():
    """Verify tests pass."""
    print("\n6. Running tests...")
    import subprocess
    result = subprocess.run(
        ["python3", "-m", "pytest", 
         "tests/test_boundary_lattice.py",
         "tests/test_lattice_guard.py",
         "tests/test_audit_runner.py",
         "-q", "--tb=no"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("   ✓ All tests pass")
        return True
    else:
        print("   ✗ Some tests failed")
        print(result.stdout)
        return False

def main():
    print("=" * 60)
    print("Lattice Guard Implementation Verification")
    print("=" * 60)
    
    checks = [
        verify_imports,
        verify_boundary_lattice,
        verify_lattice_guard,
        verify_certificate,
        verify_audit,
        verify_tests,
    ]
    
    results = [check() for check in checks]
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ ALL VERIFICATIONS PASSED")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME VERIFICATIONS FAILED")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
