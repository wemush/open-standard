# WOLS Roadmap

Strategic roadmap for the WeMush Open Labeling Standard (WOLS) project.

**Current Version**: 1.4.0
**Last Updated**: November 17, 2026
**Planning Horizon**: 2025-2027

## Vision

By 2027, WOLS will be the dominant standard for cultivation specimen tracking across mushrooms, hemp, cannabis, and specialty agriculture, with:

- **50+ commercial organizations** using WOLS in production
- **10+ academic institutions** publishing WOLS-based research
- **5+ equipment manufacturers** with native WOLS integration
- **3+ competing platforms** supporting the standard
- **International adoption** across North America, EU, and Asia

## Roadmap Overview

```text
2025 Q4: v1.0.0 ✅ Foundation
└─ Core specification
└─ Initial documentation
└─ First adopters

2026 Q1: v1.2.0 ✅ Integration & Developer Experience
└─ Type alias system
└─ Flexible ID validation
└─ Generation format flexibility
└─ Reserved _meta namespace
└─ Environment detection utilities
└─ Migration utilities
└─ Extended growth stages (7 research-grade stages)
└─ Integration feedback improvements

2026 Q4: v1.3.0 ✅ Interoperability & Conformance
└─ Encrypted format wire specification
└─ PRIMORDIA type handling
└─ Transfer depth (strain.transferDepth)
└─ Language-neutral conformance vectors

2026 Q4: v1.4.0 ✅ Signatures
└─ Ed25519 signature scheme (trust-store kids, key set documents)
└─ Numeric strain.generation tolerance for decoders
└─ Cross-library interop matrix

Next: v1.5.0 📋 IoT, Analytics & Interoperability
└─ Compact URL and species code registries
└─ HTTPS resolver form
└─ IoT sensor specs
└─ Advanced analytics
└─ Supply chain features

Future: v2.0.0 📋 Maturity
└─ Performance optimization
└─ Blockchain verification
└─ Global standards alignment
```

## Released: v1.0.0 (December 2025)

### Status: ✅ v1.0.0 RELEASED

### Goals

- [x] Launch core specification
- [x] Establish governance model
- [x] Create reference documentation
- [x] First commercial adopter (Mush Ohio)
- [x] Community infrastructure (GitHub, discussions)

### Deliverables

- [x] SPECIFICATION.md - Core data model and encoding formats
- [x] README.md - Project overview and quick start
- [x] CONTRIBUTING.md - Contribution guidelines
- [x] GOVERNANCE.md - Decision-making processes
- [x] ADOPTION.md - Adopter tracking
- [x] GitHub repository - Public source control
- [x] Initial documentation structure
- [x] @wemush/wols npm package - Published and in production use

### Metrics

- ✅ 1+ commercial adopter
- ✅ Specification published
- ✅ Community forums active
- ✅ @wemush/wols npm package in production (WeMush platform) ← NEW
- ✅ Target: 5 GitHub stars (Current: 49)
- ✅ Target: 3 discussions started

## Released: v1.2.0 (January 2026)

### Status: ✅ v1.2.0 RELEASED

### Theme: **Integration & Developer Experience**

Focus on making WOLS easier to integrate and extend for developers and equipment manufacturers. **Incorporates real-world feedback from WeMush platform integration.**

### v1.2.0 Goals

1. **Integration Feedback Improvements** (from WeMush platform)
   - **Flexible ID format validation**: Support ULIDs, UUIDs, and custom patterns
   - **Type alias system**: Map platform-specific types (LIQUID_CULTURE, GRAIN_SPAWN, PRIMORDIA) to WOLS categories
   - **Generation format flexibility**: Accept `G{n}`, `F{n}`, or numeric formats
   - **Reserved metadata namespace**: `_meta` field for round-trip implementation data
   - **Convenience API methods**: `parseOrThrow()`, `parseOrNull()` variants
   - **Environment detection helpers**: `isServer()`, `supportsWebCrypto()` utilities

