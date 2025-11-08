# Lattice Guard and Audit System

This directory contains the lattice guard and audit infrastructure for the Atlas 96×12,288 boundary lattice.

## Components

### Core Modules

#### `boundary_lattice.py`
Foundation module providing canonical indexing for the 96-class × 12,288-coordinate lattice.

**Key Functions:**
- `lin_index(anchor, v_bits)` - Encode (anchor, v_bits) to linear coordinate index
- `inv_lin_index(coord_idx)` - Decode coordinate index to (anchor, v_bits)
- `boundary_fold_48x256(coord_idx)` - Fold linear coordinate into 48×256 grid
- `boundary_unfold_48x256(row, col)` - Unfold grid position to linear coordinate
- `save_certificate(filename)` - Generate (Z/2)^11 subgroup certificate

**Constants:**
- `CLASSES = 96` (Atlas vertices)
- `ANCHORS = 6` (per class)
- `ORBIT = 2048` (2^11 Gray-coded orbit per anchor)
- `COORDS_PER_CLASS = 12288` (ANCHORS × ORBIT)

#### `lattice_guard.py`
Context validation and enrichment for scheduling steps.

**Key Functions:**
- `verify_address(class_id, coord_idx)` - Validate lattice address ranges
- `decode(class_id, coord_idx)` - Full decode to `Decoded` object
- `encode(class_id, anchor, v_bits)` - Encode to coordinate index
- `guard_context(ctx)` - Validate and enrich step contexts

**Usage:**
```python
from lattice_guard import guard_context

# With linear coordinate
ctx = guard_context({"class": 5, "coord": 1000})
# Returns: {'class': 5, 'coord': 1000, 'anchor': 0, 'v_bits': 1000, 'row': 3, 'col': 232}

# With anchor and v_bits
ctx = guard_context({"class": 10, "anchor": 3, "v_bits": 500})
# Returns: {'class': 10, 'anchor': 3, 'v_bits': 500, 'coord': 6644, 'row': 25, 'col': 244}
```

### Scripts

#### `certify_subgroup.py`
Generate and persist the (Z/2)^11 subgroup certificate.

**Usage:**
```bash
python certify_subgroup.py
# Writes: subgroup_certificate.json
```

The certificate documents:
- Lattice dimensions and parameters
- (Z/2)^11 subgroup structure (11 generators, order 2048)
- Anchor coordinates
- Sample orbit verification data
- Blake2b checksum for integrity

#### `audit_runner.py`
Fairness and compliance checker for scheduling ledgers.

**Usage:**
```bash
python audit_runner.py \
  --schedule atlas_schedule.toml \
  --bundle audit_bundle.toml \
  --ledger ledger.json
```

**Checks:**
- **Fairness**: Class and anchor distributions within tolerance
- **PETC presence**: Each committed ACE step has corresponding PETC
- **Audit intervals**: Audit entries at required frequencies

**Output:** JSON report with:
- Total steps
- Distribution by class and anchor
- Fairness status
- Missing PETC entries
- Audit compliance

### Configuration

#### `atlas_schedule.toml`
Schedule configuration for C768 fair traversal.

Parameters:
- Window size: 768 steps
- Total windows: 16 (covering all 12,288 cells)
- Round-robin scheduling across classes and anchors
- Audit interval: 768 steps

#### `audit_bundle.toml`
Audit policy configuration.

Parameters:
- `class_skew_tolerance = 1` - Maximum class distribution skew
- `anchor_skew_tolerance = 1` - Maximum anchor distribution skew
- `audit_every = 768` - Audit entry frequency in steps
- `per_step = ["ace_step", "petc"]` - Required entry kinds per step

## Integration

### Step Context Workflow

1. **Before scheduling/logging**, guard and enrich contexts:
```python
from lattice_guard import guard_context

raw_ctx = {"class": 5, "coord": 777}
enriched_ctx = guard_context(raw_ctx)
# Use enriched_ctx which now includes anchor, v_bits, row, col
```

2. **Schedule ACE steps** using your scheduler (e.g., `atlas12288.schedule.C768Schedule`)

3. **Log entries** to your ledger with enriched contexts

4. **Audit the run**:
```bash
# Export ledger to JSON
python -c "import json; json.dump(ledger.entries, open('ledger.json', 'w'))"

# Run audit
python audit_runner.py --ledger ledger.json
```

## Testing

Run tests:
```bash
pytest tests/test_boundary_lattice.py -v
pytest tests/test_lattice_guard.py -v
pytest tests/test_audit_runner.py -v
```

Run integration demo:
```bash
python examples/lattice_guard_demo.py
```

## Mathematical Foundation

### Lattice Structure
The boundary lattice is organized as:
- **96 classes** (Atlas vertices)
- Each class contains **12,288 coordinates**
- Coordinates are structured as **6 anchors × 2048 orbit points**
- The 2048-point orbit is encoded via 11-bit Gray code
- Anchors are located at `(8m, 0)` for m = 0..5 in ℤ/48 × ℤ/256

### (Z/2)^11 Symmetry
The subgroup acts via bit flips:
- **8 generators** flip bits of the byte component b ∈ ℤ/256
- **3 generators** flip low 3 bits of the p2 component in ℤ/48 = ℤ/16 × ℤ/3
- All generators commute and square to identity
- Total order: 2^11 = 2048

### Folding into 48×256 Grid
Coordinates are folded row-major:
```
row = coord_idx // 256  (0..47)
col = coord_idx % 256   (0..255)
```

This creates a rectangular layout compatible with the ℤ/48 × ℤ/256 product structure.

## Limitations

### Subgroup Certificate
- **Constructive verification** only - checksumed but not cryptographically signed
- **UNPROVEN** as formal proof object
- Suitable for computational verification, not cryptographic evidence

### Auditor
- **Pragmatic checks** - fairness, required entries, intervals
- Does **NOT** verify:
  - Full liveness properties
  - Byzantine behavior
  - Cryptographic commitments
  - State consistency beyond fairness

### Schedule Constraints
The current C768 schedule achieves:
- ✓ Uniform page marginals (16 per 768-step window)
- ✗ Uniform byte marginals (inherent constraint)
- ✗ Perfect bijection (9,228 distinct cells vs. 12,288 target)

See `atlas12288/README.md` for details on schedule limitations.

## See Also

- `atlas12288/` - Boundary complex implementation
- `multiplicity_core/` - ACE and PETC runtime
- `examples/lattice_guard_demo.py` - Integration example
