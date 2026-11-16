#!/usr/bin/env python3
"""Generate WOLS conformance test vectors.

Usage:
    pip install "cryptography>=42"
    python conformance/tools/generate_vectors.py

Writes JSON files to conformance/vectors/. Output is deterministic: the
encrypted vectors use FIXED salts and IVs so results are reproducible.
Real generators MUST use fresh random salts and IVs (SPECIFICATION.md,
Encrypted Format). The signature vectors use the Ed25519 TEST keys in
conformance/keys/test-keys.json; Ed25519 signing is deterministic.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
import unicodedata
from urllib.parse import quote
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SPEC_VERSION = "1.3.0"
SIGNATURE_SPEC_VERSION = "1.4.0-rc.1"
CONTEXT = "https://wemush.com/wols/v1"
OUT = Path(__file__).resolve().parent.parent / "vectors"
KEYS = Path(__file__).resolve().parent.parent / "keys" / "test-keys.json"


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
        **(extra or {}),
        "description": description,
        "specSection": section,
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

    def url(id_suffix, ct, kdf, s=None, n=None, *, pad=False):
        enc = b64url_padded if pad else b64url
        q = f"e={enc(ct)}&iv={enc(iv)}&kdf={kdf}"
        if s is not None:
            q += f"&salt={enc(s)}"
        if n is not None:
            q += f"&i={n}"
        return f"wemush://v1/encrypted/{id_suffix}?{q}"

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
# Signatures (1.4.0-rc.1)
# ---------------------------------------------------------------------------

SIGNING_CONTEXT = b"WOLS-SIG-1\n"
ED25519_L = 2**252 + 27742317777372353535851937790883648493


def _jcs_number(x: float) -> str:
    """ECMAScript Number::toString, as RFC 8785 requires."""
    if isinstance(x, int):
        if abs(x) > 2**53:
            raise ValueError("integer outside the I-JSON range")
        return str(x)
    if not math.isfinite(x):
        raise ValueError("non-finite number")
    if x == 0:
        return "0"
    sign = "-" if x < 0 else ""
    r = repr(abs(x))                      # shortest round-trip digits
    mant, _, exp = r.partition("e")
    int_part, _, frac = mant.partition(".")
    digits = (int_part + frac).lstrip("0")
    point = len(int_part) + (int(exp) if exp else 0)   # decimal point position in int_part+frac
    point -= len(int_part + frac) - len((int_part + frac).lstrip("0"))
    digits = digits.rstrip("0") or "0"
    k, n = len(digits), point
    if k <= n <= 21:
        out = digits + "0" * (n - k)
    elif 0 < n <= 21:
        out = digits[:n] + "." + digits[n:]
    elif -6 < n <= 0:
        out = "0." + "0" * (-n) + digits
    else:
        e = n - 1
        out = digits[0] + ("." + digits[1:] if k > 1 else "") + "e" + ("+" if e >= 0 else "-") + str(abs(e))
    return sign + out


def jcs(value: object) -> str:
    """RFC 8785 JSON Canonicalization Scheme."""
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return _jcs_number(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ",".join(jcs(v) for v in value) + "]"
    if isinstance(value, dict):
        keys = sorted(value, key=lambda k: k.encode("utf-16-be"))   # UTF-16 code units
        return "{" + ",".join(json.dumps(k, ensure_ascii=False) + ":" + jcs(value[k]) for k in keys) + "}"
    raise TypeError(type(value))


def _load_keys() -> dict[str, dict]:
    doc = json.loads(KEYS.read_text())
    out = {}
    for k in doc["keys"]:
        seed = base64.urlsafe_b64decode(k["privateKeyBase64url"] + "==")
        sk = Ed25519PrivateKey.from_private_bytes(seed)
        pub = sk.public_key().public_bytes_raw()
        assert b64url(pub) == k["publicKeyBase64url"], k["kid"]
        out[k["kid"]] = {**k, "sk": sk}
    return out


def embedded_payload(label: dict) -> bytes:
    return jcs({k: v for k, v in label.items() if k != "signature"}).encode("utf-8")


def url_payload(url: str) -> bytes:
    return url[: url.rindex("&sig=")].encode("ascii")


def sign_embedded(label: dict, kid: str, sk: Ed25519PrivateKey) -> dict:
    unsigned = {k: v for k, v in label.items() if k not in ("signature", "kid")}
    with_kid = {**unsigned, "kid": kid}
    sig = b64url(sk.sign(SIGNING_CONTEXT + embedded_payload(with_kid)))
    return {**with_kid, "signature": sig}


def sign_url(url: str, kid: str, sk: Ed25519PrivateKey) -> str:
    base = f"{url}&kid={kid}"
    return f"{base}&sig={b64url(sk.sign(SIGNING_CONTEXT + base.encode('ascii')))}"


def signature_cases() -> tuple[list[dict], dict]:
    keys = _load_keys()
    k1, k2, evil = keys["example.org:test-1"], keys["example.org:test-2"], keys["attacker.example:k1"]
    trust = {kid: k["publicKeyBase64url"] for kid, k in keys.items() if k["trusted"]}

    def text(obj: dict, indent: int | None = None) -> str:
        # Label text as a scanner reads it: NOT canonical, so verifiers must canonicalize.
        return json.dumps(obj, ensure_ascii=False, indent=indent,
                          separators=None if indent else (",", ":"))

    def verify(cid, desc, form, label_text, outcome, req="MUST"):
        return {"id": cid, "operation": "verify", "requirement": req, "description": desc,
                "input": {"form": form, "label": label_text, "trustStore": trust},
                "expected": {"outcome": outcome}}

    def sign_case(cid, desc, form, unsigned, key, signed):
        if form == "embedded":
            payload = embedded_payload(signed).decode("utf-8")
            exp = {"payload": payload, "signature": signed["signature"], "label": signed}
        else:
            payload = url_payload(signed).decode("ascii")
            exp = {"payload": payload, "signature": signed[signed.rindex("&sig=") + 5:], "url": signed}
        inp = {"form": form, ("label" if form == "embedded" else "url"): unsigned,
               "kid": key["kid"], "privateKeyBase64url": key["privateKeyBase64url"]}
        return {"id": cid, "operation": "sign", "requirement": "MUST", "description": desc,
                "input": inp, "expected": exp}

    # --- Embedded labels -----------------------------------------------------
    base = specimen("wemush:clx1a2b3c4", strain={"name": "MO-Blue-001", "generation": "F1"},
                    stage="COLONIZATION", created="2025-12-16T10:30:00Z", organization="org_mushoh")
    signed = sign_embedded(base, k1["kid"], k1["sk"])

    jcs_label = specimen(
        "wemush:clx1a2b3c4", stage="COLONIZATION",
        custom={"jcs": {
            "\U0001F344": "UTF-16 order puts this before U+FB01", "ﬁ": "ligature", "z": 3, "é": 4,
            "Z": 5, "a\nb": "tab\there \"quoted\" \\ é 🍄 \u0007",
            "numbers": [0.000001, 1e-7, 12.5, 1e21, 100, -3],
            "signature": "a nested `signature` member is covered",
        }})
    jcs_signed = sign_embedded(jcs_label, k1["kid"], k1["sk"])

    hostile_id = "wemush:Pilz-ü/🍄 \"x\" Lab A/plate+3%"
    hostile = sign_embedded(specimen(hostile_id, stage="COLONIZATION"), k1["kid"], k1["sk"])
    hostile_nfd = dict(hostile, id=unicodedata.normalize("NFD", hostile_id))

    # Field-level encrypted label, signed after encryption.
    fe_key = bytes(range(200, 232))
    fe_iv = bytes(range(12))
    fe_ct = AESGCM(fe_key).encrypt(fe_iv, serialize_value(base["strain"]).encode(),
                                   field_aad("wemush:clx1a2b3c4", "strain"))
    fe_label = dict(base, strain={"encrypted": True, "algorithm": "AES-256-GCM", "payload": b64url(fe_ct),
                                  "iv": b64url(fe_iv), "kdf": "raw"})
    fe_signed = sign_embedded(fe_label, k1["kid"], k1["sk"])

    tampered = dict(signed, stage="FRUITING")
    wrong_kid = dict(signed, kid=k2["kid"])
    unknown_kid = sign_embedded(base, "example.org:test-9", k1["sk"])
    resigned_same_kid = sign_embedded(dict(base, stage="FRUITING"), k1["kid"], evil["sk"])
    resigned_own_kid = sign_embedded(dict(base, stage="FRUITING"), evil["kid"], evil["sk"])
    self_asserted = sign_embedded(dict(base, stage="FRUITING", publicKey=evil["publicKeyBase64url"],
                                       algorithm="Ed25519"), k1["kid"], evil["sk"])
    stripped = {k: v for k, v in tampered.items() if k not in ("kid", "signature")}
    legacy = dict(base, signature="MEUCIQDlegacyOpaqueSignatureFromA13Label")
    kid_only = {k: v for k, v in signed.items() if k != "signature"}
    sig = signed["signature"]
    assert len(sig) == 86 and sig[-1] in "AQgw"
    noncanonical_last = {"A": "B", "Q": "R", "g": "h", "w": "x"}[sig[-1]]

    # Signature malleability: S + L is a different encoding of the same scalar.
    raw = base64.urlsafe_b64decode(sig + "==")
    s_plus_l = int.from_bytes(raw[32:], "little") + ED25519_L
    malleable = dict(signed, signature=b64url(raw[:32] + s_plus_l.to_bytes(32, "little")))
    pub1 = Ed25519PublicKey.from_public_bytes(base64.urlsafe_b64decode(k1["publicKeyBase64url"] + "="))
    try:
        pub1.verify(base64.urlsafe_b64decode(malleable["signature"] + "=="),
                    SIGNING_CONTEXT + embedded_payload(malleable))
        raise AssertionError("non-canonical S accepted")
    except InvalidSignature:
        pass

    duplicate_member = text(signed)[:-1] + ',"stage":"FRUITING"}'

    E = "embedded"
    embedded = [
        sign_case("sign-embedded", "Sign an embedded label: add `kid`, sign the JCS form without `signature`",
                  E, base, k1, signed),
        sign_case("sign-embedded-jcs",
                  "JCS canonicalization: UTF-16 key order, ECMAScript number form, minimal string escapes",
                  E, jcs_label, k1, jcs_signed),
        verify("verify-embedded-valid", "A label signed by a trusted key verifies", E, text(signed), "valid"),
        verify("verify-embedded-reformatted",
               "Whitespace and member order in the label text don't matter; verifiers canonicalize",
               E, json.dumps(dict(reversed(list(signed.items()))), ensure_ascii=False, indent=2), "valid"),
        verify("verify-embedded-jcs", "Canonicalization edge cases verify", E, text(jcs_signed), "valid"),
        verify("verify-embedded-hostile-id", "An ID with reserved and non-ASCII characters verifies",
               E, text(hostile), "valid"),
        verify("verify-embedded-hostile-id-nfd",
               "Canonicalization does no Unicode normalization: the same ID in NFD form is a different label",
               E, text(hostile_nfd), "invalid"),
        verify("verify-embedded-field-encrypted",
               "A label with field-level encryption verifies without the decryption key",
               E, text(fe_signed), "valid"),
        verify("verify-embedded-tampered-field", "Changing a signed field makes the signature invalid",
               E, text(tampered), "invalid"),
        verify("verify-embedded-wrong-kid",
               "Changing `kid` to another trusted key makes the signature invalid", E, text(wrong_kid), "invalid"),
        verify("verify-embedded-unknown-kid", "A `kid` that isn't in the trust store is unknown-kid",
               E, text(unknown_kid), "unknown-kid"),
        verify("verify-embedded-resigned-same-kid",
               "An edited label re-signed with an untrusted key under a trusted `kid` is invalid",
               E, text(resigned_same_kid), "invalid"),
        verify("verify-embedded-resigned-own-kid",
               "An edited label re-signed under the attacker's own `kid` is unknown-kid",
               E, text(resigned_own_kid), "unknown-kid"),
        verify("verify-embedded-self-asserted-key",
               "A public key carried in the label is never used: only the trust store is consulted",
               E, text(self_asserted), "invalid"),
        verify("verify-embedded-stripped",
               "Removing `kid` and `signature` leaves an unsigned label, so policy must require `valid`",
               E, text(stripped), "unsigned"),
        verify("verify-embedded-unsigned", "A label without `kid` or `signature` is unsigned",
               E, text(base), "unsigned"),
        verify("verify-embedded-legacy-signature",
               "A pre-1.4 `signature` without `kid` is opaque: unsigned, preserved, never verified",
               E, text(legacy), "unsigned"),
        verify("verify-embedded-kid-without-signature", "`kid` without `signature` is malformed",
               E, text(kid_only), "malformed"),
        verify("verify-embedded-signature-truncated", "A signature that doesn't decode to 64 bytes is malformed",
               E, text(dict(signed, signature=sig[:-2])), "malformed"),
        verify("verify-embedded-signature-padded", "A padded signature is malformed",
               E, text(dict(signed, signature=sig + "==")), "malformed"),
        verify("verify-embedded-signature-noncanonical",
               "A signature whose final character has non-zero unused bits is malformed",
               E, text(dict(signed, signature=sig[:-1] + noncanonical_last)), "malformed"),
        verify("verify-embedded-signature-standard-base64",
               "A signature containing standard base64 characters (`+`, `/`) is malformed",
               E, text(dict(signed, signature="+/" + sig[2:])), "malformed"),
        verify("verify-embedded-signature-not-string", "A non-string signature with `kid` is malformed",
               E, text(dict(signed, signature={"sig": sig})), "malformed"),
        verify("verify-embedded-kid-invalid", "A `kid` with characters outside the allowed set is malformed",
               E, text(sign_embedded(base, "example.org/test 1", k1["sk"])), "malformed"),
        verify("verify-embedded-malleable", "A signature with S >= L (non-canonical scalar) is invalid",
               E, text(malleable), "invalid"),
        verify("verify-embedded-duplicate-member",
               "Label text with a duplicate member name SHOULD be malformed",
               E, duplicate_member, "malformed", req="SHOULD"),
    ]

    # --- Encrypted URLs --------------------------------------------------------
    passphrase = "correct horse battery staple"
    salt, iv, iterations = bytes(range(16)), bytes(range(100, 112)), 100_000
    spec = specimen("wemush:clx1a2b3c4", strain={"name": "MO-Blue-001", "generation": "F1"},
                    stage="COLONIZATION", created="2025-12-16T10:30:00Z")
    pb_key = derive_key(passphrase, salt, iterations)

    def enc_url(full_id: str) -> str:
        ct = AESGCM(pb_key).encrypt(iv, serialize(dict(spec, id=full_id)).encode(), None)
        suffix = quote(full_id.removeprefix("wemush:"), safe="")
        return (f"wemush://v1/encrypted/{suffix}?e={b64url(ct)}&iv={b64url(iv)}&kdf=pbkdf2"
                f"&salt={b64url(salt)}&i={iterations}")

    unsigned_url = enc_url("wemush:clx1a2b3c4")
    hostile_unsigned = enc_url("wemush:Lab A/plate+3%")
    surl = sign_url(unsigned_url, k1["kid"], k1["sk"])
    hurl = sign_url(hostile_unsigned, k1["kid"], k1["sk"])
    assert "Lab%20A%2Fplate%2B3%25" in hurl
    usig = surl[surl.rindex("&sig=") + 5:]
    head = surl[: surl.rindex("&kid=")]
    params = unsigned_url.split("?", 1)[1].split("&")
    reordered = unsigned_url.split("?", 1)[0] + "?" + "&".join([params[1], params[0], *params[2:]])

    U = "url"
    urls = [
        sign_case("sign-url", "Sign an encrypted URL: append `kid`, then `sig` over everything before `&sig=`",
                  U, unsigned_url, k1, surl),
        sign_case("sign-url-hostile-id", "The signed bytes include the percent-encoded ID exactly as emitted",
                  U, hostile_unsigned, k1, hurl),
        verify("verify-url-valid", "An encrypted URL signed by a trusted key verifies", U, surl, "valid"),
        verify("verify-url-hostile-id", "A signed URL with a percent-encoded hostile ID verifies", U, hurl, "valid"),
        verify("verify-url-hostile-id-reencoded",
               "Re-encoding the ID (lowercase hex) decrypts to the same ID but changes the signed bytes",
               U, hurl.replace("%2F", "%2f"), "invalid"),
        verify("verify-url-reordered", "Parameter order is part of the signed bytes; verifiers don't reorder",
               U, reordered + surl[len(unsigned_url):], "invalid"),
        verify("verify-url-tampered", "Changing a signed parameter makes the signature invalid",
               U, surl.replace("i=100000", "i=100001"), "invalid"),
        verify("verify-url-wrong-kid", "Changing `kid` to another trusted key makes the signature invalid",
               U, surl.replace(f"kid={k1['kid']}", f"kid={k2['kid']}"), "invalid"),
        verify("verify-url-unknown-kid", "A `kid` that isn't in the trust store is unknown-kid",
               U, sign_url(unsigned_url, "example.org:test-9", k1["sk"]), "unknown-kid"),
        verify("verify-url-resigned-own-kid", "A URL re-signed under the attacker's own `kid` is unknown-kid",
               U, sign_url(unsigned_url, evil["kid"], evil["sk"]), "unknown-kid"),
        verify("verify-url-resigned-same-kid",
               "A URL re-signed with an untrusted key under a trusted `kid` is invalid",
               U, sign_url(unsigned_url, k1["kid"], evil["sk"]), "invalid"),
        verify("verify-url-unsigned", "A URL without `kid` or `sig` is unsigned", U, unsigned_url, "unsigned"),
        verify("verify-url-legacy-sig",
               "A pre-1.4 `sig` without `kid` is opaque: unsigned, preserved, never verified",
               U, unsigned_url + "&sig=bGVnYWN5LW9wYXF1ZQ", "unsigned"),
        verify("verify-url-stripped", "Removing `kid` and `sig` leaves an unsigned URL", U, head, "unsigned"),
        verify("verify-url-kid-without-sig", "`kid` without `sig` is malformed",
               U, f"{unsigned_url}&kid={k1['kid']}", "malformed"),
        verify("verify-url-sig-not-last", "`sig` MUST be the last parameter",
               U, f"{head}&sig={usig}&kid={k1['kid']}", "malformed"),
        verify("verify-url-duplicate-sig", "`sig` MUST appear once", U, f"{surl}&sig={usig}", "malformed"),
        verify("verify-url-duplicate-kid", "`kid` MUST appear once",
               U, f"{head}&kid={k1['kid']}&kid={k1['kid']}&sig={usig}", "malformed"),
        verify("verify-url-sig-truncated", "A `sig` that doesn't decode to 64 bytes is malformed",
               U, surl[:-2], "malformed"),
        verify("verify-url-malformed-before-kid-lookup",
               "Malformed is decided before the `kid` lookup: a truncated `sig` under an unknown `kid` is malformed",
               U, sign_url(unsigned_url, "example.org:test-9", k1["sk"])[:-2], "malformed"),
        verify("verify-url-sig-percent-encoded", "`sig` is literal base64url; percent-escapes are malformed",
               U, f"{head}&kid={k1['kid']}&sig={usig[:-1]}%{ord(usig[-1]):02X}", "malformed"),
        verify("verify-url-kid-percent-encoded", "`kid` is literal; percent-escapes are malformed",
               U, surl.replace(f"kid={k1['kid']}", "kid=" + k1["kid"].replace(":", "%3A")), "malformed"),
    ]
    keyfile = {"testKeys": "conformance/keys/test-keys.json"}
    return embedded + urls, keyfile


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
    sig_cases, sig_extra = signature_cases()
    write("signatures.json", "Ed25519 label signatures (embedded and encrypted URL forms)",
          "Privacy & Security > Cryptographic Signatures", sig_cases,
          version=SIGNATURE_SPEC_VERSION, extra=sig_extra)
    sums = "".join(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}\n"
                   for f in sorted(OUT.glob("*.json")))
    (OUT / "SHA256SUMS").write_text(sums)
    print(f"Wrote vectors to {OUT}")


if __name__ == "__main__":
    main()
