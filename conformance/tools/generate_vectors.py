#!/usr/bin/env python3
"""Generate WOLS conformance test vectors.

Usage:
    pip install "cryptography>=42"
    python conformance/tools/generate_vectors.py

Writes JSON files to conformance/vectors/. Output is deterministic: the
encrypted vectors use FIXED salts and IVs so results are reproducible.
Real generators MUST use fresh random salts and IVs (SPECIFICATION.md,
Encrypted Format). The signature vectors use Ed25519 test keys derived from
fixed strings and published in signatures.json; never use them for real labels.
"""

from __future__ import annotations

import base64
import hashlib
import json
import unicodedata
from urllib.parse import quote
from pathlib import Path

import math
import re

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SPEC_VERSION = "1.3.0"
SIG_SPEC_VERSION = "1.4.0"
CONTEXT = "https://wemush.com/wols/v1"
OUT = Path(__file__).resolve().parent.parent / "vectors"


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_padded(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii")


def specimen(id_: str, **fields: object) -> dict:
    base = {
        "@context": CONTEXT,
        "@type": "Specimen",
        "id": id_,
        "version": SPEC_VERSION,
        "type": "SUBSTRATE",
        "species": "Pleurotus ostreatus",
    }
    base.update(fields)
    return base


def serialize_value(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def serialize(obj: dict) -> str:
    # Compact, key order as given. Vectors carry the exact plaintext string,
    # so consumers never need to reproduce this serialization.
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


def write(name: str, description: str, section: str, cases: list[dict], *,
          version: str = SPEC_VERSION, extra: dict | None = None) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    doc = {
        "wolsVersion": version,
        "description": description,
        "specSection": section,
        **(extra or {}),
        "cases": cases,
    }
    (OUT / name).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Embedded format validation
# ---------------------------------------------------------------------------

def embedded_cases() -> list[dict]:
    ok = lambda cid, desc, obj, req="MUST": {  # noqa: E731
        "id": cid, "operation": "validate", "requirement": req,
        "description": desc, "input": obj, "expected": {"valid": True},
    }
    bad = lambda cid, desc, obj, field: {  # noqa: E731
        "id": cid, "operation": "validate", "requirement": "MUST",
        "description": desc, "input": obj,
        "expected": {"valid": False, "errorField": field},
    }
    return [
        ok("embedded-minimal", "Minimal valid specimen", specimen("wemush:clx1a2b3c4")),
        ok("embedded-full", "Specimen with optional core fields", specimen(
            "wemush:clx1a2b3c4d5e6f7g8",
            strain={"name": "Blue Oyster PoHu", "generation": "F2", "clonalGeneration": 3},
            stage="COLONIZATION", created="2025-12-16T10:30:00Z",
            batch="batch_2025_12_001", organization="org_mushoh")),
        ok("id-ulid-suffix", "ULID suffix MUST be accepted",
           specimen("wemush:01ARZ3NDEKTSV4RRFFQ69G5FAV")),
        ok("id-uuid-suffix", "UUID suffix MUST be accepted",
           specimen("wemush:550e8400-e29b-41d4-a716-446655440000")),
        ok("id-human-readable-suffix", "Any non-empty suffix MUST be accepted",
           specimen("wemush:WM-LC-250114-000001")),
        ok("custom-namespace", "Custom namespaced fields are valid", specimen(
            "wemush:clx1a2b3c4", custom={"acme_labs": {"projectCode": "PROJ-2025-42"}})),
        ok("signed-label-valid",
           "A label carrying a 1.4.0 `signature` validates like any other label: validation "
           "never verifies it (added in 1.4.0-rc.1)",
           sign_embedded_obj(specimen("wemush:clx1a2b3c4"), "mushoh-2026")),
        {
            "id": "unknown-top-level-field", "operation": "validate", "requirement": "SHOULD",
            "description": "Unknown top-level fields do not invalidate a specimen; "
                           "implementations SHOULD warn and recommend `custom`",
            "input": specimen("wemush:clx1a2b3c4", metadata={"note": "x"}),
            "expected": {"valid": True, "warningField": "metadata"},
        },
        bad("id-missing-prefix", "IDs MUST start with `wemush:`",
            specimen("WM-LC-250114-000001"), "id"),
        bad("id-empty-suffix", "The suffix after `wemush:` MUST be non-empty",
            specimen("wemush:"), "id"),
        bad("context-wrong", "`@context` MUST be the WOLS context URL",
            {**specimen("wemush:clx1a2b3c4"), "@context": "https://wols.wemush.com/v1"}, "@context"),
        bad("type-invalid", "`type` MUST be a canonical SpecimenType in serialized labels",
            specimen("wemush:clx1a2b3c4", type="PRIMORDIA"), "type"),
        bad("stage-invalid", "`stage` MUST be a defined GrowthStage",
            specimen("wemush:clx1a2b3c4", stage="PINNING"), "stage"),
        bad("species-missing", "`species` is required",
            {k: v for k, v in specimen("wemush:clx1a2b3c4").items() if k != "species"}, "species"),
    ]


# ---------------------------------------------------------------------------
# PRIMORDIA type handling (specimen creation)
# ---------------------------------------------------------------------------

def primordia_cases() -> list[dict]:
    def case(cid, desc, inp, out_type, out_stage, warn, req="MUST"):
        return {
            "id": cid, "operation": "create", "requirement": req, "description": desc,
            "input": {"species": "Pleurotus ostreatus", **inp},
            "expected": {"type": out_type, "stage": out_stage, "warning": warn},
        }
    return [
        case("primordia-no-stage", "PRIMORDIA as type resolves to FRUITING and sets stage",
             {"type": "PRIMORDIA"}, "FRUITING", "PRIMORDIA", True),
        case("primordia-with-stage", "A supplied stage MUST NOT be overridden",
             {"type": "PRIMORDIA", "stage": "FRUITING"}, "FRUITING", "FRUITING", True),
        case("primordia-lowercase", "Alias resolution is case-insensitive",
             {"type": "primordia"}, "FRUITING", "PRIMORDIA", True),
        case("fruiting-primordia-canonical", "Canonical form produces no warning",
             {"type": "FRUITING", "stage": "PRIMORDIA"}, "FRUITING", "PRIMORDIA", False),
        case("pinning-alias", "Ordinary aliases resolve type only and leave stage unset",
             {"type": "PINNING"}, "FRUITING", None, False, req="SHOULD"),
    ]


# ---------------------------------------------------------------------------
# Generation / clonalGeneration / transferDepth
# ---------------------------------------------------------------------------

def generation_cases() -> list[dict]:
    def case(cid, desc, strain, valid, req="MUST", warn=None):
        exp = {"valid": valid}
        if warn:
            exp["warningField"] = warn
        if not valid:
            exp["errorField"] = warn or "strain"
        return {
            "id": cid, "operation": "validate", "requirement": req, "description": desc,
            "input": specimen("wemush:clx1a2b3c4", strain=strain), "expected": exp,
        }
    return [
        case("transfer-depth-zero", "Original culture has transferDepth 0",
             {"name": "Blue Oyster", "generation": "P", "clonalGeneration": 0, "transferDepth": 0}, True),
        case("transfer-depth-example", "Spec example: F1, third subculture, two expansion transfers",
             {"name": "Blue Oyster", "generation": "F1", "clonalGeneration": 3, "transferDepth": 5}, True),
        {**case("transfer-depth-negative", "transferDepth MUST be a non-negative integer",
                {"name": "Blue Oyster", "transferDepth": -1}, False),
         "expected": {"valid": False, "errorField": "strain.transferDepth"}},
        {**case("transfer-depth-fraction", "transferDepth MUST be an integer",
                {"name": "Blue Oyster", "transferDepth": 1.5}, False),
         "expected": {"valid": False, "errorField": "strain.transferDepth"}},
        {**case("transfer-depth-string", "transferDepth MUST be a number, not a string",
                {"name": "Blue Oyster", "transferDepth": "3"}, False),
         "expected": {"valid": False, "errorField": "strain.transferDepth"}},
        case("transfer-depth-below-clonal",
             "transferDepth SHOULD be >= clonalGeneration; a lower value is valid but warns",
             {"name": "Blue Oyster", "clonalGeneration": 3, "transferDepth": 1}, True,
             req="SHOULD", warn="strain.transferDepth"),
        *[case(f"generation-notation-{g.lower()}", f"Generation notation `{g}` is accepted",
               {"name": "Blue Oyster", "generation": g}, True) for g in ("P", "F1", "G2", "3")],
    ]


# ---------------------------------------------------------------------------
# Encrypted format
# ---------------------------------------------------------------------------

def derive_key(passphrase: str, salt: bytes, iterations: int) -> bytes:
    # Passphrases are normalized to Unicode NFC before UTF-8 encoding.
    data = unicodedata.normalize("NFC", passphrase).encode("utf-8")
    return PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations).derive(data)


def field_aad(id_: str, field: str) -> bytes:
    return f"{id_}\n{field}".encode("utf-8")


def encrypted_cases() -> list[dict]:
    passphrase = "correct horse battery staple"
    salt = bytes(range(16))                     # FIXED for reproducibility only
    iv = bytes(range(100, 112))                 # FIXED for reproducibility only
    iterations = 100_000
    raw_key = bytes(range(200, 232))            # 32 bytes

    spec = specimen("wemush:clx1a2b3c4", strain={"name": "MO-Blue-001", "generation": "F1"},
                    stage="COLONIZATION", created="2025-12-16T10:30:00Z")
    plaintext = serialize(spec)

    def derive(pw: str, s: bytes, n: int) -> bytes:
        return derive_key(pw, s, n)

    pb_key = derive(passphrase, salt, iterations)
    pb_ct = AESGCM(pb_key).encrypt(iv, plaintext.encode(), None)
    def enc_id_ct(full_id: str) -> bytes:
        return AESGCM(pb_key).encrypt(iv, serialize(dict(spec, id=full_id)).encode(), None)

    def ok_for(full_id: str) -> dict:
        sp = dict(spec, id=full_id)
        return {"success": True, "plaintext": serialize(sp), "specimen": sp}

    bom_ct = AESGCM(pb_key).encrypt(iv, b"\xef\xbb\xbf" + plaintext.encode(), None)
    nfc_pass = unicodedata.normalize("NFC", "Pilzzüchter Ångström")
    nfc_ct = AESGCM(derive(nfc_pass, salt, iterations)).encrypt(iv, plaintext.encode(), None)
    raw_ct = AESGCM(raw_key).encrypt(iv, plaintext.encode(), None)

    def url(id_suffix, ct, kdf, s=None, n=None, *, pad=False, sig=None):
        enc = b64url_padded if pad else b64url
        q = f"e={enc(ct)}&iv={enc(iv)}&kdf={kdf}"
        if s is not None:
            q += f"&salt={enc(s)}"
        if n is not None:
            q += f"&i={n}"
        if sig is not None:
            q += f"&sig={sig}"
        return f"wemush://v1/encrypted/{id_suffix}?{q}"

    # `sig` is reserved in 1.3.x: no algorithm is defined, so this is arbitrary bytes that are
    # not a valid signature over anything. Decoders keep it and never verify it.
    reserved_sig = b64url(bytes(range(64)))

    pb_secret = {"kdf": "pbkdf2", "passphrase": passphrase}
    raw_secret = {"kdf": "raw", "keyBase64url": b64url(raw_key)}
    ok = {"success": True, "plaintext": plaintext, "specimen": spec}

    tampered = bytearray(pb_ct)
    tampered[0] ^= 0x01
    low_iter_key = derive(passphrase, salt, 9_999)
    low_iter_ct = AESGCM(low_iter_key).encrypt(iv, plaintext.encode(), None)
    other = specimen("wemush:zzz999", stage="COLONIZATION")
    other_ct = AESGCM(pb_key).encrypt(iv, serialize(other).encode(), None)

    def case(cid, desc, u, secret, expected, req="MUST"):
        return {"id": cid, "operation": "decrypt", "requirement": req, "description": desc,
                "input": {"url": u, "secret": secret}, "expected": expected}

    return [
        {
            "id": "pbkdf2-intermediates", "operation": "derive", "requirement": "MUST",
            "description": "PBKDF2-HMAC-SHA256 key derivation (intermediate value for debugging)",
            "input": {"passphrase": passphrase, "saltBase64url": b64url(salt), "iterations": iterations},
            "expected": {"keyBase64url": b64url(pb_key)},
        },
        case("decrypt-pbkdf2", "Decrypt a passphrase-protected label",
             url("clx1a2b3c4", pb_ct, "pbkdf2", salt, iterations), pb_secret, ok),
        case("decrypt-raw", "Decrypt a raw-key label (no salt or i)",
             url("clx1a2b3c4", raw_ct, "raw"), raw_secret, ok),
        case("decrypt-padded-base64url", "Decoders SHOULD accept padded base64url",
             url("clx1a2b3c4", pb_ct, "pbkdf2", salt, iterations, pad=True), pb_secret, ok, req="SHOULD"),
        case("reject-tampered-ciphertext", "GCM authentication MUST fail on tampered ciphertext",
             url("clx1a2b3c4", bytes(tampered), "pbkdf2", salt, iterations), pb_secret,
             {"success": False, "reason": "authentication-failed"}),
        case("reject-wrong-passphrase", "A wrong passphrase MUST fail authentication",
             url("clx1a2b3c4", pb_ct, "pbkdf2", salt, iterations),
             {"kdf": "pbkdf2", "passphrase": "wrong passphrase"},
             {"success": False, "reason": "authentication-failed"}),
        case("reject-id-mismatch", "Decrypted id MUST equal wemush:{id} from the URL path",
             url("clx1a2b3c4", other_ct, "pbkdf2", salt, iterations), pb_secret,
             {"success": False, "reason": "id-mismatch"}),
        case("reject-low-iterations", "Decoders MUST reject fewer than 10,000 PBKDF2 iterations",
             url("clx1a2b3c4", low_iter_ct, "pbkdf2", salt, 9_999), pb_secret,
             {"success": False, "reason": "insufficient-iterations"}),
        case("reject-pbkdf2-missing-salt", "`salt` is required when kdf=pbkdf2",
             url("clx1a2b3c4", pb_ct, "pbkdf2", None, iterations), pb_secret,
             {"success": False, "reason": "missing-parameter"}),
        case("reject-raw-with-salt", "`salt` and `i` MUST be omitted when kdf=raw",
             url("clx1a2b3c4", raw_ct, "raw", salt, iterations), raw_secret,
             {"success": False, "reason": "unexpected-parameter"}),
        case("reject-unknown-kdf", "Unknown kdf values MUST be rejected",
             url("clx1a2b3c4", pb_ct, "scrypt", salt, iterations), pb_secret,
             {"success": False, "reason": "unsupported-kdf"}),
        case("decrypt-percent-encoded-id",
             "The ID suffix is percent-encoded as one path segment and decoded before the id check",
             url(quote("Lab A/plate+3%", safe=""), enc_id_ct("wemush:Lab A/plate+3%"), "pbkdf2", salt, iterations),
             pb_secret, ok_for("wemush:Lab A/plate+3%")),
        case("decrypt-percent-encoded-utf8-id", "Non-ASCII ID suffixes are percent-encoded UTF-8",
             url(quote("Pilz-ü", safe=""), enc_id_ct("wemush:Pilz-ü"), "pbkdf2", salt, iterations),
             pb_secret, ok_for("wemush:Pilz-ü")),
        case("reject-invalid-percent-encoding", "Decoders MUST reject an ID suffix with invalid percent-encoding",
             url("clx1a2b3c4%zz", pb_ct, "pbkdf2", salt, iterations), pb_secret,
             {"success": False, "reason": "invalid-encoding"}),
        case("reject-percent-encoded-invalid-utf8",
             "Decoders MUST reject a percent-decoded ID suffix that is not valid UTF-8",
             url("clx%C3%28", pb_ct, "pbkdf2", salt, iterations), pb_secret,
             {"success": False, "reason": "invalid-encoding"}),
        case("reject-non-decimal-iterations", "`i` MUST be plain decimal digits",
             url("clx1a2b3c4", pb_ct, "pbkdf2", salt, "1e5"), pb_secret,
             {"success": False, "reason": "invalid-parameter"}),
        case("reject-huge-iterations",
             "Iteration counts beyond any integer type MUST be rejected without deriving a key",
             url("clx1a2b3c4", pb_ct, "pbkdf2", salt, "99999999999999999999"), pb_secret,
             {"success": False, "reason": "excessive-iterations"}),
        case("reject-plaintext-bom", "Decoders SHOULD reject a plaintext that starts with a UTF-8 byte order mark",
             url("clx1a2b3c4", bom_ct, "pbkdf2", salt, iterations), pb_secret,
             {"success": False, "reason": "invalid-plaintext"}, req="SHOULD"),
        case("reject-excessive-iterations",
             "Decoders MUST reject more than 10,000,000 PBKDF2 iterations without deriving a key",
             url("clx1a2b3c4", pb_ct, "pbkdf2", salt, 10_000_001), pb_secret,
             {"success": False, "reason": "excessive-iterations"}),
        {
            "id": "pbkdf2-nfc-normalization", "operation": "derive", "requirement": "MUST",
            "description": "Passphrases are normalized to NFC before derivation: a decomposed (NFD) "
                           "passphrase derives the same key as its composed form",
            "input": {"passphrase": unicodedata.normalize("NFD", nfc_pass),
                      "saltBase64url": b64url(salt), "iterations": iterations},
            "expected": {"keyBase64url": b64url(derive(nfc_pass, salt, iterations))},
        },
        case("decrypt-nfd-passphrase",
             "A label encrypted with an NFC passphrase decrypts with the same passphrase typed in NFD form",
             url("clx1a2b3c4", nfc_ct, "pbkdf2", salt, iterations),
             {"kdf": "pbkdf2", "passphrase": unicodedata.normalize("NFD", nfc_pass)}, ok),
        case("decrypt-with-sig",
             "A reserved `sig` parameter does not affect decryption; decoders MUST preserve it and "
             "MUST NOT treat it as verified (added in 1.3.1-rc.1)",
             url("clx1a2b3c4", pb_ct, "pbkdf2", salt, iterations, sig=reserved_sig), pb_secret,
             {**ok, "sig": reserved_sig, "sigVerified": False}),
        case("decrypt-signed-url",
             "A 1.4.0 signed URL decrypts like any other: decoding never verifies `sig`, keeps it "
             "unchanged, and doesn't report it as verified (added in 1.4.0-rc.1)",
             signed_url_pbkdf2 := sign_url(url("clx1a2b3c4", pb_ct, "pbkdf2", salt, iterations),
                                           "mushoh-2026"),
             pb_secret,
             {**ok, "sig": signed_url_pbkdf2.rsplit("&sig=", 1)[1], "sigVerified": False}),
    ]


def field_cases() -> list[dict]:
    passphrase = "correct horse battery staple"
    salt = bytes(range(16, 32))                 # FIXED for reproducibility only
    iterations = 100_000
    raw_key = bytes(range(200, 232))
    id_ = "wemush:clx1a2b3c4"
    pb_key = derive_key(passphrase, salt, iterations)

    strain = {"name": "MO-Blue-001", "generation": "F1"}
    batch = "batch_2025_12_001"

    def enc(field, value, *, key=pb_key, kdf="pbkdf2", iv_seed=0, aad_id=id_, aad_field=None, n=iterations,
            s=salt):
        iv = bytes((iv_seed + k) % 256 for k in range(12))
        ct = AESGCM(key).encrypt(iv, serialize_value(value).encode(), field_aad(aad_id, aad_field or field))
        obj = {"encrypted": True, "algorithm": "AES-256-GCM", "payload": b64url(ct), "iv": b64url(iv), "kdf": kdf}
        if kdf == "pbkdf2":
            obj["salt"] = b64url(s)
            obj["iterations"] = n
        return obj

    clear = specimen(id_, strain=strain, stage="COLONIZATION", batch=batch)
    pb_secret = {"kdf": "pbkdf2", "passphrase": passphrase}
    raw_secret = {"kdf": "raw", "keyBase64url": b64url(raw_key)}

    def case(cid, desc, label, secret, expected, req="MUST"):
        return {"id": cid, "operation": "decryptFields", "requirement": req, "description": desc,
                "input": {"specimen": label, "secret": secret}, "expected": expected}

    two = specimen(id_, strain=enc("strain", strain, iv_seed=1), stage="COLONIZATION",
                   batch=enc("batch", batch, iv_seed=2))
    swapped = dict(two, strain=two["batch"], batch=two["strain"])
    moved = specimen(id_, strain=enc("strain", strain, iv_seed=3, aad_id="wemush:zzz999"),
                     stage="COLONIZATION", batch=batch)
    ident = specimen(id_, strain=strain, stage="COLONIZATION", batch=batch)
    ident["species"] = enc("species", "Pleurotus ostreatus", iv_seed=4)
    costly = specimen(id_, strain=enc("strain", strain, iv_seed=5, n=6_000_000, s=bytes(range(40, 56))),
                      stage="COLONIZATION",
                      batch=enc("batch", batch, iv_seed=6, n=6_000_000, s=bytes(range(60, 76))))
    # Costly payloads are never decrypted; they are encrypted with the 100k key only so the
    # objects are well-formed. Decoders must refuse before deriving any key.

    return [
        case("decrypt-fields-pbkdf2", "Decrypt two passphrase-encrypted fields in an embedded label",
             two, pb_secret, {"success": True, "specimen": clear}),
        case("decrypt-fields-raw", "Decrypt a raw-key encrypted field",
             specimen(id_, strain=enc("strain", strain, key=raw_key, kdf="raw", iv_seed=7),
                      stage="COLONIZATION", batch=batch),
             raw_secret, {"success": True, "specimen": clear}),
        case("reject-swapped-fields", "Encrypted values swapped between fields MUST fail authentication",
             swapped, pb_secret, {"success": False, "reason": "authentication-failed"}),
        case("reject-field-from-other-label",
             "An encrypted value copied from another label MUST fail authentication",
             moved, pb_secret, {"success": False, "reason": "authentication-failed"}),
        case("reject-encrypted-identifying-field",
             "Identifying fields (@context, @type, id, version, type, species) MUST NOT be encrypted",
             ident, pb_secret, {"success": False, "reason": "identifying-field"}),
        case("reject-excessive-total-cost",
             "Decoders MUST reject a label whose total PBKDF2 cost exceeds 10,000,000 iterations "
             "before deriving any key",
             costly, pb_secret, {"success": False, "reason": "excessive-iterations"}),
    ]


# ---------------------------------------------------------------------------
# Signatures (1.4.0)
# ---------------------------------------------------------------------------
#
# Everything below follows SPECIFICATION.md, Cryptographic Signatures. The
# generator also verifies every `verify` case with its own implementation and
# refuses to write a case whose computed status differs from the intended one.

SIG_DOMAIN = "WOLS-SIG-v1"
FORM_EMBEDDED = "embedded"
FORM_URL = "encrypted-url"
ENCRYPTED_PREFIX = "wemush://v1/encrypted/"
KID_RE = re.compile(r"[A-Za-z0-9_-]{1,64}")
SIG_RE = re.compile(r"[A-Za-z0-9_-]{86}")
ED25519_L = 2**252 + 27742317777372353535851937790883648493

# Test keys. Seeds are derived from fixed strings so anyone can reproduce them.
# They are published in the vector file: never use them for real labels.
KEY_NAMES = ("mushoh-2026", "acme-lab-1", "attacker-1")
TRUSTED = {"mushoh-2026": "mushoh-2026", "mushoh-alias": "mushoh-2026", "acme-lab-1": "acme-lab-1"}


def test_seed(name: str) -> bytes:
    return hashlib.sha256(f"WOLS 1.4.0 conformance test key: {name}".encode()).digest()


def private_key(name: str) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(test_seed(name))


def public_raw(name: str) -> bytes:
    return private_key(name).public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)


