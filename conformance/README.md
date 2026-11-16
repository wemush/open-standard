# WOLS Conformance Test Vectors

Shared, language-neutral test cases that every WOLS implementation should pass. They target the **WOLS 1.3.0** wire format, which 1.3.1 and 1.4.0 don't change, plus the **1.4.0** signature scheme (currently release candidate `1.4.0-rc.1`, which builds on `1.3.1-rc.1`). See [SPECIFICATION.md](../SPECIFICATION.md).

## Files

| File | Covers | Operations |
| ---- | ------ | ---------- |
| [`vectors/embedded.json`](./vectors/embedded.json) | Embedded JSON-LD validation, ID formats | `validate` |
| [`vectors/primordia.json`](./vectors/primordia.json) | `PRIMORDIA` supplied as a type, alias resolution | `create` |
| [`vectors/generation.json`](./vectors/generation.json) | `generation`, `clonalGeneration`, `transferDepth` | `validate` |
| [`vectors/encrypted.json`](./vectors/encrypted.json) | Encrypted format wire specification, passphrase normalization, iteration limits | `derive`, `decrypt` |
| [`vectors/field-encryption.json`](./vectors/field-encryption.json) | Field-level encryption, AAD binding, identifying fields, total cost limit | `decryptFields` |
| [`vectors/signatures.json`](./vectors/signatures.json) | Ed25519 signatures over embedded labels and encrypted URLs, JCS canonicalization, verification statuses (1.4.0) | `sign`, `verify` |

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

What `expected` means for each operation:

- **`validate`**: The input is a specimen object.
  - `valid` is the required outcome.
  - `errorField`, when present, names the field that must be reported.
  - `warningField`, when present, names a field that should produce a warning without failing validation.
- **`create`**: The input is the argument to the implementation's specimen factory. Check the resulting `type` and `stage` (`null` means no stage), and whether a `warning` was emitted.
- **`derive`**: PBKDF2-HMAC-SHA256 intermediate value, provided for debugging key derivation.
- **`decrypt`**: The input is an encrypted URL plus a `secret`, which is either `{ kdf: "pbkdf2", passphrase }` or `{ kdf: "raw", keyBase64url }`.
  - On success, the decrypted bytes must equal `plaintext` exactly and parse to `specimen`.
  - `sig` and `sigVerified`, when present, check the reserved `sig` parameter. The decoder must keep `sig` with the decoded label, equal to this value, and must not report it as verified. `sigVerified` is always `false`, because decoding never verifies; verification is the separate `verify` operation. Implementations that don't expose URL parameters can check only that decryption succeeds.
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

### Signatures (`signatures.json`, 1.4.0)

`signatures.json` has the usual fields, with `wolsVersion` set to `"1.4.0"`, plus three more at the top level:

```json
{
  "wolsVersion": "1.4.0",
  "signingDomain": "WOLS-SIG-v1",
  "testKeys": {
    "mushoh-2026": { "seedBase64url": "…", "publicKeyBase64url": "…", "trusted": true },
    "acme-lab-1":  { "seedBase64url": "…", "publicKeyBase64url": "…", "trusted": true },
    "attacker-1":  { "seedBase64url": "…", "publicKeyBase64url": "…", "trusted": false }
  },
  "trustStore": {
    "mushoh-2026":  { "alg": "Ed25519", "publicKeyBase64url": "…" },
    "mushoh-alias": { "alg": "Ed25519", "publicKeyBase64url": "…" },
    "acme-lab-1":   { "alg": "Ed25519", "publicKeyBase64url": "…" }
  },
  "cases": [ ]
}
```

- **`testKeys`**: Ed25519 key pairs keyed by name. The seed is the 32-byte RFC 8032 private key; the public key is the 32-byte encoded point. Both are base64url without padding. Each seed is the SHA-256 of `WOLS 1.4.0 conformance test key: {name}`. These keys are public: **never use them for real labels.**
- **`trustStore`**: The trust store that every `verify` case uses, mapping kid to key. `mushoh-alias` is a second kid for the `mushoh-2026` key, so the vectors can check that the kid is signed. `attacker-1` is deliberately absent.
- **`signingDomain`**: The first line of every signing input.

