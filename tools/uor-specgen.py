#!/usr/bin/env python3
"""Deterministic code generation from specification invariants."""
import argparse
import os
from typing import Dict, Iterable, List, Tuple

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - runtime fallback when PyYAML missing
    yaml = None

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVARIANTS_PATH = os.path.join(SRC, "docs", "specs", "v2", "invariants.yaml")
LEAN_OUTPUT_DIR = os.path.join(SRC, "docs", "proofs", "lean")
CODEGEN_MAP_PATH = os.path.join(SRC, "schemas", "codegen.map.yaml")


def _load_yaml(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as handle:
        if yaml is not None:
            return yaml.safe_load(handle)
        return _fallback_yaml_parse(handle.read().splitlines())


def _fallback_yaml_parse(lines: Iterable[str]) -> Dict:
    invariants: List[Dict[str, str]] = []
    current: Dict[str, str] | None = None
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- id:"):
            if current:
                invariants.append(current)
            current = {"id": stripped.split(":", 1)[1].strip()}
        elif ":" in stripped and current is not None:
            key, value = stripped.split(":", 1)
            current[key.strip()] = value.strip()
    if current:
        invariants.append(current)
    return {"invariants": invariants}


def _sanitize_id(identifier: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in identifier)


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def _generate_lean_stubs(invariants: Iterable[Dict[str, str]]) -> None:
    for invariant in sorted(invariants, key=lambda entry: entry["id"]):
        stub = invariant.get("proof_stub")
        if not stub:
            continue
        output_path = os.path.join(LEAN_OUTPUT_DIR, stub)
        name = _sanitize_id(invariant["id"])
        body = (
            "import Mathlib\n\n"
            f"theorem {name} : True := by\n"
            f"  -- auto-generated stub for {invariant['id']}\n"
            "  trivial\n"
        )
        _write(output_path, body)


def _generate_api_stubs(mapping: Dict) -> None:
    spec_to_api: List[Tuple[str, str]] = sorted(mapping.get("spec_to_api", {}).items(), key=lambda item: item[0])
    for spec_id, location in spec_to_api:
        file_path, signature = location.split("::", 1)
        abs_path = os.path.join(SRC, file_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        signature = signature.strip().removeprefix("fn ")
        function_name = signature.split("(")[0].split()[-1]
        content = (
            f"// auto-generated from spec {spec_id}\n"
            f"pub fn {signature} {{\n"
            f"    unimplemented!(\"spec binding {function_name}\");\n"
            "}\n"
        )
        _write(abs_path, content)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deterministic", action="store_true", help="no-op flag kept for compatibility")
    _ = parser.parse_args()

    invariants = _load_yaml(INVARIANTS_PATH).get("invariants", [])
    _generate_lean_stubs(invariants)

    if os.path.exists(CODEGEN_MAP_PATH):
        mapping = _load_yaml(CODEGEN_MAP_PATH)
        _generate_api_stubs(mapping)

    print("uor-specgen: OK")


if __name__ == "__main__":
    main()
