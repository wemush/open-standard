# WOLS Interoperability Notes

> **Status**: Non-normative. This document records where implementations of WOLS currently differ from each other or from [SPECIFICATION.md](../SPECIFICATION.md). Where this document and the specification disagree, **the specification is authoritative**. Proposed resolutions are tracked in [ROADMAP.md](../ROADMAP.md#next-v160).

**Implementations reviewed**: `@wemush/wols` 1.5.0 (TypeScript), `wols` 1.5.0 (Python), and labels produced by the WeMush Platform. Both 1.5.0 libraries pass every `MUST` and `SHOULD` case in the [conformance vectors](../conformance/README.md), including the 1.5 files (`data-model.json`, `bundle.json`, `compact.json` and `compact-signatures.json`). Both test suites also run the 51-case [interop matrix](../conformance/interop/README.md), in which each library decrypts the other's labels; both libraries have passed it since 1.4.0. Notes about 1.4.0, 1.3.0 and 1.2.0 behavior are kept where older labels or libraries may still be in use.
**Last reviewed**: November 28, 2026

---

## Summary

| Area | Interoperable today? | Safe choice for implementers |
| ---- | -------------------- | ---------------------------- |
| Embedded JSON-LD | ✅ Yes (conformance vectors, 1.3.0 and later libraries) | Prefer embedded format for cross-system exchange |
| Compact URL | ✅ Yes (`compact.json` vectors, 1.5.0 libraries); ⚠️ only partially with 1.4.x and earlier | Use `wemush://` and the registered species code, or the full species name when there is none |
| Encrypted format | ✅ Yes for the 1.3.0 wire format; ❌ not for labels made by 1.2.0 libraries | Generate with a 1.3.0 or later library; decode legacy labels only with the library that made them |
| ID formats | ✅ Yes for `wemush:` + any non-empty suffix (1.3.0 and later libraries) | Emit `wemush:` + lowercase alphanumeric for older readers |
| Type aliases and `PRIMORDIA` | ✅ Yes (1.3.0 and later libraries) | Emit canonical types; accept aliases on input |
| Signatures | ✅ Yes (conformance vectors; 1.4.0 libraries for embedded labels and encrypted URLs, 1.5.0 libraries for compact URLs too) | Resolve keys only from your own trust store |
| Numeric `strain.generation` | ✅ Yes in 1.4.0 and later libraries; ❌ TypeScript 1.3.0 rejects it | Write `generation` as a string |
| 1.5 label members | ✅ Yes (`data-model.json` vectors, 1.5.0 libraries); 1.4.x libraries warn and drop them on re-save | Re-save labels that carry them only with a 1.5.0 or later library |
| `_meta` key spelling | ✅ Yes (1.5.0 libraries write camelCase and read either) | Write `sourceId`, `sourceSystem`, `importedAt`, `schemaVersion` |
| Generation semantics | ⚠️ Inconsistent in older labels | Use `generation` only for filial generations and `transferDepth` for transfers |

---

## 1. Compact URL format

**Resolved in 1.5.0.** The rest of this section describes the 1.4.0 and earlier libraries, whose compact URLs other readers may still meet.

Before 1.5.0 the specification documented `wemush://v1/{id}?s={species_code}&st={stage}&t={timestamp}` and its example used a five-letter species code (`POSTR`) and full stage name (`COLONIZATION`).

| Aspect | Specification (before 1.5.0) | TypeScript library | Python library |
| ------ | ------------- | ------------------ | -------------- |
| Default scheme | `wemush://` | `wemush://` | `web+wemush://` (also supports `wemush://` and `https://{base}/v1/{id}`) |
| Species code (`s`) | Example: `POSTR` | 5-letter codes (`POSTR`), falls back to the full species name | 2-letter codes (`PO`); raises an error if the species has no code |
| Stage (`st`) | Example: `COLONIZATION` | Full stage name | 3-letter code (`COL`) |
| Timestamp (`t`) | Unix seconds | Emitted when `created` is set | Not emitted |
| Additional parameters | Not specified | `ty` (type), `b` (batch), `sn` (strain name), `sg` (strain generation) | None |
| Version reported on parse | Not specified | `1.1.0` for any `v1` path | Not reported |
| Parsed `id` | Not specified | Re-adds the `wemush:` prefix | Returns the bare suffix |

**Effect** (verified by round-tripping both libraries):

- The TypeScript parser **rejects** the Python default `web+wemush://…` URL outright ("URL must start with wemush://").
- For a Python `wemush://…?s=PO&st=COL` URL, the TypeScript parser returns `species: "PO"` and `stage: "COL"`, neither of which is a valid value.
- For a TypeScript `wemush://…?s=POSTR&st=COLONIZATION…` URL, the Python parser drops the stage and leaves `POSTR` unresolved.

The 1.3.0 and 1.4.0 libraries don't change compact URL output. The Python parser accepts both `wemush://` and `web+wemush://`; the TypeScript parser still accepts only `wemush://`.

**In 1.5.0**: The specification settles every row above in [Compact URL rules](../SPECIFICATION.md#compact-url-rules-v150) and the [Species Code Registry](../SPECIFICATION.md#species-code-registry-v150), and [`compact.json`](../conformance/vectors/compact.json) tests it. Decoders read both schemes, both stage spellings, the 27 registered five-letter codes, and the 24 two-letter codes that earlier Python releases wrote, as legacy codes with a warning. Generators write the registered code, or the full species name when the species has none, and never a legacy code. `td` (`strain.transferDepth`) is registered, unregistered parameters are kept rather than rejected, and new parameters defined outside the specification start with `x-`. The decoded ID is `wemush:` plus the percent-decoded path segment, and the `v1` segment names the major version only. Both 1.5.0 libraries pass every `compact.json` case, so a compact URL that either one writes decodes to the same label in both. The Python `to_compact_url()` still writes `web+wemush://` by default; pass `scheme="wemush"` for the form the specification recommends, and for any URL you will sign.

**Today**: Generate compact URLs with a 1.5.0 or later library and the `wemush://` scheme. If they must also scan in 1.4.x or earlier readers, expect partial results, as the table above shows: the TypeScript parser rejects `web+wemush://`, reads only full stage names and leaves two-letter codes unresolved, and the Python parser reads only three-letter stage codes and leaves five-letter codes unresolved.

## 2. Encrypted format

**Resolved in 1.3.0.** The [Encrypted Format](../SPECIFICATION.md#3-encrypted-format-researchcommercial) now defines the wire format: `iv`, `kdf`, a per-label `salt`, `i`, base64url encoding, NFC-normalized passphrases, iteration limits, and field-level AAD. Both 1.3.0 libraries pass the `encrypted` and `field-encryption` conformance vectors, so labels made by one decrypt with the other.

The rest of this section describes the **1.2.0** libraries, whose labels are still not interchangeable. WOLS 1.2.0 documented `wemush://v1/encrypted/{id}?e={encrypted_payload}&sig={signature}` with AES-256-GCM but did not define key derivation, IV/nonce transport, or payload encoding, so implementations chose differently:

| Aspect | TypeScript library | Python library |
| ------ | ------------------ | -------------- |
| Key input | Password string, derived with PBKDF2-SHA256 (fixed library salt, 100,000 iterations by default), or a `CryptoKey` | Raw 32-byte key, or base64 of one |
| IV / nonce | Separate 12-byte `iv` field | 12-byte nonce prepended to the ciphertext |
| Encoding | base64url without padding | Standard base64 |
| Self-description | Includes `algorithm`, `cryptoVersion`, `iterations` | None |

The WeMush Platform carries the IV in the URL as `?e={payload}&iv={iv}` instead of `sig`.

**Effect**: Encrypted labels made by the 1.2.0 libraries cannot be decrypted across implementations, even with the same shared secret.

**Today**: Generate encrypted labels with a 1.3.0 or later library. These libraries never generate the legacy formats; decoding them is available only behind an explicit option. `@wemush/wols` 1.3.0 normalized the passphrase to NFC on that legacy path too, so a 1.2.x label made with a non-NFC passphrase failed to open; 1.4.0 derives legacy keys as 1.2.x did. Don't rely on `sig` being present, and verify it only with the [signature scheme](#12-signatures).

## 3. Specimen IDs

The specification states that implementations **MUST accept any non-empty suffix** after `wemush:`. **Resolved in the 1.3.0 libraries**, which accept any non-empty suffix by default and keep strict CUID/ULID checks as an opt-in mode. The 1.2.0 libraries validated strictly by default: TypeScript rejected ULIDs such as `wemush:01ARZ3NDEKTSV4RRFFQ69G5FAV`, and Python required a full-length CUID, rejecting even the specification's example ID `wemush:clx1a2b3c4`.

The WeMush Platform puts its human-readable identification code (for example `WM-LC-250114-000001`) in the `id` field **without** the `wemush:` prefix. Both libraries reject these labels, so the platform falls back to lenient parsing when it reads its own labels.

**Today**: Generators should emit `wemush:` + lowercase alphanumeric for the widest compatibility with older readers.

## 4. `PRIMORDIA` as a specimen type

**Resolved in 1.3.0.** `PRIMORDIA` supplied as a type resolves to `FRUITING` and defaults `stage` to `PRIMORDIA`, with a warning, and is never emitted as a type. Both 1.3.0 libraries pass the `primordia` conformance vectors.

The 1.2.0 specification said implementations **MUST reject** `PRIMORDIA` as a type, which conflicted with its own alias table. The 1.2.0 libraries disagreed: TypeScript resolved it to `FRUITING` without setting the stage, and Python rejected it.

**Today**: Emit `type: "FRUITING", stage: "PRIMORDIA"`.

## 5. `created` and `stage`

**Resolved in 1.5.0.** Both are optional, and generators SHOULD write both. When present, `created` MUST be an RFC 3339 date-time with a time offset; a date alone is invalid (see [Required and optional members](../SPECIFICATION.md#required-and-optional-members)). The `wols` 1.5.0 Python library reports a `created` without a time zone as a validation error, and treats a datetime without one passed to `create_specimen(created=...)` as UTC, with a `WolsWarning`.

Before 1.5.0 the core `SpecimenLabel` interface declared `stage` and `created` without `?`, which read as required. In practice:

- The TypeScript `createSpecimen()` treats `stage` as optional and doesn't set `created` unless the caller passes it. Since 1.3.0 it accepts a `created` input (ISO 8601 string or `Date`); without one, the compact URL omits `t`.
- The Python `create_specimen()` defaults `created` to the current time.
- Both validators accept specimens without `stage`.

**Today**: Always set `created` and `stage` when generating labels.

## 6. Generation without a strain

`generation` and `clonalGeneration` live under `strain`, and before 1.5.0 `strain.name` was required. A specimen with a known generation but no named strain therefore couldn't record its generation in standard fields. The WeMush Platform omits generation in this case.

**Resolved in 1.5.0**: `strain.name` is optional, so `generation`, `clonalGeneration` and `transferDepth` can be recorded for a strain that has no name. Both 1.5.0 libraries accept such a strain.

## 7. Extended data fields

The specification defines `EnvironmentalData`, `SubstrateFormula`, and `CircularEconomyData` but does not say where they attach to a specimen. The REST example response uses `metadata.substrate` and `observations`, and neither is a known field in the core model. Both validators accept such specimens but emit an `UNKNOWN_FIELD` warning.

**Resolved in 1.5.0**: The [Records Bundle](../SPECIFICATION.md#records-bundle-v150) carries this data next to the labels, for exchange between systems: `Observation.environment` replaces `EnvironmentalData`, `Recipe` replaces `SubstrateFormula`, and a `SpecimenRecord` holds `circularEconomy`. Both 1.5.0 libraries validate bundles. A bundle is never printed in a QR code.

**Today**: Exchange extended data in a Records Bundle. On a printed label, carry it under `custom.{namespace}`.

## 8. Lineage

`strain.lineage` holds a single parent specimen ID. Some workflows have more than one parent: combined spawn, multi-spore isolates, or a retail package made from several blocks. Before 1.5.0 the only way to record the additional parents was under `custom`.

**Resolved in 1.5.0**: The `derivedFrom` member lists every parent, each with an optional `relation` and `quantity`. `strain.lineage` stays for 1.4 readers, and when both are present it MUST equal `derivedFrom[0].id`.

## 9. Generation semantics

The specification defines `strain.generation` as the *filial* (sexual) generation and `strain.clonalGeneration` as the subculture count. The WeMush Platform increments a single generation counter on every transfer (culture → grain → substrate) and emits it as `strain.generation: "F{n}"`. As a result, platform labels can show `F3` for a third-transfer block of the original strain.

**Today**: Readers shouldn't assume that `F{n}` on a label produced before this note reflects sexual generations. Generators should keep `generation` constant across expansion transfers and record ancestry with `strain.lineage`.

**Resolved in 1.3.0**: The `strain.transferDepth` field carries a per-transfer counter, and both 1.3.0 libraries support it. Platforms that count transfers should emit it as `transferDepth` instead of `generation` (see [Generation, Subculture, and Transfer Tracking](../SPECIFICATION.md#generation-subculture-and-transfer-tracking-v130)). From 1.5.0 compact URLs carry it as the `td` parameter.

## 10. Scannability with phone cameras

Native phone camera apps generally don't open custom schemes such as `wemush://` or `web+wemush://`. The WeMush Platform registers `web+wemush://` as a PWA protocol handler and also prints plain HTTPS tracking URLs for camera scanning. WOLS 1.5.0 doesn't define an HTTPS form either: decoders MAY accept one such as `https://{host}/{path}/v1/{id}`, and the resolver form itself is planned for a later release. The Python library's HTTPS form (`https://wemush.com/s/v1/{id}`) is not a resolver endpoint on wemush.com today.

## 11. Numeric `strain.generation`

The specification types `strain.generation` as a string. The Python `wols` 1.3.0 library accepted a JSON integer there and wrote it unchanged (for example `"generation": 1`). The TypeScript `@wemush/wols` 1.3.0 library rejects such a label, including after decrypting it.

**Resolved in 1.4.0**: Generators MUST write a string, and decoders SHOULD read a JSON integer as its decimal string, with a warning (see [Generation Notation](../SPECIFICATION.md#generation-notation-v120)). The `SHOULD` conformance cases are `generation-numeric`, `decrypt-numeric-generation`, and `decrypt-fields-numeric-generation`. Both 1.4.0 libraries pass them and always write a string.

## 12. Signatures

WOLS 1.4.0 defines Ed25519 signatures for embedded labels and encrypted URLs (see [Cryptographic Signatures](../SPECIFICATION.md#cryptographic-signatures)). Both 1.4.0 libraries sign and verify, and pass every `signatures.json` vector. The 1.3.0 libraries can't verify, but they decode signed labels and keep the token unchanged.

**In 1.5.0**: Compact URLs can be signed too, under the form `compact-url`, over the exact URL bytes before `&sig=` ([Compact URL signatures](../SPECIFICATION.md#compact-url-signatures-v150)). Both 1.5.0 libraries sign and verify them and pass every `compact-signatures.json` case, including the optional unwrap step for `web+wemush://` and `https://{host}/wols/` links. A 1.4 verifier still reports a signed compact URL as `malformed`; show that as "signature not verifiable by this app", not as tampering. Decoding is unaffected: both 1.4.0 libraries decode a signed compact URL exactly as the unsigned one.

**Today**: Resolve kids only through a trust store you control, never from the label, and treat any status other than `valid` as unverified.

## 13. `_meta` key spelling

The Python `wols` 1.4.0 library wrote the standard `_meta` keys in snake_case (`source_id`, `source_system`, `imported_at`, `schema_version`); the TypeScript library wrote camelCase.

**Resolved in 1.5.0**: Generators MUST write camelCase (`sourceId`, `sourceSystem`, `importedAt`, `schemaVersion`). Decoders SHOULD read snake_case and re-encode it in camelCase; when a label has both spellings of a key, they use the camelCase value and keep the snake_case member unchanged (see [Decoding, unknown members and `_meta`](../SPECIFICATION.md#decoding-unknown-members-and-_meta)). Both 1.5.0 libraries write camelCase on the wire.

---

## Reporting a divergence

Open an issue at [github.com/wemush/open-standard](https://github.com/wemush/open-standard/issues) with:

- the implementation and version
- the exact payload produced or rejected
- the section of the specification involved
