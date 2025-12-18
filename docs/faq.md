# FAQ - Frequently Asked Questions

Common questions about the WeMush Open Labeling Standard (WOLS).

## General Questions

### What is WOLS?

WOLS (WeMush Open Labeling Standard) is an open-source specification for encoding cultivation specimen data in machine-readable QR codes. It enables traceability, interoperability, and transparency in agriculture and research.

### Is WOLS free to use?

Yes! WOLS is completely free under Creative Commons Attribution 4.0 (CC BY 4.0) for the specification and documentation. Code examples in the docs can also be used under Apache 2.0. Reference implementations (in separate repositories) are licensed under Apache 2.0. There are no licensing fees, ever.

### Who created WOLS?

WOLS was created by Mark Beacom and is supported by the WeMush Foundation, Farmer Veteran Coalition, and the Transatlantic Sustainability Transition Initiative.

### Can I use WOLS commercially?

Absolutely! WOLS is designed for commercial use. Many farms and companies use it for production tracking and customer transparency.

### Is WOLS only for mushrooms?

No. While WOLS was designed for mushroom cultivation, it works for any biological specimen tracking including cannabis, hemp, plants, seeds, cultures, and more.

## Technical Questions

### What data can WOLS encode?

WOLS can encode:

- Species and strain information
- Growth stage and lifecycle
- Environmental conditions (temperature, humidity, CO₂)
- Substrate composition
- Harvest yields
- Parent-child lineage
- Custom fields for your specific needs
- Cryptographic signatures for verification

### What QR code format does WOLS use?

WOLS supports standard QR codes that can be read by any QR scanner. The data inside follows the WOLS specification with three encoding options: compact, embedded (JSON), or encrypted.

### How much data fits in a QR code?

- **Compact format**: ~200 bytes (basic info)
- **Embedded format**: ~1-2 KB (full JSON)
- **For larger datasets**: Store on server, encode reference ID

### Can I add custom fields?

Yes! Use the `custom` namespace to add organization-specific fields:

```json
{
  "species": "Pleurotus ostreatus",
  "custom": {
    "yourCompany": {
      "customerReference": "ABC123",
      "lotNumber": "2025-001"
    }
  }
}
```

### What programming languages are supported?

Official libraries:

- JavaScript/TypeScript (planned)
- Python (planned)
- Go (planned)
- Rust (planned)

You can also implement WOLS in any language by following the specification.

### Do I need special printers?

No. Any printer that can print QR codes works:

- Brother label printers
- Dymo label printers
- Rollo thermal printers
- Regular inkjet/laser printers with sticker paper

## Privacy & Security

### Is my data private?

You control your data privacy:

- **Public labels**: Encode all data in QR code (transparent)
- **Private labels**: Store sensitive data on your server, encode only ID
- **Encrypted labels**: Use encryption for proprietary information

### How does encryption work?

WOLS supports encrypted payloads where sensitive data is encrypted before encoding. Only parties with the decryption key can read the full data.

### Can others steal my strain information?

Not if you use encryption or private labels. Public labels are intentionally transparent for traceability. Use encrypted format for proprietary genetics.

### Who owns the data in WOLS labels?

You do. WOLS is just a data format specification. You own all specimen data you generate.

### Is WOLS compliant with GDPR/privacy laws?

WOLS itself is data-agnostic. It's your responsibility to ensure compliance:

- Don't encode personal data in public labels
- Use encryption for sensitive information
- Follow your local privacy regulations
- Provide users control over their data

## Implementation Questions

### How do I get started?

1. Read the [Getting Started Guide](./getting-started.md)
2. Choose your implementation path (use WeMush, build your own, integrate)
3. Generate your first label
4. Print and test

### Do I need the WeMush platform?

No. WeMush is one implementation of WOLS, but WOLS is an open standard. You can:

- Build your own software
- Integrate into existing systems
- Use any WOLS-compatible platform
- Generate labels manually

### Can I integrate WOLS with my existing software?

Yes! Use the WOLS libraries to generate/parse labels within your current system.

### What if I need features not in WOLS?

1. Use custom fields for organization-specific data
2. Propose additions via GitHub Discussions
3. Submit RFC for specification changes

### How do I migrate from my current system?

1. Map your data model to WOLS fields
2. Generate WOLS labels for existing specimens
3. Run both systems in parallel during transition
4. Validate data consistency
5. Complete cutover

## Adoption & Community

### Who is using WOLS?

See [ADOPTION.md](../ADOPTION.md) for current adopters. Early commercial adopter: Mush Ohio.

### Can I build a competing platform?

Yes! WOLS is open source specifically to enable competition. Build the best implementation and let users choose.

### How do I contribute?

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines. Contributions welcome:

- Code improvements
- Documentation
- Use cases and feedback
- Bug reports
- Feature proposals

### How are decisions made?

See [GOVERNANCE.md](../GOVERNANCE.md). Summary:

- Community discussion
- Steering committee review
- Consensus-seeking approach
- Transparent process

