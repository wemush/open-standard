# Commercial Farm Traceability Example

How a commercial mushroom farm uses WOLS for complete supply chain traceability and regulatory compliance.

## The Problem

**Mush Ohio**, a commercial oyster mushroom farm, faces challenges:

- **Regulatory compliance**: Food safety audits require complete tracking
- **Customer transparency**: Restaurants want verified local sourcing
- **Batch recalls**: Need to trace contaminated batches quickly
- **Quality control**: Identify problems in production process
- **Scalability**: Growing from 100 to 1000 lbs/week

**Without proper tracking**: Risk of failed audits, customer distrust, inefficient recalls, slow problem resolution

## The Solution: WOLS Implementation

Mush Ohio implements WOLS across their entire operation.

### System Architecture

```bash
[Culture Library] → [Spawn Production] → [Growing Room] → [Harvest] → [Distribution]
     ↓                    ↓                   ↓              ↓            ↓
  QR Label           QR Label            QR Label       QR Label     Customer QR
```

Every stage gets a WOLS label with complete traceability.

### Implementation Details

#### 1. Master Culture Library

**Setup**:

- Each strain gets permanent WOLS label
- Stored in database as "master genetics"
- Sub-cultured monthly with child labels

**Example - Master Culture**:

```typescript
import { createSpecimen, toQRCodeDataURL } from '@wemush/wols';

// createSpecimen() has no `created` input, so set the timestamp on the result.
const masterCulture = {
  ...createSpecimen({
    species: "Pleurotus ostreatus",
    strain: {
      name: "MO-Blue-001", // Internal strain ID
      source: "agar", // How the culture is maintained ("spore", "tissue", "agar", "liquid")
    },
    type: "CULTURE",
    stage: "COLONIZATION",
    organization: "mush-ohio",
    custom: {
      mushOhio: {
        internalId: "MC-001",
        supplier: "Commercial supplier",
        location: "Culture library - Rack A1",
        subCultureSchedule: "Monthly",
        notes: "Consistent performer, high yield"
      }
    }
  }),
  created: "2025-01-01T00:00:00Z",
};

const qrDataUrl = await toQRCodeDataURL(masterCulture, { size: 300, errorCorrection: 'M' });
```

**Label placed on**: Culture tube in -80°C freezer

#### 2. Spawn Production

**Process**:

- Pull master culture for spawn run
- Generate batch label with parent linkage
- Sterilize grain, inoculate, colonize
- Label each spawn bag in batch

**Example - Spawn Batch**:

> **Note**: WOLS 1.2 defines the `SubstrateFormula` and `EnvironmentalData` structures but not yet where they attach on a Specimen, so this example carries them under `custom.mushOhio`. A standard placement is proposed for 1.3 in [ROADMAP.md](../ROADMAP.md).

```typescript
const spawnBatch = {
  ...createSpecimen({
    species: "Pleurotus ostreatus",
    type: "SPAWN",
    stage: "INOCULATION",
    batch: "SB-2025-048", // Spawn Batch number
    organization: "mush-ohio",
    strain: {
      name: "MO-Blue-001",
      // Grain spawn is an expansion of the same genetics, so the filial
      // generation does not change. Ancestry is recorded with lineage.
      lineage: masterCulture.id,
    },
    custom: {
      mushOhio: {
        batchSize: "50 bags",
        operatorId: "OP-103",
        room: "Spawn production room",
        expectedReady: "2025-12-15",
        qualityCheck: {
          sterileTest: "PASS",
          inspector: "QC-Manager"
        },
        substrate: {
          components: [
            { ingredient: "Organic rye grain", percentage: 98 },
            { ingredient: "Gypsum", percentage: 2 }
          ],
          hydration: 50,
          sterilization: {
            method: "autoclave",
            temperature: 121, // 15 PSI
            unit: "C",
            duration: 90,
            timestamp: "2025-12-01T06:00:00Z"
          }
        },
        environment: {
          temperature: { value: 75, unit: "F", timestamp: "2025-12-01T08:00:00Z" },
          humidity: { value: 60, timestamp: "2025-12-01T08:00:00Z" }
        }
      }
    }
  }),
  created: "2025-12-01T08:00:00Z",
};
```

**Label placed on**: Master spawn bag (representative of batch)

#### 3. Substrate/Fruiting Blocks

**Process**:

- Create substrate batches (5 lb blocks)
- Inoculate with labeled spawn
- Each block gets individual label
- Track through fruiting

**Example - Individual Block**:

