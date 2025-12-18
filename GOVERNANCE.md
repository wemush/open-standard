# WOLS Governance

This document describes the governance structure, decision-making processes, and roles within the WeMush Open Labeling Standard (WOLS) project.

## Vision & Mission

### Vision

To become the universal standard for encoding and sharing cultivation specimen data across the global agriculture and research community.

### Mission

Develop and maintain an open, vendor-agnostic specification that enables:

- **Interoperability**: Data flows freely between systems
- **Transparency**: Cultivation practices can be verified
- **Research**: Scientific reproducibility and collaboration
- **Trust**: Cryptographic proof of authenticity
- **Privacy**: Cultivators control their own data

## Core Principles

1. **Open by Default**: Specification is free and publicly available
2. **Consensus-Seeking**: Decisions consider all stakeholder perspectives
3. **Evidence-Based**: Requirements driven by real use cases
4. **Backward Compatible**: Changes maintain compatibility where possible
5. **Vendor-Neutral**: No company controls the standard
6. **Community-Driven**: All voices welcome in the process
7. **Scientifically Sound**: Validated by research and testing

## Organizational Structure

### Steering Committee

**Role**: Strategic direction, specification approval, conflict resolution

**Composition**:

- 5-7 members representing key stakeholder groups
- 2-year terms, renewable once
- Meets quarterly (more often if needed)
- Decisions by consensus when possible, simple majority vote when necessary

**Current Members**:

| Name | Affiliation | Role | Term |
|------|-------------|------|------|
| Mark Beacom | WeMush Foundation | Chair | 2025-2027 |
| [Open] | Commercial Industry | Industry Rep | TBD |
| [Open] | Academic Institution | Research Rep | TBD |
| [Open] | Open Source Community | Community Rep | TBD |
| [Open] | Equipment Manufacturer | Manufacturing Rep | TBD |

**Responsibilities**:

- Approve major specification changes
- Set project roadmap and priorities
- Resolve disputes and conflicts
- Ensure diverse stakeholder representation
- Maintain project vision and values
- Appoint maintainers and working groups

**Selection Process**:

1. Open nomination period (30 days)
2. Candidates submit statement of interest
3. Current committee reviews qualifications
4. Community feedback period (14 days)
5. Committee vote (2/3 majority required)
6. Public announcement

**Qualifications**:

- Active participation in WOLS community
- Domain expertise (cultivation, research, software, etc.)
- Commitment to open standards principles
- Ability to represent broader stakeholder interests
- Time availability for quarterly meetings

### Maintainers

**Role**: Day-to-day management, code review, issue triage

**Current Maintainers**:

- **Specification**: Mark Beacom (@mbeacom)
- **JavaScript/TypeScript**: [TBD]
- **Python**: [TBD]
- **Documentation**: [TBD]

**Responsibilities**:

- Review and merge pull requests
- Triage and respond to issues
- Maintain reference implementations
- Update documentation
- Support community members
- Enforce code of conduct

**Selection**:

- Nominated by steering committee or existing maintainers
- Demonstrated technical expertise and community involvement
- Approved by steering committee
- 1-year terms, renewable indefinitely

### Working Groups

**Role**: Focus on specific topics or initiatives

**Current Working Groups**:

- **Specification**: Core data model and encoding formats
- **Security**: Encryption, signatures, privacy
- **Research**: Scientific validation and academic outreach
- **Industry**: Commercial adoption and integration
- **Documentation**: Guides, tutorials, translations

**Formation**:

- Anyone can propose a working group
- Must have clear scope and deliverables
- Requires 3+ active participants
- Approved by steering committee
- Reports progress quarterly

### Contributors

**Role**: Anyone who participates in the project

**How to Contribute**: See [CONTRIBUTING.md](./CONTRIBUTING.md)

**Recognition**:

- Listed in AUTHORS file
- Mentioned in release notes
- Invited to community calls
- Eligible for maintainer/committee roles

