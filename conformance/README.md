# WOLS Conformance Test Vectors

Shared, language-neutral test cases that every WOLS implementation should pass. They target **WOLS 1.3.0**, except `signatures.json`, which targets the **1.4.0-rc.1** release candidate. See [SPECIFICATION.md](../SPECIFICATION.md).

## Files

| File | Covers | Operations |
| ---- | ------ | ---------- |
| [`vectors/embedded.json`](./vectors/embedded.json) | Embedded JSON-LD validation, ID formats | `validate` |
| [`vectors/primordia.json`](./vectors/primordia.json) | `PRIMORDIA` supplied as a type, alias resolution | `create` |
| [`vectors/generation.json`](./vectors/generation.json) | `generation`, `clonalGeneration`, `transferDepth` | `validate` |
| [`vectors/encrypted.json`](./vectors/encrypted.json) | Encrypted format wire specification, passphrase normalization, iteration limits | `derive`, `decrypt` |
| [`vectors/field-encryption.json`](./vectors/field-encryption.json) | Field-level encryption, AAD binding, identifying fields, total cost limit | `decryptFields` |
| [`vectors/signatures.json`](./vectors/signatures.json) | Ed25519 signatures on embedded labels and encrypted URLs (1.4.0-rc.1) | `sign`, `verify` |
| [`keys/test-keys.json`](./keys/test-keys.json) | Ed25519 test keys used by `signatures.json` | — |

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
      "operation": "validate | create | derive | decrypt | decryptFields | sign | verify",
      "requirement": "MUST | SHOULD",
      "description": "…",
      "input": { },
      "expected": { }
    }
  ]
}
```

`signatures.json` also has a top-level `testKeys` member with the path of the key file, and its `wolsVersion` is `1.4.0-rc.1`.

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

- **`sign`** (`signatures.json`): The input has a `form` (`embedded` or `url`), the unsigned `label` (an object) or `url` (a string), a `kid`, and the signer's 32-byte Ed25519 private key as `privateKeyBase64url`. Ed25519 is deterministic, so the output must match exactly:
  - `payload` is the payload as a string: the JCS form of the label without `signature` (embedded), or the URL up to the final `&sig=` (URL). The bytes actually signed are `WOLS-SIG-1`, a line feed, then the UTF-8 payload.
  - `signature` is the expected signature, base64url without padding.
  - `label` (embedded) is the signed label object, with `kid` and `signature` set. Its member order doesn't matter. `url` (URL) is the exact signed URL.
- **`verify`** (`signatures.json`): The input has a `form`, the `label` as the exact text a scanner would read (a JSON string for `embedded`, deliberately not in canonical form; a URL for `url`), and a `trustStore` mapping each trusted `kid` to its public key, base64url. The verifier must report `expected.outcome` exactly. Verification never needs a decryption key, and the trust store is the only source of keys: a case passes only if nothing in the label is used as a key.

  | Outcome | Meaning |
  | ------- | ------- |
  | `unsigned` | No `kid`: no signature, or an opaque pre-1.4 `signature`/`sig`. Decode normally, preserve any `sig`, don't treat as verified |
  | `malformed` | `kid` present, but the signature fields break the encoding or structure rules |
  | `unknown-kid` | Well-formed, but `kid` isn't in the trust store |
  | `invalid` | The trusted key for `kid` doesn't verify the signature |
  | `valid` | The signature verifies with the trusted key for `kid` |

A case marked `SHOULD` is recommended behavior. An implementation that skips it can still conform.

> **Fixed salts and IVs**: The encrypted vectors use fixed salts and IVs so the output is reproducible. Real generators **MUST** use fresh random values.

## Passing the signature vectors

To pass `signatures.json`, an implementation must:

1. Canonicalize embedded labels with RFC 8785 (JCS), not with its usual serializer. The `sign-embedded-jcs` case checks UTF-16 member ordering (`🍄` sorts before `ﬁ`), ECMAScript number formatting (`0.000001`, `1e-7`, `1e+21`), minimal string escapes, and no Unicode normalization. In Python, the general-purpose `json` module gets the number and ordering rules wrong; use an RFC 8785 library such as `rfc8785`, or check your own code against this case.
2. Remove only the top-level `signature` member before canonicalizing, and keep `kid` in the payload.
3. Sign URLs over the exact bytes before the final `&sig=`, with no decoding, re-encoding, or reordering. `verify-url-hostile-id-reencoded` and `verify-url-reordered` fail any verifier that normalizes the URL.
4. Prefix the payload with `WOLS-SIG-1` and a line feed before signing or verifying.
5. Accept only exactly 86 canonical base64url characters for a signature, and reject non-canonical scalars (`verify-embedded-malleable`). Standard Ed25519 libraries (OpenSSL, WebCrypto, libsodium, `cryptography`) already do the latter.
6. Look up `kid` in the supplied trust store and nowhere else. `verify-embedded-self-asserted-key` carries the attacker's public key in the label.
7. Decide the outcome in the order given in the specification (`unsigned`, `malformed`, `unknown-kid`, then `invalid` or `valid`), so a broken signature under an unknown `kid` is `malformed`.
8. Keep decoding unsigned, legacy-signed, and failed-signature labels as before. Signature checks don't change the `decrypt` or `decryptFields` results.

### Test keys

[`keys/test-keys.json`](./keys/test-keys.json) holds three Ed25519 key pairs, taken from the RFC 8032 §7.1 test vectors so anyone can check them. Their private keys are public. They exist only for this suite:

| `kid` | RFC 8032 | In `trustStore` | Role |
| ----- | -------- | --------------- | ---- |
| `example.org:test-1` | TEST 1 | Yes | The legitimate signer |
| `example.org:test-2` | TEST 3 | Yes | A second trusted key, for wrong-`kid` cases |
| `attacker.example:k1` | TEST 2 | No | An attacker who re-signs edited labels |

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

Results against the `1.3.0` vectors, and the `1.4.0-rc.1` signature vectors, November 2026:

| Library | embedded | primordia | generation | encrypted | field-encryption | signatures |
| ------- | -------- | --------- | ---------- | --------- | ---------------- | ---------- |
| [`@wemush/wols`](https://github.com/wemush/specimen-labels-js) 1.3.0 (TypeScript) | 12/12 + 1/1 | 4/4 + 1/1 | 9/9 + 1/1 | 19/19 + 2/2 | 6/6 | Not implemented |
| [`wols`](https://github.com/wemush/specimen-labels-py) 1.3.0 (Python) | 12/12 + 1/1 | 4/4 + 1/1 | 9/9 + 1/1 | 19/19 + 2/2 | 6/6 | Not implemented |

Each cell shows `MUST` cases passed, then `SHOULD` cases passed. Both libraries vendor these vectors with matching `SHA256SUMS`.
