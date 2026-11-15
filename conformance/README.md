# WOLS Conformance Test Vectors

Shared, language-neutral test cases that every WOLS implementation should pass. They target **WOLS 1.3.0** (currently release candidate `1.3.0-rc.1`). See [SPECIFICATION.md](../SPECIFICATION.md).

## Files

| File | Covers | Operations |
| ---- | ------ | ---------- |
| [`vectors/embedded.json`](./vectors/embedded.json) | Embedded JSON-LD validation, ID formats | `validate` |
| [`vectors/primordia.json`](./vectors/primordia.json) | `PRIMORDIA` supplied as a type, alias resolution | `create` |
| [`vectors/generation.json`](./vectors/generation.json) | `generation`, `clonalGeneration`, `transferDepth` | `validate` |
| [`vectors/encrypted.json`](./vectors/encrypted.json) | Encrypted format wire specification | `derive`, `decrypt` |

Compact URL vectors will be added once the compact parameter and code registries are settled (see [ROADMAP.md](../ROADMAP.md)).

## Case format

Every file has this shape:

```json
{
  "wolsVersion": "1.3.0",
  "description": "…",
  "specSection": "…",
  "cases": [
    {
      "id": "stable-case-id",
      "operation": "validate | create | derive | decrypt",
      "requirement": "MUST | SHOULD",
      "description": "…",
      "input": { },
      "expected": { }
    }
  ]
}
```

What `expected` means for each operation:

- **`validate`**: The input is a specimen object.
  - `valid` is the required outcome.
  - `errorField`, when present, names the field that must be reported.
  - `warningField`, when present, names a field that should produce a warning without failing validation.
- **`create`**: The input is the argument to the implementation's specimen factory. Check the resulting `type` and `stage` (`null` means no stage), and whether a `warning` was emitted.
- **`derive`**: PBKDF2-HMAC-SHA256 intermediate value, provided for debugging key derivation.
- **`decrypt`**: The input is an encrypted URL plus a `secret`, which is either `{ kdf: "pbkdf2", passphrase }` or `{ kdf: "raw", keyBase64url }`.
  - On success, the decrypted bytes must equal `plaintext` exactly and parse to `specimen`.
  - On failure, decryption must be refused. `reason` is a suggested error category and doesn't have to match exactly.

A case marked `SHOULD` is recommended behavior. An implementation that skips it can still conform.

> **Fixed salts and IVs**: The encrypted vectors use fixed salts and IVs so the output is reproducible. Real generators **MUST** use fresh random values.

## Tools

```bash
# Regenerate the vectors (deterministic)
pip install "cryptography>=42"
python conformance/tools/generate_vectors.py

# Check every vector against an independent implementation of the spec (Node.js 20+, no dependencies)
node conformance/tools/verify_vectors.mjs
```

`verify_vectors.mjs` implements the parts of the specification that the vectors exercise, using only WebCrypto. It is a cross-check that the vectors match the specification text, not a reference library.

## Current library status

These results are from testing the vectors in November 2026. The encrypted vector was tried with the TypeScript library only.

| Vector file | `@wemush/wols` 1.2.0 | `wols` 1.2.0 (Python) |
| ----------- | -------------------- | --------------------- |
| `embedded.json` | 10 of 13 pass. Rejects ULID, UUID, and other non-CUID suffixes. | 6 of 13 pass. Rejects every short ID, including the spec's own `wemush:clx1a2b3c4`. |
| `primordia.json` | 3 of 5 pass. Resolves the type but doesn't set the stage. | 1 of 5 pass. Rejects `PRIMORDIA` and `PINNING` as types. |
| `generation.json` | 6 of 10 pass. Doesn't know `transferDepth`. | 3 of 10 pass. ID rejection masks most cases. |
| `encrypted.json` | Fails. Uses a fixed salt and can't accept a per-label `salt`. | Not tried yet. Its format is known to differ (see [Interoperability Notes](../docs/interoperability-notes.md#2-encrypted-format)). |

The 1.3.0 draft introduced `transferDepth` and the `PRIMORDIA` stage rule, so the 1.2.0 libraries were expected to fail those cases. The ID failures are 1.2.0 conformance bugs.