Each case's `input.form` is `"embedded"` or `"encrypted-url"`. Embedded labels are given as **JSON text** in `input.label`, exactly as a scanner would read it. Parse that text yourself: several cases depend on how the text is spelled, such as escapes, number spellings, member order, and lone surrogates. Encrypted URLs are given in `input.url`.

- **`sign`**: Input is `{ form, label | url, kid, key }`. `key` names an entry in `testKeys`; sign with its seed, and put `kid` in the token.
  - `expected.signingInput` is the exact signing input, as a string. Encode it as UTF-8 to get the bytes Ed25519 signs. Compare it first when debugging.
  - `expected.signature` is the exact token, `{kid}.{base64url signature}`. Ed25519 is deterministic, so it must match byte for byte.
  - For `encrypted-url`, `expected.url` is the signed URL: `input.url` + `&sig=` + token.
  - For `embedded`, put the token in the label's top-level `signature` member. Member position isn't checked.
  - `sign-embedded-replaces-signature` gives a label that already has a `signature`. The signer ignores it, so the token is the same as for `sign-embedded`.
  - The `sign-jcs-*` cases exercise RFC 8785 member ordering, string escaping, and number formatting. Their `signingInput` shows the canonical form.
- **`verify`**: Input is `{ form, label | url }`. Verify against the file's `trustStore`.
  - `expected.status` is one of `valid`, `invalid`, `unknown-kid`, `malformed`, `unsigned`, and must match exactly.
  - When the status is `valid`, `expected.kid` is the kid to report. `expected.signingInput` is the input that verified, for debugging.
  - Statuses are checked in a fixed order (`unsigned`, then every `malformed` rule, then the trust store lookup, then the signature). So a case that breaks several rules has exactly one correct status.

To implement `signSpecimen` and `verifySpecimen` from this file:

1. **Signing input**: `"WOLS-SIG-v1\n" + form + "\n" + kid + "\n"` followed by the body.
2. **Embedded body**: Parse the label text, remove only the top-level `signature`, and produce the RFC 8785 (JCS) canonical form, encoded as UTF-8. A label that isn't an object, or that contains a lone surrogate or a non-finite number, is `malformed`.
3. **URL body**: The URL up to, but not including, its final `&sig=…` parameter, byte for byte, with nothing decoded or re-encoded. A URL without a parameter named exactly `sig` is `unsigned`. The URL is `malformed` if any of these hold:
   - `sig` is not the last parameter, or appears more than once.
   - The URL has a fragment.
   - The URL has a character outside `!` through `~`.
   - The URL doesn't start with `wemush://v1/encrypted/`.
4. **Token**: Matches `^[A-Za-z0-9_-]{1,64}\.[A-Za-z0-9_-]{86}$`, and the signature part decodes to 64 bytes whose base64url re-encoding is identical (the unused bits are zero). Anything else is `malformed`.
5. **Kid**: Not in the trust store means `unknown-kid`. Never fall back to a key in the label: the `*-untrusted-*` cases carry an attacker's `publicKey` in the label.
6. **Signature**: Ed25519 verification (RFC 8032 §5.1.7, rejecting `S ≥ L`) gives `valid` or `invalid`.

Signed labels must also keep decoding. `encrypted.json` has `decrypt-signed-url` and `embedded.json` has `signed-label-valid`. A 1.3.x decoder passes both, because it treats the token as the reserved value it preserves.

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

`1.4.0-rc.1` adds `signatures.json` (67 `MUST` cases), plus `decrypt-signed-url` in `encrypted.json` and `signed-label-valid` in `embedded.json`. Neither library implements signing or verification yet. Run against the 1.3.0 libraries, the two decoding cases pass: both decrypt a signed URL and keep its `sig` token unchanged, and both validate a signed embedded label.
