#!/usr/bin/env python3
"""Integration example demonstrating the lattice guard and audit workflow.

This script shows how to:
1. Generate a subgroup certificate
2. Use lattice_guard to validate step contexts
3. Create a simple ledger
4. Audit the ledger for fairness
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from boundary_lattice import save_certificate
from lattice_guard import guard_context
from audit_runner import audit


def main():
    print("=== Lattice Guard and Audit Integration Example ===\n")
    
    # Step 1: Generate subgroup certificate
    print("1. Generating subgroup certificate...")
    save_certificate("subgroup_certificate.json")
    print("   ✓ Created subgroup_certificate.json\n")
    
    # Step 2: Demonstrate context guarding
    print("2. Validating and enriching step contexts...")
    
    # Example with coord
    ctx1 = {"class": 5, "coord": 1000}
    enriched1 = guard_context(ctx1)
    print(f"   Input:  {ctx1}")
    print(f"   Output: {enriched1}")
    
    # Example with anchor/v_bits
    ctx2 = {"class": 10, "anchor": 3, "v_bits": 500}
    enriched2 = guard_context(ctx2)
    print(f"   Input:  {ctx2}")
    print(f"   Output: {enriched2}\n")
    
    # Step 3: Create a sample ledger
    print("3. Creating sample ledger...")
    ledger = []
    
    # Simulate 100 ACE steps with PETC entries
    for i in range(100):
        # ACE step
        ace_entry = {
            "kind": "ace_step",
            "status": "committed",
            "entry_id": f"ace_{i}",
            "t": i,
            "context": {
                "class": i % 96,
                "anchor": i % 6,
                "coord": (i * 123) % 12288,
            }
        }
        ledger.append(ace_entry)
        
        # Corresponding PETC
        petc_entry = {
            "kind": "petc",
            "entry_id": f"petc_{i}",
            "context": {"ace": f"ace_{i}"}
        }
        ledger.append(petc_entry)
    
    # Add audit entries at intervals
    ledger.append({"kind": "audit", "t": 768})
    
    print(f"   ✓ Created ledger with {len(ledger)} entries\n")
    
    # Step 4: Audit the ledger
    print("4. Running audit...")
    schedule = {"schedule": {"window_size": 768}}
    bundle = {
        "policy": {"class_skew_tolerance": 5, "anchor_skew_tolerance": 5},
        "intervals": {"audit_every": 768},
        "indexing": {"classes": 96, "anchors": 6},
    }
    
    report = audit(ledger, schedule, bundle)
    
    print(f"   Total steps: {report['total_steps']}")
    print(f"   Fair classes: {'✓' if report['fair_classes_ok'] else '✗'}")
    print(f"   Fair anchors: {'✓' if report['fair_anchors_ok'] else '✗'}")
    print(f"   Missing PETC: {len(report['missing_petc'])}")
    print(f"   Audit compliance: {'✓' if report['audit_ok'] else '✗'}\n")
    
    # Print distribution
    print("5. Class distribution (first 10 classes):")
    for i in range(min(10, 96)):
        count = report['by_class'].get(str(i), 0)
        print(f"   Class {i:2d}: {count:3d} steps")
    
    print("\n6. Anchor distribution:")
    for i in range(6):
        count = report['by_anchor'].get(str(i), 0)
        print(f"   Anchor {i}: {count:3d} steps")
    
    print("\n=== Integration example complete ===")


if __name__ == "__main__":
    main()
