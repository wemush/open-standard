# WOLS Interoperability Notes

> **Status**: Non-normative. This document records where implementations of WOLS 1.2.0 currently differ from each other or from [SPECIFICATION.md](../SPECIFICATION.md). Where this document and the specification disagree, **the specification is authoritative**. Proposed resolutions are tracked in [ROADMAP.md](../ROADMAP.md#future-v130-q2-2026).

**Implementations reviewed**: `@wemush/wols` 1.2.0 (TypeScript), `wols` 1.2.0 (Python), and labels produced by the WeMush Platform.
**Last reviewed**: November 2026

---

## Summary

| Area | Interoperable today? | Safe choice for implementers |
| ---- | -------------------- | ---------------------------- |
| Embedded JSON-LD | ✅ Yes (verified round-trip in both directions), when `id` is `wemush:` + lowercase alphanumeric | Prefer embedded format for cross-system exchange |
| Compact URL | ⚠️ Partially | Use `wemush://`, full stage names, and the full species name in `s` |
| Encrypted format | ❌ No (cross-language) | Only exchange encrypted labels between identical implementations |
| ID formats | ⚠️ Partially | Use `wemush:` + lowercase alphanumeric (CUID-style) suffix |
| Type aliases | ⚠️ Partially | Emit canonical types; accept aliases on input |
| Generation semantics | ⚠️ Inconsistent in practice | Use `generation` only for filial generations |

---

## 1. Compact URL format

The specification documents `wemush://v1/{id}?s={species_code}&st={stage}&t={timestamp}` and its example uses a five-letter species code (`POSTR`) and full stage name (`COLONIZATION`).

| Aspect | Specification | TypeScript library | Python library |
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

The [Implementation Guide](./implementation-guide.md#appendix-species-codes-compact-format) defines the 5-letter species code table, which the TypeScript library follows and the Python library does not.

**Today**: Generate compact URLs with `wemush://`, full stage names, and full species names (or codes from the specification's example), and treat unrecognized parameters as optional.

## 2. Encrypted format

The specification documents `wemush://v1/encrypted/{id}?e={encrypted_payload}&sig={signature}` with AES-256-GCM. It does not define key derivation, IV/nonce transport, or payload encoding, so implementations chose differently:

| Aspect | TypeScript library | Python library |
| ------ | ------------------ | -------------- |
| Key input | Password string, derived with PBKDF2-SHA256 (fixed library salt, 100,000 iterations by default), or a `CryptoKey` | Raw 32-byte key, or base64 of one |
| IV / nonce | Separate 12-byte `iv` field | 12-byte nonce prepended to the ciphertext |
| Encoding | base64url without padding | Standard base64 |
| Self-description | Includes `algorithm`, `cryptoVersion`, `iterations` | None |

The WeMush Platform carries the IV in the URL as `?e={payload}&iv={iv}` instead of `sig`.

**Effect**: Encrypted labels cannot be decrypted across implementations, even with the same shared secret.

**Today**: Treat encrypted labels as implementation-specific. Don't rely on `sig` being present.

**Resolution (1.3.0 draft)**: The [Encrypted Format](../SPECIFICATION.md#3-encrypted-format-researchcommercial) now defines the wire format: `iv`, `kdf`, a per-label `salt`, `i`, and base64url encoding. Both libraries need updates to conform. The TypeScript changes are smaller: replace the fixed salt and carry `kdf`, `salt`, and `i` in the URL.

## 3. Specimen IDs

The specification states that implementations **MUST accept any non-empty suffix** after `wemush:`. Both libraries validate strictly by default (`wemush:[a-z0-9]+`). The TypeScript `parseSpecimen()` rejects a ULID such as `wemush:01ARZ3NDEKTSV4RRFFQ69G5FAV` unless a different ID mode is configured.

The WeMush Platform puts its human-readable identification code (for example `WM-LC-250114-000001`) in the `id` field **without** the `wemush:` prefix. Both libraries reject these labels, so the platform falls back to lenient parsing when it reads its own labels.

**Today**: Parsers should accept any non-empty suffix as the specification requires. Generators should emit `wemush:` + lowercase alphanumeric for the widest compatibility.

## 4. `PRIMORDIA` as a specimen type

The specification's Type Aliases note says implementations **MUST reject** `PRIMORDIA` as a specimen type. However, the 1.2.0 changelog lists `PRIMORDIA → FRUITING` as an alias and `PRIMORDIA` appears in `WOLS_TO_PLATFORM_MAP`. The libraries disagree: the published `@wemush/wols` 1.2.0 `createSpecimen()` silently resolves `type: "PRIMORDIA"` to `FRUITING`, while Python `create_specimen()` rejects it (its alias table includes the mapping, but creation doesn't apply it).

**Today**: Emit `type: "FRUITING", stage: "PRIMORDIA"`. Never emit `PRIMORDIA` as a type.

**Resolution (1.3.0 draft)**: `PRIMORDIA` supplied as a type resolves to `FRUITING` and defaults `stage` to `PRIMORDIA`, with a warning. The TypeScript library must also set the stage; the Python library must stop rejecting it.

## 5. `created` and `stage`

The core `SpecimenLabel` interface declares `stage` and `created` without `?`, which reads as required. In practice:

- The TypeScript `createSpecimen()` treats `stage` as optional and **never sets `created`**. Callers must assign it (`specimen.created = new Date().toISOString()`), or the compact URL omits `t`.
- The Python `create_specimen()` defaults `created` to the current time.
- Both validators accept specimens without `stage`.

**Today**: Always set `created` and `stage` when generating labels.

## 6. Generation without a strain

`generation` and `clonalGeneration` live under `strain`, and `strain.name` is required. A specimen with a known generation but no named strain therefore cannot record its generation in standard fields. The WeMush Platform omits generation in this case.

## 7. Extended data fields

The specification defines `EnvironmentalData`, `SubstrateFormula`, and `CircularEconomyData` but does not say where they attach to a specimen. The REST example response uses `metadata.substrate` and `observations`, and neither is a known field in the core model. Both validators accept such specimens but emit an `UNKNOWN_FIELD` warning.

**Today**: Carry extended data under `custom.{namespace}` using the field names from the specification's interfaces.

## 8. Lineage

`strain.lineage` holds a single parent specimen ID. Some workflows have more than one parent: combined spawn, multi-spore isolates, or a retail package made from several blocks. The only way to record the additional parents today is under `custom`.

## 9. Generation semantics

The specification defines `strain.generation` as the *filial* (sexual) generation and `strain.clonalGeneration` as the subculture count. The WeMush Platform increments a single generation counter on every transfer (culture → grain → substrate) and emits it as `strain.generation: "F{n}"`. As a result, platform labels can show `F3` for a third-transfer block of the original strain.

**Today**: Readers shouldn't assume that `F{n}` on a label produced before this note reflects sexual generations. Generators should keep `generation` constant across expansion transfers and record ancestry with `strain.lineage`.

**Resolution (1.3.0 draft)**: The new `strain.transferDepth` field carries a per-transfer counter. Platforms that count transfers must emit it as `transferDepth` instead of `generation` (see [Generation, Subculture, and Transfer Tracking](../SPECIFICATION.md#generation-subculture-and-transfer-tracking-v130)).

## 10. Scannability with phone cameras

Native phone camera apps generally don't open custom schemes such as `wemush://` or `web+wemush://`. The WeMush Platform registers `web+wemush://` as a PWA protocol handler and also prints plain HTTPS tracking URLs for camera scanning. WOLS 1.2.0 doesn't define an HTTPS form. The Python library's HTTPS form (`https://wemush.com/s/v1/{id}`) is not a resolver endpoint on wemush.com today.

---

## Reporting a divergence

Open an issue at [github.com/wemush/open-standard](https://github.com/wemush/open-standard/issues) with:

- the implementation and version
- the exact payload produced or rejected
- the section of the specification involved