class Malformed(Exception):
    pass


def _jcs_string(s: str) -> str:
    out = ['"']
    for ch in s:
        o = ord(ch)
        if 0xD800 <= o <= 0xDFFF:
            raise Malformed("lone surrogate")
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif ch in "\b\f\n\r\t":
            out.append({"\b": "\\b", "\f": "\\f", "\n": "\\n", "\r": "\\r", "\t": "\\t"}[ch])
        elif o < 0x20:
            out.append(f"\\u{o:04x}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _jcs_number(x: float) -> str:
    """ECMAScript Number::toString, as RFC 8785 section 3.2.2.3 requires."""
    if not math.isfinite(x):
        raise Malformed("non-finite number")
    if x == 0:
        return "0"
    sign = "-" if x < 0 else ""
    mant, _, exp = repr(abs(x)).partition("e")
    ip, _, fp = mant.partition(".")
    digits = ip + fp
    n = len(ip) + (int(exp) if exp else 0)
    stripped = digits.lstrip("0")
    n -= len(digits) - len(stripped)
    digits = stripped.rstrip("0")
    k = len(digits)
    if k <= n <= 21:
        body = digits + "0" * (n - k)
    elif 0 < n <= 21:
        body = digits[:n] + "." + digits[n:]
    elif -6 < n <= 0:
        body = "0." + "0" * (-n) + digits
    else:
        e = n - 1
        es = f"e{'+' if e >= 0 else '-'}{abs(e)}"
        body = (digits if k == 1 else digits[0] + "." + digits[1:]) + es
    return sign + body


def jcs(v: object) -> str:
    """RFC 8785 JSON Canonicalization Scheme."""
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, int):
        return _jcs_number(float(v))
    if isinstance(v, float):
        return _jcs_number(v)
    if isinstance(v, str):
        return _jcs_string(v)
    if isinstance(v, list):
        return "[" + ",".join(jcs(x) for x in v) + "]"
    if isinstance(v, dict):
        for k in v:
            _jcs_string(k)
        keys = sorted(v, key=lambda k: k.encode("utf-16-be"))
        return "{" + ",".join(_jcs_string(k) + ":" + jcs(v[k]) for k in keys) + "}"
    raise TypeError(type(v))


