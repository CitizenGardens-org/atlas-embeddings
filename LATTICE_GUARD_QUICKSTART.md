# Lattice Guard Quick Start

## Installation

No additional dependencies beyond the project requirements:
```bash
pip install -r requirements.txt
```

The implementation uses:
- Standard library modules (json, hashlib, dataclasses)
- atlas12288 (already in project)
- tomli (for TOML parsing on Python < 3.11)

## Quick Examples

### 1. Generate Subgroup Certificate

```bash
python certify_subgroup.py
```

Output: `subgroup_certificate.json` with (Z/2)^11 structure documentation.

### 2. Guard and Enrich Step Contexts

```python
from lattice_guard import guard_context

# Example 1: Starting with linear coordinate
ctx1 = {"class": 5, "coord": 1000}
enriched1 = guard_context(ctx1)
print(enriched1)
# Output: {'class': 5, 'coord': 1000, 'anchor': 0, 'v_bits': 1000, 'row': 3, 'col': 232}

# Example 2: Starting with anchor and v_bits
ctx2 = {"class": 10, "anchor": 3, "v_bits": 500}
enriched2 = guard_context(ctx2)
print(enriched2)
# Output: {'class': 10, 'anchor': 3, 'v_bits': 500, 'coord': 6644, 'row': 25, 'col': 244}
```

### 3. Audit a Ledger

First, create or export your ledger to JSON:

```python
import json
from multiplicity_core.ledger import Ledger

# Export existing ledger
ledger = Ledger()
# ... add entries ...
with open('ledger.json', 'w') as f:
    json.dump(ledger.entries, f)
```

Then audit it:

```bash
python audit_runner.py \
    --schedule atlas_schedule.toml \
    --bundle audit_bundle.toml \
    --ledger ledger.json
```

Output: JSON report with fairness analysis and compliance status.

### 4. Run Integration Demo

```bash
python examples/lattice_guard_demo.py
```

This demonstrates the complete workflow:
1. Certificate generation
2. Context guarding
3. Ledger creation
4. Audit execution

## API Reference

### boundary_lattice module

```python
from boundary_lattice import (
    CLASSES, ANCHORS, ORBIT, COORDS_PER_CLASS,
    lin_index, inv_lin_index,
    boundary_fold_48x256, boundary_unfold_48x256,
    save_certificate
)

# Linear indexing
coord = lin_index(anchor=3, v_bits=500)  # Returns: 6644
a, v = inv_lin_index(coord)              # Returns: (3, 500)

# Grid folding
row, col = boundary_fold_48x256(coord)   # Returns: (25, 244)
coord2 = boundary_unfold_48x256(row, col) # Returns: 6644

# Certificate
save_certificate("subgroup_certificate.json")
```

### lattice_guard module

```python
from lattice_guard import (
    Decoded, verify_address, decode, encode, guard_context
)

# Address validation
verify_address(class_id=5, coord_idx=1000)  # Raises ValueError if invalid

# Decoding
d = decode(class_id=5, coord_idx=1000)
# Returns: Decoded(class_id=5, coord_idx=1000, anchor=0, v_bits=1000, row=3, col=232)

# Encoding
coord = encode(class_id=5, anchor=0, v_bits=1000)  # Returns: 1000

# Context guarding (primary API)
enriched = guard_context({"class": 5, "coord": 1000})
```

### audit_runner module

```python
from audit_runner import audit, load_toml, load_ledger

# Load configuration
schedule = load_toml("atlas_schedule.toml")
bundle = load_toml("audit_bundle.toml")
ledger = load_ledger("ledger.json")

# Run audit
report = audit(ledger, schedule, bundle)

# Check results
print(f"Fair classes: {report['fair_classes_ok']}")
print(f"Fair anchors: {report['fair_anchors_ok']}")
print(f"Missing PETC: {len(report['missing_petc'])}")
```

## Common Patterns

### Pattern 1: Schedule with Context Guard

```python
from atlas12288 import C768Schedule
from lattice_guard import guard_context

schedule = C768Schedule()

for t in range(768):
    p, b = schedule.at(t)
    # Convert to lattice coordinates
    ctx = guard_context({
        "class": p % 96,  # Map page to class
        "coord": (p * 256 + b) % 12288  # Combine p,b into coord
    })
    # Now ctx has anchor, v_bits, row, col
    process_step(ctx)
```

### Pattern 2: Ledger with Audit

```python
from multiplicity_core.ledger import Ledger
from lattice_guard import guard_context
import json

# Build ledger
ledger = Ledger()

for i in range(100):
    ctx = guard_context({"class": i % 96, "coord": (i * 123) % 12288})
    
    # Add ACE step
    ledger.append({
        "kind": "ace_step",
        "status": "committed",
        "context": ctx,
        "t": i
    })
    
    # Add PETC
    ledger.append({
        "kind": "petc",
        "context": {"ace": f"ace_{i}"}
    })

# Export and audit
with open("run_ledger.json", "w") as f:
    json.dump(ledger.entries, f)

# Then: python audit_runner.py --ledger run_ledger.json
```

## Testing

Run all lattice guard tests:
```bash
pytest tests/test_boundary_lattice.py tests/test_lattice_guard.py tests/test_audit_runner.py -v
```

Run a specific test:
```bash
pytest tests/test_lattice_guard.py::test_guard_context_with_coord -v
```

## Troubleshooting

**Q: ImportError: No module named 'tomli'**
A: Install tomli: `pip install tomli`

**Q: ValueError: class_id out of range**
A: Classes must be in [0, 96). Check your class_id values.

**Q: ValueError: coord_idx out of range**
A: Coordinates must be in [0, 12288). Check your coord_idx values.

**Q: Audit reports unfairness**
A: This is expected if your schedule doesn't distribute evenly. Adjust tolerances in audit_bundle.toml or improve scheduling.

**Q: Certificate checksum mismatch**
A: The certificate is regenerated each time. Checksums will differ if the input data (anchors, Gray code) changes.

## Next Steps

- See `LATTICE_GUARD_README.md` for comprehensive documentation
- See `IMPLEMENTATION_SUMMARY.txt` for implementation details
- See `atlas12288/README.md` for boundary complex background
- Run `examples/lattice_guard_demo.py` for a complete workflow example
