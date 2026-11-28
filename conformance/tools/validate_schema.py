#!/usr/bin/env python3
"""Check the 1.5 JSON Schemas against the conformance vectors and examples.

The schemas are normative from 1.5.0-rc.1 (SPECIFICATION.md, Schema and Data
Model). This tool enforces the sync rule: every `validate` and
`validateBundle` vector gets the same verdict and the same error field from
the schema plus the few rules JSON Schema can't express. Needs `jsonschema`
(>=4.18).
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
VECTOR_FILES = ["embedded.json", "generation.json", "data-model.json", "bundle.json"]
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


def error_path(e) -> str:
    """Dot path of an error, naming the missing member for `required`."""
    parts = [str(p) for p in e.absolute_path]
    if e.validator == "required":
        parts.append(e.message.split("'")[1])
    return ".".join(parts)


def first_error_path(errors) -> str:
    e = min(errors, key=lambda e: len(e.absolute_path))
    return error_path(e)


def label_rules(label: dict, prefix: str = "") -> list[tuple[str, str]]:
    """Label rules JSON Schema can't express, as (error field, message)."""
    problems = []
    st = label.get("strain")
    parents = label.get("derivedFrom")
    if isinstance(st, dict) and isinstance(parents, list) and parents and isinstance(parents[0], dict):
        if "lineage" in st and st["lineage"] != parents[0].get("id"):
            problems.append((f"{prefix}strain.lineage", "strain.lineage must equal derivedFrom[0].id"))
    return problems


def check_vectors(label_v, bundle_v) -> int:
    failures = 0
    for name in VECTOR_FILES:
        for case in load(ROOT / "conformance" / "vectors" / name)["cases"]:
            op = case["operation"]
            if op == "roundtrip":
                # The expected output must itself be a valid label.
                out = case["expected"]["output"]
                ok = not list(label_v.iter_errors(out)) and not label_rules(out)
                status = "ok  " if ok else "FAIL"
                failures += not ok
                print(f"{status} {name}:{case['id']} (roundtrip output valid)")
                continue
            if op == "validate":
                errors = [error_path(e) for e in label_v.iter_errors(case["input"])]
                rules = label_rules(case["input"])
            elif op == "validateBundle":
                errors = [error_path(e) for e in bundle_v.iter_errors(case["input"])]
                rules = semantic_checks(case["input"]) if not errors else []
            else:
                continue
            fields = errors + [f for f, _ in rules]
            want = case["expected"]["valid"]
            got = not fields
            ok = got == want
            if ok and not want:
                field = min(errors, key=lambda f: f.count(".")) if errors else fields[0]
                ok = field == case["expected"]["errorField"]
            status = "ok  " if ok else "FAIL"
            failures += not ok
            print(f"{status} {name}:{case['id']} (valid={want})")
    return failures


def semantic_checks(bundle: dict) -> list[tuple[str, str]]:
    """Bundle rules JSON Schema can't express, as (error field, message)."""
    problems = []
    ids = {s["id"] for s in bundle.get("specimens", [])}
    strains = {s["id"] for s in bundle.get("strains", [])}
    recipes = {r["id"] for r in bundle.get("recipes", [])}
    for i, s in enumerate(bundle.get("specimens", [])):
        problems += label_rules(s, f"specimens.{i}.")
        st = s.get("strain", {})
        for j, p in enumerate(s.get("derivedFrom", [])):
            if p["id"] not in ids:
                problems.append((f"specimens.{i}.derivedFrom.{j}.id", f"{s['id']}: parent {p['id']} not in bundle"))
        if "transferDepth" in st and "clonalGeneration" in st and st["transferDepth"] < st["clonalGeneration"]:
            print(f"warn {s['id']}: transferDepth below clonalGeneration")
        if s.get("strainRef") and s["strainRef"] not in strains:
            problems.append((f"specimens.{i}.strainRef", f"{s['id']}: strainRef {s['strainRef']} not in bundle"))
        if s.get("recipeRef") and s["recipeRef"] not in recipes:
            problems.append((f"specimens.{i}.recipeRef", f"{s['id']}: recipeRef {s['recipeRef']} not in bundle"))
    for kind in ("observations", "harvests"):
        for i, rec in enumerate(bundle.get(kind, [])):
            if rec["specimen"] not in ids:
                problems.append((f"{kind}.{i}.specimen", f"{rec['id']}: specimen {rec['specimen']} not in bundle"))
    return problems


def main() -> int:
    label_v, bundle_v = validators()
    failures = check_vectors(label_v, bundle_v)
    for path in EXAMPLES:
        doc = load(path)
        errors = sorted(bundle_v.iter_errors(doc), key=lambda e: list(e.absolute_path))
        for e in errors:
            print(f"FAIL {path.name}: {'/'.join(map(str, e.absolute_path))}: {e.message}")
        problems = semantic_checks(doc)
        for _, p in problems:
            print(f"FAIL {path.name}: {p}")
        failures += len(errors) + len(problems)
        if not errors and not problems:
            print(f"ok   {path.name}")
    print("all checks passed" if not failures else f"{failures} check(s) failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