def parse_label(text: str) -> object:
    def pairs(ps):
        d = {}
        for k, val in ps:
            if k in d:
                raise Malformed("duplicate member name")
            d[k] = val
        return d

    def bad_constant(c):
        raise Malformed(f"non-JSON constant {c}")

    try:
        return json.loads(text, object_pairs_hook=pairs, parse_constant=bad_constant)
    except json.JSONDecodeError as e:
        raise Malformed(str(e)) from e


def signing_input(form: str, kid: str, body: bytes) -> bytes:
    return f"{SIG_DOMAIN}\n{form}\n{kid}\n".encode("ascii") + body


def raw_sign(key_name: str, message: bytes) -> bytes:
    return private_key(key_name).sign(message)


def token(kid: str, sig: bytes) -> str:
    return f"{kid}.{b64url(sig)}"


def embedded_body(label: dict) -> bytes:
    return jcs({k: v for k, v in label.items() if k != "signature"}).encode("utf-8")


def sign_embedded_obj(label: dict, kid: str, key_name: str | None = None) -> dict:
    sig = raw_sign(key_name or TRUSTED.get(kid, kid), signing_input(FORM_EMBEDDED, kid, embedded_body(label)))
    return {**label, "signature": token(kid, sig)}


def sign_url(url: str, kid: str, key_name: str | None = None, *, form: str = FORM_URL) -> str:
    sig = raw_sign(key_name or TRUSTED.get(kid, kid), signing_input(form, kid, url.encode("ascii")))
    return f"{url}&sig={token(kid, sig)}"


