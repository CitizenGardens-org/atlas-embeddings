"""Audit Runner - Fairness and compliance checker for Atlas scheduling.

Validates:
- Fairness across classes and anchors (within tolerance)
- PETC presence per accepted ACE step
- Audit interval compliance

Usage:
    python audit_runner.py --schedule atlas_schedule.toml --bundle audit_bundle.toml --ledger ledger.json
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from typing import Dict, List, Any


def load_toml(path: str) -> Dict[str, Any]:
    """Load TOML configuration file."""
    try:
        import tomli
    except ImportError:
        # Fallback for Python 3.11+
        try:
            import tomllib as tomli
        except ImportError:
            raise ImportError("Please install tomli for Python < 3.11: pip install tomli")
    
    with open(path, "rb") as f:
        return tomli.load(f)


def load_ledger(path: str) -> List[Dict[str, Any]]:
    """Load ledger from JSON file."""
    with open(path, "r") as f:
        data = json.load(f)
    # Expect either a list of entries or a dict with "entries" key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "entries" in data:
        return data["entries"]
    else:
        raise ValueError("Ledger must be a JSON list or dict with 'entries' key")


def audit(ledger: List[Dict[str, Any]], schedule: Dict[str, Any], bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Audit ledger against schedule and bundle policies.
    
    Args:
        ledger: List of ledger entries
        schedule: Schedule configuration
        bundle: Audit bundle policy
    
    Returns:
        Audit report dictionary
    """
    entries = ledger
    
    # Extract policy parameters
    policy = bundle.get("policy", {})
    class_tol = policy.get("class_skew_tolerance", 1)
    anchor_tol = policy.get("anchor_skew_tolerance", 1)
    
    intervals_cfg = bundle.get("intervals", {})
    audit_every = intervals_cfg.get("audit_every", 768)
    
    indexing = bundle.get("indexing", {})
    num_classes = indexing.get("classes", 96)
    num_anchors = indexing.get("anchors", 6)
    
    # Track step counts
    by_class: Dict[int, int] = defaultdict(int)
    by_anchor: Dict[int, int] = defaultdict(int)
    n = 0  # Total committed steps
    
    # Track PETC presence
    ace_to_petc: Dict[str, int] = defaultdict(int)
    
    # Process entries
    for e in entries:
        kind = e.get("kind")
        status = e.get("status")
        
        # Count committed ace_step entries
        if kind == "ace_step" and status == "committed":
            n += 1
            ctx = e.get("context", {})
            # Count by class
            if "class" in ctx:
                c = int(ctx["class"])
                by_class[c] += 1
            # Count by anchor
            if "anchor" in ctx:
                a = int(ctx["anchor"])
                by_anchor[a] += 1
        
        # Track PETC entries referencing ACE steps
        if kind == "petc":
            ctx = e.get("context", {})
            ref = ctx.get("ace")
            if ref:
                ace_to_petc[ref] += 1
    
    # Check fairness
    if n > 0:
        avg_per_class = n / num_classes
        avg_per_anchor = n / num_anchors
    else:
        avg_per_class = 0
        avg_per_anchor = 0
    
    bad_classes = []
    for c in range(num_classes):
        count = by_class.get(c, 0)
        if abs(count - avg_per_class) > class_tol:
            bad_classes.append({"class": c, "count": count, "expected": avg_per_class})
    
    bad_anchors = []
    for a in range(num_anchors):
        count = by_anchor.get(a, 0)
        if abs(count - avg_per_anchor) > anchor_tol:
            bad_anchors.append({"anchor": a, "count": count, "expected": avg_per_anchor})
    
    # Check missing PETC
    missing_petc = []
    for e in entries:
        if e.get("kind") == "ace_step" and e.get("status") == "committed":
            eid = e.get("entry_id")
            if eid and ace_to_petc.get(eid, 0) == 0:
                missing_petc.append(eid)
    
    # Audit interval presence
    audit_hits = [e for e in entries if e.get("kind") == "audit"]
    audit_ok = True
    if audit_every:
        seen = set([x.get("t") for x in audit_hits if "t" in x])
        # check latest step produces integer multiples up to n
        for k in range(audit_every, n + 1, audit_every):
            if k not in seen:
                audit_ok = False
                break
    
    return {
        "total_steps": n,
        "by_class": dict(by_class),
        "by_anchor": dict(by_anchor),
        "fair_classes_ok": len(bad_classes) == 0,
        "fair_anchors_ok": len(bad_anchors) == 0,
        "bad_classes": bad_classes,
        "bad_anchors": bad_anchors,
        "missing_petc": missing_petc,
        "audit_entries": len(audit_hits),
        "audit_ok": audit_ok,
    }


def main() -> None:
    """Main entry point."""
    ap = argparse.ArgumentParser(description="Audit Atlas scheduling fairness and compliance")
    ap.add_argument("--schedule", default="atlas_schedule.toml", help="Schedule configuration file")
    ap.add_argument("--bundle", default="audit_bundle.toml", help="Audit bundle policy file")
    ap.add_argument("--ledger", required=True, help="Ledger JSON file")
    args = ap.parse_args()
    
    sched = load_toml(args.schedule)
    bund = load_toml(args.bundle)
    ledg = load_ledger(args.ledger)
    
    report = audit(ledg, sched, bund)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
