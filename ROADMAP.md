# WOLS Roadmap

Strategic roadmap for the WeMush Open Labeling Standard (WOLS) project.

**Current Version**: 1.2.0
**Last Updated**: January 26, 2026
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

2026 Q2: v1.3.0 📋 IoT & Analytics
└─ IoT sensor specs
└─ Advanced analytics
└─ Supply chain features

2026 Q3-Q4: v2.0.0 📋 Maturity
└─ Performance optimization
└─ Blockchain verification
└─ Global standards alignment
```

## Current: v1.0.0 (December 2025)

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

## Current: v1.2.0 (January 2026)

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
   - JavaScript/TypeScript library (v0.1.0) ✅ @wemush/wols published
   - Python library (v1.0) - v0.1.1 update in progress
   - CLI tool for label generation

4. **Migration Utilities**
   - Version comparison functions
   - Specimen migration handlers
   - Backward compatibility preserved

### v1.2.0 Deliverables

- [x] @wemush/wols npm package v0.1.0 ([specimen-labels-js](https://github.com/wemush/specimen-labels-js)) ✅ DONE
- [x] Type alias system with 20+ built-in aliases ✅ DONE
- [x] ID validation modes (strict, ulid, uuid, any) ✅ DONE
- [x] Generation normalization utilities ✅ DONE
- [x] Environment detection helpers ✅ DONE
- [x] Migration utilities ✅ DONE
- [x] Reserved `_meta` namespace ✅ DONE
- [x] Extended growth stages (7 research-grade stages) ✅ DONE
- [ ] wols Python package v1.2 ([specimen-labels-py](https://github.com/wemush/specimen-labels-py)) - IN PROGRESS
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

## Future: v1.3.0 (Q2 2026)

### Status: 📋 PLANNED

### Theme: **IoT & Analytics**

Focus on enterprise features, IoT integration, and supply chain tracking.

### v1.3.0 Goals

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
   - Blockchain-ready verification hooks
   - Multi-signature support for supply chains

### v1.3.0 Deliverables

- [ ] IoT Integration Guide
- [ ] Analytics specification
- [ ] Supply chain guide
- [ ] Enhanced security documentation
- [ ] API specification document (REST, GraphQL)

### v1.3.0 Success Metrics

- 🎯 25+ organizations
- 🎯 5+ supply chain integrations
- 🎯 1 academic paper published using WOLS
- 🎯 100+ GitHub stars

### v1.3.0 Timeline

- **April 2026**: Spec drafts, community feedback
- **May 2026**: Implementation and testing
- **June 2026**: v1.3.0 release

## Long-Term: v2.0.0 (Q3-Q4 2026)

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

- **Q3 2026**: RFC period, breaking change proposals
- **Q4 2026**: Implementation, testing, migration guides
- **Late 2026/Early 2027**: v2.0.0 release

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
| IoT sensor integration | - | 📋 Planned | v1.3.0 |
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

**Last Updated**: January 26, 2026
**Next Review**: April 2026
**Version**: 1.2.0 (Roadmap document version)

---

## Built with 🍄 by cultivators, for cultivators

[⭐ Star this repo](https://github.com/wemush/open-standard) • [📖 Read the spec](./SPECIFICATION.md) • [💬 Discuss](https://github.com/wemush/open-standard/discussions)