### Can I join the steering committee?

Yes! We're looking for representatives from:

- Commercial industry
- Academic research
- Equipment manufacturing
- Open source community

Apply via GitHub Discussions when seats open.

## Comparison Questions

### How is WOLS different from GS1 barcodes?

| Feature | WOLS | GS1 |
|---------|------|-----|
| **License** | Free, open source | Membership fees required |
| **Focus** | Agriculture/research | General retail |
| **Data** | Cultivation-specific | Generic product info |
| **Flexibility** | Extensible custom fields | Rigid structure |
| **Privacy** | Encryption support | Public by design |

WOLS can complement GS1 for retail integration.

### How is WOLS different from blockchain tracking?

WOLS is a **data format**, not a storage/verification system:

- Can be used **with or without** blockchain
- Lighter weight (no blockchain fees)
- Faster (no consensus delays)
- More flexible (works offline)
- Can integrate with blockchain for verification if desired

### Can WOLS work with blockchain?

Yes! WOLS v2.0 will include blockchain integration patterns. You can:

- Store WOLS labels on IPFS
- Record label hashes on blockchain
- Use NFTs for specimen ownership
- Verify authenticity via smart contracts

### How does WOLS compare to spreadsheets?

| Aspect | WOLS | Spreadsheets |
|--------|------|--------------|
| **Traceability** | Built-in lineage | Manual tracking |
| **Scanning** | QR codes | N/A |
| **Interoperability** | Standard format | No standard |
| **Verification** | Cryptographic | None |
| **Customer access** | Scannable labels | Not accessible |

WOLS is designed to replace paper/spreadsheet tracking.

## Business Questions

### What's the relationship between WOLS and WeMush?

**WOLS** = Open standard (free forever)
**WeMush** = Proprietary platform implementing WOLS

Think: HTTP (standard) vs Google Chrome (one implementation)

### Why is WOLS open but WeMush proprietary?

**Open standards drive adoption.** Everyone can build on WOLS.
**Proprietary platforms drive sustainability.** WeMush funds continued development.

This model ensures long-term success for both.

### Can I sell products/services using WOLS?

Yes! You can:

- Build commercial software using WOLS
- Offer consulting services
- Sell label printing services
- Create competing platforms
- Charge for your implementations

### Do I have to credit WOLS?

For the specification: Yes (CC BY 4.0 requires attribution)
For code libraries: No (Apache 2.0, but appreciated)

Example attribution: "Powered by WOLS" or link to github.com/wemush/open-standard

### What if WeMush goes out of business?

The WOLS standard lives on:

- Specification is permanently public
- Other platforms can continue support
- Your data is exportable (no lock-in)
- Community can maintain libraries

That's the power of open standards!

## Support Questions

### Where do I get help?

- **Questions**: [GitHub Discussions](https://github.com/wemush/open-standard/discussions)
- **Bugs**: [GitHub Issues](https://github.com/wemush/open-standard/issues)
- **Email**: [support@wemush.com](mailto:support@wemush.com)
- **Documentation**: [docs/](.)

### How fast will you respond?

Community support:

- **Issues**: 1-2 business days
- **PRs**: 3-5 business days
- **Discussions**: Community responds as available
- **Security**: Within 24 hours

### Is there paid support available?

Not yet. WOLS is community-supported. WeMush Platform offers paid support for platform-specific issues.

### Can I hire someone to implement WOLS?

Yes! Options:

- Post in GitHub Discussions
- Email [opensource@wemush.com](mailto:opensource@wemush.com) for referrals
- Hire developers familiar with the stack
- WeMush may offer consulting in future

## Future Plans

### What's on the roadmap?

See [ROADMAP.md](../ROADMAP.md) for details:

- **v1.1.0** (Q1 2026): IoT integration, developer tools
- **v1.2.0** (Q2 2026): Analytics, supply chain, translations
- **v2.0.0** (Q3-Q4 2026): Blockchain, standards alignment

### Can I request features?

Yes! [Start a discussion](https://github.com/wemush/open-standard/discussions/categories/ideas) with:

- Your use case
- Why it's needed
- How many others would benefit
- Proposed implementation (optional)

### Will there be breaking changes?

Not in v1.x releases. Breaking changes only in major versions (v2.0, v3.0) with:

- Migration guides
- Deprecation warnings
- Backward compatibility period

### How long will WOLS be maintained?

Long-term commitment. As long as there's community interest, WOLS will be maintained and improved.

## Still Have Questions?

**Ask the community**: [GitHub Discussions](https://github.com/wemush/open-standard/discussions/categories/q-a)

**Contact us**: [support@wemush.com](mailto:support@wemush.com)

**Read more**:

- [Getting Started](./getting-started.md)
- [Full Specification](../SPECIFICATION.md)
- [Implementation Guide](./implementation.md)
- [Use Cases](./use-cases.md)

---

**Can't find your answer?** [Ask a new question!](https://github.com/wemush/open-standard/discussions/new?category=q-a)