def parse_token(tok: object) -> tuple[str, bytes]:
    if not isinstance(tok, str):
        raise Malformed("signature is not a string")
    parts = tok.split(".")
    if len(parts) != 2:
        raise Malformed("token must be {kid}.{sig}")
    kid, s = parts
    if not KID_RE.fullmatch(kid):
        raise Malformed("bad kid")
    if not SIG_RE.fullmatch(s):
        raise Malformed("sig must be 86 base64url characters")
    raw = base64.urlsafe_b64decode(s + "==")
    if len(raw) != 64 or b64url(raw) != s:
        raise Malformed("non-canonical base64url")
    return kid, raw


def trust_store() -> dict[str, bytes]:
    return {kid: public_raw(name) for kid, name in TRUSTED.items()}


def _check(kid: str, raw: bytes, message: bytes) -> str:
    store = trust_store()
    if kid not in store:
        return "unknown-kid"
    try:
        Ed25519PublicKey.from_public_bytes(store[kid]).verify(raw, message)
    except InvalidSignature:
        return "invalid"
    return "valid"


def verify_embedded(text: str) -> tuple[str, bytes | None]:
    try:
        label = parse_label(text)
        if not isinstance(label, dict):
            raise Malformed("label is not a JSON object")
        if "signature" not in label:
            return "unsigned", None
        kid, raw = parse_token(label["signature"])
        message = signing_input(FORM_EMBEDDED, kid, embedded_body(label))
    except Malformed:
        return "malformed", None
    return _check(kid, raw, message), message


