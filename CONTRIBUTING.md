# Contributing to WOLS

Thank you for your interest in contributing to the WeMush Open Labeling Standard (WOLS)! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Contribution Types](#contribution-types)
- [Development Process](#development-process)
- [Specification Changes](#specification-changes)
- [Code Contributions](#code-contributions)
- [Documentation Contributions](#documentation-contributions)
- [Testing Requirements](#testing-requirements)
- [Style Guidelines](#style-guidelines)
- [Community Guidelines](#community-guidelines)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you are expected to uphold this code. Key principles:

- **Be respectful**: Treat all contributors with respect, regardless of experience level
- **Be collaborative**: Work together to improve the standard
- **Be inclusive**: Welcome diverse perspectives from growers, developers, researchers, and industry
- **Be constructive**: Provide helpful feedback and accept criticism gracefully
- **Be scientific**: Base decisions on data, research, and real-world use cases

## How to Contribute

### 1. Start a Discussion

For major changes or new features, start with a [GitHub Discussion](https://github.com/wemush/open-standard/discussions):

- **Use Cases**: Share how you're using WOLS or want to use it
- **Ideas**: Propose new features or improvements
- **Questions**: Ask about implementation or design decisions
- **Show & Tell**: Share your WOLS integration or project

### 2. Open an Issue

For bugs, documentation errors, or well-defined enhancements:

- Search existing issues first to avoid duplicates
- Use issue templates when available
- Provide clear, reproducible examples
- Include relevant context (your use case, environment, etc.)

### 3. Submit a Pull Request

For code, documentation, or specification changes:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Test thoroughly
5. Commit with clear messages
6. Push to your fork
7. Open a pull request with detailed description

## Contribution Types

### 🐛 Bug Fixes

**What**: Fix errors in specification, documentation, or reference implementations

**Examples**:

- Typos or grammatical errors
- Broken links
- Incorrect code examples
- Schema validation errors
- Encoding/decoding bugs

**Process**:

1. Open issue describing the bug
2. Submit PR with fix
3. Include tests proving the fix works

### ✨ Enhancements

**What**: Improve existing features without changing core specification

**Examples**:

- Better documentation examples
- Additional validation rules
- Performance improvements
- Error message clarity
- Developer experience improvements

**Process**:

1. Open discussion or issue
2. Get community feedback
3. Submit PR with implementation
4. Update relevant documentation

### 🎉 New Features

**What**: Propose additions to the WOLS specification

**Examples**:

- New optional fields
- Additional encoding formats
- New specimen types or stages
- Extended metadata schemas
- Integration specifications (IoT, blockchain, etc.)

**Process**:

1. Open GitHub Discussion with RFC (Request for Comments)
2. Community discussion period (minimum 14 days)
3. Steering committee review
4. Draft specification change
5. Implementation in reference libraries
6. Final review and merge

**Requirements**:

- Must maintain backward compatibility (or justify breaking change)
- Must not require proprietary technology
- Must serve real use cases from multiple organizations
- Must include test cases and examples
- Must update all affected documentation

### 📚 Documentation

**What**: Write tutorials, guides, translations, or improve existing docs

**Examples**:

- Getting started tutorials
- Integration guides for specific platforms
- API documentation
- Use case examples
- Translations to other languages
- Video tutorials or diagrams

**Process**:

1. Open issue describing what you'll document
2. Submit PR with documentation
3. Request review from someone familiar with the topic

**Style Guidelines**:

- Use clear, concise language
- Include code examples that work
- Test all commands and code snippets
- Use proper Markdown formatting
- Add diagrams for complex concepts

### 💬 Community Discussion

**What**: Participate in design discussions, use case sharing, or technical debates

**Examples**:

- Share your cultivation operation's needs
- Discuss privacy vs. transparency tradeoffs
- Debate field naming conventions
- Propose governance changes
- Academic validation of approaches

**Process**:

- Join [GitHub Discussions](https://github.com/wemush/open-standard/discussions)
- Be respectful and constructive
- Provide evidence or real-world examples
- Listen to diverse perspectives

## Development Process

### Specification Changes

**Small Changes** (typos, clarifications, examples):

1. Fork repo
2. Make changes
3. Submit PR
4. 1-2 reviewers approve
5. Merge

**Medium Changes** (new optional fields, minor additions):

1. Open GitHub Discussion
2. Community feedback (7 days)
3. Draft PR with changes
4. Steering committee review
5. 2-3 reviewers approve
6. Merge

**Large Changes** (new encoding formats, breaking changes):

1. RFC (Request for Comments) in Discussions
2. Community feedback (14+ days)
3. Steering committee deliberation
4. Draft specification PR
5. Reference implementation PR
6. Public comment period (7 days)
7. Final steering committee vote
8. Merge and version bump

### Versioning

WOLS follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (2.0.0): Breaking changes, incompatible API changes
- **MINOR** (1.1.0): New features, backward-compatible additions
- **PATCH** (1.0.1): Bug fixes, clarifications, documentation

### Backward Compatibility

**Must maintain backward compatibility** unless justified by extraordinary circumstances:

- Old labels must still decode in new versions
- Deprecated fields must be marked and supported for at least 1 major version
- Breaking changes require RFC and steering committee approval
- Migration guides must be provided

## Code Contributions

### Reference Implementations

We maintain official libraries in multiple languages. Each must:

1. **Follow language conventions**: Use idiomatic code for that language
2. **Pass all tests**: 100% test coverage for core functionality
3. **Include examples**: Real-world usage examples in README
4. **Document APIs**: Clear inline documentation and generated API docs
5. **Handle errors**: Graceful error handling with helpful messages
6. **Validate data**: Strict validation of WOLS fields
7. **Support all encodings**: Compact, embedded, and encrypted formats

### Code Style

**JavaScript/TypeScript**:

- Use ESLint with Airbnb config
- Prettier for formatting
- JSDoc comments for all public APIs
- TypeScript strict mode enabled

**Python**:

- PEP 8 style guide
- Black for formatting
- Type hints for all functions
- Docstrings in Google style

**Go**:

- `gofmt` for formatting
- `golint` for linting
- GoDoc comments for public APIs

**Rust**:

- `rustfmt` for formatting
- `clippy` for linting
- Rustdoc comments for public APIs

### Testing Requirements

**All code contributions must include tests:**

1. **Unit tests**: Test individual functions
2. **Integration tests**: Test encoding/decoding round trips
3. **Example tests**: Ensure examples in docs actually work
4. **Edge cases**: Test boundary conditions and error cases

**Test Coverage**:

- Minimum 90% code coverage
- 100% coverage for core encoding/decoding logic
- All spec examples must be tested

**Sample Test Structure**:

```typescript
describe('generateLabel', () => {
  it('should create valid minimal label', () => {
    const label = generateLabel({
      species: 'Pleurotus ostreatus',
      type: 'SUBSTRATE',
      stage: 'COLONIZATION',
      created: '2025-12-18T00:00:00Z',
    });

    expect(label).toBeDefined();
    expect(label.version).toBe('1.0.0');
    expect(validateLabel(label)).toBe(true);
  });

  it('should handle all specimen types', () => {
    const types = ['CULTURE', 'SPAWN', 'SUBSTRATE', 'FRUITING'];
    types.forEach(type => {
      const label = generateLabel({ /* ... */ type });
      expect(label.type).toBe(type);
    });
  });

  it('should reject invalid data', () => {
    expect(() => generateLabel({ /* invalid */ }))
      .toThrow('Invalid species');
  });
});
```

## Documentation Contributions

### Documentation Standards

1. **Accuracy**: All information must be technically accurate
2. **Completeness**: Cover all relevant scenarios
3. **Examples**: Include working code examples
4. **Clarity**: Use simple, clear language
5. **Structure**: Use headings, lists, and formatting effectively

### Documentation Sections

**Getting Started**: For beginners, assumes no prior knowledge
**Implementation Guide**: Technical details for integrators
**API Reference**: Complete API documentation with all parameters
**Use Cases**: Real-world scenarios with full examples
**FAQ**: Common questions with clear answers

### Writing Style

- Use active voice: "The library validates" not "The data is validated"
- Use present tense: "The function returns" not "The function will return"
- Use examples: Show, don't just tell
- Use consistent terminology: Refer to the [Glossary](./docs/glossary.md)
- Use headers: Break content into scannable sections
- Use lists: Bulleted or numbered lists for multiple items
- Use code blocks: Format code properly with syntax highlighting

### Markdown Formatting

```markdown
# Main Title (H1) - One per document

## Section (H2)

### Subsection (H3)

**Bold** for emphasis
*Italic* for terminology
`code` for inline code

- Bulleted list item
- Another item

1. Numbered list
2. Next item

[Link text](URL)

![Image alt text](image-url)

> Blockquote for important notes

\`\`\`typescript
// Code block with language
const example = 'syntax highlighting';
\`\`\`
```

## Style Guidelines

### Field Naming

- Use camelCase for JSON fields: `batchId`, `createdAt`
- Use SCREAMING_SNAKE_CASE for enums: `COLONIZATION`, `FRUITING`
- Use lowercase for URL parameters: `version`, `species`
- Be consistent across all encodings

### Data Types

- **Dates**: ISO 8601 format (`2025-12-18T10:30:00Z`)
- **IDs**: Use ULIDs or UUIDs (no sequential integers for public IDs)
- **Decimals**: Use strings for precision (`"23.5"` not `23.5`)
- **Optional fields**: Always nullable, never empty strings
- **Arrays**: Always use arrays, never comma-separated strings

### Error Messages

- Be specific: "Species must be scientific name" not "Invalid species"
- Be helpful: "Expected ISO 8601 date like '2025-12-18T00:00:00Z'"
- Be consistent: Use same message for same error across languages
- Be actionable: Tell users how to fix the problem

### Privacy & Security

**Never include in examples**:

- Real API keys or tokens
- Real user data without consent
- Proprietary strain information
- Location data that could identify individuals

**Always**:

- Use example.com for domains
- Use placeholder names like "Sample Strain"
- Use fictional data in examples
- Mark encrypted examples clearly

## Community Guidelines

### Respectful Communication

✅ **Do**:

- Welcome newcomers warmly
- Assume good intentions
- Ask clarifying questions
- Provide constructive feedback
- Share your use case and context
- Credit others' contributions
- Admit when you don't know something

❌ **Don't**:

- Dismiss ideas without explanation
- Use condescending language
- Make personal attacks
- Demand features without contributing
- Spam or self-promote excessively
- Share others' private information

### Crediting Contributors

- All merged PRs add contributor to AUTHORS file
- Significant contributions recognized in release notes
- Major features credit original proposer
- Documentation improvements credited

### Decision Making

**Consensus-seeking**: We strive for consensus but recognize not everyone will always agree.

**When consensus isn't possible**:

1. Community discussion to understand all perspectives
2. Steering committee deliberates
3. Vote if necessary (simple majority)
4. Document decision rationale

**Disagreements**:

- Focus on technical merits, not personalities
- Provide evidence or use cases
- Acknowledge tradeoffs
- Accept final decisions gracefully

## Legal

### Contributor License Agreement

By contributing, you agree:

1. **You own your contribution** or have permission to submit it
2. **You grant CC BY 4.0 license** for specification and documentation contributions
3. **You grant Apache 2.0 license** for code example contributions
4. **Your contribution doesn't violate** any copyrights or patents
5. **You understand contributions are public** and permanent

### Copyright Notice

Add this to new specification/documentation files:

```text
Copyright (c) 2025 WeMush Foundation Contributors
Licensed under CC BY 4.0 - https://creativecommons.org/licenses/by/4.0/
```

Code examples may additionally note:

```text
Code examples licensed under Apache 2.0 - https://www.apache.org/licenses/LICENSE-2.0
```

### Third-Party Code

If including third-party code:

- Must be compatible with Apache 2.0 or CC BY 4.0
- Must include original license and copyright notice
- Must be clearly marked as third-party
- Prefer permissive licenses (Apache 2.0, MIT, BSD)

## Getting Help

### Where to Ask

- **General questions**: [GitHub Discussions - Q&A](https://github.com/wemush/open-standard/discussions/categories/q-a)
- **Bug reports**: [GitHub Issues](https://github.com/wemush/open-standard/issues)
- **Security issues**: Email [security@wemush.com](mailto:security@wemush.com) (not public)
- **Private matters**: Email [opensource@wemush.com](mailto:opensource@wemush.com)

### Response Times

- **Issues**: Within 1-2 business days
- **PRs**: Initial review within 3-5 business days
- **Discussions**: Community responds as available
- **Security reports**: Within 24 hours

### Maintainer Availability

Maintainers are primarily in US timezones (EST/PST). We review contributions during business hours but respond to security issues urgently.

## Recognition

### Hall of Fame

Outstanding contributors recognized:

- Featured on wemush.com/contributors
- Listed in AUTHORS file
- Mentioned in release announcements
- Invited to steering committee consideration

### Types of Recognition

🏆 **Founding Contributor**: First 10 merged PRs
🌟 **Core Contributor**: 25+ merged PRs
💎 **Specification Architect**: Major spec contributions
📚 **Documentation Hero**: Outstanding documentation work
🔬 **Research Contributor**: Academic validation or papers
🏭 **Industry Pioneer**: First organization to adopt WOLS

## Thank You

Every contribution, big or small, helps make WOLS better for the entire cultivation community. Whether you're fixing a typo, proposing a new feature, or integrating WOLS into your operation, we appreciate your effort.

**Together we're building the future of transparent, traceable cultivation.** 🍄

---

**Questions?** Open a [discussion](https://github.com/wemush/open-standard/discussions) or email [opensource@wemush.com](mailto:opensource@wemush.com)
