# WeMush Open Labeling Standard

> 📖 **Read Online**: [wemush.com/open-standard/specification](https://wemush.com/open-standard/specification)

**Status**: Active
**Version**: 1.2.0
**Date**: January 26, 2026
**Author**: Mark Beacom, WeMush Foundation
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
  version: string;               // Spec version (e.g., "1.1.0")
  type: SpecimenType;            // CULTURE | SPAWN | SUBSTRATE | FRUITING | HARVEST
  species: string;               // Scientific name (e.g., "Pleurotus ostreatus")

  // Taxonomy & Genetics
  strain?: {
    name: string;                // Strain name or identifier
    generation?: string;         // Filial generation (e.g., "F1", "F2", "P")
    clonalGeneration?: number;   // Subculture/clone count (e.g., 1, 2, 3...)
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

  // Verification (Optional)
  signature?: string;            // Cryptographic signature for authenticity
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

**Note**: `PRIMORDIA` is a `GrowthStage` value (not a `SpecimenType`), representing the pin initiation phase. A `FRUITING` type specimen progresses through stages including `PRIMORDIA` → `FRUITING` → `SENESCENCE`. Implementations MUST reject `PRIMORDIA` as a specimen type and SHOULD provide a helpful error message directing users to use `stage: "PRIMORDIA"` instead. See Extended Growth Stages below.

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
  "version": "1.1.0",
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
**Encryption**: AES-256-GCM with shared key or public key

```bash
wemush://v1/encrypted/{id}?e={encrypted_payload}&sig={signature}
```

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

- JavaScript/TypeScript: `qrcode` npm package
- Python: `qrcode` or `python-qrcode`
- Go: `github.com/skip2/go-qrcode`

**Example (TypeScript)**:

```typescript
import QRCode from 'qrcode';

async function generateSpecimenLabel(specimen: SpecimenLabel): Promise<string> {
  const payload = JSON.stringify(specimen);

  // Generate QR code as data URL
  const qrDataUrl = await QRCode.toDataURL(payload, {
    errorCorrectionLevel: 'M',
    type: 'image/png',
    width: 300,
    margin: 1,
  });

  return qrDataUrl;
}
```

### Scanning & Parsing

**Mobile Integration**:

```typescript
import { BrowserQRCodeReader } from '@zxing/browser';

async function scanSpecimenLabel(): Promise<SpecimenLabel> {
  const codeReader = new BrowserQRCodeReader();
  const result = await codeReader.decodeFromVideoDevice(null, 'video');

  // Parse embedded JSON
  if (result.getText().startsWith('{')) {
    return JSON.parse(result.getText());
  }

  // Parse compact format
  if (result.getText().startsWith('wemush://')) {
    const url = new URL(result.getText());
    const id = url.pathname.split('/').pop();

    // Fetch full data from API
    const response = await fetch(`https://api.wemush.com/v1/specimens/${id}`);
    return response.json();
  }

  throw new Error('Invalid QR code format');
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
  "version": "1.1.0",
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

### Cryptographic Signatures

For authenticity verification:

```typescript
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
  "version": "1.1.0",
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

**JavaScript/TypeScript**: [`@wemush/wols`](https://github.com/wemush/specimen-labels-js)

```bash
npm install @wemush/wols
```

**Python**: [`wols`](https://github.com/wemush/specimen-labels-py)

```bash
pip install wols
```

**Container/CLI**: [`specimen-labels-py`](https://ghcr.io/wemush/specimen-labels-py) (arm64/amd64)

```bash
docker pull ghcr.io/wemush/specimen-labels-py:latest
```

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

**Current Version**: 1.2.0
**Stability**: Active (feedback welcome)

---

## Governance

### Contribution Process

1. Submit issue on [GitHub](https://github.com/wemush/open-standard)
2. Discuss in community forum
3. Submit PR with proposed changes
4. Review by steering committee
5. Public comment period (14 days)
6. Merge and release

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

1. Community feedback period (December 2025)
2. Reference implementation release (January 2026)
3. Interoperability testing (Q1 2026)
4. Version 1.1 with community enhancements (Q2 2026)