```typescript
const block = {
  ...createSpecimen({
    species: "Pleurotus ostreatus",
    type: "SUBSTRATE",
    stage: "INOCULATION",
    batch: "FB-2025-321", // Fruiting Block batch
    organization: "mush-ohio",
    strain: {
      name: "MO-Blue-001",
      lineage: spawnBatch.id,
    },
    custom: {
      mushOhio: {
        blockNumber: "FB-2025-321-087", // Individual block in batch
        weight: "5.0 lbs",
        room: "Growing room 2",
        rack: "R4-S3",
        expectedFruit: "2026-01-05",
        operatorId: "OP-107",
        inoculationRate: 10, // 10% spawn by weight
        substrate: {
          components: [
            { ingredient: "Hardwood sawdust (oak)", percentage: 68 },
            { ingredient: "Wheat bran", percentage: 27 },
            { ingredient: "Gypsum", percentage: 5 }
          ],
          hydration: 62,
          sterilization: {
            method: "autoclave",
            temperature: 121, // 15 PSI
            unit: "C",
            duration: 150,
            timestamp: "2025-12-15T04:00:00Z"
          }
        }
      }
    }
  }),
  created: "2025-12-15T10:00:00Z",
};
```

**Label placed on**: Each 5 lb fruiting block

#### 4. Harvest Tracking

**Process**:

- Scan block label at harvest
- Record yield, quality, date
- Update the block's record (same ID, so the printed label keeps working)
- Generate harvest batch ID

**Example - Harvest Update**:

```typescript
// The library has no update call: a stage change is a new value of the
// specimen, saved by the farm's own system (or a platform such as WeMush).
const harvestedBlock = {
  ...block,
  stage: "HARVEST" as const,
  custom: {
    mushOhio: {
      ...(block.custom?.mushOhio as object),
      // WOLS 1.2 has no standard yield field, so yields live in custom too.
      yields: [
        {
          date: "2026-01-12T06:00:00Z",
          weight: { value: 1.8, unit: "lbs" },
          quality: "PREMIUM",
          flushNumber: 1
        }
      ],
      harvestBatch: "HB-2026-008",
      harvester: "OP-112",
      packagingDate: "2026-01-12T08:00:00Z",
      destinationCustomer: "Restaurant-Alpine-Bistro",
      deliveryDate: "2026-01-12T14:00:00Z"
    }
  }
};
await farmDb.save(harvestedBlock); // your own persistence layer
```

#### 5. Customer-Facing Labels

**Process**:

- Generate public label for retail packages
- Link to full traceability data
- Customer scans at restaurant or home

**Example - Retail Package Label**:

```typescript
const retailLabel = {
  ...createSpecimen({
    species: "Pleurotus ostreatus",
    type: "HARVEST", // Harvested mushrooms (FRESH is an accepted alias)
    stage: "HARVEST",
    batch: "HB-2026-008",
    organization: "mush-ohio",
    strain: {
      name: "MO-Blue-001",
      lineage: block.id, // Links to specific block
    },
    custom: {
      mushOhio: {
        packageId: "PKG-2026-008-12",
        packageWeight: "0.5 lbs",
        harvestDate: "2026-01-12T06:00:00Z",
        certifications: ["USDA Organic", "Local (Ohio)"],
        price: "$8.00",
        bestBy: "2026-01-19",
        customerMessage: "Grown locally in Columbus, OH. Farm-to-table in 24 hours!",
        farmInfo: {
          name: "Mush Ohio",
          location: "Columbus, OH",
          website: "https://mushohio.com",
          sustainabilityScore: 95
        }
      }
    }
  }),
  created: "2026-01-12T08:00:00Z",
};

const packageQr = await toQRCodeDataURL(retailLabel, { size: 300, errorCorrection: 'M' });
```

**Label placed on**: Retail package (QR code printed on box)

**Customer scans and sees**:

- Farm name and location
- Harvest date (today!)
- Growing method (organic, sustainable)
- Complete history (if they want details)
- Farm story and values

## Benefits Achieved

### 1. Regulatory Compliance

**Before WOLS**:

- Manual spreadsheet tracking
- 2-3 hours to compile audit reports
- Missing data gaps
- Failed mock audits

**With WOLS**:

- Instant digital traceability
- 15 minutes to generate complete audit trail
- Zero data gaps
- **Passed FDA audit** on first try

**Example audit query**: "Show all blocks from spawn batch SB-2025-048"

```typescript
// Query against the farm's own specimen store (WOLS defines the data,
// not the database). Children point at their parent via strain.lineage.
const blocks = await farmDb.query({
  organization: "mush-ohio",
  "strain.lineage": spawnBatch.id
});
// Returns all 50 blocks with complete history
```

### 2. Batch Recall Efficiency

**Scenario**: Contamination detected in one harvest batch

**Before WOLS**:

- 4-6 hours to identify affected blocks
- Manual checking of paper logs
- Incomplete recall scope

**With WOLS**:

- 5 minutes to identify all affected products
- Automatic tracing forward and backward
- Complete recall scope

