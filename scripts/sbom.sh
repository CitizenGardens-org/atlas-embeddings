#!/usr/bin/env bash
set -euo pipefail
mkdir -p dist
syft dir:. -o spdx-json > dist/sbom.spdx.json
grype sbom:dist/sbom.spdx.json -o json > dist/vuln.json
