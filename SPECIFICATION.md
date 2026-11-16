# WeMush Open Labeling Standard

> 📖 **Read Online**: [wemush.com/open-standard/specification](https://wemush.com/open-standard/specification)

**Status**: Release candidate — public comment period (see [Governance](#governance))
**Version**: 1.4.0-rc.1
**Date**: November 16, 2026
**Authors**: [Amy Beacom](https://github.com/abeacom), [Mark Beacom](https://github.com/mbeacom), [WeMush Foundation](https://github.com/wemush)
**License**: CC BY 4.0

The WOLS specification and reference libraries are open source.

The WeMush Platform (which implements WOLS) is proprietary
but offers a generous free tier.

This model ensures:
✅ Interoperability (anyone can support WOLS)
✅ Innovation (companies can build competing platforms)
✅ Sustainability (WeMush can fund development)

---

## Executive Summary

The WeMush Open Labeling Standard (WOLS) is an open-source specification for encoding cultivation specimen data in machine-readable QR codes. WOLS enables:

- **Traceability**: Complete lineage tracking from culture to harvest
- **Interoperability**: Vendor-agnostic data exchange between platforms
- **Transparency**: Verifiable cultivation practices for circular food systems
- **Privacy**: Cryptographic options for sensitive research data

This standard is designed for mushroom cultivation but extensible to any biological specimen tracking application.

---

## Design Principles

1. **Open by Default**: No licensing fees, no vendor lock-in
2. **Privacy-Preserving**: Support for both public and encrypted data
3. **Extensible**: Custom fields without breaking compatibility
4. **Offline-First**: QR codes work without internet connectivity
5. **Research-Grade**: Sufficient detail for scientific reproducibility

---

## Core Data Model

### Specimen Object (Core)

The foundational entity representing a biological specimen at any stage of cultivation. WOLS uses JSON-LD format for semantic web interoperability.

```typescript
interface SpecimenLabel {
  // JSON-LD Context (Required)
  "@context": string;            // Schema URL: "https://wemush.com/wols/v1"
  "@type": string;               // Entity type: "Specimen"

  // Required Fields
  id: string;                    // Unique identifier with wemush: prefix (e.g., "wemush:clx1a2b3c4")
  version: string;               // Spec version (e.g., "1.3.0")
  type: SpecimenType;            // CULTURE | SPAWN | SUBSTRATE | FRUITING | HARVEST
  species: string;               // Scientific name (e.g., "Pleurotus ostreatus")

  // Taxonomy & Genetics
  strain?: {
    name: string;                // Strain name or identifier
    generation?: string;         // Filial generation (e.g., "F1", "F2", "P")
    clonalGeneration?: number;   // Culture-to-culture subculture count (0 = original culture)
    transferDepth?: number;      // Total transfers from the original culture, any kind (v1.3.0)
    lineage?: string;            // Parent specimen ID reference
    source?: string;             // "spore", "tissue", "agar", "liquid"
  };

  // Lifecycle Tracking
  stage: GrowthStage;            // INOCULATION | INCUBATION | COLONIZATION | PRIMORDIA | FRUITING | SENESCENCE | HARVEST
  created: string;               // ISO 8601 timestamp
  batch?: string;                // Associated batch identifier

  // Attribution
  organization?: string;         // Organization ID
  creator?: string;              // User ID (optional for privacy)

  // Extensibility
  custom?: Record<string, any>; // Vendor-specific extensions

  // Implementation Metadata (v1.2.0)
  _meta?: {
    sourceId?: string;           // Original ID from source system
    sourceSystem?: string;       // Identifier of importing system
    importedAt?: string;         // ISO 8601 import timestamp
    schemaVersion?: string;      // Source system schema version
    [key: string]: unknown;      // Extensible for implementation use
  };

  // Verification (Optional, v1.4.0: see Cryptographic Signatures)
  signature?: string;            // Signature token "{kid}.{sig}"; verified only against a caller-supplied trust store
}
```

### Specimen Types

```typescript
enum SpecimenType {
  CULTURE = "CULTURE",         // Agar, liquid culture
  SPAWN = "SPAWN",             // Grain spawn, sawdust spawn
  SUBSTRATE = "SUBSTRATE",     // Inoculated substrate
  FRUITING = "FRUITING",       // Fruiting block/bag
  HARVEST = "HARVEST",         // Harvested mushrooms
}

enum GrowthStage {
  INOCULATION = "INOCULATION",   // Initial inoculation of substrate/medium
  INCUBATION = "INCUBATION",     // Post-inoculation monitoring period (v1.2.0)
  COLONIZATION = "COLONIZATION", // Active mycelial colonization
  PRIMORDIA = "PRIMORDIA",       // Pin initiation stage (v1.2.0)
  FRUITING = "FRUITING",         // Active fruiting body development
  SENESCENCE = "SENESCENCE",     // End-of-life/declining productivity (v1.2.0)
  HARVEST = "HARVEST",           // Harvested mushrooms
}
```

### Type Aliases (v1.2.0)

Implementations SHOULD support common type aliases to improve usability:

| Alias | Canonical Type |
| ----- | -------------- |
| LIQUID_CULTURE, LC, AGAR, PETRI, SLANT, CULTURE_PLATE | CULTURE |
| GRAIN_SPAWN, SAWDUST_SPAWN, PLUG_SPAWN, DOWEL | SPAWN |
| BLOCK, BAG, BED, LOG, BUCKET | SUBSTRATE |
| FLUSH, PINNING, FRUIT, FIRST_FLUSH | FRUITING |
| FRESH, DRIED, PROCESSED, EXTRACT | HARVEST |

**Note — `PRIMORDIA` (v1.3.0)**: `PRIMORDIA` is a `GrowthStage` value (not a `SpecimenType`), representing the pin initiation phase. A `FRUITING` type specimen progresses through stages including `PRIMORDIA` → `FRUITING` → `SENESCENCE`. Because users commonly supply it as a type, `PRIMORDIA` is a reserved type alias with special handling. When `PRIMORDIA` is supplied as a specimen type, implementations:

- MUST resolve the type to `FRUITING`
- MUST set `stage` to `PRIMORDIA` if no stage was supplied, and MUST NOT override a stage that was supplied
- SHOULD emit a warning recommending `type: "FRUITING", stage: "PRIMORDIA"`
- MUST NOT emit `PRIMORDIA` as a `type` value in any serialized label

This replaces the v1.2.0 requirement to reject `PRIMORDIA` as a type. That requirement conflicted with the v1.2.0 alias table. See Extended Growth Stages below.

Custom aliases can be registered via library functions. Alias resolution is case-insensitive.

### Extended Growth Stages (v1.2.0)

WOLS v1.2.0 introduces research-grade lifecycle tracking with 7 growth stages:

| Stage | Description | Typical Duration | Key Observations |
| ----- | ----------- | ---------------- | ---------------- |
| **INOCULATION** | Initial introduction of spawn/culture to substrate | Day 0 | Inoculation date, spawn rate, technique |
| **INCUBATION** | Post-inoculation rest period before visible growth | 1-7 days | Temperature, humidity, contamination watch |
| **COLONIZATION** | Active mycelial growth through substrate | 2-6 weeks | Colonization %, growth rate, vigor |
| **PRIMORDIA** | Pin initiation and early fruit body formation | 3-10 days | Pin count, distribution, environmental triggers |
| **FRUITING** | Active fruit body development and maturation | 5-14 days | Size, morphology, flush number |
| **SENESCENCE** | Declining productivity, end-of-life phase | Variable | Yield decline, contamination risk, disposal |
| **HARVEST** | Mushrooms harvested and processed | N/A | Yield weight, quality grade, storage |

**Scientific Rationale:**

- **INCUBATION** vs **COLONIZATION**: Incubation is the initial rest period where spawn recovers from inoculation stress; colonization is active hyphal extension. Research protocols often track these separately.
- **PRIMORDIA** vs **FRUITING**: Primordia formation (pinning) is a distinct morphological event triggered by environmental changes. Separating this allows researchers to correlate environmental parameters with pin initiation.
- **SENESCENCE**: Tracking end-of-life allows yield optimization studies and substrate reuse research.

**Backward Compatibility:** v1.0/v1.1 parsers will accept specimens with new stages but may not recognize them. Implementations SHOULD handle unknown stages gracefully.

### Generation Notation (v1.2.0)

The `strain.generation` field accepts multiple formats:

| Format | Example | Description |
| ------ | --------- | ------------- |
| Filial | F1, F2, F3 | Preferred notation |
| Parental | P, P1 | Parent/original culture |
| Generational | G1, G2, G3 | Alternative notation |
| Numeric | 1, 2, 3 | Simplified format |

Implementations SHOULD normalize to filial notation (F{n}) by default.

### Generation, Subculture, and Transfer Tracking (v1.3.0)

The `strain` object carries three independent counters. Implementations MUST NOT use one to represent another.

| Field | Meaning | Changes when |
| ----- | ------- | ------------ |
| `generation` | Filial (sexual) generation of the strain | A new strain is bred from spores or a cross (e.g., P → F1). It does **not** change on any transfer of the same genetics. |
| `clonalGeneration` | Culture-to-culture subculture count. The original culture is `0`. | Mycelium is transferred from one culture to another culture medium (agar to agar, agar to liquid culture, liquid culture to agar). Expansion to grain or substrate does not increment it. |
| `transferDepth` | Total transfers from the original culture of this strain, of any kind | Any transfer: subculture, culture to grain, grain to grain, grain to substrate. The original culture is `0`. |

Rules:

- `transferDepth`, when present, MUST be a non-negative integer, and SHOULD be at least `clonalGeneration` when both are present.
- Specimens produced by expansion (grain spawn, substrate, fruiting blocks) SHOULD carry the same `generation` and `clonalGeneration` as their source culture, and SHOULD record ancestry with `lineage`.
- Implementations that track a single per-transfer counter MUST encode it as `transferDepth`, not as `generation`.
- Parsers SHOULD treat `F{n}` values on labels created before v1.3.0 by systems known to count transfers as transfer depth, not filial generation.

**Example**: A grain spawn bag made from the third agar subculture of an original F1 culture, with one grain-to-grain transfer, has `generation: "F1"`, `clonalGeneration: 3`, and `transferDepth: 5` (three subcultures, culture to grain, grain to grain).

### ID Format Options (v1.2.0)

The `id` field MUST start with `wemush:` prefix. The suffix format is flexible:

| Mode | Pattern | Example |
| ------ | --------- | --------- |
| Default | `wemush:[a-z0-9]+` | wemush:clx1a2b3c4 |
| ULID | `wemush:{ULID}` | wemush:01ARZ3NDEKTSV4RRFFQ69G5FAV |
| UUID | `wemush:{UUID}` | wemush:550e8400-e29b-41d4-a716-446655440000 |

Implementations MUST accept any non-empty suffix after `wemush:` prefix.

---

## QR Code Encoding

### Format Options

WOLS supports three encoding formats optimized for different use cases:

#### 1. Compact Format (Recommended for Small Labels)

**Use Case**: Petri dishes, small bags, culture tubes
**Data Limit**: 500 bytes (alphanumeric QR code)

```bash
wemush://v1/{id}?s={species_code}&st={stage}&t={timestamp}
```

**Example**:

```bash
wemush://v1/clx1a2b3c4?s=POSTR&st=COLONIZATION&t=1734307200
```

**Resolution**: Full data retrieved via API endpoint:

```bash
GET https://api.wemush.com/v1/specimens/clx1a2b3c4
```

#### 2. Embedded Format (Recommended for Most Applications)

**Use Case**: Substrate bags, fruiting blocks, labels with space
**Data Limit**: 2,000 bytes (binary QR code)

Embedded format uses JSON-LD for semantic interoperability:

```json
{
  "@context": "https://wemush.com/wols/v1",
  "@type": "Specimen",
  "id": "wemush:clx1a2b3c4d5e6f7g8",
  "version": "1.3.0",
  "type": "SUBSTRATE",
  "species": "Pleurotus ostreatus",
  "strain": {
    "name": "Blue Oyster PoHu",
    "generation": "F2",
    "clonalGeneration": 3
  },
  "stage": "COLONIZATION",
  "created": "2025-12-16T10:30:00Z",
  "batch": "batch_2025_12_001",
  "organization": "org_mushoh"
}
```

**Size**: ~380 bytes — well within QR capacity with error correction level M

#### 3. Encrypted Format (Research/Commercial)

**Use Case**: Proprietary strains, sensitive research
**Encryption**: AES-256-GCM with a shared key, either supplied directly or derived from a passphrase

```bash
wemush://v1/encrypted/{id}?e={ciphertext}&iv={iv}&kdf={kdf}[&salt={salt}&i={iterations}][&sig={kid}.{signature}]
```

**Wire format (v1.3.0)**:

| Parameter | Required | Value |
| --------- | -------- | ----- |
| `{id}` | Yes | Specimen ID suffix (without `wemush:`), percent-encoded as a single path segment (see below). The ID is visible in cleartext; don't put sensitive data in it. |
| `e` | Yes | AES-256-GCM ciphertext with the 16-byte authentication tag appended, base64url without padding |
| `iv` | Yes | 12-byte random IV, base64url without padding. MUST be unique for every encryption under the same key. |
| `kdf` | Yes | `pbkdf2` (key derived from a passphrase) or `raw` (32-byte key shared out of band) |
| `salt` | When `kdf=pbkdf2` | At least 16 random bytes generated per label, base64url without padding |
| `i` | When `kdf=pbkdf2` | PBKDF2 iteration count, as plain decimal digits (`[0-9]+`). No sign, exponent, hex, or whitespace. |
| `sig` | No | Signature token (v1.4.0). When present it MUST be the last parameter. It is not part of decryption (see [Cryptographic Signatures](#cryptographic-signatures)). |

Requirements:

- **ID path segment**: Generators MUST percent-encode the UTF-8 ID suffix as a single RFC 3986 path segment. At minimum they MUST encode `%`, `/`, `?`, `#`, space, `+`, control characters, and all non-ASCII characters. Generators MAY also percent-encode any other character. This includes the sub-delimiters `!`, `*`, `'`, `(`, and `)`, which JavaScript's `encodeURIComponent` leaves unencoded while other encoders escape them. Both forms are valid, and decoders MUST accept either, since percent-decoding yields the same ID. Decoders MUST percent-decode the segment as UTF-8 before comparing it with the decrypted `id`. They MUST treat `+` as a literal character, and MUST reject malformed escapes or invalid UTF-8. For example, the ID `wemush:Lab A/plate+3%` appears in the URL as `Lab%20A%2Fplate%2B3%25`.
- **Plaintext**: The UTF-8 embedded JSON-LD serialization of the specimen (see Embedded Format), without a byte order mark. Decoders SHOULD reject a plaintext that starts with a byte order mark. The decrypted specimen's `id` MUST equal `wemush:` followed by the percent-decoded `{id}`; decoders MUST reject a mismatch.
- **`kdf=pbkdf2`**: PBKDF2-HMAC-SHA256 over the passphrase and the per-label `salt`, producing a 256-bit key. Generators MUST NOT use a fixed or library-wide salt. This rule compares the decoded salt bytes, not their text encoding.
  - **Passphrase encoding**: Implementations MUST normalize the passphrase to Unicode Normalization Form C (NFC) and then encode it as UTF-8 before derivation, so the same passphrase typed on different platforms produces the same key.
  - **Iterations**: Generators MUST use at least 100,000 and SHOULD default to 600,000, following current OWASP guidance. Labels carry their ciphertext publicly, so the default favors resistance to offline guessing. Implementations MAY offer a lower setting, down to 100,000, for faster scanning. At 100,000 iterations each passphrase guess costs an attacker one sixth as much as at the default, so implementations that offer a lower setting SHOULD tell the user that it weakens resistance to guessing, and SHOULD recommend a high-entropy passphrase or `kdf=raw` alongside it (see Offline guessing in [What Encryption Protects](#what-encryption-protects)).
  - **Decoder limits**: Decoders MUST reject iteration counts below 10,000 or above 10,000,000, including values too large for the implementation's integer types. They MUST check the limit before deriving a key. The limit bounds the work a crafted label can force, but the bound isn't small: 10,000,000 iterations of PBKDF2-HMAC-SHA256 is about 17 times the 600,000 default. As a rough guide, that is under a second on a current desktop CPU with a native implementation, several seconds on many phones, and much longer with a non-native (pure script) implementation. The cost is paid on every decryption attempt, including each retry with a different passphrase. Generators MUST NOT exceed 10,000,000.
  - **Responsiveness**: Implementations SHOULD run key derivation off the UI thread (for example, in a Web Worker or a background thread), so that a label at the iteration limit doesn't freeze a scanning app.
  - **Validation order**: Decoders SHOULD validate every parameter and encoding before deriving the key.
- **`kdf=raw`**: The key is exactly 32 bytes. `salt` and `i` MUST be omitted.
- **Encoding**: All binary parameters use base64url (RFC 4648 §5) without padding. Generators MUST emit the canonical form: no padding, and any unused bits in the final character set to zero. Decoders SHOULD also accept padded input.
- **Field-level encryption**: Implementations that encrypt individual top-level fields inside an embedded label MUST replace each field's value with an object of the form `{ "encrypted": true, "algorithm": "AES-256-GCM", "payload": e, "iv": iv, "kdf": kdf, "salt"?: salt, "iterations"?: i }`. It uses the same encodings and key rules as the URL format, and the plaintext is the UTF-8 JSON serialization of the field value.
  - **Binding**: The AES-GCM additional authenticated data (AAD) MUST be the UTF-8 encoding of the label's full `id`, a line feed (U+000A), and the field name. For example, `wemush:clx1a2b3c4` followed by a line feed and `strain`. This binds each encrypted value to its field and label, so values swapped between fields or copied from another label fail authentication.
  - **Identifying fields**: `@context`, `@type`, `id`, `version`, `type`, and `species` MUST NOT be encrypted. Decoders MUST reject a label in which any of them is an encrypted object, and MUST NOT substitute a decrypted value for them.
  - **Total cost**: Before deriving any key, decoders MUST add up the iterations of each distinct `salt` and `iterations` pair in the label, and reject the label if the total exceeds 10,000,000.
  - Each encrypted field MUST use its own IV.
- **`sig`**: Decoders MUST preserve a `sig` value they receive, so that it is still available to the caller and to anything that re-serializes the label, and MUST NOT reject a label because it carries one. Decoding never verifies `sig`. Decoders MUST NOT report a label as signed, authentic, or unmodified because it carries one; only the separate verification operation in [Cryptographic Signatures](#cryptographic-signatures) can, and only when it returns `valid`.
- **Legacy labels**: Encrypted URLs without a `kdf` parameter predate v1.3.0 and are implementation-specific. Decoders MAY support them but MUST NOT generate them.
  - WOLS 1.2.0 named the encrypted URL but never fully specified it: it defined no key derivation, IV transport, or payload encoding. Each 1.2.0 library chose its own, so there is no single legacy format a decoder could be required to read. That is why legacy decoding is a MAY, and why each 1.3.x library reads only the legacy format that its own 1.2.0 release produced (see [Interoperability Notes](./docs/interoperability-notes.md#2-encrypted-format)). The [wire-format compatibility](./GOVERNANCE.md#wire-format-compatibility) rule covers the encrypted format as specified from 1.3.0 onward.

---

## Extended Data Fields

### Environmental Conditions

Track cultivation parameters for optimization:

```typescript
interface EnvironmentalData {
  temperature?: {
    value: number;              // Celsius or Fahrenheit
    unit: "C" | "F";            // Unit for temperature
    timestamp: string;          // ISO 8601
  };
  humidity?: {
    value: number;              // Percentage
    timestamp: string;
  };
  co2?: {
    value: number;              // PPM
    timestamp: string;
  };
  light?: {
    spectrum?: string[];        // ["red", "blue", "white"]
    intensity?: number;         // Lux
    photoperiod?: number;       // Hours
  };
}
```

### Substrate Composition

For reproducibility and optimization:

```typescript
interface SubstrateFormula {
  components: Array<{
    ingredient: string;         // "hardwood sawdust", "wheat bran", etc.
    percentage: number;         // By dry weight
    supplier?: string;          // Optional supplier tracking
  }>;
  hydration?: number;           // Moisture percentage
  supplementation?: number;     // Percentage of supplements
  sterilization?: {
    method: string;             // "autoclave", "pasteurization"
    temperature: number;        // Celsius or Fahrenheit
    unit: "C" | "F";            // Unit for temperature
    duration: number;           // Minutes
    timestamp: string;
  };
}
```

### Circular Economy Integration

Track waste streams and sustainability:

```typescript
interface CircularEconomyData {
  wasteSource?: {
    type: "BREWERY" | "RESTAURANT" | "FARM" | "COFFEE_SHOP";
    partnerId?: string;
    collectionDate?: string;
    composition?: string[];     // ["spent grain", "coffee grounds"]
  };
  sustainability?: {
    carbonOffset?: number;      // kg CO2e
    wasteUtilized?: number;     // kg
    localSourcing?: boolean;
  };
}
```

---

## Implementation Guide

### Generating QR Codes

**Recommended Libraries**:

- JavaScript/TypeScript: [`@wemush/wols`](https://github.com/wemush/specimen-labels-js) (uses the `qrcode` npm package as an optional peer dependency)
- Python: [`wols`](https://github.com/wemush/specimen-labels-py) with the `qr` extra (`pip install "wols[qr]"`)
- Other languages: any ISO/IEC 18004 QR encoder (e.g., Go: `github.com/skip2/go-qrcode`) applied to the serialized payload

**Example (TypeScript)**:

```typescript
import { createSpecimen, toQRCodeDataURL } from '@wemush/wols';

async function generateSpecimenLabel(): Promise<string> {
  const specimen = createSpecimen({
    type: 'SUBSTRATE',
    species: 'Pleurotus ostreatus',
    strain: 'Blue Oyster',        // string shorthand expands to { name: 'Blue Oyster' }
    stage: 'COLONIZATION',
  });
  specimen.created = new Date().toISOString();

  // Embedded JSON-LD QR code as a PNG data URL
  return toQRCodeDataURL(specimen, {
    size: 300,
    errorCorrection: 'M',
  });
}
```

### Scanning & Parsing

**Mobile Integration**:

```typescript
import { BrowserQRCodeReader } from '@zxing/browser';
import { parseSpecimen, parseCompactUrl } from '@wemush/wols';

async function scanSpecimenLabel() {
  const codeReader = new BrowserQRCodeReader();
  const result = await codeReader.decodeOnceFromVideoDevice(undefined, 'video');
  const text = result.getText();

  // Embedded JSON-LD format
  if (text.trim().startsWith('{')) {
    const parsed = parseSpecimen(text);
    if (parsed.success) return parsed.data;
    throw parsed.error;
  }

  // Compact URL format
  if (text.startsWith('wemush://')) {
    const parsed = parseCompactUrl(text);
    if (!parsed.success) throw parsed.error;

    // Compact labels carry a reference; resolve full details if a resolver is available.
    // The resolution endpoint takes the ID without the `wemush:` prefix.
    const id = parsed.data.id.replace(/^wemush:/, '');
    const response = await fetch(`https://api.wemush.com/v1/specimens/${id}`);
    return response.ok ? response.json() : parsed.data;
  }

  throw new Error('Not a WOLS label');
}
```

---

## API Specification

### REST Endpoints

For compact format resolution:

```bash
GET /v1/specimens/{id}
GET /v1/specimens/{id}/observations
GET /v1/specimens/{id}/lineage
POST /v1/specimens
PATCH /v1/specimens/{id}
```

**Authentication**: Bearer token (OAuth 2.0 / API Key)

**Example Response**:

```json
{
  "@context": "https://wemush.com/wols/v1",
  "@type": "Specimen",
  "id": "wemush:clx1a2b3c4d5e6f7g8",
  "version": "1.3.0",
  "type": "SUBSTRATE",
  "species": "Pleurotus ostreatus",
  "strain": {
    "name": "Blue Oyster PoHu",
    "generation": "F2",
    "clonalGeneration": 3
  },
  "stage": "COLONIZATION",
  "created": "2025-12-16T10:30:00Z",
  "batch": "batch_2025_12_001",
  "organization": "org_mushoh",
  "metadata": {
    "substrate": {
      "components": [
        {"ingredient": "hardwood sawdust", "percentage": 70},
        {"ingredient": "wheat bran", "percentage": 20},
        {"ingredient": "gypsum", "percentage": 5},
        {"ingredient": "water", "percentage": 5}
      ],
      "hydration": 60,
      "sterilization": {
        "method": "autoclave",
        "temperature": 121,
        "duration": 90
      }
    }
  },
  "observations": [
    {
      "timestamp": "2025-12-18T14:00:00Z",
      "colonizationPercent": 25,
      "contamination": false,
      "notes": "Healthy mycelium growth"
    }
  ]
}
```

---

## Privacy & Security

### Data Classification

| Level | Description | Encoding | Examples |
| ------- | ----------- | --------- | --------- |
| **Public** | Non-sensitive cultivation data | Embedded JSON | Species, growth stage, harvest date |
| **Organization** | Internal operational data | Compact + API | Substrate formulas, vendor info |
| **Research** | Proprietary genetics/methods | Encrypted | Novel strains, trade secrets |

### What Encryption Protects

- **Confidentiality**: Encryption, whether a whole label in the URL format or individual fields, keeps the encrypted values secret from anyone without the key.
- **Placement**: Field-level AAD binds each encrypted value to its label `id` and field name. A value moved to another field or another label fails to decrypt.
- **Rollback**: The AAD binds a value to its label and field, not to a point in time. Someone holding an older copy of the same label can replace an encrypted field with the older ciphertext of that same field, and it decrypts normally. Neither form detects replacing a whole label with an older one.
- **Integrity**: Neither form makes the cleartext parts of a label tamper-evident. Someone who can edit a label can change its cleartext fields, or remove encrypted fields entirely. Encryption doesn't detect this; a [signature](#cryptographic-signatures) does, for a verifier that trusts the signer's key.
- **Visible metadata**: The ID and the presence of encrypted fields are always visible. AES-GCM doesn't hide length, so each ciphertext also reveals the exact byte length of its plaintext. For field-level encryption that is the length of each field's JSON value, which can be enough to tell short values apart (for example, which of a few known strain names a field holds). 1.3.x defines no padding, so don't rely on encryption to hide how long a value is.
- **Offline guessing**: The ciphertext, salt, and iteration count are printed on the label, so anyone holding the label can try passphrases offline, as fast as their hardware allows, with no rate limit and no way for the owner to notice. PBKDF2 iterations only slow each guess down; they can't protect a guessable passphrase. Use a high-entropy passphrase (for example, a randomly generated passphrase of five or more words, or a long random string) or `kdf=raw` with a randomly generated 32-byte key. Don't use a short, reused, or human-chosen passphrase for labels that leave your control.

### Cryptographic Signatures

*(v1.4.0. Replaces the 1.3.x reservation and the earlier non-normative sketch.)*

A signature lets a verifier check two things: the label's bytes were signed with a private key the verifier already trusts, and they haven't changed since. 1.4.0 defines signatures for two forms:

- **Embedded labels** (JSON-LD), in the top-level `signature` member
- **Encrypted URLs**, in the `sig` parameter

**Compact URLs can't be signed in 1.4.0.** Their parameter set and code registries aren't normative yet (see [ROADMAP.md](./ROADMAP.md)), so there are no fixed bytes to sign. Compact signing will be defined together with the compact URL conformance vectors.

Signing and verifying are separate operations from decoding. Nothing in this section changes how a label decodes (see [Decoding and compatibility](#decoding-and-compatibility)).

#### Algorithm

- Signers MUST use **Ed25519** as defined in [RFC 8032](https://www.rfc-editor.org/rfc/rfc8032) §5.1: PureEdDSA over the message itself. It is not Ed25519ph (prehashed) and not Ed25519ctx. It is the only algorithm in 1.4.0.
- A public key is the 32-byte encoded point. A private key is the 32-byte seed. A signature is 64 bytes.
- Verifiers MUST verify as RFC 8032 §5.1.7 specifies, and MUST reject a signature whose `S` value is not less than the group order `L`. Without that check the same signature has a second, malleated form that some libraries accept.
- Ed25519 is deterministic: the same key and the same signing input always give the same signature, so the conformance vectors check signing output exactly.

#### Signature token

The `signature` member and the `sig` parameter both hold a **signature token**: the key identifier, one `.` (U+002E), and the signature encoded as base64url ([RFC 4648 §5](https://www.rfc-editor.org/rfc/rfc4648#section-5)) without padding.

```abnf
token = kid "." sig
kid   = 1*64( ALPHA / DIGIT / "-" / "_" )   ; case-sensitive
sig   = 86( ALPHA / DIGIT / "-" / "_" )     ; the 64-byte signature, base64url, no padding
```

Example: `mushoh-2026.nZzoNsitU1s5QMmVvLnw6WZUNCMsTgwdMITGHgYTH_AXZEcZeiM8se78ciZn5iIhij9Zi3U9LbXPR_wGXV9gBw`

- 86 characters carry 516 bits, so the last 4 bits are unused. They MUST be zero, so the last character is one of `A`, `Q`, `g`, or `w`. Exactly one encoding is valid for each signature.
- A token is **malformed** if it doesn't match the grammar above. That includes padding (`=`), any character outside the base64url alphabet, a decoded length other than 64 bytes, nonzero unused bits, leading or trailing whitespace, and a missing or extra `.`. Verifiers MUST NOT try to repair a malformed token.
- Every character of a token is in the RFC 3986 unreserved set. A token goes into a URL without percent-encoding, and `encodeURIComponent` or Python's `quote(..., safe="")` leave it unchanged.

> **Why the kid is inside the token** (non-normative): the 1.3.x reference libraries already preserve the reserved `signature` member and `sig` parameter as opaque strings, as 1.3.1 requires. A separate `kid` member or parameter would not survive: both 1.3.0 libraries drop an unknown top-level member or URL parameter when they re-serialize a label, the Python library rejects unknown top-level members in strict validation, and it rejects a `signature` that isn't a string. Keeping the kid inside the token means a signed label passes through a 1.3.x decoder with its signature intact.

#### Signing input

Ed25519 signs this byte string:

```text
signing input = "WOLS-SIG-v1" LF form LF kid LF body
```

- `LF` is a single line feed (U+000A).
- `form` is `embedded` for an embedded label, or `encrypted-url` for an encrypted URL.
- `kid` is the token's kid, exactly as it appears in the token.
- `body` is the form's canonical bytes, defined below.

Everything before `body` is ASCII. The prefix does two jobs:

- **Domain separation**: a signature over one form never verifies as the other, even over identical body bytes. It also never verifies as a signature over the bare body.
- **Kid binding**: the kid is signed. Moving a signature to a different kid fails, even when both kids name the same key.

##### Embedded body

1. Parse the label text as JSON. The result MUST be a JSON object.
2. Remove the top-level `signature` member, if there is one. Members named `signature` at other depths are kept.
3. `body` is the UTF-8 encoding of the remaining object, canonicalized with the JSON Canonicalization Scheme ([RFC 8785](https://www.rfc-editor.org/rfc/rfc8785), JCS).

JCS works on parsed values. Member order, whitespace, and how strings or numbers were spelled in the received text don't affect `body`. The rules that most often go wrong:

- **Member order**: Members are sorted by the UTF-16 code units of their names, compared as unsigned integers. That isn't code point order. For example, U+1F344 (surrogates `D83C DF44`) sorts before U+FB01.
- **Strings**: Only `"`, `\`, and U+0000 through U+001F are escaped. Use `\b`, `\t`, `\n`, `\f`, and `\r` where they exist, and lowercase `\u00xx` for the other control characters. Everything else is written as literal UTF-8, including `/`, U+007F, U+2028, and non-ASCII characters.
- **Unicode**: JCS doesn't normalize Unicode. The NFC and NFD forms of a name are different bodies.
- **Numbers**: Every number is an IEEE 754 double, written with the ECMAScript `Number.prototype.toString` rules. So `1.0` is `1`, `-0` is `0`, `1E21` is `1e+21`, and `0.0000001` is `1e-7`. Integers beyond 2^53 are rounded to the nearest double first.

A label is **malformed** for verification, and signers MUST refuse to sign it, if any of these hold:

- It isn't a JSON object.
- Any member name or string value contains a lone surrogate (it isn't [I-JSON](https://www.rfc-editor.org/rfc/rfc7493)).
- It contains a non-finite number. Some parsers accept `NaN` or `Infinity`.

Verifiers SHOULD also treat a label with duplicate member names in any object as malformed, and signers MUST NOT produce one. Different JSON parsers keep different duplicates, so a duplicated member could display one value and verify another.

The body covers every member except the top-level `signature`, including `version`, `custom`, `_meta`, and members the verifier doesn't recognize. Field-level encryption objects are covered as printed, as ciphertext.

**Canonicalize what was received.** A verifier MUST canonicalize the label as it was parsed from the label text. It MUST NOT canonicalize an object model the library rebuilt from it. Libraries commonly drop unknown members, resolve type aliases, normalize `generation`, or fill in defaults, and any of those changes the body. For the same reason, a signer MUST sign exactly the object it serializes. The signature is computed last, over the final object.

##### Encrypted URL body

The body is the URL exactly as transmitted, with the `sig` parameter removed. Nothing else is changed or normalized.

A signer builds the complete unsigned URL as it will be printed, with `sig` absent. That URL is the body. The signed URL is the body followed by `&sig=` and the token. `sig` is always the last parameter, and nothing follows it.

A verifier finds the body as follows:

1. Split the URL at its first `?`. Split the text after it on `&`. Each piece is a parameter, and its name is the text before its first `=` (or the whole piece, if it has no `=`). Names are compared as exact text, with no percent-decoding. If no parameter is named `sig`, the URL is `unsigned`.
2. The URL is **malformed** if any of these hold:
   - It contains a character outside U+0021 through U+007E. Spaces and non-ASCII characters must be percent-encoded.
   - It contains `#`.
   - It doesn't start with `wemush://v1/encrypted/`.
   - More than one parameter is named `sig`.
   - The `sig` parameter isn't the last parameter, or it is the only one.
   - The `sig` parameter has no `=`.
3. The token is the text after `sig=`, used as is. Verifiers MUST NOT percent-decode it.
4. The body is the URL with its last `&` and everything after it removed. That is the first `len(url) - len("&sig=" + token)` characters, encoded as ASCII bytes.

Verifiers MUST NOT re-normalize the body. Parameter order, the scheme, the path, and percent-encoding are kept exactly as received, including the case of hex digits (`%2F` and `%2f` are different bodies). The body covers the cleartext ID segment, `e`, `iv`, `kdf`, `salt`, `i`, and any other parameter before `sig`. So a URL that a decoder re-serialized verifies only if it is byte-for-byte identical to the one that was signed.

Example: the unsigned URL `wemush://v1/encrypted/clx1a2b3c4?e=…&iv=ZGVmZ2hpamtsbW5v&kdf=pbkdf2&salt=AAECAwQFBgcICQoLDA0ODw&i=100000` is the body. The signed URL ends `…&i=100000&sig=mushoh-2026.nZzo…gBw` (vector `sign-encrypted-url`).

#### Plaintext or ciphertext

Signatures cover what is printed. For an encrypted URL that is the ciphertext; for an embedded label with field-level encryption, it is the encrypted field objects.

- **Anyone can verify.** Anyone holding the trust store can verify, without the decryption key. A scanner can verify before it spends PBKDF2 work on the label.
- **The parameters are covered.** The signature covers the cleartext ID and the key derivation parameters. A signed label's `i` or `salt` can't be changed without breaking the signature.
- **It doesn't prove knowledge of the plaintext.** Anyone can sign someone else's ciphertext under their own kid. A `valid` result says only that the kid's key holder issued these bytes.

To also authenticate the plaintext to key holders, sign the embedded label first and then encrypt it. The plaintext of an encrypted URL is an embedded label, so it MAY carry its own `signature`. That signature is verified after decryption, as an embedded label. A label MAY carry both signatures.

#### Key identification and the trust store

- **Trust store**: The kid identifies a public key in a **trust store** that the verifier's caller supplies. A trust store maps each kid to an algorithm (`Ed25519`) and a 32-byte public key. It MUST NOT map one kid to more than one key. Several kids MAY map to the same key.
- **Keys come from outside the label.** Verifiers MUST resolve the kid only through the trust store. They MUST NOT use a key, key URL, certificate, or key hint carried in the label, whether in `publicKey`, `custom`, `_meta`, `organization`, or anywhere else. Whoever edits a label controls all of its contents.
- **Kids aren't globally unique.** A kid is unique only within a trust store; there is no global registry. Issuers SHOULD choose kids that are unlikely to collide with other issuers' kids, such as an organization prefix plus a key generation (`mushoh-2026`).
- **No network access.** Verification MUST NOT fetch keys or make network requests. The caller builds the trust store first, so verification works offline.
- **Key set document (optional)**: An issuer MAY publish its public keys at `https://{issuer-host}/.well-known/wols-keys.json`:

  ```json
  { "keys": [ { "kid": "mushoh-2026", "alg": "Ed25519", "publicKey": "<32 bytes, base64url, no padding>" } ] }
  ```

  A verifier MAY load a trust store from this document for hosts it chose to trust independently of any label. It MUST NOT choose the host from the label's contents. Fetching, caching, and HTTPS validation happen before verification and are outside it.

#### Verification result

Verification takes a label (embedded label text, or an encrypted URL) and a trust store. It returns exactly one of these statuses:

| Status | Meaning |
| ------ | ------- |
| `unsigned` | The label has no top-level `signature` member, or the URL has no `sig` parameter |
| `malformed` | A signature is present, but the token, the label, or the URL breaks a rule in this section |
| `unknown-kid` | The token is well-formed, but its kid isn't in the trust store (or its entry isn't an Ed25519 key) |
| `invalid` | The kid is in the trust store, and the signature doesn't verify under that key |
| `valid` | The signature verifies under the trust store's key for the kid |

- **Check order**: Verifiers MUST check in this order: `unsigned`, then every `malformed` rule, then the trust store lookup (`unknown-kid`), then the signature (`invalid` or `valid`). With a fixed order, every implementation returns the same status for the same input.
- **Only `valid` is authentic.** Only a `valid` result may be presented as signed, authentic, or unmodified. A `valid` result MUST also report its kid.
- **Other statuses**: A verifier MAY report the kid with `unknown-kid` or `invalid`, for diagnostics. It MUST NOT present `unknown-kid` as valid; "signed by an unknown key" is an accurate description.
- Verification never fails decoding, and decoding never verifies.

#### Signing

- To sign an embedded label, a signer removes any top-level `signature` member, computes the body and the signing input, and sets `signature` to the token. Re-signing a label therefore replaces its old signature.
- A signer MUST refuse to sign an encrypted URL that already has a `sig` parameter. To re-sign it, remove the old `sig` first. The unsigned URL MUST also satisfy the verifier's rules: ASCII only, no fragment, and the `wemush://v1/encrypted/` prefix.
- Signers MUST emit the canonical token encoding.

#### Decoding and compatibility

- **Decoding ignores signatures.** Decoders MUST decode a signed label exactly as they would the same label without its signature. They MUST NOT fail decoding because of a signature's status. An application MAY refuse to act on a label that doesn't verify as `valid`; that is policy, not decoding.
- **1.3.x decoders**: A token is an opaque string in the reserved `signature` member or `sig` parameter, which 1.3.1 already requires decoders to preserve. The 1.3.0 reference libraries decode signed labels and keep the token unchanged. Both re-serialize a signed encrypted URL in the order this specification gives (`e`, `iv`, `kdf`, `salt`, `i`, `sig`), which leaves its bytes unchanged.
- **Older labels**: 1.4.0 decoders decode unsigned labels and 1.3.x labels unchanged. A 1.3.x `signature` or `sig` value that isn't a token verifies as `malformed`, never as `valid`.
- **Re-emitting signed labels**: Implementations that re-emit labels MUST keep `signature` and `sig` exactly as received. They SHOULD re-emit a signed URL as received rather than rebuilding it. Re-encoding, reordering, adding, or dropping a parameter invalidates a URL signature. Rebuilding an embedded label invalidates its signature if any value changes.

#### What a signature proves

A `valid` result proves one thing: the holder of the private key that your trust store lists for the kid signed these exact bytes, in this form. It does **not** prove any of the following:

- **Freshness**: A signature has no timestamp, nonce, or expiry. `created` is whatever the signer wrote. Someone holding an older validly signed label, from an earlier stage or a previous batch, can reprint it or swap it in, and it still verifies (rollback and replay).
- **That the label belongs on this item**: A valid label can be copied onto another bag. Signatures authenticate data, not physical objects.
- **That the content is true**: The signer vouches for the label, nothing more.
- **That the signer knew the plaintext** of the encrypted values it signed (see [Plaintext or ciphertext](#plaintext-or-ciphertext)).

Other considerations:

- **Stripping**: Anyone can remove a signature. The label is then `unsigned`, not `invalid`. A verifier that requires signatures MUST treat `unsigned` as a failure under its own policy.
- **Linkability**: The kid is cleartext, even on an encrypted URL. Every label signed with one key can be linked to that key, and so to its issuer. Issuers who care about that SHOULD use separate keys for separate purposes.
- **Key compromise and rotation**: Printed labels can't be re-signed or recalled, and a label carries no revocation information.
  - **Rotation**: Rotate by issuing a new key under a new kid. Keep the old public key in trust stores while labels signed with it are in circulation.
  - **Compromise**: If a key is compromised, remove its kid from every trust store. Every label under that kid then verifies as `unknown-kid`, including the genuine ones. That can't be avoided: there is no trusted timestamp, so a stolen key can sign backdated labels that are indistinguishable from real ones.
  - **Limiting the damage**: Keep private keys offline or in hardware where possible. A key per site or device limits what one compromise affects.
- **Trust store distribution**: The trust store is the root of trust. How it reaches the verifier (shipped with the app, pinned, or fetched over HTTPS from a host chosen in advance) determines what `valid` means. A key set document is only as trustworthy as its host and the way the verifier chose that host. Kids from different issuers must not collide within one store.
- **Display what you verified**: Applications SHOULD display the values from the same parse they verified, not from a separate parse of the label text.

---

## Extensibility

### Custom Namespaces

Organizations can add custom fields under reserved namespaces:

```json
{
  "@context": "https://wemush.com/wols/v1",
  "@type": "Specimen",
  "id": "wemush:clx1a2b3c4",
  "version": "1.3.0",
  "species": "Hericium erinaceus",
  "custom": {
    "mushoh": {
      "baggerId": "thor_001",
      "qcChecked": true,
      "shelfPosition": "A3"
    },
    "acme_labs": {
      "projectCode": "PROJ-2025-42",
      "fundingSource": "NSF-1234567"
    }
  }
}
```

**Namespace Registration**: Submit PR to [github.com/wemush/open-standard](https://github.com/wemush/open-standard)

---

## Reference Implementation

### Open Source Libraries

**TypeScript/JavaScript**: [`@wemush/wols`](https://github.com/wemush/specimen-labels-js) (Apache 2.0)

```bash
npm install @wemush/wols    # or: bun add @wemush/wols / pnpm add @wemush/wols
```

**Python**: [`wols`](https://github.com/wemush/specimen-labels-py) (Apache 2.0)

```bash
pip install wols             # core
pip install "wols[qr]"       # + QR generation and scanning
pip install "wols[crypto]"   # + encryption
pip install "wols[cli]"      # + command-line interface
pip install "wols[all]"      # everything
```

**Container/CLI**: [`specimen-labels-py`](https://github.com/wemush/specimen-labels-py/pkgs/container/specimen-labels-py) (arm64/amd64)

```bash
docker pull ghcr.io/wemush/specimen-labels-py:latest
docker run --rm ghcr.io/wemush/specimen-labels-py create \
  --species "Pleurotus ostreatus" --type SUBSTRATE --json
```

**Conformance test vectors**: [`conformance/`](./conformance/README.md) contains language-neutral test cases (validation, `PRIMORDIA` handling, generation tracking, encrypted format, signatures) that implementations SHOULD pass.

> **Interoperability note (non-normative):** The 1.3.0 reference libraries pass every conformance vector, so embedded and encrypted labels interoperate across languages. Compact URLs still differ between them, and encrypted labels made by the 1.2.0 libraries are not interchangeable. See [Interoperability Notes](./docs/interoperability-notes.md) before mixing implementations.

**API**: `https://api.wemush.com/v1`

**Playground**: `https://labels.wemush.com`

---

## Library API Reference (v1.2.0)

### Environment Detection

Implementations SHOULD provide runtime environment detection for selecting appropriate crypto backends:

```typescript
// Runtime environment detection
isServer(): boolean           // Node.js environment
isBrowser(): boolean          // Browser window context
isWebWorker(): boolean        // Web Worker context
isDeno(): boolean             // Deno runtime
isBun(): boolean              // Bun runtime
getRuntimeEnvironment(): RuntimeEnvironment  // 'node' | 'browser' | 'webworker' | 'deno' | 'bun' | 'unknown'

// Crypto capability detection
isCryptoSupported(): boolean  // Any crypto available
supportsWebCrypto(): boolean  // Web Crypto API available
supportsNodeCrypto(): boolean // Node.js crypto available

// Feature detection
supportsTextEncoding(): boolean  // TextEncoder/TextDecoder available
supportsURLAPIs(): boolean       // URL/URLSearchParams available
```

**Use Case**: Selecting appropriate encryption implementation for cross-platform libraries.

### Convenience Methods

Implementations SHOULD provide convenience wrappers for common parse operations:

```typescript
// Standard parse (returns discriminated union)
parseCompactUrl(url: string): ParseResult<SpecimenRef>
// Usage: if (result.success) { use(result.data) } else { handle(result.error) }

// Exception-throwing variant
parseCompactUrlOrThrow(url: string): SpecimenRef
// Throws WolsParseError on failure

// Null-returning variant
parseCompactUrlOrNull(url: string): SpecimenRef | null
// Returns null on failure (for optional chaining)
```

### Signatures (v1.4.0)

Implementations that support [signatures](#cryptographic-signatures) SHOULD provide signing and verification functions shaped like these. The names are a recommendation; the behavior is defined by the specification and the `signatures.json` vectors.

```typescript
type SignatureStatus = 'valid' | 'invalid' | 'unknown-kid' | 'malformed' | 'unsigned';
type TrustStore = Record<string, { alg: 'Ed25519'; publicKey: Uint8Array }>;  // kid -> key

interface VerificationResult {
  status: SignatureStatus;
  kid?: string;                  // always set when status is 'valid'
  reason?: string;               // human-readable detail for 'malformed' and other failures
}

// Embedded label text (or a parsed JSON object). Returns signed label text.
signSpecimen(label: string | object, options: { privateKey: Uint8Array; kid: string }): Promise<string>
// Unsigned encrypted URL. Returns the URL with `&sig=` and the token appended.
signEncryptedUrl(url: string, options: { privateKey: Uint8Array; kid: string }): Promise<string>

// Accepts embedded label text, a parsed JSON object, or an encrypted URL. Never throws for a
// bad signature; every outcome is a status.
verifySpecimen(label: string | object, trustStore: TrustStore): Promise<VerificationResult>
```

A verifier SHOULD accept the label text exactly as scanned. When it accepts a parsed object, it MUST be the raw JSON value, not the library's own specimen model (see [Canonicalize what was received](#embedded-body)).

### Migration Utilities

Implementations SHOULD provide version management utilities:

```typescript
// Version comparison
compareVersions(a: string, b: string): -1 | 0 | 1
isOutdated(version: string): boolean    // Older than library version
isNewer(version: string): boolean       // Newer than library version
getCurrentVersion(): string             // Current library WOLS version

// Migration registry
registerMigration(fromVersion: string, toVersion: string, handler: MigrationHandler): void
canMigrate(specimen: Specimen): boolean
migrate(specimen: Specimen): Specimen   // Chains migrations automatically
getMigrations(): Array<[string, string]>
```

### Type Mapping

Implementations SHOULD export centralized type mappings for UI integration:

```typescript
// Canonical WOLS types to platform-friendly names
const WOLS_TO_PLATFORM_MAP: Record<SpecimenType, string[]> = {
  CULTURE: ['Liquid Culture', 'LC', 'Agar', 'Petri', 'Slant', 'Culture Plate'],
  SPAWN: ['Grain Spawn', 'Sawdust Spawn', 'Plug Spawn', 'Dowel'],
  SUBSTRATE: ['Block', 'Bag', 'Bed', 'Log', 'Bucket'],
  FRUITING: ['Pinning', 'Primordia', 'Fruiting', 'Flush', 'First Flush'],
  HARVEST: ['Fresh', 'Dried', 'Processed', 'Extract'],
};

// Mapping functions
mapToWolsType(platformType: string): SpecimenType | null
mapFromWolsType(wolsType: SpecimenType): string[]
registerPlatformType(platformType: string, wolsType: SpecimenType): void
```

---

## Use Cases

### 1. Home Cultivator Tracking

**Problem**: Lost track of which substrate recipe works best
**Solution**: Scan QR → See historical yields → Reproduce success

### 2. Commercial Traceability

**Problem**: Regulatory compliance for food safety
**Solution**: QR on retail packaging → Full cultivation history

### 3. Research Reproducibility

**Problem**: Can't replicate experimental results
**Solution**: QR encodes exact parameters → Perfect replication

### 4. Circular Economy Transparency

**Problem**: Consumers want proof of sustainability claims
**Solution**: QR shows brewery waste source → Carbon offset calculation

### 5. Equipment Integration

**Problem**: Manual data entry is error-prone
**Solution**: IoT sensors auto-generate QR labels → Seamless tracking

---

## Versioning

This specification uses [Semantic Versioning](https://semver.org/):

- **Major**: Breaking changes to core schema
- **Minor**: Backwards-compatible additions
- **Patch**: Clarifications, bug fixes

**Current Version**: 1.4.0-rc.1 (release candidate; it builds on 1.3.1-rc.1, and 1.3.0 remains the latest final release)
**Stability**: Release candidate (feedback welcome; requirements may change before the final release)

---

## Governance

### Contribution Process

1. Submit issue on [GitHub](https://github.com/wemush/open-standard)
2. Discuss in community forum
3. Submit PR with proposed changes
4. Merge and tag as a release candidate (for example, `1.3.0-rc.1`)
5. Feedback period (no minimum for minor versions; at least 14 days for major versions)
6. Final release once the [conformance vectors](./conformance/README.md) pass in at least one library

See [GOVERNANCE.md](./GOVERNANCE.md#pre-releases) for the full pre-release process.

### Steering Committee

- [Mark Beacom](https://github.com/mbeacom) (WeMush Foundation) - Chair
- [Amy Beacom](https://github.com/abeacom) (WeMush Foundation) - Co-Chair & Science Advisor
- [Open positions for industry representatives]
- [Open position for academic representative]

---

## Adoption

### Organizations Using WOLS

| Organization | Use Case | Since |
| ------------ | -------- | ----- |
| WeMush Platform | Full cultivation tracking | 2025 |
| Mush Ohio | Commercial production tracking | 2025 |
| [Your organization?] | [Submit PR to add] | [Year] |

---

## FAQ

**Q: Is this standard required to use WeMush platform?**
A: No. The platform supports any labeling format, but WOLS enables advanced features.

**Q: Can I use WOLS with other software?**
A: Yes! That's the point. WOLS is vendor-agnostic.

**Q: What about existing barcodes/labels?**
A: WOLS can coexist. Many operations use both during transition.

**Q: Who owns the data?**
A: The cultivator who generated it. WOLS is just a format.

**Q: How do I report security issues?**
A: Email [security@wemush.com](mailto:security@wemush.com) (PGP key available)

**Q: Can I use this for cannabis/hemp?**
A: Yes, the standard is crop-agnostic.

---

## License

### Creative Commons Attribution 4.0 International (CC BY 4.0)

You are free to:

- **Share** — copy and redistribute
- **Adapt** — remix, transform, and build upon

Under these terms:

- **Attribution** — Give appropriate credit

Full license: [https://creativecommons.org/licenses/by/4.0/](https://creativecommons.org/licenses/by/4.0/)

---

## References

1. ISO 8601 - Date and time format
2. RFC 4122 - UUID specification
3. QR Code Specification (ISO/IEC 18004)
4. JSON Schema Specification
5. OAuth 2.0 Authorization Framework
6. RFC 3986 - Uniform Resource Identifier (URI): Generic Syntax
7. RFC 4648 - The Base16, Base32, and Base64 Data Encodings (§5, base64url)
8. RFC 8032 - Edwards-Curve Digital Signature Algorithm (EdDSA)
9. RFC 8785 - JSON Canonicalization Scheme (JCS)

---

## Contact

**Project Lead**: Mark Beacom
**Email**: [mark@wemush.com](mailto:mark@wemush.com)
**GitHub**: [https://github.com/wemush/open-standard](https://github.com/wemush/open-standard)
**Website**: [https://wemush.com](https://wemush.com)

---

## Changelog

### Version 1.4.0-rc.1 (Release candidate — November 16, 2026)

Defines the signature scheme that 1.3.1-rc.1 reserved. This candidate builds on `1.3.1-rc.1` and includes its clarifications. Nothing here changes how any label decodes: unsigned labels and 1.3.x labels decode exactly as before. Signing and verifying are new, separate operations.

Normative changes, subject to the public comment period:

- **Cryptographic Signatures**: Replaces the non-normative sketch with a normative scheme:
  - **Algorithm**: Ed25519 (RFC 8032, pure). Verifiers reject `S ≥ L`.
  - **Signature token**: `{kid}.{sig}`, carried in the embedded `signature` member and the encrypted URL's `sig` parameter. The signature is 64 bytes in canonical unpadded base64url.
  - **Signing input**: `"WOLS-SIG-v1" LF form LF kid LF body`, with the form and the kid both signed.
  - **Embedded body**: RFC 8785 (JCS) of the label without its top-level `signature`.
  - **Encrypted URL body**: The exact URL bytes before the `&sig=` parameter, which must come last. Nothing is re-normalized.
  - **Keys**: Resolved only through a caller-supplied trust store, never from the label, with an optional `/.well-known/wols-keys.json` key set document.
  - **Verification result**: One of five statuses (`valid`, `invalid`, `unknown-kid`, `malformed`, `unsigned`), checked in a fixed order.
- **Compact URLs** can't be signed yet. Compact signing will be defined with the compact URL vectors.
- **`sig` parameter**: Now a signature token instead of a reserved value. When present it is the last parameter. Decoding still never verifies it.
- **Security considerations**: Adds what a valid signature does and doesn't prove (no freshness, so rollback and replay are possible), plus key compromise and rotation, trust store distribution, stripping, and linkability.
- **Library API Reference**: Adds the recommended `signSpecimen`, `signEncryptedUrl`, and `verifySpecimen` shapes.
- **Conformance**:
  - Adds `signatures.json` with `sign` and `verify` cases, published test keys, and a trust store.
  - Adds `decrypt-signed-url` to `encrypted.json` and `signed-label-valid` to `embedded.json`. Both show that signed labels decode and validate unchanged.
  - The existing cases are unchanged.

### Version 1.3.1-rc.1 (Release candidate — November 16, 2026)

Clarifications to 1.3.0, from a review of what the 1.3.0 text and vectors actually guarantee. Nothing here changes the 1.3.0 wire format or which labels decode: every label that 1.3.0 allowed decodes the same way, and generator limits (including the 100,000-iteration minimum) are unchanged.

Normative clarifications, subject to the public comment period:

- **Signatures reserved**: `sig` and the embedded `signature` field are reserved. Decoders MUST preserve them and MUST NOT treat them as verified. The Cryptographic Signatures sketch is now marked non-normative, with warnings that a public key embedded in the label proves nothing and that `JSON.stringify` has no canonical form. A full signature scheme is planned for 1.4.0.
- **Key derivation responsiveness**: Implementations SHOULD run key derivation off the UI thread. Implementations that offer fewer than the default 600,000 iterations SHOULD tell the user that it weakens resistance to guessing, and SHOULD recommend a high-entropy passphrase or `kdf=raw`.

Editorial:

- **Decoder limits**: Replaces "can't stall a scanner" with the actual bound that the 10,000,000-iteration limit gives.
- **What Encryption Protects**: Adds that AES-GCM reveals each value's plaintext length, that field binding doesn't prevent rollback to an older ciphertext of the same field, and that anyone holding a label can guess passphrases offline.
- **Legacy labels**: Explains why decoding pre-1.3.0 encrypted labels is a MAY: 1.2.0 never fully specified the format, so each library reads only its own. [GOVERNANCE.md](./GOVERNANCE.md#wire-format-compatibility) now says the wire-format compatibility rule applies from 1.3.0 onward.
- **ID path segment**: The 1.3.0 text recommended encoding everything outside the RFC 3986 unreserved set "as `encodeURIComponent` does". That was contradictory, because `encodeURIComponent` leaves `!*'()` unencoded. The text now lists only the required minimum set, permits encoding any other character, and says decoders MUST accept either form. This was already implied by percent-decoding, so which encodings are valid hasn't changed.
- **Conformance**: Adds `decrypt-with-sig` to `encrypted.json`: a label with a `sig` parameter decrypts, and the decoder keeps `sig` without verifying it. The existing cases are unchanged.

### Version 1.3.0 (November 15, 2026)

Final release. It combines the two release candidates below with no further normative changes. Both reference libraries pass every conformance vector: `@wemush/wols` 1.3.0 (TypeScript) and `wols` 1.3.0 (Python). Example labels now use `"version": "1.3.0"`.

#### 1.3.0-rc.2 (November 15, 2026)

Changes since `1.3.0-rc.1`, from implementation feedback:

- **Passphrase normalization**: Passphrases are normalized to NFC before PBKDF2.
- **Iteration limits**: Generators SHOULD default to 600,000 iterations. Decoders MUST reject more than 10,000,000, checked before any key is derived, including the total for field-level encryption.
- **Field-level binding**: Field-level encryption uses AAD (`{id}` + line feed + field name), so swapped or copied values fail authentication.
- **Identifying fields**: `@context`, `@type`, `id`, `version`, `type`, and `species` can't be encrypted.
- **ID path encoding**: The ID suffix in an encrypted URL is percent-encoded by generators and percent-decoded by decoders before the id check.
- **Strict parameters**: `i` must be plain decimal digits. Generators emit canonical unpadded base64url. The plaintext has no byte order mark.
- **Security note**: Adds "What Encryption Protects", which separates confidentiality, placement, and integrity.
- **Conformance**:
  - Adds `field-encryption.json`.
  - Adds new cases to `encrypted.json`. The existing cases are unchanged.
  - Adds `SHA256SUMS` for the vector files.

#### 1.3.0-rc.1 (November 14, 2026)

Normative changes:

- **`PRIMORDIA` type handling**: `PRIMORDIA` supplied as a type now resolves to `FRUITING` and defaults `stage` to `PRIMORDIA`. Implementations warn and never emit `PRIMORDIA` as a type. This replaces the v1.2.0 "MUST reject" rule, which conflicted with the v1.2.0 alias table.
- **Encrypted format wire specification**: Defines the `iv`, `kdf`, `salt`, and `i` parameters, base64url encoding, a per-label random salt, PBKDF2 minimums, the ID binding check, and field-level encryption objects. `sig` is now an optional detached signature.
- **Conformance test vectors**: Adds a [`conformance/`](./conformance/README.md) suite with a deterministic generator and an independent verifier.
- **Generation tracking**: New `strain.transferDepth` field. Clarifies that `generation` is filial only and that `clonalGeneration` counts culture-to-culture subcultures, not expansion transfers.

### Unreleased (editorial, no normative changes)

- Updated `version` values in examples from `1.1.0` to `1.2.0`
- Implementation Guide examples now use the `@wemush/wols` reference library API
- Expanded reference implementation install options (Python extras, container CLI usage)
- Added non-normative [Interoperability Notes](./docs/interoperability-notes.md) documenting known divergences between implementations
- Refreshed Next Steps
- Updated Next Steps for the released 1.3.0: marked cross-implementation interoperability and 1.3.0 complete, and added 1.4.0

### Version 1.2.0 (January 26, 2026)

- **Extended growth stages**: Research-grade lifecycle tracking with 7 stages (added INCUBATION, PRIMORDIA, SENESCENCE)
- **Flexible ID formats**: Accept ULID, UUID in addition to CUID after `wemush:` prefix
- **Type aliases**: Built-in mapping for common platform types (e.g., `LIQUID_CULTURE` → `CULTURE`, `PRIMORDIA` → `FRUITING`)
- **Generation flexibility**: Accept `G{n}` and numeric notation in addition to `F{n}`
- **`_meta` namespace**: Reserved field for implementation metadata (preserved through operations)
- **Migration utilities**: Version comparison and upgrade helpers for future-proofing
- **Environment detection**: Runtime detection helpers for crypto and platform selection
- **Convenience methods**: `parseCompactUrlOrThrow()` and `parseCompactUrlOrNull()` wrappers
- **Type mapping exports**: Centralized `WOLS_TO_PLATFORM_MAP` for UI integration
- **Library API Reference**: New section documenting implementation requirements

### Version 1.1.0 (January 4, 2026)

- **JSON-LD format adoption**: Added `@context` and `@type` fields for semantic web interoperability
- **Structured strain object**: Strain field now supports `name`, `generation`, `clonalGeneration`, `lineage`, and `source` subfields
- **Dual generation tracking**: `generation` for filial (F1, F2) and `clonalGeneration` for subculture count (1, 2, 3...)
- **ID prefix**: Specimen IDs now use `wemush:` prefix for namespace clarity (e.g., `wemush:clx1a2b3c4`)
- **Context URL**: Schema hosted at `https://wemush.com/wols/v1`
- **Field naming consistency**: Renamed `batchId` → `batch`, `organizationId` → `organization`, `v` → `version`
- **QR capacity verified**: JSON-LD format at ~400-450 bytes, well within 2,000 byte QR limit
- **Backwards compatible**: Existing parsers can ignore `@context`/`@type` and continue working

### Version 1.0.0 (December 18, 2025)

- Initial release
- Core specimen schema defined
- QR encoding formats specified
- Privacy and security guidelines
- Reference implementation roadmap

---

**Next Steps**:

1. Community feedback period (December 2025) — Complete
2. Reference implementation release (January 2026) — Complete ([npm](https://www.npmjs.com/package/@wemush/wols), [PyPI](https://pypi.org/project/wols/), [container](https://github.com/wemush/specimen-labels-py/pkgs/container/specimen-labels-py))
3. WOLS v1.2.0 released (January 26, 2026) — Complete
4. Cross-language interoperability for embedded and encrypted labels — Complete in 1.3.0, with conformance vectors that both reference libraries pass; compact URLs still differ (see [Interoperability Notes](./docs/interoperability-notes.md))
5. WOLS v1.3.0 released (November 15, 2026) — Complete
6. Version 1.4.0 — Not yet scheduled; see [ROADMAP.md](./ROADMAP.md) for scope and proposals