def split_signed_url(url: str) -> tuple[str, str] | None:
    """Return (body, token), None when unsigned; raise Malformed."""
    q = url.find("?")
    params = url[q + 1:].split("&") if q != -1 else []
    names = [p.split("=", 1)[0] for p in params]
    if "sig" not in names:
        return None
    if any(ord(c) < 0x21 or ord(c) > 0x7E for c in url):
        raise Malformed("non-ASCII or space")
    if "#" in url:
        raise Malformed("fragment")
    if not url.startswith(ENCRYPTED_PREFIX):
        raise Malformed("not an encrypted URL")
    if names.count("sig") != 1 or names[-1] != "sig" or len(params) < 2:
        raise Malformed("sig must appear once, as the last parameter")
    last = params[-1]
    if not last.startswith("sig="):
        raise Malformed("sig without value")
    return url[: len(url) - len(last) - 1], last[4:]


def verify_url(url: str) -> tuple[str, bytes | None]:
    try:
        split = split_signed_url(url)
        if split is None:
            return "unsigned", None
        body, tok = split
        kid, raw = parse_token(tok)
        message = signing_input(FORM_URL, kid, body.encode("ascii"))
    except Malformed:
        return "malformed", None
    return _check(kid, raw, message), message


def signature_cases() -> list[dict]:
    label = specimen("wemush:clx1a2b3c4", version=SIG_SPEC_VERSION,
                     strain={"name": "Blue Oyster PoHu", "generation": "F2", "clonalGeneration": 3},
                     stage="COLONIZATION", created="2025-12-16T10:30:00Z",
                     batch="batch_2025_12_001", organization="org_mushoh")
    signed = sign_embedded_obj(label, "mushoh-2026")
    good_tok = signed["signature"]
    good_kid, good_raw = parse_token(good_tok)

    # Encrypted URLs, built exactly as in encrypted.json.
    passphrase = "correct horse battery staple"
    salt, iv, iterations = bytes(range(16)), bytes(range(100, 112)), 100_000
    raw_key = bytes(range(200, 232))
    pb_key = derive_key(passphrase, salt, iterations)
    inner = specimen("wemush:clx1a2b3c4", strain={"name": "MO-Blue-001", "generation": "F1"},
                     stage="COLONIZATION", created="2025-12-16T10:30:00Z")

    def enc_url(id_suffix: str, full_id: str, *, kdf: str = "pbkdf2") -> str:
        key = pb_key if kdf == "pbkdf2" else raw_key
        ct = AESGCM(key).encrypt(iv, serialize(dict(inner, id=full_id)).encode(), None)
        q = f"e={b64url(ct)}&iv={b64url(iv)}&kdf={kdf}"
        if kdf == "pbkdf2":
            q += f"&salt={b64url(salt)}&i={iterations}"
        return f"{ENCRYPTED_PREFIX}{id_suffix}?{q}"

    u_pb = enc_url("clx1a2b3c4", "wemush:clx1a2b3c4")
    u_raw = enc_url("clx1a2b3c4", "wemush:clx1a2b3c4", kdf="raw")
    hostile = quote("Lab A/plate+3%", safe="")
    u_host = enc_url(hostile, "wemush:Lab A/plate+3%")
    s_pb, s_raw, s_host = (sign_url(u, "mushoh-2026") for u in (u_pb, u_raw, u_host))
    url_tok = s_pb.rsplit("&sig=", 1)[1]

    cases: list[dict] = []

    def emb_text(obj: dict) -> str:
        return serialize(obj)

    def v_emb(cid, desc, text, status, req="MUST", kid=None):
        cases.append({"id": cid, "operation": "verify", "requirement": req, "description": desc,
                      "input": {"form": FORM_EMBEDDED, "label": text},
                      "expected": {"status": status, **({"kid": kid} if kid else {})}})

    def v_url(cid, desc, u, status, req="MUST", kid=None):
        cases.append({"id": cid, "operation": "verify", "requirement": req, "description": desc,
                      "input": {"form": FORM_URL, "url": u},
                      "expected": {"status": status, **({"kid": kid} if kid else {})}})

    def s_emb(cid, desc, text, kid, key_name=None):
        lbl = parse_label(text)
        msg = signing_input(FORM_EMBEDDED, kid, embedded_body(lbl))
        tok = token(kid, raw_sign(key_name or TRUSTED[kid], msg))
        cases.append({"id": cid, "operation": "sign", "requirement": "MUST", "description": desc,
                      "input": {"form": FORM_EMBEDDED, "label": text, "kid": kid,
                                "key": key_name or TRUSTED[kid]},
                      "expected": {"signingInput": msg.decode("utf-8"), "signature": tok}})
        return tok

    def s_url(cid, desc, u, kid):
        out = sign_url(u, kid)
        msg = signing_input(FORM_URL, kid, u.encode("ascii"))
        cases.append({"id": cid, "operation": "sign", "requirement": "MUST", "description": desc,
                      "input": {"form": FORM_URL, "url": u, "kid": kid, "key": TRUSTED[kid]},
                      "expected": {"signingInput": msg.decode("ascii"),
                                   "signature": out.rsplit("&sig=", 1)[1], "url": out}})

    # --- sign ---------------------------------------------------------------
    s_emb("sign-embedded", "Sign an embedded label: JCS of the label without `signature`, after the "
          "domain prefix", emb_text(label), "mushoh-2026")
    s_emb("sign-embedded-replaces-signature",
          "Signing ignores an existing `signature` member, so re-signing gives the same token",
          emb_text({**label, "signature": "old-value"}), "mushoh-2026")
    s_url("sign-encrypted-url", "Sign an encrypted URL: its exact bytes, then `&sig=` is appended",
          u_pb, "mushoh-2026")
    s_url("sign-encrypted-url-percent-encoded-id",
          "Percent-encoding in the path is signed exactly as written", u_host, "mushoh-2026")

    # JCS edge cases: each is signed from one spelling and verified from another.
    base_text = serialize(label)[:-1]

    def with_custom(raw_custom: str) -> str:
        return base_text + ',"custom":' + raw_custom + "}"

    keys_custom = ('{"jcs":{"b":1,"a":2,"A":3,"_":4,"10":5,"9":6,"é":7,'
                   '"ﬁ":8,"\U0001F344":9,"":10}}')
    keys_custom_reordered = ('{"jcs":{"\\ud83c\\udf44":9,"":10,"\\ufb01":8,"9":6,"10":5,'
                             '"_":4,"A":3,"a":2,"b":1,"\\u00e9":7}}')
    tok_keys = s_emb("sign-jcs-key-order",
                     "JCS sorts member names by UTF-16 code units, not code points: U+1F344 "
                     "(surrogates D83C DF44) sorts before U+FB01", with_custom(keys_custom), "mushoh-2026")
    uni_value = "Pilz-\u00fc \U0001F344 \x01\t\n\r\b\f \" \\ / \u2028\x7f\u00a0"

    def escape_everything(s: str) -> str:
        # Every non-alphanumeric character as an uppercase \uXXXX escape (surrogate pairs above
        # the BMP), and `/` as `\/`: the same value as the literal form, spelled differently.
        out = []
        for ch in s:
            if ch.isascii() and ch.isalnum():
                out.append(ch)
            elif ch == "/":
                out.append("\\/")
            elif ord(ch) > 0xFFFF:
                hi, lo = divmod(ord(ch) - 0x10000, 0x400)
                out.append(f"\\u{0xD800 + hi:04X}\\u{0xDC00 + lo:04X}")
            else:
                out.append(f"\\u{ord(ch):04X}")
        return '"' + "".join(out) + '"'

    uni_custom = '{"jcs":{"s":' + _jcs_string(uni_value) + "}}"
    uni_custom_alt = '{"jcs":{"s":' + escape_everything(uni_value) + "}}"
    tok_uni = s_emb("sign-jcs-strings",
                    "JCS string escaping: only `\"`, `\\\\`, and control characters are escaped "
                    "(short forms where they exist, else lowercase \\u00xx); `/`, U+2028, DEL, and "
                    "non-ASCII are literal UTF-8", with_custom(uni_custom), "mushoh-2026")
    num_custom = ('{"jcs":{"n":[1.0,100,-0,1E21,1e20,1e-7,0.0000010,1.5,5e-324,'
                  '1.7976931348623157e308,9007199254740993,0.1,333333333.33333329,-1.25e-10,4.50]}}')
    num_custom_alt = ('{"jcs":{"n":[1,1.00e2,-0.0,1e+21,100000000000000000000,0.0000001,1e-6,15e-1,'
                      '4.9406564584124654e-324,1.7976931348623157E+308,9007199254740992,1e-1,'
                      '333333333.3333333,-0.000000000125,4.5]}}')
    tok_num = s_emb("sign-jcs-numbers",
                    "JCS numbers use the ECMAScript Number-to-String rules on IEEE 754 doubles: 1.0 is "
                    "1, -0 is 0, 1e21 is 1e+21, integers above 2^53 round to the nearest double",
                    with_custom(num_custom), "mushoh-2026")

    # --- verify: embedded -------------------------------------------------------
    v_emb("verify-embedded-valid", "A label signed by a trusted kid verifies", emb_text(signed),
          "valid", kid="mushoh-2026")
    reordered = {k: signed[k] for k in reversed(list(signed))}
    v_emb("verify-embedded-reordered",
          "Member order and whitespace don't matter: the verifier canonicalizes the parsed label",
          json.dumps(reordered, indent=2, ensure_ascii=True), "valid", kid="mushoh-2026")
    v_emb("verify-embedded-escaped-strings",
          "String escapes don't matter: \\u0050leurotus and \\/ parse to the same values",
          emb_text(signed).replace('"Pleurotus', '"\\u0050leurotus').replace(
              "https://", "https:\\/\\/"), "valid", kid="mushoh-2026")
    v_emb("verify-jcs-key-order", "Verifies the key-order label from members in a different order",
          with_custom(keys_custom_reordered)[:-1] + f',"signature":"{tok_keys}"}}', "valid",
          kid="mushoh-2026")
    v_emb("verify-jcs-strings", "Verifies the string label written with different escapes",
          with_custom(uni_custom_alt)[:-1] + f',"signature":"{tok_uni}"}}', "valid", kid="mushoh-2026")
    v_emb("verify-jcs-numbers", "Verifies the number label written with different number spellings",
          with_custom(num_custom_alt)[:-1] + f',"signature":"{tok_num}"}}', "valid", kid="mushoh-2026")
    nfd = dict(signed, strain=dict(signed["strain"], name="Pilz-ü"))
    nfd = sign_embedded_obj(nfd, "mushoh-2026")
    nfd["strain"] = dict(nfd["strain"], name=unicodedata.normalize("NFD", "Pilz-ü"))
    v_emb("verify-embedded-not-unicode-normalized",
          "JCS does not normalize Unicode: the same name in NFD form is different bytes",
          emb_text(nfd), "invalid")
    v_emb("verify-embedded-tampered-field", "A changed top-level field fails verification",
          emb_text({**signed, "stage": "FRUITING"}), "invalid")
    v_emb("verify-embedded-tampered-nested", "A changed nested field fails verification",
          emb_text({**signed, "strain": {**signed["strain"], "clonalGeneration": 4}}), "invalid")
    v_emb("verify-embedded-added-field", "An added field fails verification",
          emb_text({**signed, "creator": "someone-else"}), "invalid")
    v_emb("verify-embedded-removed-field", "A removed field fails verification",
          emb_text({k: v for k, v in signed.items() if k != "batch"}), "invalid")
    v_emb("verify-embedded-number-type", "A number replaced with the equal string fails verification",
          emb_text({**signed, "strain": {**signed["strain"], "clonalGeneration": "3"}}), "invalid")

    att_pub = b64url(public_raw("attacker-1"))
    forged = {**label, "stage": "FRUITING", "publicKey": att_pub}
    v_emb("verify-embedded-untrusted-kid",
          "Edited and re-signed with a key that isn't in the trust store (its public key is even "
          "embedded in the label): the verifier ignores the embedded key",
          emb_text(sign_embedded_obj(forged, "attacker-1", "attacker-1")), "unknown-kid")
    v_emb("verify-embedded-untrusted-key-trusted-kid",
          "Edited and re-signed with an untrusted key that claims a trusted kid fails verification",
          emb_text(sign_embedded_obj(forged, "mushoh-2026", "attacker-1")), "invalid")
    v_emb("verify-embedded-wrong-kid",
          "Signed by one trusted key, labelled with another trusted kid: fails verification",
          emb_text(sign_embedded_obj(label, "acme-lab-1", "mushoh-2026")), "invalid")
    v_emb("verify-embedded-kid-swapped",
          "The kid is part of the signed bytes: replacing it with another kid for the same key fails",
          emb_text({**signed, "signature": "mushoh-alias." + good_tok.split(".")[1]}), "invalid")
    v_emb("verify-embedded-unsigned", "A label without `signature` is unsigned, not invalid",
          emb_text(label), "unsigned")
    v_emb("verify-embedded-reserved-1-3-signature",
          "A pre-1.4.0 `signature` string that isn't a 1.4.0 token is malformed, never valid",
          emb_text({**label, "signature": "MEUCIQDx+b0/sketch=="}), "malformed")

    good_sig = good_tok.split(".")[1]
    # 64 bytes in 86 characters leave 4 unused bits, so the last character is one of A, Q, g, w;
    # the next character in the alphabet sets an unused bit.
    assert good_sig[-1] in "AQgw"
    long_sig = b64url(good_raw + bytes(1))
    bad_tokens = {
        "padding": f"mushoh-2026.{good_sig}==",
        "non-base64url-character": f"mushoh-2026.{good_sig[:-2]}+/",
        "short": f"mushoh-2026.{b64url(good_raw[:63])}",
        "long": f"mushoh-2026.{long_sig}",
        "non-canonical-bits": f"mushoh-2026.{good_sig[:-1]}{chr(ord(good_sig[-1]) + 1)}",
        "no-kid": good_sig,
        "empty-kid": f".{good_sig}",
        "kid-bad-character": f"mushoh 2026.{good_sig}",
        "kid-too-long": f"{'k' * 65}.{good_sig}",
        "extra-dot": f"mushoh.2026.{good_sig}",
        "whitespace": f" {good_tok}",
    }
    for name, tok in bad_tokens.items():
        v_emb(f"verify-embedded-malformed-{name}", f"Malformed signature token ({name})",
              emb_text({**label, "signature": tok}), "malformed")
    v_emb("verify-embedded-malformed-not-a-string", "A `signature` that isn't a string is malformed",
          emb_text({**label, "signature": {"kid": "mushoh-2026", "sig": good_sig}}), "malformed")
    v_emb("verify-embedded-malformed-lone-surrogate",
          "A label with a lone surrogate isn't I-JSON and can't be canonicalized",
          emb_text(signed)[:-1].replace('"batch_2025_12_001"', '"batch_\\ud800"') + "}", "malformed")
    v_emb("verify-embedded-malformed-not-an-object", "A label that isn't a JSON object is malformed",
          json.dumps([signed]), "malformed")

    s_int = int.from_bytes(good_raw[32:], "little") + ED25519_L
    malleable = good_raw[:32] + s_int.to_bytes(32, "little")
    v_emb("verify-embedded-non-canonical-s",
          "Verifiers MUST reject S >= L (RFC 8032 section 5.1.7): S + L is a malleated copy",
          emb_text({**label, "signature": token("mushoh-2026", malleable)}), "invalid")

    v_emb("verify-embedded-url-signature-replayed",
          "A signature taken from a signed URL doesn't verify on an embedded label",
          emb_text({**label, "signature": url_tok}), "invalid")
    no_prefix = raw_sign("mushoh-2026", embedded_body(label))
    v_emb("verify-embedded-missing-domain-prefix",
          "A signature over the canonical JSON without the domain prefix fails verification",
          emb_text({**label, "signature": token("mushoh-2026", no_prefix)}), "invalid")
    wrong_form = raw_sign("mushoh-2026", signing_input(FORM_URL, "mushoh-2026", embedded_body(label)))
    v_emb("verify-embedded-wrong-form-prefix",
          "A signature made with the encrypted-url prefix doesn't verify as embedded",
          emb_text({**label, "signature": token("mushoh-2026", wrong_form)}), "invalid")

    field_iv = bytes(range(50, 62))
    strain_ct = AESGCM(raw_key).encrypt(field_iv, serialize_value(label["strain"]).encode(),
                                        field_aad(label["id"], "strain"))
    fl = {**label, "strain": {"encrypted": True, "algorithm": "AES-256-GCM", "payload": b64url(strain_ct),
                              "iv": b64url(field_iv), "kdf": "raw"}}
    fl_signed = sign_embedded_obj(fl, "mushoh-2026")
    v_emb("verify-embedded-field-encrypted",
          "A signature over a label with field-level encryption covers the encrypted objects as "
          "printed, and verifies without any decryption key", emb_text(fl_signed), "valid",
          kid="mushoh-2026")
    tampered_fl = json.loads(json.dumps(fl_signed))
    tampered_fl["strain"]["iv"] = b64url(bytes(range(51, 63)))
    v_emb("verify-embedded-field-encrypted-tampered",
          "Changing an encrypted field object fails verification", emb_text(tampered_fl), "invalid")

    # --- verify: encrypted URL -------------------------------------------------
    v_url("verify-url-valid", "A signed pbkdf2 URL verifies", s_pb, "valid", kid="mushoh-2026")
    v_url("verify-url-valid-raw", "A signed raw-key URL verifies", s_raw, "valid", kid="mushoh-2026")
    v_url("verify-url-valid-percent-encoded-id", "A signed URL with a percent-encoded ID verifies",
          s_host, "valid", kid="mushoh-2026")
    v_url("verify-url-percent-encoding-case",
          "Verifiers don't re-normalize: %2F rewritten as %2f decodes the same but fails",
          s_host.replace("%2F", "%2f"), "invalid")
    e_val = s_pb.split("e=", 1)[1].split("&", 1)[0]
    flipped = ("B" if e_val[0] != "B" else "C") + e_val[1:]
    v_url("verify-url-tampered-ciphertext", "A changed ciphertext fails verification",
          s_pb.replace(f"e={e_val}", f"e={flipped}"), "invalid")
    v_url("verify-url-tampered-iterations", "A changed `i` fails verification",
          s_pb.replace("&i=100000&", "&i=600000&"), "invalid")
    v_url("verify-url-tampered-id", "A changed ID path segment fails verification",
          s_pb.replace("/clx1a2b3c4?", "/clx1a2b3c5?"), "invalid")
    parts = s_pb.split("?", 1)[1].split("&")
    swapped_q = "&".join([parts[1], parts[0], *parts[2:]])
    v_url("verify-url-reordered-parameters",
          "Parameter order is part of the signed bytes: swapping `e` and `iv` fails",
          s_pb.split("?", 1)[0] + "?" + swapped_q, "invalid")
    v_url("verify-url-added-parameter",
          "A parameter added before `sig` fails verification",
          s_pb.replace("&sig=", "&x=1&sig="), "invalid")
    v_url("verify-url-parameter-after-sig", "`sig` MUST be the last parameter", s_pb + "&x=1",
          "malformed")
    v_url("verify-url-duplicate-sig", "`sig` MUST appear once",
          s_pb.replace("&sig=", f"&sig={url_tok}&sig="), "malformed")
    v_url("verify-url-percent-encoded-token", "The token is never percent-decoded",
          s_pb.replace(f"&sig={good_kid}.", f"&sig={good_kid}%2E"), "malformed")
    v_url("verify-url-fragment", "A signed URL with a fragment is malformed", s_pb + "#x", "malformed")
    v_url("verify-url-non-ascii", "A signed URL must be ASCII (non-ASCII is percent-encoded)",
          sign_url(enc_url("Pilz-%C3%BC", "wemush:Pilz-ü"), "mushoh-2026").replace(
              "Pilz-%C3%BC", "Pilz-ü"), "malformed")
    v_url("verify-url-other-scheme", "Only `wemush://v1/encrypted/` URLs can be verified",
          s_pb.replace("wemush://", "web+wemush://", 1), "malformed")
    forged_url = sign_url(u_pb.replace("&i=100000", "&i=100001"), "attacker-1", "attacker-1")
    v_url("verify-url-untrusted-kid", "A URL re-signed with a key not in the trust store",
          forged_url, "unknown-kid")
    v_url("verify-url-wrong-kid", "Signed by one trusted key, labelled with another trusted kid",
          sign_url(u_pb, "acme-lab-1", "mushoh-2026"), "invalid")
    v_url("verify-url-unsigned", "A URL without `sig` is unsigned", u_pb, "unsigned")
    v_url("verify-url-reserved-1-3-sig",
          "The reserved 1.3.1 `sig` value (64 bytes, no kid) is malformed, never valid",
          u_pb + "&sig=" + b64url(bytes(range(64))), "malformed")
    v_url("verify-url-malformed-padding", "A padded signature is malformed",
          s_pb + "==", "malformed")
    v_url("verify-url-embedded-signature-replayed",
          "Cross-form replay: an embedded label's signature doesn't verify on a URL",
          u_pb + "&sig=" + good_tok, "invalid")
    v_url("verify-url-wrong-form-prefix",
          "A signature over the URL bytes made with the embedded prefix fails verification",
          sign_url(u_pb, "mushoh-2026", form=FORM_EMBEDDED), "invalid")

    # Self-check: every verify case must compute the status it claims.
    for c in cases:
        if c["operation"] != "verify":
            continue
        fn = verify_embedded if c["input"]["form"] == FORM_EMBEDDED else verify_url
        status, msg = fn(c["input"].get("label") or c["input"].get("url"))
        if status != c["expected"]["status"]:
            raise SystemExit(f"{c['id']}: computed {status}, expected {c['expected']['status']}")
        if status == "valid":
            c["expected"]["signingInput"] = msg.decode("utf-8")
    return cases