## Decision-Making Process

### Types of Decisions

#### Type 1: Minor Changes

**Examples**: Typos, documentation fixes, clarifications

**Process**:

1. Submit pull request
2. 1 maintainer review and approval
3. Merge immediately

**Timeline**: 1-3 days

#### Type 2: Standard Changes

**Examples**: New optional fields, additional examples, non-breaking enhancements

**Process**:

1. Open issue or discussion
2. Community feedback (7 days minimum)
3. Pull request with implementation
4. 2 maintainer reviews and approvals
5. Steering committee notification
6. Merge

**Timeline**: 2-3 weeks

#### Type 3: Significant Changes

**Examples**: New encoding formats, breaking changes, major features

**Process**:

1. RFC (Request for Comments) in Discussions
2. Community debate and refinement (14 days minimum)
3. Steering committee review and recommendation
4. Draft specification PR
5. Reference implementation
6. Public comment period (7 days)
7. Steering committee vote
8. Merge and announce

**Timeline**: 4-8 weeks

#### Type 4: Governance Changes

**Examples**: Committee membership, process changes, project scope

**Process**:

1. Proposal in Discussions
2. Community input (21 days minimum)
3. Steering committee deliberation
4. Vote (2/3 majority required)
5. Update governance documents
6. Public announcement

**Timeline**: 6-12 weeks

### Voting

**When Required**:

- Steering committee membership
- Breaking changes to specification
- Governance changes
- Disputes without consensus
- Budget decisions (when applicable)

**Who Votes**: Steering committee members

**Voting Threshold**:

- Simple majority (50% + 1): Standard decisions
- 2/3 majority (66%+): Governance, membership, breaking changes
- Unanimous: Changes to voting rules

**Abstentions**: Count toward quorum but not toward majority

**Conflicts of Interest**: Members with conflicts must abstain

### Consensus Building

We strive for consensus before voting. Consensus means:

- All voices heard and considered
- Objections addressed or acknowledged
- No member strongly opposes
- Everyone can live with the decision

**Consensus Process**:

1. Present proposal clearly
2. Gather feedback and concerns
3. Iterate and refine
4. Test consensus ("Any objections?")
5. If objections, address or escalate
6. If no resolution, vote

## Specification Development

### Versioning

