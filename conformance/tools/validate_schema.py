#!/usr/bin/env python3
"""Check the draft 1.5 JSON Schemas against the conformance vectors and examples.

Draft tooling for proposals/wols-1.5-data-model.md. Needs `jsonschema` (>=4.18).
Run from the repository root:  python3 conformance/tools/validate_schema.py
Exit status is non-zero if any check fails.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schema" / "1.5"
VECTOR_FILES = ["embedded.json", "generation.json"]
EXAMPLES = sorted((ROOT / "examples" / "records").glob("*.json"))


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


FORMATS = FormatChecker()


@FORMATS.checks("date-time", raises=ValueError)
def _date_time(value) -> bool:
    # RFC 3339 needs a time zone. Registered here so the check works without
    # the optional rfc3339-validator package.
    if not isinstance(value, str):
        return True
    if "T" not in value.upper() or not (value.endswith(("Z", "z")) or value[-6] in "+-"):
        raise ValueError("not an RFC 3339 date-time with offset")
    datetime.fromisoformat(value.replace("z", "Z").replace("Z", "+00:00"))
    return True


@FORMATS.checks("date", raises=ValueError)
def _date(value) -> bool:
    if isinstance(value, str):
        date.fromisoformat(value)
    return True


def validators():
    label = load(SCHEMA_DIR / "label.schema.json")
    bundle = load(SCHEMA_DIR / "bundle.schema.json")
    registry = Registry().with_resources(
        [(s["$id"], Resource.from_contents(s)) for s in (label, bundle)]
    )
    for s in (label, bundle):
        Draft202012Validator.check_schema(s)
    fc = FORMATS
    return (
        Draft202012Validator(label, registry=registry, format_checker=fc),
        Draft202012Validator(bundle, registry=registry, format_checker=fc),
    )


def first_error_path(errors) -> str:
    e = min(errors, key=lambda e: len(e.absolute_path))
    path = ".".join(str(p) for p in e.absolute_path)
    if not path and e.validator == "required":
        path = e.message.split("'")[1]
    return path


def check_vectors(label_v) -> int:
    failures = 0
    for name in VECTOR_FILES:
        for case in load(ROOT / "conformance" / "vectors" / name)["cases"]:
            if case["operation"] != "validate":
                continue
            errors = list(label_v.iter_errors(case["input"]))
            want = case["expected"]["valid"]
            got = not errors
            ok = got == want
            if ok and not want:
                field = first_error_path(errors)
                ok = field == case["expected"]["errorField"]
            status = "ok  " if ok else "FAIL"
            failures += not ok
            print(f"{status} {name}:{case['id']} (valid={want})")
    return failures


def semantic_checks(bundle: dict) -> list[str]:
    """Rules JSON Schema can't express."""
    problems = []
    ids = {s["id"] for s in bundle.get("specimens", [])}
    strains = {s["id"] for s in bundle.get("strains", [])}
    recipes = {r["id"] for r in bundle.get("recipes", [])}
    for s in bundle.get("specimens", []):
        st = s.get("strain", {})
        parents = s.get("derivedFrom", [])
        if st.get("lineage") and parents and st["lineage"] != parents[0]["id"]:
            problems.append(f"{s['id']}: strain.lineage must equal derivedFrom[0].id")
        for p in parents:
            if p["id"] not in ids:
                problems.append(f"{s['id']}: parent {p['id']} not in bundle")
        if "transferDepth" in st and "clonalGeneration" in st and st["transferDepth"] < st["clonalGeneration"]:
            print(f"warn {s['id']}: transferDepth below clonalGeneration")
        if s.get("strainRef") and s["strainRef"] not in strains:
            problems.append(f"{s['id']}: strainRef {s['strainRef']} not in bundle")
        if s.get("recipeRef") and s["recipeRef"] not in recipes:
            problems.append(f"{s['id']}: recipeRef {s['recipeRef']} not in bundle")
    for rec in bundle.get("observations", []) + bundle.get("harvests", []):
        if rec["specimen"] not in ids:
            problems.append(f"{rec['id']}: specimen {rec['specimen']} not in bundle")
    return problems


def main() -> int:
    label_v, bundle_v = validators()
    failures = check_vectors(label_v)
    for path in EXAMPLES:
        doc = load(path)
        errors = sorted(bundle_v.iter_errors(doc), key=lambda e: list(e.absolute_path))
        for e in errors:
            print(f"FAIL {path.name}: {'/'.join(map(str, e.absolute_path))}: {e.message}")
        problems = semantic_checks(doc)
        for p in problems:
            print(f"FAIL {path.name}: {p}")
        failures += len(errors) + len(problems)
        if not errors and not problems:
            print(f"ok   {path.name}")
    print("all checks passed" if not failures else f"{failures} check(s) failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
