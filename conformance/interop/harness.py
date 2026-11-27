"""WOLS cross-library round-trip harness (Python side).

Generates a corpus of encrypted labels from ``matrix.json`` with the installed
``wols`` package, and verifies a corpus produced by any implementation
(normally ``@wemush/wols``) by decrypting it with the installed ``wols``.

Usage::

    python harness.py generate matrix.json corpus.json
    python harness.py verify matrix.json corpus.json

``verify`` exits non-zero if any case fails, or if a case listed in the
matrix's ``expectedFailures`` unexpectedly passes.

The canonical copy is ``conformance/interop/`` in the WOLS specification
repository. wemush/specimen-labels-py and wemush/specimen-labels-js carry
byte-identical copies in ``tests/interop/``. It uses only the public ``wols``
API, so it also runs against a published release.
"""

from __future__ import annotations

import base64
import copy
import dataclasses
import hashlib
import json
import re
import sys
import traceback
import unicodedata
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import unquote_to_bytes

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import wols
from wols import Specimen
from wols.crypto import (
    decrypt_specimen,
    decrypt_specimen_bytes,
    decrypt_specimen_fields,
    encrypt_specimen,
    encrypt_specimen_fields,
    parse_encrypted_url,
)
from wols.exceptions import WolsEncryptionError

DECODER = "python"
IDENTIFYING = ("@context", "@type", "id", "version", "type", "species")

# RFC 3986 pchar minus pct-encoded: unreserved / sub-delims / ":" / "@".
_PCHAR_RE = re.compile(r"(?:[A-Za-z0-9\-._~!$&'()*+,;=:@]|%[0-9A-Fa-f]{2})*")
# Characters a generator MUST percent-encode (SPECIFICATION.md 1.3.0).
_MUST_ENCODE_RE = re.compile(r"[%/?# +\x00-\x1f\x7f]|[^\x00-\x7f]")
_B64URL_RE = re.compile(r"[A-Za-z0-9_-]*")
# Query parameters of the encrypted URL (SPECIFICATION.md, Wire format).
_URL_PARAMS = frozenset({"e", "iv", "kdf", "salt", "i", "sig"})
# Spaces, controls and non-ASCII characters must be percent-encoded.
_PRINTABLE_ASCII_RE = re.compile(r"[\x21-\x7e]*")
_BAD_ESCAPE_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")


class CheckError(AssertionError):
    """A case did not meet an interop or wire-format requirement."""


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise CheckError(message)


# WOLS 1.5 draft: `_meta` keys are camelCase on the wire, and decoders SHOULD
# accept snake_case and re-emit camelCase. So a `_meta` written either way is
# the same value: comparisons read the snake_case standard keys as camelCase.
_META_WIRE_KEYS = {
    "source_id": "sourceId",
    "imported_at": "importedAt",
    "source_system": "sourceSystem",
    "schema_version": "schemaVersion",
}


def _wire_meta(meta: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in meta.items():
        wire = _META_WIRE_KEYS.get(key)
        if wire is None:
            out[key] = value
        elif wire not in meta:
            out[wire] = value
    return out


def _with_wire_meta(value: Any) -> Any:
    if isinstance(value, dict) and isinstance(value.get("_meta"), dict):
        return {**value, "_meta": _wire_meta(value["_meta"])}
    return value


def _canonical(value: Any) -> str:
    # Type-strict comparison: True != 1 and 1 != 1.0 once serialized.
    return json.dumps(
        _with_wire_meta(value),
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    )


def _same_doc(actual: Any, expected: dict[str, Any]) -> bool:
    return isinstance(actual, dict) and _canonical(actual) == _canonical(expected)


def _b64url(value: str) -> bytes:
    pad = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + pad)


def _canonical_b64url(name: str, value: object) -> bytes:
    _check(isinstance(value, str), f"{name} must be a string")
    assert isinstance(value, str)
    _check(
        bool(_B64URL_RE.fullmatch(value)), f"{name} must be base64url without padding"
    )
    raw = _b64url(value)
    _check(
        base64.urlsafe_b64encode(raw).rstrip(b"=").decode() == value,
        f"{name} is not canonical base64url (non-zero trailing bits)",
    )
    return raw


