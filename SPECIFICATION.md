# WeMush Open Labeling Standard

> 📖 **Read Online**: [wemush.com/open-standard/specification](https://wemush.com/open-standard/specification)

**Status**: Active
**Version**: 1.0.0
**Date**: December 18, 2025
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

The foundational entity representing a biological specimen at any stage of cultivation.

```typescript
interface SpecimenLabel {
  // Required Fields
  id: string;                    // Unique identifier (CUID)
  version: string;               // Spec version (e.g., "1.0.0")
  type: SpecimenType;            // CULTURE | SPAWN | SUBSTRATE | FRUITING | HARVEST
  species: string;               // Scientific name (e.g., "Pleurotus ostreatus")

  // Taxonomy & Genetics
  strain?: string;               // Strain name or identifier
  genetics?: {
    source?: string;             // Origin of genetic material
    generation?: number;         // Passage number
    parentIds?: string[];        // Parent specimen IDs
  };

  // Lifecycle Tracking
  stage: GrowthStage;            // INOCULATION | COLONIZATION | FRUITING | HARVEST
  created: string;               // ISO 8601 timestamp
  batchId?: string;              // Associated batch identifier

  // Attribution
  organization?: string;         // Organization ID
  creator?: string;              // User ID (optional for privacy)

  // Extensibility
  custom?: Record<string, any>; // Vendor-specific extensions

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
  INOCULATION = "INOCULATION",
  COLONIZATION = "COLONIZATION",
  FRUITING = "FRUITING",
  HARVEST = "HARVEST",
}
```

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

```json
{
  "v": "1.0.0",
  "id": "clx1a2b3c4d5e6f7g8",
  "type": "SUBSTRATE",
  "species": "Pleurotus ostreatus",
  "strain": "Blue Oyster PoHu",
  "stage": "COLONIZATION",
  "created": "2025-12-16T10:30:00Z",
  "batch": "batch_2025_12_001",
  "org": "org_mushoh"
}
```

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
  "id": "clx1a2b3c4d5e6f7g8",
  "type": "SUBSTRATE",
  "species": "Pleurotus ostreatus",
  "strain": "Blue Oyster PoHu",
  "stage": "COLONIZATION",
  "created": "2025-12-16T10:30:00Z",
  "batchId": "batch_2025_12_001",
  "organizationId": "org_mushoh",
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
|-------|-------------|----------|----------|
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
  "id": "clx1a2b3c4",
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

**JavaScript/TypeScript**: `@wemush/specimen-label`

```bash
npm install @wemush/specimen-label
```

**Python**: `wemush-labels`

```bash
pip install wemush-labels
```

**API**: `https://api.wemush.com/v1`

**Playground**: `https://labels.wemush.com`

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

**Current Version**: 1.0.0
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
|--------------|----------|-------|
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

**Creative Commons Attribution 4.0 International (CC BY 4.0)**

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