**Example recall**:

```typescript
// Find all products from contaminated batch
const affected = await farmDb.query({
  organization: "mush-ohio",
  "custom.mushOhio.harvestBatch": "HB-2026-008" // Contaminated batch
});

// Also trace backwards to source
const sourceBlocks = await farmDb.query({
  id: { $in: affected.map(p => p.strain?.lineage) }
});

// Alert all customers automatically
affected.forEach(product => {
  notifyCustomer(product.custom.mushOhio.destinationCustomer);
});
```

**Result**: Complete recall in 1 hour vs 1-2 days

### 3. Customer Transparency & Trust

**Before WOLS**:

- "We're local and sustainable" (trust us)
- No way to verify claims
- Generic product

**With WOLS**:

- **Provable transparency**: Customers scan and verify
- **Farm-to-table proof**: Harvest date visible
- **Premium pricing**: $16/lb vs $12/lb (33% increase)
- **Restaurant partnerships**: Chefs love traceability

**Customer feedback**:
> "We can show diners exactly where their mushrooms came from this morning. That's powerful storytelling." - Alpine Bistro Chef

### 4. Quality Control

**Use case**: Identifying optimal growing conditions

**Analysis**:

```typescript
// Query all harvests, group by conditions
const harvests = await farmDb.query({
  organization: "mush-ohio",
  type: "SUBSTRATE",
  stage: "HARVEST"
});

const analysis = harvests.reduce((acc, block) => {
  const data = block.custom.mushOhio;
  const temp = data.environment.temperature.value;
  const yieldLbs = data.yields[0].weight.value;
  acc[temp] = acc[temp] || [];
  acc[temp].push(yieldLbs);
  return acc;
}, {});

// Result: 68°F optimal (2.1 lb avg vs 1.7 lb at 72°F)
```

**Action**: Adjust all growing rooms to 68°F

**Result**: 24% yield increase across farm

### 5. Operational Efficiency

**Metrics**:

- **Time to label**: 30 seconds per batch
- **Time to update**: 15 seconds per stage change
- **Data entry reduction**: 70% (automated scanning)
- **Inventory accuracy**: 99.8% (was 92%)
- **Training time**: 1 hour for new workers (was 1 week)

**ROI**:

- **Investment**: $2,000 (printers, software, setup)
- **Labor savings**: $10,000/year
- **Premium pricing**: $20,000/year additional revenue
- **Avoided recall cost**: $50,000+ (estimated)
- **Payback**: 1 month

## Technical Implementation

### Infrastructure

```typescript
import {
  createSpecimen,
  parseSpecimen,
  parseCompactUrl,
  toQRCodeDataURL,
  type Specimen,
} from '@wemush/wols';

// Farm management system (database and printer are the farm's own services)
class FarmManagementSystem {
  async createCultureBatch(masterCulture: Specimen, quantity: number) {
    const batch = [];
    for (let i = 0; i < quantity; i++) {
      const specimen = {
        ...createSpecimen({
          type: "CULTURE",
          species: masterCulture.species,
          stage: "INOCULATION",
          organization: "mush-ohio",
          strain: {
            name: masterCulture.strain!.name,
            // Agar-to-agar subculture: count it as a clonal generation
            clonalGeneration: (masterCulture.strain?.clonalGeneration ?? 0) + 1,
            lineage: masterCulture.id,
          },
        }),
        created: new Date().toISOString(),
      };
      await this.database.save(specimen);
      await this.printer.print(await toQRCodeDataURL(specimen, { size: 300, errorCorrection: 'M' }));
      batch.push(specimen);
    }
    return batch;
  }

  async scanAndUpdate(qrData: string, updates: Partial<Specimen>) {
    // Embedded labels carry the full record; compact labels carry an ID to look up
    const parsed = qrData.trim().startsWith('{')
      ? parseSpecimen(qrData)
      : parseCompactUrl(qrData);
    if (!parsed.success) throw parsed.error;

    const current = await this.database.findById(parsed.data.id);
    const updated = { ...current, ...updates };
    await this.database.save(updated);
    return updated;
  }

  async traceLineage(specimenId: string) {
    const specimen = await this.database.findById(specimenId);
    const lineage = [];
    let current = specimen;

    while (current.strain?.lineage) {
      const parent = await this.database.findById(current.strain.lineage);
      lineage.unshift(parent);
      current = parent;
    }

    return lineage;
  }

  async generateAuditReport(startDate: Date, endDate: Date) {
    const allLabels = await this.database.query({
      organization: "mush-ohio",
      created: { $gte: startDate, $lte: endDate }
    });

    return {
      totalBatches: allLabels.length,
      cultures: allLabels.filter(l => l.type === "CULTURE"),
      spawn: allLabels.filter(l => l.type === "SPAWN"),
      blocks: allLabels.filter(l => l.type === "SUBSTRATE"),
      harvests: allLabels.flatMap(l => l.custom?.mushOhio?.yields || []),
      lineageMap: await this.buildLineageMap(allLabels)
    };
  }
}
```

