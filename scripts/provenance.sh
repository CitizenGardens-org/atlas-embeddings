#!/usr/bin/env bash
set -euo pipefail
# Placeholder provenance creation and attestation
mkdir -p dist
echo '{}' > dist/provenance.json
cosign attest --predicate dist/provenance.json --type slsaprovenance --yes ${IMAGE_DIGEST:-""} || true
