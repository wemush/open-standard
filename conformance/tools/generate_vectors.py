#!/usr/bin/env python3
"""Generate WOLS conformance test vectors.

Usage:
    pip install "cryptography>=42"
    python conformance/tools/generate_vectors.py

Writes JSON files to conformance/vectors/. Output is deterministic: the
encrypted vectors use FIXED salts and IVs so results are reproducible.
Real generators MUST use fresh random salts and IVs (SPECIFICATION.md,
Encrypted Format).
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SPEC_VERSION = "1.3.0"
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


def serialize(obj: dict) -> str:
    # Compact, key order as given. Vectors carry the exact plaintext string,
    # so consumers never need to reproduce this serialization.
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


def write(name: str, description: str, section: str, cases: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    doc = {
        "wolsVersion": SPEC_VERSION,
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
        return PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=s, iterations=n).derive(pw.encode())

    pb_key = derive(passphrase, salt, iterations)
    pb_ct = AESGCM(pb_key).encrypt(iv, plaintext.encode(), None)
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
    ]


def main() -> None:
    write("embedded.json", "Embedded JSON-LD validation", "Core Data Model; ID Format Options",
          embedded_cases())
    write("primordia.json", "PRIMORDIA supplied as a specimen type", "Type Aliases (Note — PRIMORDIA)",
          primordia_cases())
    write("generation.json", "Generation, subculture, and transfer depth",
          "Generation, Subculture, and Transfer Tracking", generation_cases())
    write("encrypted.json", "Encrypted format wire specification",
          "QR Code Encoding > Encrypted Format", encrypted_cases())
    print(f"Wrote vectors to {OUT}")


if __name__ == "__main__":
    main()