def _percent_decode(name: str, value: str) -> str:
    """Strict UTF-8 percent-decoding; '+' is literal."""
    try:
        _check(not _BAD_ESCAPE_RE.search(value), "malformed escape")
        return unquote_to_bytes(value).decode("utf-8")
    except (CheckError, UnicodeDecodeError):
        raise CheckError(
            f"{name} {value!r} is not valid UTF-8 percent-encoding"
        ) from None


def load_json(path: str | Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def matrix_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expected_document(
    matrix: dict[str, Any], case: dict[str, Any], name: str | None = None
) -> dict[str, Any]:
    """``specimens[name]`` with ``id`` set to ``specimenId``.

    ``name`` defaults to the case's input ``specimen``.
    """
    template = matrix["specimens"][name if name is not None else case["specimen"]]
    doc: dict[str, Any] = {}
    for key, value in template.items():
        doc[key] = copy.deepcopy(value)
        if key == "@type":
            doc["id"] = case["specimenId"]
    doc.setdefault("id", case["specimenId"])
    return doc


@dataclasses.dataclass(frozen=True)
class _Expected:
    """What a decoder must return, and the legacy input a 1.3.0 generator wrote."""

    document: dict[str, Any]
    legacy: dict[str, Any] | None


def _expectations(matrix: dict[str, Any], case: dict[str, Any]) -> _Expected:
    document = expected_document(
        matrix, case, case.get("expectSpecimen", case["specimen"])
    )
    legacy = expected_document(matrix, case) if case.get("legacyPlaintext") else None
    return _Expected(document, legacy)


_NO_LEGACY = object()


def _match_written(value: Any, expected: Any, legacy: Any = _NO_LEGACY) -> str | None:
    """Match a written value against the expected one, then the legacy one."""
    if _canonical(value) == _canonical(expected):
        return "current"
    if legacy is not _NO_LEGACY and _canonical(value) == _canonical(legacy):
        return "legacy"
    return None


def _secret(case: dict[str, Any], passphrase: str | None = None) -> str | bytes:
    if case["kdf"] == "raw":
        return _b64url(case["key"])
    return passphrase if passphrase is not None else case["passphrase"]


def _iteration_kwargs(case: dict[str, Any]) -> dict[str, int]:
    return {"iterations": case["iterations"]} if "iterations" in case else {}


# =============================================================================
# GENERATE
# =============================================================================


def generate_case(matrix: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    doc = expected_document(matrix, case)
    secret = _secret(case)
    if case["form"] == "url":
        url = encrypt_specimen(
            Specimen.from_dict(doc), secret, **_iteration_kwargs(case)
        )
        if "sig" in case:
            label = parse_encrypted_url(url)
            url = dataclasses.replace(label, signature=case["sig"]).to_url()
        return {"url": url}
    if case["form"] == "fields":
        document = encrypt_specimen_fields(
            doc, secret, list(case["fields"]), **_iteration_kwargs(case)
        )
        return {"document": document}
    raise ValueError(f"unknown form {case['form']!r}")


def generate(matrix: dict[str, Any], matrix_hash: str) -> dict[str, Any]:
    return {
        "corpusVersion": 1,
        "matrixVersion": matrix["matrixVersion"],
        "matrixSha256": matrix_hash,
        "generator": {
            "implementation": "wols",
            "language": "python",
            "version": getattr(wols, "__version__", "unknown"),
        },
        "cases": {case["id"]: generate_case(matrix, case) for case in matrix["cases"]},
    }


# =============================================================================
# VERIFY
# =============================================================================


def _check_url_wire(case: dict[str, Any], url: str) -> None:
    """Generator-side wire rules, checked on the raw URL text."""
    prefix = "wemush://v1/encrypted/"
    _check(url.startswith(prefix), f"URL must start with {prefix}")
    rest = url[len(prefix) :]
    _check("#" not in rest, "URL must not contain a fragment")
    segment, sep, query = rest.partition("?")
    _check(sep == "?", "URL has no query")
    _check(
        bool(_PCHAR_RE.fullmatch(segment)),
        f"ID path segment {segment!r} is not a valid RFC 3986 segment",
    )
    unescaped = re.sub(r"%[0-9A-Fa-f]{2}", "", segment)
    _check(
        not _MUST_ENCODE_RE.search(unescaped),
        f"ID path segment {segment!r} leaves a character unencoded that MUST be encoded",
    )
    suffix = case["specimenId"][len("wemush:") :]
    _check(
        _percent_decode("ID path segment", segment) == suffix,
        f"ID path segment {segment!r} does not percent-decode to {suffix!r}",
    )
    if "expectPathSegment" in case:
        _check(
            segment == case["expectPathSegment"],
            f"ID path segment {segment!r} != expected {case['expectPathSegment']!r}",
        )
    _check(
        bool(_PRINTABLE_ASCII_RE.fullmatch(query)),
        "URL query must be printable ASCII "
        "(spaces, controls and non-ASCII must be percent-encoded)",
    )

    params: dict[str, str] = {}
    for pair in query.split("&"):
        key, _, value = pair.partition("=")
        _check(key in _URL_PARAMS, f"unknown parameter {key!r}")
        _check(key not in params, f"duplicate parameter {key!r}")
        params[key] = value
    _check(params.get("kdf") == case["kdf"], f"kdf must be {case['kdf']}")
    _check(
        len(_canonical_b64url("e", params.get("e"))) >= 16, "e is shorter than the tag"
    )
    _check(len(_canonical_b64url("iv", params.get("iv"))) == 12, "iv must be 12 bytes")
    _check_kdf_params(case, params.get("salt"), params.get("i"), "salt", "i")
    if "sig" in case:
        _check("sig" in params, "sig parameter missing")
        # The raw query value, percent-decoded ('+' literal), must be the input.
        sig = _percent_decode("sig", params["sig"])
        _check(
            sig == case["sig"],
            f"sig parameter {params['sig']!r} decodes to {sig!r}, "
            f"expected {case['sig']!r}",
        )
    else:
        _check("sig" not in params, "unexpected sig parameter")


def _check_kdf_params(
    case: dict[str, Any], salt: object, iterations: object, salt_name: str, i_name: str
) -> None:
    if case["kdf"] == "pbkdf2":
        _check(len(_canonical_b64url(salt_name, salt)) >= 16, "salt under 16 bytes")
        if isinstance(iterations, str):
            _check(
                bool(re.fullmatch(r"[1-9][0-9]*", iterations)),
                f"{i_name} {iterations!r} must be decimal digits without a leading zero",
            )
            iterations = int(iterations)
        _check(
            type(iterations) is int and iterations == case["expectIterations"],
            f"{i_name} is {iterations!r}, expected {case['expectIterations']}",
        )
    else:
        _check(salt is None, f"{salt_name} must be omitted for kdf=raw")
        _check(iterations is None, f"{i_name} must be omitted for kdf=raw")


def _expect_auth_failure(fn: Callable[[], Any], what: str) -> None:
    try:
        fn()
    except WolsEncryptionError as e:
        _check(
            e.code == "AUTHENTICATION_FAILED",
            f"{what}: expected AUTHENTICATION_FAILED, got {e.code}",
        )
        return
    raise CheckError(f"{what}: decryption unexpectedly succeeded")


def verify_url(case: dict[str, Any], exp: _Expected, url: object) -> bool:
    """Verify a URL case; return whether the label carried legacy plaintext."""
    expected = exp.document
    _check(isinstance(url, str), "corpus entry has no url")
    assert isinstance(url, str)
    _check_url_wire(case, url)

    label = parse_encrypted_url(url)
    _check(label.specimen_id == case["specimenId"], f"parsed id {label.specimen_id!r}")
    _check(label.payload.kdf == case["kdf"], "parsed kdf differs")
    _check(
        label.signature == case.get("sig"),
        f"sig not preserved: got {label.signature!r}, expected {case.get('sig')!r}",
    )
    if case["kdf"] == "pbkdf2":
        _check(label.payload.iterations == case["expectIterations"], "iterations")

    passphrases = case.get("decryptPassphrases", [None])
    written: str | None = None
    legacy = exp.legacy if exp.legacy is not None else _NO_LEGACY
    for passphrase in passphrases:
        secret = _secret(case, passphrase)
        plaintext = decrypt_specimen_bytes(url, secret)
        document = json.loads(plaintext.decode("utf-8"))
        written = (
            _match_written(document, expected, legacy)
            if isinstance(document, dict)
            else None
        )
        _check(
            written is not None,
            f"decrypted document differs (passphrase={passphrase!r}): "
            f"{plaintext.decode('utf-8')}",
        )
    specimen = decrypt_specimen(url, _secret(case, passphrases[0]))
    _check(specimen.id == case["specimenId"], "decrypt_specimen id differs")
    _check(specimen.species == expected["species"], "decrypt_specimen species differs")
    expected_strain = expected.get("strain")
    if isinstance(expected_strain, dict) and "generation" in expected_strain:
        generation = getattr(specimen.strain, "generation", None)
        _check(
            generation == expected_strain["generation"]
            and type(generation) is type(expected_strain["generation"]),
            f"decrypt_specimen strain.generation is {generation!r}, "
            f"expected {expected_strain['generation']!r}",
        )

    for wrong in case.get("rejectPassphrases", []):
        _expect_auth_failure(
            lambda w=wrong: decrypt_specimen_bytes(url, w), f"passphrase {wrong!r}"
        )
    return written == "legacy"


def verify_fields(case: dict[str, Any], exp: _Expected, doc: object) -> bool:
    """Verify a fields case; return whether the label carried legacy values."""
    expected = exp.document
    _check(isinstance(doc, dict), "corpus entry has no document")
    assert isinstance(doc, dict)
    fields = list(case["fields"])
    _check(set(doc) == set(expected), f"document keys differ: {sorted(doc)}")
    saw_legacy = False

    def written(value: Any, key: str, what: str) -> None:
        nonlocal saw_legacy
        legacy = (
            exp.legacy.get(key, _NO_LEGACY) if exp.legacy is not None else _NO_LEGACY
        )
        if key == "_meta":
            value, want = {"_meta": value}, {"_meta": expected[key]}
            if legacy is not _NO_LEGACY:
                legacy = {"_meta": legacy}
        else:
            want = expected[key]
        match = _match_written(value, want, legacy)
        _check(match is not None, what)
        saw_legacy = saw_legacy or match == "legacy"

    ivs: set[str] = set()
    salts: set[object] = set()
    for key in expected:
        if key not in fields:
            written(doc[key], key, f"cleartext field {key!r} changed")
            continue
        _check(key not in IDENTIFYING, f"identifying field {key!r} encrypted")
        obj = doc[key]
        _check(isinstance(obj, dict), f"field {key!r} is not an encryption object")
        _check(obj.get("encrypted") is True, f"{key}.encrypted must be true")
        _check(obj.get("algorithm") == "AES-256-GCM", f"{key}.algorithm")
        _check(obj.get("kdf") == case["kdf"], f"{key}.kdf must be {case['kdf']}")
        _check(
            len(_canonical_b64url(f"{key}.payload", obj.get("payload"))) >= 16, "tag"
        )
        _check(len(_canonical_b64url(f"{key}.iv", obj.get("iv"))) == 12, "iv length")
        _check(obj["iv"] not in ivs, f"{key}.iv reused across fields")
        ivs.add(obj["iv"])
        _check_kdf_params(
            case,
            obj.get("salt"),
            obj.get("iterations"),
            f"{key}.salt",
            f"{key}.iterations",
        )
        salts.add(obj.get("salt"))
        allowed = {
            "encrypted",
            "algorithm",
            "payload",
            "iv",
            "kdf",
            "salt",
            "iterations",
        }
        _check(
            set(obj) <= allowed, f"{key} has unexpected members {set(obj) - allowed}"
        )

    for passphrase in case.get("decryptPassphrases", [None]):
        # decrypt_specimen_fields restores the whole label, which must equal
        # expectSpecimen even when the label carries legacy values ...
        restored = decrypt_specimen_fields(doc, _secret(case, passphrase))
        _check(
            _same_doc(restored, expected),
            f"restored document differs (passphrase={passphrase!r}): {restored}",
        )
        # ... and each field must hold exactly what the generator encrypted.
        for field in fields:
            value = _decrypt_field_value(case, doc[field], doc["id"], field, passphrase)
            written(value, field, f"decrypted field {field!r} differs: {value!r}")
    for wrong in case.get("rejectPassphrases", []):
        _expect_auth_failure(
            lambda w=wrong: decrypt_specimen_fields(doc, w), f"passphrase {wrong!r}"
        )
    return saw_legacy


def _decrypt_field_value(
    case: dict[str, Any],
    obj: dict[str, Any],
    label_id: str,
    field: str,
    passphrase: str | None,
) -> Any:
    """Decrypt one field object without wols, to see the value as written.

    ``wols`` has no public single-field decrypt, and its label decrypt reads a
    legacy integer ``strain.generation`` as a string, so the harness opens the
    field itself: AES-256-GCM with AAD ``{id}\\n{field}`` (WOLS 1.3.0).
    """
    if case["kdf"] == "raw":
        key = _b64url(case["key"])
    else:
        secret = passphrase if passphrase is not None else case["passphrase"]
        key = hashlib.pbkdf2_hmac(
            "sha256",
            unicodedata.normalize("NFC", secret).encode("utf-8"),
            _b64url(obj["salt"]),
            int(obj["iterations"]),
            32,
        )
    try:
        plaintext = AESGCM(key).decrypt(
            _b64url(obj["iv"]),
            _b64url(obj["payload"]),
            f"{label_id}\n{field}".encode(),
        )
    except InvalidTag:
        raise CheckError(
            f"field {field!r} does not decrypt with AAD id/field"
        ) from None
    return json.loads(plaintext.decode("utf-8"))


@dataclasses.dataclass
class CaseResult:
    case_id: str
    status: str  # "pass", "fail", "xfail", "xpass"
    detail: str = ""
    # A legacyPlaintext case whose label carried the input unchanged (as a
    # 1.3.0 generator wrote it) and decoded to expectSpecimen.
    legacy: bool = False


def _expected_failure(
    matrix: dict[str, Any], case_id: str, generator: str
) -> dict[str, Any] | None:
    for entry in matrix.get("expectedFailures", []):
        if (
            entry["case"] == case_id
            and entry.get("generator", generator) == generator
            and entry.get("decoder", DECODER) == DECODER
        ):
            return dict(entry)
    return None


def verify(matrix: dict[str, Any], corpus: dict[str, Any]) -> list[CaseResult]:
    generator = corpus["generator"]["language"]
    results: list[CaseResult] = []
    for case in matrix["cases"]:
        entry = corpus["cases"].get(case["id"])
        legacy = False
        try:
            _check(entry is not None, "case missing from corpus")
            assert entry is not None
            exp = _expectations(matrix, case)
            if case["form"] == "url":
                legacy = verify_url(case, exp, entry.get("url"))
            else:
                legacy = verify_fields(case, exp, entry.get("document"))
            ok, detail = True, ""
        except Exception as e:
            ok, legacy = False, False
            detail = (
                f"{type(e).__name__}: {e}"
                if isinstance(e, CheckError | WolsEncryptionError)
                else traceback.format_exc()
            )
        xfail = _expected_failure(matrix, case["id"], generator)
        if xfail is None:
            status = "pass" if ok else "fail"
        else:
            status = "xpass" if ok else "xfail"
            if ok:
                detail = f"listed in expectedFailures but passed: {xfail.get('reason')}"
            else:
                detail = f"{xfail.get('reason')} ({xfail.get('reference')}): {detail}"
        if legacy and status == "pass":
            detail = (
                "legacy plaintext (the input unchanged, as 1.3.0 wrote it) "
                "decoded to expectSpecimen"
            )
        results.append(CaseResult(case["id"], status, detail, legacy))
    return results


def _summary(corpus: dict[str, Any], results: list[CaseResult]) -> int:
    gen = corpus["generator"]
    print(
        f"interop: {gen['implementation']} {gen['version']} ({gen['language']}) -> "
        f"wols {getattr(wols, '__version__', 'unknown')} (python)"
    )
    for r in results:
        line = f"  {r.status.upper():5} {r.case_id}"
        show = r.status != "pass" or r.legacy
        print(line + (f"\n        {r.detail}" if show else ""))
    bad = [r for r in results if r.status in ("fail", "xpass")]
    counts = {
        s: sum(r.status == s for r in results)
        for s in ("pass", "fail", "xfail", "xpass")
    }
    counts["legacy"] = sum(r.legacy for r in results)
    print(
        f"interop: {len(results)} cases: "
        + ", ".join(f"{v} {k}" for k, v in counts.items())
    )
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if len(argv) != 4 or argv[1] not in ("generate", "verify"):
        print(__doc__, file=sys.stderr)
        return 2
    command, matrix_path, corpus_path = argv[1:]
    matrix = load_json(matrix_path)
    if command == "generate":
        corpus = generate(matrix, matrix_sha256(matrix_path))
        with open(corpus_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(corpus, f, indent=2, ensure_ascii=True)
            f.write("\n")
        print(f"interop: wrote {len(corpus['cases'])} cases to {corpus_path}")
        return 0
    corpus = load_json(corpus_path)
    return _summary(corpus, verify(matrix, corpus))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
