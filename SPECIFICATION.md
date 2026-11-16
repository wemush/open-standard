# WeMush Open Labeling Standard

> 📖 **Read Online**: [wemush.com/open-standard/specification](https://wemush.com/open-standard/specification)

**Status**: Release candidate — public comment period (see [Governance](#governance))
**Version**: 1.3.1-rc.1
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

  // Verification (Optional, reserved: see Cryptographic Signatures)
  signature?: string;            // Reserved for a future signature scheme; not verified in 1.3.x
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
wemush://v1/encrypted/{id}?e={ciphertext}&iv={iv}&kdf={kdf}[&salt={salt}&i={iterations}][&sig={signature}]
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
| `sig` | No | Reserved for a detached signature. 1.3.x defines no signature algorithm, encoding, or key discovery, and `sig` is not part of decryption (see [Cryptographic Signatures](#cryptographic-signatures)). |

Requirements:

- **ID path segment**: Generators MUST percent-encode the UTF-8 ID suffix as a single RFC 3986 path segment. At minimum they MUST encode `%`, `/`, `?`, `#`, space, `+`, control characters, and all non-ASCII characters. Encoding every character outside the RFC 3986 unreserved set, as `encodeURIComponent` does, is recommended. Decoders MUST percent-decode the segment as UTF-8 before comparing it with the decrypted `id`. They MUST treat `+` as a literal character, and MUST reject malformed escapes or invalid UTF-8. For example, the ID `wemush:Lab A/plate+3%` appears in the URL as `Lab%20A%2Fplate%2B3%25`.
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
- **`sig`**: The `sig` parameter is reserved. Decoders MUST preserve a `sig` value they receive, so that it is still available to the caller and to anything that re-serializes the label, and MUST NOT reject a label because it carries one. Decoders MUST NOT treat `sig` as verified, and MUST NOT report a label as signed, authentic, or unmodified because it carries one.
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
- **Integrity**: Neither form makes the cleartext parts of a label tamper-evident. Someone who can edit a label can change its cleartext fields, or remove encrypted fields entirely. 1.3.x defines no signature scheme that detects this (see [Cryptographic Signatures](#cryptographic-signatures)).
- **Visible metadata**: The ID and the presence of encrypted fields are always visible. AES-GCM doesn't hide length, so each ciphertext also reveals the exact byte length of its plaintext. For field-level encryption that is the length of each field's JSON value, which can be enough to tell short values apart (for example, which of a few known strain names a field holds). 1.3.x defines no padding, so don't rely on encryption to hide how long a value is.
- **Offline guessing**: The ciphertext, salt, and iteration count are printed on the label, so anyone holding the label can try passphrases offline, as fast as their hardware allows, with no rate limit and no way for the owner to notice. PBKDF2 iterations only slow each guess down; they can't protect a guessable passphrase. Use a high-entropy passphrase (for example, a randomly generated passphrase of five or more words, or a long random string) or `kdf=raw` with a randomly generated 32-byte key. Don't use a short, reused, or human-chosen passphrase for labels that leave your control.

### Cryptographic Signatures

> **Reserved.** 1.3.x does not define a signature scheme, and this section is non-normative except for this paragraph. The embedded `signature` field and the encrypted URL's `sig` parameter are reserved. Decoders MUST preserve them and MUST NOT treat them as verified (for `sig`, see the [Encrypted Format](#3-encrypted-format-researchcommercial) requirements). A full signature scheme is planned for 1.4.0.

The sketch below shows the intended shape only. It is **not safe to implement** as written:

- **The embedded public key proves nothing.** It verifies against `specimen.publicKey`, which comes from the signed object itself. Anyone can edit a label, generate their own key pair, re-sign it, and embed their own public key, and the check still passes. A verifier must get the signer's key from a source it already trusts, outside the label.
- **There are no canonical bytes.** `JSON.stringify` has no canonical form: key order, whitespace, and number and string escaping can differ between implementations, or after a parse and re-serialize, so a valid signature can fail to verify elsewhere.

```typescript
// NON-NORMATIVE SKETCH. Do not use: see the warnings above.
interface SignedSpecimen extends SpecimenLabel {
  signature: string;            // ECDSA signature
  publicKey: string;            // Organization's public key
  algorithm: "ECDSA-SHA256";
}

// Verification
async function verifySpecimen(specimen: SignedSpecimen): Promise<boolean> {
  const payload = JSON.stringify(omit(specimen, ['signature']));
  const verified = await crypto.subtle.verify(
    { name: 'ECDSA', hash: 'SHA-256' },
    specimen.publicKey,
    specimen.signature,
    payload
  );
  return verified;
}
```

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

**Conformance test vectors**: [`conformance/`](./conformance/README.md) contains language-neutral test cases (validation, `PRIMORDIA` handling, generation tracking, encrypted format) that implementations SHOULD pass.

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

**Current Version**: 1.3.1-rc.1 (release candidate; 1.3.0 remains the latest final release until 1.3.1 is final)
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

---

## Contact

**Project Lead**: Mark Beacom
**Email**: [mark@wemush.com](mailto:mark@wemush.com)
**GitHub**: [https://github.com/wemush/open-standard](https://github.com/wemush/open-standard)
**Website**: [https://wemush.com](https://wemush.com)

---

## Changelog

### Version 1.3.1-rc.1 (Release candidate — November 16, 2026)

Clarifications to 1.3.0, from a review of what the 1.3.0 text and vectors actually guarantee. Nothing here changes the 1.3.0 wire format or which labels decode: every label that 1.3.0 allowed decodes the same way, and generator limits (including the 100,000-iteration minimum) are unchanged.

Normative clarifications, subject to the public comment period:

- **Signatures reserved**: `sig` and the embedded `signature` field are reserved. Decoders MUST preserve them and MUST NOT treat them as verified. The Cryptographic Signatures sketch is now marked non-normative, with warnings that a public key embedded in the label proves nothing and that `JSON.stringify` has no canonical form. A full signature scheme is planned for 1.4.0.
- **Key derivation responsiveness**: Implementations SHOULD run key derivation off the UI thread. Implementations that offer fewer than the default 600,000 iterations SHOULD tell the user that it weakens resistance to guessing, and SHOULD recommend a high-entropy passphrase or `kdf=raw`.

Editorial:

- **Decoder limits**: Replaces "can't stall a scanner" with the actual bound that the 10,000,000-iteration limit gives.
- **What Encryption Protects**: Adds that AES-GCM reveals each value's plaintext length, that field binding doesn't prevent rollback to an older ciphertext of the same field, and that anyone holding a label can guess passphrases offline.
- **Legacy labels**: Explains why decoding pre-1.3.0 encrypted labels is a MAY: 1.2.0 never fully specified the format, so each library reads only its own. [GOVERNANCE.md](./GOVERNANCE.md#wire-format-compatibility) now says the wire-format compatibility rule applies from 1.3.0 onward.
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
4. Cross-implementation interoperability — In progress; see [Interoperability Notes](./docs/interoperability-notes.md)
5. Version 1.3.0 — See [ROADMAP.md](./ROADMAP.md) for scope and proposals
