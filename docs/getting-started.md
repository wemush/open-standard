# Getting Started with WOLS

A beginner-friendly guide to understanding and implementing the WeMush Open Labeling Standard (WOLS).

## What is WOLS?

WOLS (WeMush Open Labeling Standard) is an open-source specification for encoding cultivation specimen data in machine-readable QR codes. It enables:

- **Traceability**: Track specimens from culture to harvest
- **Interoperability**: Share data between different systems
- **Transparency**: Prove cultivation claims with verifiable data
- **Research**: Enable reproducible experiments and collaboration

## Quick Start

### For Home Cultivators

**Goal**: Start tracking your mushroom grows with QR code labels

1. **Choose a platform**:
   - Use [WeMush](https://wemush.com) (free tier available)
   - Or build your own using WOLS libraries

2. **Generate your first label**:

   ```typescript
   import { createSpecimen, toQRCodeDataURL } from '@wemush/wols';

   const specimen = createSpecimen({
     species: "Pleurotus ostreatus",
     strain: "Blue Oyster",
     type: "SUBSTRATE",
     stage: "COLONIZATION",
   });
   specimen.created = new Date().toISOString();

   const qrDataUrl = await toQRCodeDataURL(specimen);
   ```

3. **Print the QR code**:
   - Use any label printer (Brother, Dymo, Rollo)
   - Print `qrDataUrl` as an image
   - Stick on your grow bag or container

4. **Scan and track**:
   - Scan with any QR reader app
   - View specimen history
   - Log observations and yields

**Next steps**: [Home Cultivator Example](../examples/home-cultivator.md)

### For Commercial Growers

**Goal**: Implement full farm traceability with WOLS

1. **Assess your needs**:
   - Regulatory compliance requirements
   - Traceability depth (culture → retail)
   - Integration with existing systems

2. **Choose implementation**:
   - Use WeMush Platform (managed solution)
   - Integrate WOLS into your existing software
   - Build custom solution with WOLS libraries

3. **Design label workflow**:
   - What gets labeled? (cultures, spawn, substrates, fruiting)
   - When are labels generated? (inoculation, transfer, harvest)
   - Who scans labels? (workers, inspectors, customers)

4. **Train your team**:
   - Label generation process
   - Scanning and data entry
   - Quality checks and verification

**Next steps**: [Commercial Traceability Example](../examples/commercial-traceability.md)

### For Developers

**Goal**: Build software that generates or reads WOLS labels

1. **Read the specification**:
   - [SPECIFICATION.md](../SPECIFICATION.md)
   - Understand data model and encoding formats

2. **Install library**:

   ```bash
   # JavaScript/TypeScript
   npm install @wemush/wols

   # Python
   pip install wols

   # Container/CLI (arm64/amd64)
   docker pull ghcr.io/wemush/specimen-labels-py:latest
   ```

3. **Generate a label**:

   ```typescript
   import { createSpecimen, serializeSpecimen, toCompactUrl, toQRCodeDataURL } from '@wemush/wols';

   const specimen = createSpecimen({
     species: "Pleurotus ostreatus",
     type: "SUBSTRATE",
     stage: "COLONIZATION",
   });
   specimen.created = "2025-12-18T00:00:00Z"; // createSpecimen() does not set `created`

   console.log(serializeSpecimen(specimen));        // Embedded JSON-LD
   console.log(toCompactUrl(specimen));             // Compact wemush:// URL
   console.log(await toQRCodeDataURL(specimen));    // QR code image (PNG data URL)
   ```

4. **Parse a label**:

   ```python
   from wols import parse_specimen

   specimen = parse_specimen(qr_code_data)  # embedded JSON-LD text
   print(f"Species: {specimen.species}")
   print(f"Stage: {specimen.stage}")
   ```

**Next steps**: [Implementation Guide](./implementation-guide.md)

### For Researchers

**Goal**: Use WOLS for reproducible experiments

1. **Design experiment**:
   - Define variables to track
   - Plan specimen labeling strategy
   - Determine data collection points

2. **Generate labels**:
   - Label all experimental specimens
   - Encode full environmental parameters
   - Include lineage and genetic information

3. **Collect data**:
   - Scan labels during observations
   - Log measurements and outcomes
   - Maintain complete audit trail

4. **Share findings**:
   - Include WOLS labels in publications
   - Enable others to replicate your work
   - Export data for analysis

**Next steps**: [Research Use Cases](../SPECIFICATION.md#3-research-reproducibility)

## Core Concepts

### Specimen Types

WOLS defines five primary specimen types:

| Type | Description | Example |
| ----- | ------------- | --------- |
| **CULTURE** | Pure cultures on agar or in liquid | Agar plate, liquid culture jar |
| **SPAWN** | Colonized grain or substrate for inoculation | Grain spawn, sawdust spawn |
| **SUBSTRATE** | Growing medium being colonized | Fruiting blocks, bags, logs |
| **FRUITING** | Mature specimens producing mushrooms | Fruiting chamber specimens |
| **HARVEST** | Harvested and processed specimens | Fresh mushrooms, dried product |

### Growth Stages

Track specimens through their lifecycle (v1.2.0 includes 7 research-grade stages):

- **INOCULATION**: Initial introduction of spawn/culture to substrate
- **INCUBATION**: Post-inoculation rest period before visible growth
- **COLONIZATION**: Active mycelial growth through substrate
- **PRIMORDIA**: Pin initiation and early fruit body formation
- **FRUITING**: Active fruit body development and maturation
- **SENESCENCE**: Declining productivity, end-of-life phase
- **HARVEST**: Mushrooms harvested and processed

### Encoding Formats

WOLS supports three encoding formats:

**1. Compact** (minimal data, smallest QR):

```bash
wemush://v1/clx1a2b3c4?s=POSTR&st=COLONIZATION&t=1734307200
```

**2. Embedded** (full JSON-LD, most common):

```json
{
  "@context": "https://wemush.com/wols/v1",
  "@type": "Specimen",
  "id": "wemush:clx1a2b3c4",
  "version": "1.2.0",
  "type": "SUBSTRATE",
  "species": "Pleurotus ostreatus",
  "stage": "COLONIZATION"
}
```

**3. Encrypted** (proprietary data):

```bash
wemush://v1/encrypted/clx1a2b3c4?e={payload}&sig={signature}
```

## Common Workflows

### Workflow 1: Culture to Harvest

Track a complete grow cycle:

1. **Create culture** (agar plate):

   ```typescript
   import { createSpecimen } from '@wemush/wols';

   const culture = createSpecimen({
     type: "CULTURE",
     species: "Pleurotus ostreatus",
     strain: {
       name: "Blue Oyster",
       generation: "P",      // original/parental culture
       clonalGeneration: 1,  // first agar plate
     },
     stage: "COLONIZATION",
   });
   ```

2. **Transfer to spawn**:

   ```typescript
   const spawn = createSpecimen({
     type: "SPAWN",
     species: "Pleurotus ostreatus",
     strain: {
       name: "Blue Oyster",
       generation: "P",          // same genetics: grain expansion is not a new generation
       lineage: culture.id,      // link to parent specimen
     },
     stage: "INOCULATION",
   });
   ```

3. **Inoculate substrate**:

   ```typescript
   const substrate = createSpecimen({
     type: "SUBSTRATE",
     species: "Pleurotus ostreatus",
     strain: {
       name: "Blue Oyster",
       generation: "P",
       lineage: spawn.id,
     },
     stage: "INOCULATION",
   });
   ```

4. **Move to fruiting** (the same block advances through stages):

   ```typescript
   const fruiting = {
     ...substrate,
     type: "FRUITING" as const,
     stage: "PRIMORDIA" as const, // PRIMORDIA is a stage, never a type
   };
   ```

   > **Generation vs. lineage**: `strain.generation` is the *filial* (sexual) generation and only changes when a new strain is bred (e.g., spores from a fruit → F1). `strain.clonalGeneration` counts agar-to-agar subcultures. Expanding a culture to grain and substrate keeps the same generation; record ancestry with `strain.lineage`.

5. **Harvest and record yields**

### Workflow 2: Customer Transparency

Enable customers to scan retail packages:

1. **Generate public label** with full history
2. **Print QR on packaging**
3. **Customer scans** at store or home
4. **View complete story**: farm, substrate, dates, sustainability

### Workflow 3: Research Collaboration

Share reproducible experiment data:

1. **Encode all parameters** in WOLS label
2. **Include label in paper** (QR code in methods section)
3. **Other researchers scan** to get exact specifications
4. **Perfect replication** of experiment

## Best Practices

### Label Generation

✅ **Do**:

- Generate unique IDs for each specimen
- Include as much data as possible
- Use ISO 8601 timestamps
- Link parents with genetics field
- Add custom fields for your specific needs

❌ **Don't**:

- Reuse label IDs
- Use relative timestamps ("3 days ago")
- Include personally identifiable information in public labels
- Hardcode sensitive data in compact format

### Data Quality

✅ **Do**:

- Validate data before encoding
- Use scientific names for species
- Record environmental data consistently
- Document any deviations

❌ **Don't**:

- Use common names only
- Omit important metadata
- Mix units (always specify)
- Forget to update stage as specimens progress

### Privacy

✅ **Do**:

- Use encrypted format for proprietary strains
- Keep sensitive data on private servers
- Give customers choice of data visibility
- Follow GDPR/privacy regulations

❌ **Don't**:

- Expose trade secrets in public labels
- Include personal information
- Share location data without consent

## Troubleshooting

### QR Code Won't Scan

**Problem**: QR code is unreadable

**Solutions**:

- Ensure sufficient contrast (black on white)
- Increase QR code size (minimum 1" x 1")
- Check printer resolution (300 DPI minimum)
- Avoid glossy labels (use matte)
- Keep codes clean and undamaged

### Data Too Large

**Problem**: QR code too complex to scan reliably

**Solutions**:

- Use compact encoding format
- Store detailed data on server, reference by ID
- Split into multiple labels if necessary
- Remove unnecessary custom fields

### Validation Errors

**Problem**: Label generation fails validation

**Solutions**:

- Check required fields (species, type, stage, created)
- Use proper ISO 8601 date format
- Validate species name (scientific name recommended)
- Check stage is valid for specimen type

## Next Steps

**Beginners**: Start with a simple label and grow from there
**Commercial**: Review [Implementation Guide](./implementation-guide.md)
**Developers**: Explore [API Documentation](https://github.com/wemush/specimen-labels-js#readme)
**Researchers**: Read [Research Use Cases](../SPECIFICATION.md#3-research-reproducibility)

## Additional Resources

- 📘 [Full Specification](../SPECIFICATION.md)
- 🔧 [Implementation Guide](./implementation-guide.md)
- 🔐 [Security & Privacy](../SPECIFICATION.md#privacy--security)
- 💡 [Use Cases](../SPECIFICATION.md#use-cases)
- ❓ [FAQ](./faq.md)
- 💬 [Community Discussions](https://github.com/wemush/open-standard/discussions)

## Get Help

- **Questions**: [GitHub Discussions](https://github.com/wemush/open-standard/discussions)
- **Bugs**: [GitHub Issues](https://github.com/wemush/open-standard/issues)
- **Email**: [support@wemush.com](mailto:support@wemush.com)

---

**Ready to get started?** Pick your path above and dive in! 🍄