### Hardware Setup

**Label Printers**:

- Brother QL-820NWB (WiFi networked)
- Placed at each workstation:
  - Culture lab (1)
  - Spawn production (1)
  - Growing rooms (3)
  - Packaging area (2)

**Scanners**:

- Workers use smartphones with QR app
- Tablet at each station for updates

**Network**:

- Farm-wide WiFi
- Cloud backup (AWS S3)
- Local redundancy

### Integration

```typescript
// Integrate with existing systems
class IntegrationLayer {
  // Inventory management
  async syncToInventory(label: Specimen) {
    await this.inventorySystem.update({
      sku: label.custom.mushOhio.blockNumber,
      quantity: 1,
      status: label.stage,
      location: label.custom.mushOhio.room
    });
  }

  // Order fulfillment
  async packageOrder(orderId: string, blocks: string[]) {
    const labels = await Promise.all(
      blocks.map(id => this.database.findById(id))
    );

    const packageLabel = {
      ...createSpecimen({
        type: "HARVEST",
        species: labels[0].species,
        stage: "HARVEST",
        organization: "mush-ohio",
        // strain.lineage holds one parent ID, so list every source block in custom
        strain: { name: labels[0].strain!.name, lineage: labels[0].id },
        custom: { mushOhio: { orderId, sourceBlocks: labels.map(l => l.id) } },
      }),
      created: new Date().toISOString(),
    };

    return packageLabel;
  }

  // Customer notification
  async notifyCustomer(customerId: string, labelId: string) {
    const label = await this.database.findById(labelId);
    await this.email.send({
      to: customerId,
      subject: "Your mushrooms are ready!",
      qrCode: await toQRCodeDataURL(label, { size: 300, errorCorrection: 'M' }),
      harvestDate: label.custom.mushOhio.harvestDate,
      farmInfo: label.custom.mushOhio.farmInfo
    });
  }
}
```

## Key Learnings

### What Worked Well

✅ **Phased rollout**: Started with just cultures, added stages gradually
✅ **Worker training**: Hands-on practice before go-live
✅ **Custom fields**: Flexibility for farm-specific data
✅ **Mobile-first**: Workers use phones, not computers
✅ **Visual labels**: Large QR codes, color-coded by type

### Challenges Overcome

❌ **WiFi dead zones**: Added access points in growing rooms
❌ **Label durability**: Switched to waterproof labels
❌ **Worker resistance**: Showed time savings, not extra work
❌ **Data entry errors**: Added validation and scanning confirmation
❌ **Integration complexity**: Built API adapter layer

### Best Practices

1. **Start small**: One strain, one room
2. **Train thoroughly**: Practice before production
3. **Validate data**: Check accuracy weekly
4. **Backup everything**: Cloud + local storage
5. **Review regularly**: Monthly data quality audits
6. **Engage workers**: Listen to feedback, iterate

## Cost-Benefit Analysis

### Implementation Costs

**One-time**:

- Software development: $5,000
- Hardware (printers, scanners): $2,000
- Worker training: $1,000
- **Total**: $8,000

**Annual Ongoing**:

- Labels and supplies: $500
- Software maintenance: $1,200
- **Total**: $1,700/year

### Benefits (Annual)

**Direct**:

- Labor savings: $10,000
- Premium pricing: $20,000
- Reduced waste: $3,000
- **Total**: $33,000/year

**Indirect** (estimated):

- Avoided recalls: $50,000+
- Customer retention: $15,000
- Regulatory compliance: Priceless
- Brand reputation: Immeasurable

**ROI**: 412% first year, ongoing

## Conclusion

WOLS transformed Mush Ohio from a small operation with manual tracking to a professional farm with:

- Complete digital traceability
- Regulatory compliance
- Customer transparency
- Premium market positioning
- Scalable operations

**Key success factor**: WOLS provided the standardized data model needed to build farm management systems that work across the entire industry.

## Next Steps for Commercial Farms

1. **Assess current tracking**: Identify gaps
2. **Review WOLS spec**: [SPECIFICATION.md](../SPECIFICATION.md)
3. **Plan implementation**: Phased rollout
4. **Choose platform**: WeMush or build custom
5. **Train team**: Hands-on practice
6. **Start small**: One room, one strain
7. **Scale gradually**: Add features over time

**Need help?** [Contact Mush Ohio](https://mushohio.com) or join [GitHub Discussions](https://github.com/wemush/open-standard/discussions)

---

**Ready to transform your farm?** Start your WOLS journey today! 🍄