def signature_metadata() -> dict:
    return {
        "signingDomain": SIG_DOMAIN,
        "testKeys": {
            name: {"seedBase64url": b64url(test_seed(name)), "publicKeyBase64url": b64url(public_raw(name)),
                   "trusted": name in TRUSTED.values()}
            for name in KEY_NAMES
        },
        "trustStore": {kid: {"alg": "Ed25519", "publicKeyBase64url": b64url(public_raw(name))}
                       for kid, name in TRUSTED.items()},
    }


def main() -> None:
    write("embedded.json", "Embedded JSON-LD validation", "Core Data Model; ID Format Options",
          embedded_cases())
    write("primordia.json", "PRIMORDIA supplied as a specimen type", "Type Aliases (Note — PRIMORDIA)",
          primordia_cases())
    write("generation.json", "Generation, subculture, and transfer depth",
          "Generation, Subculture, and Transfer Tracking", generation_cases())
    write("encrypted.json", "Encrypted format wire specification",
          "QR Code Encoding > Encrypted Format", encrypted_cases())
    write("field-encryption.json", "Field-level encryption in embedded labels",
          "QR Code Encoding > Encrypted Format (Field-level encryption)", field_cases())
    write("signatures.json", "Ed25519 signatures over embedded labels and encrypted URLs",
          "Privacy & Security > Cryptographic Signatures", signature_cases(),
          version=SIG_SPEC_VERSION, extra=signature_metadata())
    sums = "".join(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}\n"
                   for f in sorted(OUT.glob("*.json")))
    (OUT / "SHA256SUMS").write_text(sums)
    print(f"Wrote vectors to {OUT}")


if __name__ == "__main__":
    main()
