# WOLS Conformance Test Vectors

Shared, language-neutral test cases that every WOLS implementation should pass. They target the **WOLS 1.3.0** wire format, which 1.3.1 doesn't change (currently release candidate `1.3.1-rc.1`, which adds one case). See [SPECIFICATION.md](../SPECIFICATION.md).

## Files

| File | Covers | Operations |
| ---- | ------ | ---------- |
| [`vectors/embedded.json`](./vectors/embedded.json) | Embedded JSON-LD validation, ID formats | `validate` |
| [`vectors/primordia.json`](./vectors/primordia.json) | `PRIMORDIA` supplied as a type, alias resolution | `create` |
| [`vectors/generation.json`](./vectors/generation.json) | `generation`, `clonalGeneration`, `transferDepth` | `validate` |
| [`vectors/encrypted.json`](./vectors/encrypted.json) | Encrypted format wire specification, passphrase normalization, iteration limits | `derive`, `decrypt` |
| [`vectors/field-encryption.json`](./vectors/field-encryption.json) | Field-level encryption, AAD binding, identifying fields, total cost limit | `decryptFields` |

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
      "operation": "validate | create | derive | decrypt | decryptFields",
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
  - `sig` and `sigVerified`, when present, check the reserved `sig` parameter. The decoder must keep `sig` with the decoded label, equal to this value, and must not report it as verified (`sigVerified` is always `false` in 1.3.x). Implementations that don't expose URL parameters can check only that decryption succeeds.
  - On failure, decryption must be refused. `reason` is a suggested error category and doesn't have to match exactly.
- **Suggested `reason` values**:

  | Reason | Meaning |
  | ------ | ------- |
  | `invalid-url` | Not an encrypted URL |
  | `invalid-encoding` | Malformed percent-encoding, or a decoded value that is not valid UTF-8 |
  | `missing-parameter` | A required parameter is absent |
  | `unexpected-parameter` | A parameter appears where it's forbidden |
  | `invalid-parameter` | A parameter is malformed (for example, `i` that isn't plain decimal digits) |
  | `legacy-format` | A URL or field object without `kdf` (pre-1.3.0) |
  | `unsupported-kdf` | Unknown `kdf` value |
  | `insufficient-iterations` | Fewer than 10,000 PBKDF2 iterations |
  | `excessive-iterations` | More than 10,000,000 PBKDF2 iterations, alone or in total |
  | `invalid-key` | Wrong key length |
  | `authentication-failed` | AES-GCM authentication failed |
  | `invalid-plaintext` | The plaintext has a byte order mark or isn't valid JSON |
  | `id-mismatch` | The decrypted `id` doesn't match the URL |
  | `identifying-field` | An identifying field is encrypted |

- **`decryptFields`**: The input is an embedded label whose fields may hold field-level encryption objects, plus a `secret` in the same form as `decrypt`.
  - On success, decrypting every encrypted field must produce `specimen`.
  - On failure, the label must be refused, with `reason` as for `decrypt`.

A case marked `SHOULD` is recommended behavior. An implementation that skips it can still conform.

> **Fixed salts and IVs**: The encrypted vectors use fixed salts and IVs so the output is reproducible. Real generators **MUST** use fresh random values.

## Checksums

[`vectors/SHA256SUMS`](./vectors/SHA256SUMS) lists the SHA-256 hash of every vector file, in `sha256sum` format. Implementations that vendor the vectors can check what they copied with `sha256sum -c SHA256SUMS`. The generator rewrites the file, and the verifier checks it.

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

Results against the `1.3.0` vectors, November 2026:

| Library | embedded | primordia | generation | encrypted | field-encryption |
| ------- | -------- | --------- | ---------- | --------- | ---------------- |
| [`@wemush/wols`](https://github.com/wemush/specimen-labels-js) 1.3.0 (TypeScript) | 12/12 + 1/1 | 4/4 + 1/1 | 9/9 + 1/1 | 19/19 + 2/2 | 6/6 |
| [`wols`](https://github.com/wemush/specimen-labels-py) 1.3.0 (Python) | 12/12 + 1/1 | 4/4 + 1/1 | 9/9 + 1/1 | 19/19 + 2/2 | 6/6 |

Each cell shows `MUST` cases passed, then `SHOULD` cases passed. Both libraries vendor these vectors with matching `SHA256SUMS`.

`1.3.1-rc.1` adds one `MUST` case, `decrypt-with-sig`, to `encrypted.json` (20 `MUST` cases in total). Both 1.3.0 libraries already preserve `sig` without verifying it, but neither has yet run this case against its vendored vectors.
