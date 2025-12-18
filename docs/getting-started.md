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
   import { generateLabel } from '@wemush/specimen-labels';

   const label = await generateLabel({
     species: "Pleurotus ostreatus",
     strain: "Blue Oyster",
     type: "SUBSTRATE",
     stage: "COLONIZATION",
     created: new Date().toISOString(),
   });
   ```

3. **Print the QR code**:
   - Use any label printer (Brother, Dymo, Rollo)
   - Print `label.qrDataUrl` as image
   - Stick on your grow bag or container

4. **Scan and track**:
   - Scan with any QR reader app
   - View specimen history
   - Log observations and yields

**Next steps**: [Home Cultivator Guide](./use-cases/home-cultivator.md)

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

**Next steps**: [Commercial Implementation Guide](./implementation.md)

### For Developers

**Goal**: Build software that generates or reads WOLS labels

1. **Read the specification**:
   - [SPECIFICATION.md](../SPECIFICATION.md)
   - Understand data model and encoding formats

2. **Install library**:

   ```bash
   # JavaScript/TypeScript
   npm install @wemush/specimen-labels

   # Python
   pip install wemush-labels
   ```

3. **Generate a label**:

   ```typescript
   import { generateLabel } from '@wemush/specimen-labels';

   const label = await generateLabel({
     species: "Pleurotus ostreatus",
     type: "SUBSTRATE",
     stage: "COLONIZATION",
     created: "2025-12-18T00:00:00Z",
   });

   console.log(label.json); // Full specimen data
   console.log(label.qrDataUrl); // QR code image
   ```

4. **Parse a label**:

   ```python
   from wemush_labels import parse_label

   specimen = parse_label(qr_code_data)
   print(f"Species: {specimen.species}")
   print(f"Stage: {specimen.stage}")
   ```

**Next steps**: [Developer Guide](./implementation.md)

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

**Next steps**: [Research Use Cases](./use-cases/research-reproducibility.md)

## Core Concepts

### Specimen Types

WOLS defines four primary specimen types:

| Type | Description | Example |
|------|-------------|---------|
| **CULTURE** | Pure cultures on agar or in liquid | Agar plate, liquid culture jar |
| **SPAWN** | Colonized grain or substrate for inoculation | Grain spawn, sawdust spawn |
| **SUBSTRATE** | Growing medium being colonized | Fruiting blocks, bags, logs |
| **FRUITING** | Mature specimens producing mushrooms | Fruiting chamber specimens |

### Growth Stages

Track specimens through their lifecycle:

- **INOCULATION**: Just inoculated
- **COLONIZATION**: Mycelium spreading
- **CONSOLIDATION**: Fully colonized, strengthening
- **PRIMORDIA**: Pins forming
- **FRUITING**: Mushrooms growing
- **HARVEST**: Ready to harvest
- **COMPLETE**: Harvest finished

### Encoding Formats

WOLS supports three encoding formats:

**1. Compact** (minimal data, smallest QR):

```bash
wemush://v1/clx1a2b3c4?s=POSTR&st=COLONIZATION&t=1734307200
```

**2. Embedded** (full JSON, most common):

```json
{
  "v": "1.0.0",
  "id": "clx1a2b3c4",
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
   const culture = generateLabel({
     type: "CULTURE",
     species: "Pleurotus ostreatus",
     strain: "Blue Oyster",
     stage: "COLONIZATION",
   });
   ```

2. **Transfer to spawn**:

   ```typescript
   const spawn = generateLabel({
     type: "SPAWN",
     species: "Pleurotus ostreatus",
     strain: "Blue Oyster",
     stage: "COLONIZATION",
     genetics: {
       parentId: culture.id, // Link to parent
       generation: 1,
     },
   });
   ```

3. **Inoculate substrate**:

   ```typescript
   const substrate = generateLabel({
     type: "SUBSTRATE",
     stage: "INOCULATION",
     genetics: {
       parentId: spawn.id,
       generation: 2,
     },
   });
   ```

4. **Move to fruiting**:

   ```typescript
   const fruiting = generateLabel({
     type: "FRUITING",
     stage: "PRIMORDIA",
     genetics: {
       parentId: substrate.id,
       generation: 3,
     },
   });
   ```

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
**Commercial**: Review [Implementation Guide](./implementation.md)
**Developers**: Explore [API Documentation](./api/javascript.md)
**Researchers**: Read [Research Use Cases](./use-cases/research-reproducibility.md)

## Additional Resources

- 📘 [Full Specification](../SPECIFICATION.md)
- 🔧 [Implementation Guide](./implementation.md)
- 🔐 [Security & Privacy](./security.md)
- 💡 [Use Cases](./use-cases.md)
- ❓ [FAQ](./faq.md)
- 💬 [Community Discussions](https://github.com/wemush/open-standard/discussions)

## Get Help

- **Questions**: [GitHub Discussions](https://github.com/wemush/open-standard/discussions)
- **Bugs**: [GitHub Issues](https://github.com/wemush/open-standard/issues)
- **Email**: [support@wemush.com](mailto:support@wemush.com)

---

**Ready to get started?** Pick your path above and dive in! 🍄
