#!/usr/bin/env python3
"""Check the WOLS JSON-LD context against the conformance vectors and example records.

Every embedded-format label in the vectors and every document in examples/records/
must expand with context/v1.jsonld without losing a member, and compact back to the
document it started from. The context URL is resolved to the local file, so this
runs offline.

Needs PyLD 2.0 or later:  python3 -m pip install PyLD
"""

import copy
import json
import pathlib
import sys

from pyld import jsonld

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONTEXT_URL = "https://wemush.com/wols/v1"
CONTEXT_DOC = json.loads((ROOT / "context" / "v1.jsonld").read_text())


def loader(url, options=None):
    if url.rstrip("/") != CONTEXT_URL:
        raise jsonld.JsonLdError(f"unexpected remote document: {url}", "jsonld.LoadDocumentError")
    return {"contextUrl": None, "documentUrl": url, "document": CONTEXT_DOC}


OPTS = {"documentLoader": loader}


def labels(obj):
    """Yield every JSON object that carries the WOLS context."""
    if isinstance(obj, dict):
        if obj.get("@context") == CONTEXT_URL:
            yield obj
            return
        for value in obj.values():
            yield from labels(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from labels(value)
    elif isinstance(obj, str) and obj.lstrip().startswith("{") and CONTEXT_URL in obj:
        try:
            yield from labels(json.loads(obj))
        except json.JSONDecodeError:
            pass


def normalize(doc):
    """Compare documents the way compaction writes them.

    Compaction writes one-element arrays as plain values, and it drops a nested
    "@context" that repeats the one already in scope, so both are ignored here.
    """
    if isinstance(doc, dict):
        return {k: normalize(v) for k, v in doc.items() if not (k == "@context" and v == CONTEXT_URL)}
    if isinstance(doc, list):
        return normalize(doc[0]) if len(doc) == 1 else [normalize(v) for v in doc]
    return doc


def check(doc, where):
    expanded = jsonld.expand(copy.deepcopy(doc), OPTS)
    if not expanded:
        return f"{where}: expanded to nothing"
    compacted = jsonld.compact(expanded, CONTEXT_URL, OPTS)
    compacted["@context"] = CONTEXT_URL
    if normalize(compacted) != normalize(doc):
        return f"{where}: did not round-trip"
    return None


def main():
    sources = sorted((ROOT / "conformance" / "vectors").glob("*.json"))
    sources += sorted((ROOT / "examples" / "records").glob("*.json"))
    failures, count = [], 0
    for path in sources:
        data = json.loads(path.read_text())
        for i, doc in enumerate(labels(data)):
            count += 1
            problem = check(doc, f"{path.relative_to(ROOT)} #{i}")
            if problem:
                failures.append(problem)
    for problem in failures:
        print("FAIL", problem)
    print(f"{count} documents checked, {len(failures)} failed")
    if count == 0:
        print("FAIL no documents found")
        return 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