2. **Extended Growth Stages** (Research-Grade Precision)
   - **7 lifecycle stages**: INOCULATION → INCUBATION → COLONIZATION → PRIMORDIA → FRUITING → SENESCENCE → HARVEST
   - **INCUBATION**: Post-inoculation monitoring before visible colonization
   - **PRIMORDIA**: Pin initiation tracking for precise timing
   - **SENESCENCE**: End-of-life monitoring for research specimens
   - **Backward compatible**: Older parsers gracefully handle new stages

3. **Developer Tools & Libraries**
   - JavaScript/TypeScript library (v1.2.0) ✅ @wemush/wols published
   - Python library (v1.2.0) ✅ wols published (PyPI + GHCR container)
   - CLI tool (v1.2.0) ✅ `wols` command available

4. **Migration Utilities**
   - Version comparison functions
   - Specimen migration handlers
   - Backward compatibility preserved

### v1.2.0 Deliverables

- [x] @wemush/wols npm package v1.2.0 ([specimen-labels-js](https://github.com/wemush/specimen-labels-js)) ✅ DONE
- [x] Type alias system with 20+ built-in aliases ✅ DONE
- [x] ID validation modes (strict, ulid, uuid, any) ✅ DONE
- [x] Generation normalization utilities ✅ DONE
- [x] Environment detection helpers ✅ DONE
- [x] Migration utilities ✅ DONE
- [x] Reserved `_meta` namespace ✅ DONE
- [x] Extended growth stages (7 research-grade stages) ✅ DONE
- [x] wols Python package v1.2.0 ([specimen-labels-py](https://github.com/wemush/specimen-labels-py)) ✅ DONE
- [x] CLI tool (`wols` command) ✅ DONE
- [x] Container image (GHCR) ✅ DONE
- [ ] Migration guide from v1.0/v1.1 to v1.2

### Success Metrics

- ✅ 1+ commercial platform integration (WeMush)
- 🎯 3+ equipment manufacturers in discussions
- 🎯 10+ organizations using WOLS
- 🎯 50+ GitHub stars
- 🎯 1000+ label generations via libraries

### Timeline

- **January 2026**: v1.2.0 specification and JS/TS library released ✅
- **February 2026**: Python library v1.2, community feedback
- **March 2026**: Documentation finalized, adoption push

## Released: v1.3.0 (November 2026)

### Status: ✅ v1.3.0 RELEASED

### Theme: **Interoperability & Conformance**

Closes the cross-implementation gaps found while integrating the WeMush Platform. See [Interoperability Notes](./docs/interoperability-notes.md) for what remains open.

### Deliverables

- [x] Encrypted format wire specification: `kdf`, per-label `salt`, `i`, separate `iv`, base64url, NFC passphrases, iteration limits, and field-level AAD ✅ DONE
- [x] `PRIMORDIA` type handling: resolves to `FRUITING` and defaults `stage` ✅ DONE
- [x] `strain.transferDepth` for per-transfer counting ✅ DONE
- [x] Conformance vectors for embedded, `PRIMORDIA`, generation, encrypted, and field-level encryption cases ([`conformance/`](./conformance/README.md)) ✅ DONE
- [x] Pre-release process and wire-format compatibility rule ([GOVERNANCE.md](./GOVERNANCE.md)) ✅ DONE
- [x] `@wemush/wols` 1.3.0 ([specimen-labels-js](https://github.com/wemush/specimen-labels-js)) passes every conformance vector ✅ DONE
- [x] `wols` 1.3.0 ([specimen-labels-py](https://github.com/wemush/specimen-labels-py)) passes every conformance vector ✅ DONE

### Timeline

- **November 2026**: 1.3.0-rc.1, 1.3.0-rc.2, and the final 1.3.0 release, with both libraries ✅

## Current: v1.4.0 (November 2026)

### Status: ✅ v1.4.0 RELEASED

### Theme: **Signatures**

Lets a verifier check that a label was signed with a key it trusts and hasn't changed since. It also folds in the 1.3.1-rc.1 clarifications, which were not released separately.

### Deliverables

- [x] Signature scheme: Ed25519 over RFC 8785 (JCS) canonical JSON for embedded labels and over the exact URL bytes for encrypted URLs, with a domain-separated signing input, a `{kid}.{sig}` token in the `signature` field and `sig` parameter, kids resolved only through a caller-supplied trust store, and five verification statuses ✅ DONE
- [x] Key set documents (`/.well-known/wols-keys.json`), with entries for unsupported algorithms skipped ✅ DONE
- [x] Numeric `strain.generation`: generators write a string, decoders read an integer as its decimal string with a warning ✅ DONE
- [x] 1.3.1-rc.1 clarifications: reserved `sig`, key derivation responsiveness, what encryption does and doesn't protect, ID path encoding ✅ DONE
- [x] `signatures.json` conformance vectors (112 `MUST` cases) ✅ DONE
- [x] Cross-library interop matrix ([`conformance/interop/`](./conformance/interop/README.md), 51 cases) with both reference harnesses ✅ DONE
- [x] `@wemush/wols` 1.4.0 ([specimen-labels-js](https://github.com/wemush/specimen-labels-js)) passes every conformance vector ✅ DONE
- [x] `wols` 1.4.0 ([specimen-labels-py](https://github.com/wemush/specimen-labels-py)) passes every conformance vector ✅ DONE

### Timeline

- **November 2026**: 1.3.1-rc.1, 1.4.0-rc.1, and the final 1.4.0 release, with both libraries ✅

## Real-World Integration Learnings

### WeMush Platform Integration (January 2026)

The WeMush cultivation tracking platform completed full integration with `@wemush/wols`:

**Features Successfully Implemented:**

- ✅ Compact URL encoding for QR codes on petri dishes and culture tubes
- ✅ Embedded JSON format for larger labels
- ✅ AES-256-GCM encryption for sensitive research specimens
- ✅ Round-trip encryption/decryption with metadata preservation
- ✅ Browser (Web Crypto API) and server (Node.js) decryption
- ✅ PWA protocol handler for `wemush://` URLs

**Issues Resolved in v1.2.0:**

| Challenge | v1.0 Workaround | v1.2.0 Solution |
| ----------- | ------------ | -------------- |
| Strict ID format | Store original ID in `custom._originalId` | ✅ `idMode: 'ulid' \| 'uuid' \| 'any'` |
| Limited types | Map via `PLATFORM_TO_WOLS_TYPE` | ✅ `registerTypeAlias()` with 20+ built-ins |
| F{n} only generation | Transform G{n} to F{n} on encode | ✅ `normalizeGeneration()` |
| parseCompactUrl API | Check `.success` then access `.data` | ✅ `parseCompactUrlOrThrow()`, `parseCompactUrlOrNull()` |
| Metadata loss | Store in `custom` field | ✅ Reserved `_meta` namespace |
| Env detection | Manual checks | ✅ `isServer()`, `isCryptoSupported()` |

**Extended Growth Stages (Delivered in v1.2.0):**

The platform uses 7 growth stages internally. WOLS v1.2.0 now supports all 7 research-grade stages:

| Platform Stage | WOLS v1.2.0 | Notes |
| -------------- | ----------- | ----- |
| INOCULATION | ✅ | Initial spore/culture introduction |
| INCUBATION | ✅ | Post-inoculation, pre-visible growth |
| COLONIZATION | ✅ | Active mycelial growth |
| PRIMORDIA | ✅ | Pin initiation (hyphal knots) |
| FRUITING | ✅ | Fruiting body development |
| SENESCENCE | ✅ | End-of-life monitoring |
| HARVEST | ✅ | Final harvest stage |

## Next: v1.5.0

### Status: 🧪 RELEASE CANDIDATE (`1.5.0-rc.2`, November 28, 2026)

### Theme: **IoT & Analytics**

Focus on enterprise features, IoT integration, and supply chain tracking.

### v1.5.0 Goals

1. **IoT Sensor Integration Specification**
   - Standard for encoding sensor data in WOLS labels
   - Examples: temperature, humidity, CO₂, light sensors
   - Real-time monitoring integration patterns

2. **Advanced Analytics Schema**
   - Yield prediction data fields
   - Quality metrics standardization
   - Time-series data encoding

3. **Supply Chain Integration**
   - Multi-party verification patterns
   - Custody transfer tracking
   - Wholesale/retail integration specs

4. **Enhanced Security Features**
   - **Compact URL signing**: Follows the compact URL vectors. The signature scheme itself shipped in [1.4.0](#current-v140-november-2026).
   - Blockchain-ready verification hooks
   - Multi-signature support for supply chains

5. **Interoperability & Conformance** *(proposed from platform integration review; open for community comment)*

   These proposals close gaps documented in [Interoperability Notes](./docs/interoperability-notes.md). Each one needs a decision through the [contribution process](./SPECIFICATION.md#contribution-process) before it becomes normative.

   - **Compact URL parameter registry**: Make the full parameter set normative (`s`, `ty`, `st`, `t`, `b`, `sn`, `sg`). Choose one stage encoding (full names or 3-letter codes) and say whether parsers must accept both. Define how the minor version is signaled, since `v1` alone cannot distinguish 1.0 from 1.2. *In `1.5.0-rc.2`: every parameter is normative, including the platform's `td`; decoders accept both stage spellings and generators may write either; `v1` names the major version only, and the registries are append-only, so no minor version needs signaling; external parameters use an `x-` prefix.*
   - **Species code registry**: Move the 5-letter table from the [Implementation Guide](./docs/implementation-guide.md#appendix-species-codes-compact-format) into the specification, define the fallback for unregistered species (full name or error), and add a registration process like the one for custom namespaces. The Python library currently uses a different 2-letter table. *In `1.5.0-rc.2`: the five-letter table is the registry, with 17 more species; unregistered species are written by full name; the two-letter codes are legacy codes that decoders still read.*
   - **HTTPS resolver form**: Native phone cameras don't open `wemush://` or `web+wemush://`. Define an `https://` form that is equivalent to the compact URL, how a resolver base is chosen or discovered, and how it relates to the `@context` URL. *Not in 1.5: rc.2 only lets decoders accept such a URL; the form itself moves to a later release.*
   - **Required-field clarity**: State whether `stage` and `created` are required. The core interface implies yes; both libraries treat `stage` as optional, and the TypeScript library sets `created` only when the caller passes it.
   - **Multiple parents**: Allow `strain.lineage` to hold several parent IDs (combined spawn, multi-spore isolates, packages made from several blocks). *In `1.5.0-rc.1` as the new `derivedFrom` member, so `strain.lineage` stays a single ID for 1.4 readers.*
   - **Generation without a named strain**: Let specimens record `generation` and `clonalGeneration` when `strain.name` is unknown.
   - **Extended data attachment**: Define where `EnvironmentalData`, `SubstrateFormula`, and `CircularEconomyData` attach to a specimen, and align the REST example (`metadata`, `observations`) with the core model.
   - **Specimen condition**: Add an optional field for terminal or abnormal states (for example contaminated, disposed, archived). Today implementations must map a contaminated specimen to a growth stage, which loses information.
   - **Container/vessel (optional)**: Add an optional field for vessel and size (petri dish, jar, bag, monotub). Several current type aliases (`PETRI`, `BAG`, `BUCKET`) describe vessels rather than specimen types.

### v1.5.0 Deliverables

- [ ] IoT Integration Guide
- [ ] Analytics specification
- [ ] Supply chain guide
- [ ] Enhanced security documentation
- [ ] API specification document (REST, GraphQL)
- [ ] Compact URL conformance vectors (other formats are covered in [`conformance/`](./conformance/README.md) as of 1.3.0)
- [x] Published JSON-LD context document at `https://wemush.com/wols/v1` ([`context/v1.jsonld`](./context/v1.jsonld), served since November 27, 2026)
- [x] Draft 1.5 proposals: [data model and JSON Schema](./proposals/wols-1.5-data-model.md) ([`schema/1.5/`](./schema/1.5/)) and [compact URL signatures](./proposals/wols-1.5-compact-signatures.md)
- [x] `1.5.0-rc.1`: normative JSON Schema and data model (required-field clarity, multiple parents, generation without a named strain, extended data attachment through the Records Bundle, specimen condition, container), with [`data-model.json`](./conformance/vectors/data-model.json) and [`bundle.json`](./conformance/vectors/bundle.json) vectors
- [ ] `1.5.0-rc.2`: compact URL parameter registry, species code registry and compact URL signatures, with compact URL vectors
- [ ] A maintained library passes every `MUST` vector of the final candidate

### v1.5.0 Success Metrics

- 🎯 25+ organizations
- 🎯 5+ supply chain integrations
- 🎯 1 academic paper published using WOLS
- 🎯 100+ GitHub stars

### v1.5.0 Timeline

`1.5.0-rc.1` (data model) and `1.5.0-rc.2` (compact URL registries and signatures) are out for feedback. The final release follows once a library passes every `MUST` vector and the print-and-scan test in the [compact signatures proposal](./proposals/wols-1.5-compact-signatures.md) is done. Normative changes ship as release candidates first (see [GOVERNANCE.md](./GOVERNANCE.md)).

## Long-Term: v2.0.0

### Status: 📋 CONCEPTUAL

### Theme: **Maturity & Global Standards**

Major version focused on performance, global adoption, and standards body recognition.

### v2.0.0 Goals

1. **Performance Optimization**
   - Compressed encoding formats
   - Efficient bulk operations
   - Streaming data support

2. **Blockchain Verification**
   - Native blockchain integration (Ethereum, Polygon, etc.)
   - NFT-based specimen tracking
   - Decentralized verification

3. **Standards Body Alignment**
   - ANSI/ISO standard submission
   - Alignment with GS1 standards
   - FDA/regulatory compliance documentation

4. **Advanced Field Data**
   - GPS tracking for outdoor cultivation
   - Weather data integration
   - Soil composition encoding

5. **Machine Learning Ready**
   - Schema optimization for ML pipelines
   - Training data export formats
   - Model metadata encoding

### Potential Breaking Changes

- Optimized field names (shorter for compact encoding)
- Deprecated field removal
- New required fields (with migration guide)

### v2.0.0 Deliverables

- [ ] v2.0 specification
- [ ] Standards body submission
- [ ] Migration tools and guides
- [ ] Performance benchmarks
- [ ] ML integration documentation

### v2.0.0 Success Metrics

- 🎯 50+ organizations
- 🎯 10+ academic papers
- 🎯 Standards body recognition
- 🎯 International adoption (3+ continents)
- 🎯 500+ GitHub stars

### v2.0.0 Timeline

Not yet scheduled. Expected phases: an RFC period for breaking-change proposals, then implementation, testing, and migration guides.

## Beyond 2.0

### Future Possibilities (2027+)

**Under Consideration**:

- **Genomic Integration**: Full DNA sequence encoding
- **AR/VR Support**: 3D specimen visualization metadata
- **Automated Cultivation**: Integration with robotic systems
- **Market Integration**: Price discovery and trading data
- **Insurance**: Risk assessment and coverage metadata
- **Certification**: Organic, sustainable, fair trade proofs

**Community Input Needed**: [Share your ideas](https://github.com/wemush/open-standard/discussions/categories/ideas)

## Feature Requests

### Top Community Requests

Track community-requested features and their status:

| Feature | Votes | Status | Target Version |
| --------- | ------- | -------- | ---------------- |
| Flexible ID formats | 1 | ✅ Released | v1.2.0 |
| Type alias system | 1 | ✅ Released | v1.2.0 |
| Environment detection | 1 | ✅ Released | v1.2.0 |
| Migration utilities | 1 | ✅ Released | v1.2.0 |
| Extended growth stages | 1 | ✅ Released | v1.2.0 |
| Cryptographic signatures | - | ✅ Released | v1.4.0 |
| IoT sensor integration | - | 📋 Planned | v1.5.0 |
| Blockchain verification | - | 📋 Planned | v2.0.0 |
| Mobile app example | - | 💭 Considering | TBD |
| Video documentation | - | 💭 Considering | TBD |

**Request a feature**: [Start a discussion](https://github.com/wemush/open-standard/discussions/categories/ideas)

## Dependencies & Risks

### External Dependencies

- **JavaScript ecosystem**: Node.js, npm, TypeScript
- **Python ecosystem**: Python 3.12+, pip, uv
- **GitHub**: Repository hosting, CI/CD
- **Community**: Volunteer contributors

### Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
| ------ | -------- | ------------- | ------------ |
| Low adoption | High | Medium | Focus on developer experience, marketing |
| Competing standards emerge | High | Low | Be first to market, superior quality |
| Maintainer burnout | Medium | Medium | Expand steering committee, share workload |
| Breaking changes needed | Medium | Low | Careful design, RFC process |
| Security vulnerability | High | Low | Security audit, bug bounty program |
| Integration friction | Medium | Medium | Address real-world feedback promptly |

## Resource Requirements

### Q1 2026 (v1.1.0)

**Development**:

- 1 full-time developer (libraries)
- 1 part-time technical writer (documentation)
- Community contributors (testing, feedback)
- WeMush platform team (integration feedback and PRs)

**Infrastructure**:

- GitHub (free for open source)
- CI/CD pipeline (GitHub Actions)
- Documentation hosting (GitHub Pages or similar)

**Budget**: $0-5k (mostly volunteer-driven)

### Q2-Q4 2026

**Scaling Requirements**:

- 2 full-time developers
- 1 full-time technical writer
- Part-time community manager
- Security audit budget

**Budget**: $10-30k per quarter

## Measurement & Success

### Key Performance Indicators

**Adoption**:

- Organizations using WOLS in production
- Countries with active adopters
- Specimen types tracked

**Community**:

- GitHub stars and forks
- Discussion participation
- Pull request contributions

**Quality**:

- Test coverage percentage
- Documentation completeness
- Issue resolution time

**Impact**:

- Academic papers citing WOLS
- Media mentions
- Conference presentations

### Quarterly Reviews

Steering committee reviews roadmap quarterly:

- Progress against milestones
- Community feedback integration
- Priority adjustments
- Resource allocation

## How to Influence the Roadmap

### Share Your Needs

1. **Start a Discussion**: [Ideas forum](https://github.com/wemush/open-standard/discussions/categories/ideas)
2. **Submit Feature Request**: [GitHub Issues](https://github.com/wemush/open-standard/issues/new?template=feature_request.md)
3. **Join Steering Committee**: [Apply here](https://github.com/wemush/open-standard/discussions/categories/governance)
4. **Contribute Code**: Implement and propose features
5. **Share Use Cases**: Real-world needs drive priorities

### Priority Criteria

Features prioritized by:

1. **Community need**: How many organizations request it
2. **Use case strength**: Real-world impact
3. **Implementation effort**: Feasibility and resources
4. **Strategic alignment**: Fit with vision
5. **Backward compatibility**: Migration complexity

## Commitments

### What We Promise

- ✅ **Stability**: No breaking changes without major version bump
- ✅ **Transparency**: Public roadmap, open discussions
- ✅ **Community**: Your input shapes priorities
- ✅ **Quality**: Thorough testing and documentation
- ✅ **Support**: Responsive to issues and questions
- ✅ **Feedback Loop**: Real-world integration feedback incorporated ← NEW

### What We Don't Promise

- ❌ **Exact Timelines**: Dates are estimates, may shift
- ❌ **Every Feature**: Can't implement everything
- ❌ **Commercial Support**: Community-driven project
- ❌ **Backward Compatibility Forever**: v2.0+ may break changes

## Get Involved

### Help Build the Future

- 💻 **Developers**: Build libraries and tools
- 📚 **Writers**: Create tutorials and documentation
- 🔬 **Researchers**: Validate and publish findings
- 🏭 **Industry**: Provide use cases and feedback
- 💬 **Community**: Test, discuss, and evangelize

**Start here**: [CONTRIBUTING.md](./CONTRIBUTING.md)

## Contact

**Roadmap Questions**: [GitHub Discussions](https://github.com/wemush/open-standard/discussions/categories/roadmap)
**Email**: [roadmap@wemush.com](mailto:roadmap@wemush.com)
**Steering Committee**: [governance@wemush.com](mailto:governance@wemush.com)

---

**Last Updated**: November 17, 2026
**Next Review**: February 2027
**Version**: 1.4.0 (Roadmap document version)

---

## Built with 🍄 by cultivators, for cultivators

[⭐ Star this repo](https://github.com/wemush/open-standard) • [📖 Read the spec](./SPECIFICATION.md) • [💬 Discuss](https://github.com/wemush/open-standard/discussions)
