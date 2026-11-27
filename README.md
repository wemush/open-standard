# WeMush Open Labeling Standard (WOLS)

[![Version](https://img.shields.io/badge/version-1.4.1-blue.svg)](https://github.com/wemush/open-standard/releases)
[![License](https://img.shields.io/badge/license-CC%20BY%204.0-green.svg)](LICENSE)
[![Discussions](https://img.shields.io/github/discussions/wemush/open-standard)](https://github.com/wemush/open-standard/discussions)
[![Stars](https://img.shields.io/github/stars/wemush/open-standard?style=social)](https://github.com/wemush/open-standard/stargazers)

An open-source specification for encoding cultivation specimen data in machine-readable QR codes. **Vendor-agnostic. Privacy-preserving. Research-grade.**

🍄 [Read the Full Specification](./SPECIFICATION.md) | 📖 [View Online](https://wemush.com/open-standard) | 🌐 [WeMush Platform](https://wemush.com) | 💬 [Join the Discussion](https://github.com/wemush/open-standard/discussions)

---

## Why WOLS?

The global mushroom industry is worth **$50 billion** but operates on spreadsheets and paper notebooks. There's no standardization, no interoperability, and no way to share cultivation insights across organizations.

**WOLS fixes this.**

```bash
┌─────────────────┐
│  QR Code Label  │  ←  Scan with any device
└────────┬────────┘
         │
         ↓
┌─────────────────────────────────────────┐
│  Complete Specimen History:             │
│  • Species & strain                     │
│  • Growth stage & timeline              │
│  • Environmental conditions             │
│  • Substrate composition                │
│  • Harvest yields                       │
│  • Lineage & genetics                   │
└─────────────────────────────────────────┘
```

### Use Cases

- 🏭 **Commercial Farms**: Regulatory compliance and traceability
- 🔬 **Research Labs**: Reproducible experiments and data sharing
- 🏠 **Home Cultivators**: Track what works and optimize yields
- ♻️ **Circular Economy**: Prove sustainability claims with verifiable data
- 🤝 **Equipment Manufacturers**: Integrate tracking into products

---

## Quick Start

### Generate a Label (JavaScript/TypeScript)

```bash
npm install @wemush/wols
```

```typescript
import { createSpecimen, toQRCodeDataURL, serializeSpecimen } from '@wemush/wols';

const specimen = createSpecimen({
  species: "Pleurotus ostreatus",
  strain: {
    name: "Blue Oyster PoHu",
    generation: "F2",
  },
  type: "SUBSTRATE",
  stage: "COLONIZATION",
});
specimen.created = new Date().toISOString();

const qrDataUrl = await toQRCodeDataURL(specimen); // QR code as PNG data URL
const json = serializeSpecimen(specimen);          // Full JSON-LD specimen data
```

### Scan and Parse (Python)

```bash
pip install "wols[qr]"
```

```python
from wols import parse_specimen
from wols.qr import scan_qr

# Scan a QR code image (returns a Specimen for embedded labels,
# or a SpecimenRef for compact URLs)
result = scan_qr("path/to/qr_code.png")

# Or parse raw embedded JSON-LD text
specimen = parse_specimen(qr_code_data)

print(f"Species: {specimen.species}")
print(f"Stage: {specimen.stage}")
print(f"Created: {specimen.created}")
```

---

## Features

### 🔓 Open by Default

- **No licensing fees** - Free forever
- **No vendor lock-in** - Works with any platform
- **Community-driven** - Governance by steering committee

### 🔐 Privacy-Preserving

- **Public data option**: Share openly for research
- **Encrypted data option**: Protect proprietary strains
- **Cryptographic signatures** *(Ed25519, since 1.4.0)*: Verify that a label came from a key you trust

### 📈 Research-Grade

- **Complete lineage tracking**: Parent → child relationships
- **Environmental data**: Temp, humidity, CO₂, light
- **Substrate composition**: Reproducible formulations
- **Statistical analysis ready**: Export to CSV, JSON, or SQL

### 🔌 Extensible

- **Custom namespaces**: Add organization-specific fields
- **Multiple encoding formats**: Compact, embedded, or encrypted
- **API-first design**: Integrate with IoT sensors, equipment, or software

---

## Implementations

### Official Libraries

| Language | Package | Repository | Status |
| -------- | -------- | --------- | ------ |
| **JavaScript/TypeScript** | `npm install @wemush/wols` | [specimen-labels-js](https://github.com/wemush/specimen-labels-js) | ✅ Released |
| **Python** | `pip install wols` | [specimen-labels-py](https://github.com/wemush/specimen-labels-py) | ✅ Released |
| **Container/CLI** | `docker pull ghcr.io/wemush/specimen-labels-py:latest` | [ghcr.io/wemush/specimen-labels-py](https://ghcr.io/wemush/specimen-labels-py) | ✅ Released |
| **Go** | — | [specimen-labels-go](https://github.com/wemush/specimen-labels-go) | 📋 Planned |
| **Rust** | — | [specimen-labels-rs](https://github.com/wemush/specimen-labels-rs) | 📋 Planned |

### Platform Support

| Platform | WOLS Support | Link |
| -------- | ------------ | ---- |
| **WeMush** | ✅ Native | [wemush.com](https://wemush.com) |
| **[Your Platform?]** | [Submit PR] | [Your link] |

*Want to add your platform/library? [See Contributing Guide](#contributing)*

---

## Specification Highlights

### Core Data Model

```typescript
interface SpecimenLabel {
  // JSON-LD Context (Required)
  "@context": string;            // Schema URL: "https://wemush.com/wols/v1"
  "@type": string;               // Entity type: "Specimen"

  // Required Fields
  id: string;                    // Unique identifier with wemush: prefix
  version: string;               // Spec version (e.g., "1.4.0")
  type: SpecimenType;            // CULTURE | SPAWN | SUBSTRATE | FRUITING | HARVEST
  species: string;               // Scientific name

  // Taxonomy & Genetics
  strain?: {
    name: string;                // Strain name or identifier
    generation?: string;         // Filial generation (e.g., "F1", "F2", "P")
    clonalGeneration?: number;   // Subculture/clone count
    lineage?: string;            // Parent specimen ID reference
    source?: string;             // "spore", "tissue", "agar", "liquid"
  };

  // Lifecycle Tracking
  stage: GrowthStage;            // Current growth stage (7 stages in v1.2.0)
  created: string;               // ISO 8601 timestamp
  batch?: string;                // Associated batch identifier

  // Attribution & Extensibility
  organization?: string;         // Organization ID
  custom?: Record<string, any>;  // Extensible fields
  _meta?: Record<string, any>;   // Implementation metadata (v1.2.0)
  signature?: string;            // Signature token "{kid}.{sig}" (v1.4.0)
}
```

### Encoding Formats

**Compact** (for small labels):

```bash
wemush://v1/clx1a2b3c4?s=POSTR&st=COLONIZATION&t=1734307200
```

**Embedded** (most common):

```json
{
  "@context": "https://wemush.com/wols/v1",
  "@type": "Specimen",
  "id": "wemush:clx1a2b3c4d5e6f7g8",
  "version": "1.4.0",
  "type": "SUBSTRATE",
  "species": "Pleurotus ostreatus",
  "strain": {
    "name": "Blue Oyster PoHu",
    "generation": "F2"
  },
  "stage": "COLONIZATION",
  "created": "2025-12-16T10:30:00Z"
}
```

**Encrypted** (proprietary strains):

```bash
wemush://v1/encrypted/clx1a2b3c4?e={ciphertext}&iv={iv}&kdf=pbkdf2&salt={salt}&i=100000
```

[📖 Read Full Specification →](./SPECIFICATION.md)

## Relationship to WeMush Platform

**WOLS is open source. WeMush Platform is proprietary.**

This specification and all reference implementations are open source
and free to use. You can:

✅ Build your own platform using WOLS
✅ Generate labels using the libraries
✅ Integrate WOLS into your products
✅ Fork and modify as needed

**The WeMush Platform** (<https://wemush.com>) is a proprietary
implementation of WOLS that offers:

- Free tier with unlimited specimen tracking
- Premium features (ML, IoT, API, etc.)
- Professional support
- Hosted infrastructure

**Why this model?**

Open standards drive adoption. Proprietary platforms drive
sustainability. This model ensures WOLS succeeds long-term
while WeMush can continue investing in advanced features.

Other companies are welcome to build competing platforms.
We believe the best implementation wins, and we're confident
WeMush will be that implementation.

---

## Real-World Examples

### Example 1: Home Cultivator Tracking

**Problem**: "Which substrate gives me the best yields?"

**Solution**:

1. Print WOLS labels for each substrate bag
2. Scan to log growth observations
3. Compare yields across different recipes
4. Reproduce the winner

[See full example →](./examples/home-cultivator.md)

### Example 2: Commercial Traceability

**Problem**: "Food safety audit requires complete cultivation history"

**Solution**:

1. QR code on retail packaging
2. Customer scans → sees full history
3. Proves organic, local, or sustainable claims
4. Regulatory compliance in one scan

[See full example →](./examples/commercial-traceability.md)

### Example 3: Research Reproducibility

**Problem**: "Can't replicate experimental results from published paper"

**Solution**:

1. WOLS label encodes exact parameters
2. QR code in research paper
3. Other labs scan → perfect replication
4. Accelerates scientific progress

[See the research use case →](./SPECIFICATION.md#3-research-reproducibility)

---

## Documentation

- 📘 [Full Specification](./SPECIFICATION.md) ([View Online](https://wemush.com/open-standard/specification))
- 🚀 [Getting Started Guide](./docs/getting-started.md)
- 🔧 [Implementation Guide](./docs/implementation-guide.md)
- 🔐 [Privacy & Security](./SPECIFICATION.md#privacy--security)
- 🎨 [Design Principles](./SPECIFICATION.md#design-principles)
- 💡 [Use Cases](./SPECIFICATION.md#use-cases)
- ❓ [FAQ](./docs/faq.md)

### API Reference

- [JavaScript/TypeScript API](https://github.com/wemush/specimen-labels-js#readme)
- [Python API](https://github.com/wemush/specimen-labels-py#readme)
- [REST API Endpoints](./SPECIFICATION.md#api-specification)

---

## Contributing

We welcome contributions from:

- 🌾 **Growers**: Use cases, feedback, testing
- 💻 **Developers**: Code, documentation, bug fixes
- 🔬 **Researchers**: Academic input, validation
- 🏭 **Industry**: Equipment integration, standards alignment

### How to Contribute

1. **Join the Discussion**: [GitHub Discussions](https://github.com/wemush/open-standard/discussions)
2. **Report Issues**: [GitHub Issues](https://github.com/wemush/open-standard/issues)
3. **Submit Changes**: [Pull Request Guide](./CONTRIBUTING.md)
4. **Improve Docs**: Every page has an "Edit" button

### Contribution Types

| Type | Description | Examples |
| ---- | ----------- | -------- |
| 🐛 **Bug Fix** | Fix errors in spec or code | Typos, broken links, incorrect examples |
| ✨ **Enhancement** | Improve existing features | Better examples, clearer docs |
| 🎉 **New Feature** | Propose spec additions | New fields, encoding formats |
| 📚 **Documentation** | Write guides or tutorials | How-to articles, translations |
| 💬 **Discussion** | Start conversations | Use cases, design questions |

[📋 Read Full Contributing Guide →](./CONTRIBUTING.md)

---

## Governance

### Steering Committee

The WOLS specification is governed by a steering committee that reviews proposals and manages releases.

**Current Members**:

- **Mark Beacom** (Chair) - WeMush Foundation
- [Open seat] - Industry Representative
- [Open seat] - Academic Representative
- [Open seat] - Community Representative

**Want to join?** [Apply here](https://github.com/wemush/open-standard/discussions/1)

### Proposal Process

1. Submit issue describing proposed change
2. Community discussion (14 days)
3. Steering committee review
4. RFC (Request for Comments) draft
5. Final review and vote
6. Merge and release

[📋 Read Full Governance →](./GOVERNANCE.md)

---

## Adoption

### Organizations Using WOLS

| Organization | Type | Use Case | Since |
| ------------- | ------ | ---------- | ------- |
| **Mush Ohio** | Commercial Farm | Production tracking | 2025 |
| [Your org?] | [Type] | [Use case] | [Year] |

**Using WOLS?** [Add your organization →](https://github.com/wemush/open-standard/edit/main/ADOPTION.md)

### Academic Citations

If you use WOLS in research, please cite:

```bibtex
@techreport{beacom2025wols,
  title={WeMush Open Labeling Standard: A Vendor-Agnostic Specification for Cultivation Specimen Tracking},
  author={Beacom, Mark},
  year={2025},
  institution={WeMush Foundation},
  url={https://github.com/wemush/open-standard}
}
```

---

## Community

### Get Help

- 💬 [GitHub Discussions](https://github.com/wemush/open-standard/discussions) - Ask questions
- 🐛 [GitHub Issues](https://github.com/wemush/open-standard/issues) - Report bugs
- 📧 [Email](mailto:opensource@wemush.com) - Direct contact
- 🐦 [Twitter](https://twitter.com/wemush) - Announcements

### Stay Updated

- ⭐ **Star this repo** to follow updates
- 👀 **Watch releases** for version announcements
- 📧 **Join mailing list** for monthly updates
- 🔔 **Enable notifications** for important discussions

---

## License

**Specification & Documentation**: [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE)

You are free to:

- ✅ Share — copy and redistribute
- ✅ Adapt — remix, transform, build upon
- ✅ Commercial use — use in commercial products

**Schema, Conformance Vectors and Example Records**: The JSON Schema in [`schema/`](schema/), the JSON-LD context in [`context/`](context/), the conformance vectors and tools in [`conformance/`](conformance/), and the example records in [`examples/records/`](examples/records/) are dedicated to the public domain under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/), so implementations and code generators can copy them without attribution requirements.

**Code Examples**: Code snippets in this documentation may also be used under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0) for easy integration into your projects.

**Reference Implementations**: Official client libraries (in separate repositories) are licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).

---

## Acknowledgments

WOLS was created by **Mark Beacom** (Veteran, 2025 FVC Fellow, 2025 TSTI Fellow) and is supported by:

- **Farmer Veteran Coalition** - Supporting veteran agriculture
- **Transatlantic Sustainability Transition Initiative** - EU-US innovation collaboration
- **Open-source community** - Contributors worldwide

Special thanks to early adopters, beta testers, and everyone providing feedback.

---

## Roadmap

### Version History

#### Version 1.0.0 (Dec 2025)

- ✅ Core specification released
- ✅ Basic specimen types (CULTURE, SPAWN, SUBSTRATE, FRUITING)
- ✅ 4 growth stages (INOCULATION, COLONIZATION, FRUITING, HARVEST)
- ✅ Compact and embedded encoding formats
- ✅ Basic strain tracking (string format)
- ✅ Environmental data support

#### Version 1.1.0 (Jan 2026)

- ✅ JSON-LD format with `@context` and `@type` fields
- ✅ Enhanced strain object (name, generation, lineage, source)
- ✅ Structured ID format with `wemush:` prefix
- ✅ Added HARVEST specimen type (5 types total)
- ✅ JavaScript/TypeScript library released
- ✅ Python library released
- ✅ Field renames for clarity (`batchId`→`batch`, `organizationId`→`organization`)

#### Version 1.2.0 (Jan 2026)

- ✅ Extended growth stages (7 stages: added INCUBATION, PRIMORDIA, SENESCENCE)
- ✅ Type aliases and generation flexibility (clonalGeneration support)
- ✅ `_meta` namespace for implementation metadata
- ✅ Reference implementation (WeMush platform)
- ✅ Comprehensive documentation and examples

#### Version 1.3.0 (Nov 2026)

- ✅ Encrypted format wire specification: PBKDF2 with per-label salts, `iv` parameter, base64url, NFC passphrases, iteration limits
- ✅ Field-level encryption bound to its label and field (AES-GCM AAD)
- ✅ `strain.transferDepth`, distinct from filial `generation` and `clonalGeneration`
- ✅ `PRIMORDIA` type alias resolves to `FRUITING` with stage `PRIMORDIA`
- ✅ [Conformance test vectors](./conformance/README.md), passed by both reference libraries

#### Version 1.4.0 (Nov 2026) — Current

- ✅ Ed25519 signatures for embedded labels and encrypted URLs: a `{kid}.{sig}` token over RFC 8785 (JCS) canonical JSON or the exact URL bytes
- ✅ Keys resolved only through a caller-supplied trust store, with optional `/.well-known/wols-keys.json` key set documents
- ✅ Five verification statuses: `valid`, `invalid`, `unknown-kid`, `malformed`, `unsigned`
- ✅ Decoders tolerate a numeric `strain.generation` written by older libraries; generators always write a string
- ✅ Clarifications from 1.3.1-rc.1 (reserved `sig`, what encryption does and doesn't protect, ID path encoding), released as part of 1.4.0
- ✅ `signatures.json` conformance vectors and a 51-case cross-library interop matrix, passed by both reference libraries

### Next: Version 1.5.0 (not yet scheduled)

Drafts under discussion: the [data model and JSON Schema](./proposals/wols-1.5-data-model.md) and [compact URL signatures](./proposals/wols-1.5-compact-signatures.md). Neither changes 1.4.0.

- 🚧 Compact URL and species code registries, with compact URL conformance vectors
- 🚧 HTTPS resolver form that phone cameras can open
- 🚧 IoT sensor integration spec
- 🚧 Advanced analytics schema
- 🚧 Supply chain integration

### Future: Version 2.0.0

- 📋 Performance-optimized encoding
- 📋 Blockchain verification
- 📋 Standards body alignment (ANSI/ISO, GS1)
- 📋 Advanced field data

[📋 View Full Roadmap →](./ROADMAP.md)

---

## FAQ

**Q: Do I need to pay to use WOLS?**
A: No. WOLS is free forever. CC BY 4.0 license means zero licensing fees.

**Q: Can I use WOLS with my existing software?**
A: Yes. WOLS is vendor-agnostic and designed for interoperability.

**Q: What if I want to add custom fields?**
A: Use the `custom` namespace. All implementations support extensibility.

**Q: Is this only for mushrooms?**
A: No. WOLS works for any biological specimen tracking. Cannabis, hemp, plants, etc.

**Q: Who owns the data encoded in WOLS labels?**
A: The cultivator who generated it. WOLS is just a format specification.

**Q: How do I report security issues?**
A: Email <security@wemush.com> (PGP key available)

**Q: If the standard is open, can competitors copy WeMush?**
A: They can support the WOLS standard, but not copy our platform. Think Android (open) vs Google Pixel (proprietary but best implementation).

**Q: Do I have to buy WeMush consumables to use the platform?**
A: No. The free tier works with any WOLS-compliant labels, including ones you generate yourself.

**Q: Why not fully open-source everything?**
A: Sustainability. Open-source projects need funding. By keeping the platform proprietary while open-sourcing the standard, we ensure long-term investment in both.

**Q: What if WeMush goes out of business?**
A: The standard lives on. Your data is exportable. Other platforms can continue supporting WOLS. That's the power of open standards.

**Q: Can I use WOLS without the WeMush platform?**
A: Yes! Use the open-source libraries to generate labels, store data however you want, build your own tools. WOLS is completely independent.

[📋 Read Full FAQ →](./docs/faq.md)

---

## Support This Project

### How You Can Help

- ⭐ **Star this repository** - Increases visibility
- 🐛 **Report bugs** - Help improve quality
- 💻 **Contribute code** - Build the future
- 📢 **Spread the word** - Share with your network
- 💬 **Join discussions** - Shape the roadmap

### Sponsors

WOLS development is supported by:

- Individual contributors
- Open-source community
- [Your company? Sponsor us →](https://github.com/sponsors/wemush)

---

## Contact

**Project Lead**: Mark Beacom
**Email**: <opensource@wemush.com>
**Website**: <https://wemush.com>
**GitHub**: [@wemush](https://github.com/wemush)
**LinkedIn**: [Mark Beacom](https://linkedin.com/in/markbeacom)
**Twitter**: [@wemush](https://twitter.com/wemush)

---

<div align="center">

Built with 🍄 by cultivators, for cultivators

[⭐ Star this repo](https://github.com/wemush/open-standard) • [📖 Read the spec](https://wemush.com/open-standard/specification) • [💬 Join the discussion](https://github.com/wemush/open-standard/discussions) • [🚀 Use the platform](https://wemush.com)

</div>