WOLS uses [Semantic Versioning](https://semver.org/):

- **MAJOR** (2.0.0): Breaking changes
- **MINOR** (1.1.0): New features, backward-compatible
- **PATCH** (1.0.1): Bug fixes

### Release Process

**Patch Releases** (1.0.x):

1. Maintainer proposes patch
2. Quick review
3. Tag and release
4. Update documentation

**Minor Releases** (1.x.0):

1. Feature proposals collected
2. Community feedback
3. Draft specification
4. Reference implementation
5. Beta period (2 weeks)
6. Steering committee approval
7. Release and announcement

**Major Releases** (x.0.0):

1. RFC for breaking changes
2. Community discussion (30+ days)
3. Steering committee vote
4. Draft specification
5. Multiple reference implementations
6. Beta period (4-8 weeks)
7. Migration guide
8. Final approval and release
9. Coordinated announcement

### Deprecation Policy

**Deprecating Fields**:

1. Mark as deprecated in specification
2. Include in next minor release
3. Support for at least 1 major version
4. Provide migration guide
5. Remove in next major version

**Example Timeline**:

- v1.5.0: Field marked deprecated
- v1.6.0 - v1.x.0: Field still supported
- v2.0.0: Field removed (with migration guide)

## Conflict Resolution

### Process

1. **Direct Discussion**: Parties attempt to resolve directly
2. **Mediation**: Maintainer or neutral party mediates
3. **Escalation**: Bring to steering committee
4. **Committee Decision**: Final binding decision

### Code of Conduct Violations

1. **Report**: Email [conduct@wemush.com](mailto:conduct@wemush.com)
2. **Review**: Committee reviews within 48 hours
3. **Investigation**: Gather facts from all parties
4. **Decision**: Determine violation and response
5. **Action**: Warning, temp ban, or permanent ban
6. **Appeal**: Can appeal to full committee

### Technical Disputes

**When consensus fails**:

1. Document all perspectives
2. Identify technical criteria (performance, compatibility, etc.)
3. Create test cases if possible
4. Steering committee decides based on:
   - Technical merit
   - Alignment with project values
   - Community needs
   - Long-term sustainability

## Transparency

### Public Information

**Always Public**:

- Specification and source code
- Issues and pull requests
- Discussion forums
- Meeting agendas and minutes
- Voting records and results
- Financial information (if applicable)

**Private (Exceptions)**:

- Code of conduct violations (privacy)
- Security vulnerabilities (before fix)
- Personal information
- Confidential business discussions (if necessary)

### Communication Channels

**Public**:

- GitHub Issues: Bug reports, feature requests
- GitHub Discussions: Design, questions, RFCs
- Meetings: Quarterly community calls (recorded)
- Blog: Announcements at wemush.com/blog

**Private**:

- Email: [conduct@wemush.com](mailto:conduct@wemush.com), [security@wemush.com](mailto:security@wemush.com)
- Steering Committee: Internal discussions

## Financial Governance

### Current Model

WOLS is currently funded by:

- WeMush Foundation (primary sponsor)
- Individual contributor time
- In-kind donations

### Future Funding

If the project accepts external funding:

1. Steering committee approval required
2. No funding that compromises independence
3. Transparent reporting of all funding
4. Separate legal entity if needed

### Expenses

Anticipated expenses:

- Domain registration
- Infrastructure (if needed)
- Events and meetups
- Swag for contributors
- Travel for steering committee

**Approval**: Steering committee votes on budget annually

## Amendments

This governance document can be amended:

1. Proposal in Discussions
2. Community input (30 days)
3. Steering committee vote (2/3 majority)
4. Update this document
5. Announce changes

## Joining the Steering Committee

### Why Join?

- Shape the future of cultivation data standards
- Represent your stakeholder group
- Connect with industry leaders
- Contribute to open science and sustainability

### How to Apply

1. Review qualifications and time commitment
2. Participate actively in community (3+ months preferred)
3. Wait for open seat announcement or propose expansion
4. Submit nomination via Discussions
5. Include:
   - Your background and expertise
   - Why you want to join
   - Which stakeholder group you represent
   - Time availability
   - Vision for WOLS

### Time Commitment

- Quarterly meetings (1-2 hours)
- Async communication (~2 hours/month)
- Review proposals and PRs (~2 hours/month)
- Represent WOLS in your community

**Total**: ~5-10 hours/month

## Contact

### Governance Questions

- **Public**: [GitHub Discussions - Governance](https://github.com/wemush/open-standard/discussions/categories/governance)
- **Private**: [governance@wemush.com](mailto:governance@wemush.com)

### Committee Contact

- **Chair | Technology**: Mark Beacom ([mark@wemush.com](mailto:mark@wemush.com))
- **Co-Chair | Science**: Amy Beacom ([amy@wemush.com](mailto:amy@wemush.com))
- **General**: [opensource@wemush.com](mailto:opensource@wemush.com)

## History

- **December 2025**: WOLS project launched
- **December 2025**: Initial governance structure established
- **December 2025**: First steering committee formed (Mark Beacom, Chair)

## Acknowledgments

This governance model is inspired by:

- [Kubernetes](https://github.com/kubernetes/community/blob/master/governance.md)
- [Rust](https://www.rust-lang.org/governance)
- [Node.js](https://github.com/nodejs/node/blob/main/GOVERNANCE.md)
- [Python](https://www.python.org/dev/peps/pep-8016/)

Thank you to these projects for pioneering open-source governance.

---

**Last Updated**: December 18, 2025
**Version**: 1.0.0
