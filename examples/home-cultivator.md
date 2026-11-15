# Home Cultivator Example

How a home mushroom grower uses WOLS to track grows and optimize yields.

## The Problem

**Meet Sarah**, a home mushroom cultivator who grows oyster mushrooms in her basement. She's been growing for 2 years but struggles with:

- **Forgetting what worked**: "Did I use hardwood or straw for that amazing flush?"
- **No data tracking**: Relies on memory and scattered notes
- **Can't compare grows**: Hard to see patterns across batches
- **Lost lineage**: Doesn't know which culture produced best yields

**Result**: Inconsistent yields, repeated mistakes, slow improvement

## The Solution: WOLS Labels

Sarah implements WOLS tracking with minimal effort:

### Setup (One-time)

1. **Create free WeMush account** or use WOLS library
2. **Buy label printer** (Brother QL-820NWB, $150)
3. **Design workflow**: Label cultures, spawn, and fruiting blocks

### Workflow

#### Step 1: Start Culture

Sarah receives a new culture from a friend:

```typescript
import { createSpecimen, toQRCodeDataURL } from '@wemush/wols';

// createSpecimen() has no `created` input, so set the timestamp on the result.
const culture = {
  ...createSpecimen({
    species: "Pleurotus ostreatus",
    strain: {
      name: "Blue Oyster - Friend's Strain",
    },
    type: "CULTURE",
    stage: "COLONIZATION",
    custom: {
      sarah: {
        source: "Friend donation",
        notes: "Said this gives huge flushes"
      }
    }
  }),
  created: "2025-12-01T10:00:00Z",
};

const cultureQr = await toQRCodeDataURL(culture, { size: 300, errorCorrection: 'M' });
```

**Print label** (`cultureQr` is a PNG data URL), stick on petri dish.

#### Step 2: Transfer to Grain Spawn

Two weeks later, culture is ready:

```typescript
const spawn = {
  ...createSpecimen({
    species: "Pleurotus ostreatus",
    type: "SPAWN",
    stage: "INOCULATION",
    strain: {
      name: "Blue Oyster - Friend's Strain",
      // No generation bump: grain spawn is an expansion of the same genetics.
      // Ancestry is recorded with lineage instead.
      lineage: culture.id, // Links to parent culture
    },
    custom: {
      sarah: {
        substrate: "Rye grain",
        weight: "5 lbs",
        inoculationDate: "2025-12-15"
      }
    }
  }),
  created: "2025-12-15T14:00:00Z",
};
```

**Print label**, stick on spawn jar.

#### Step 3: Inoculate Fruiting Block

Spawn colonizes in 2 weeks:

> **Note**: WOLS 1.2 defines the `SubstrateFormula` and `EnvironmentalData` structures but not yet where they attach on a Specimen, so this example carries them under `custom.sarah`. A standard placement is proposed for 1.3 in [ROADMAP.md](../ROADMAP.md).

```typescript
const block = {
  ...createSpecimen({
    species: "Pleurotus ostreatus",
    type: "SUBSTRATE",
    stage: "INOCULATION",
    strain: {
      name: "Blue Oyster - Friend's Strain",
      lineage: spawn.id,
    },
    custom: {
      sarah: {
        bagWeight: "5 lbs",
        room: "Basement shelf 2",
        substrate: {
          components: [
            { ingredient: "Hardwood sawdust", percentage: 70 },
            { ingredient: "Wheat bran", percentage: 25 },
            { ingredient: "Gypsum", percentage: 5 }
          ],
          hydration: 60,
          sterilization: {
            method: "pressure cooker",
            temperature: 121,
            unit: "C",
            duration: 150,
            timestamp: "2025-12-29T12:00:00Z"
          }
        }
      }
    }
  }),
  created: "2025-12-29T16:00:00Z",
};
```

**Print label**, stick on grow bag.

#### Step 4: Track Fruiting

Block starts pinning after 3 weeks:

- **Scan label** to log stage change
- **Update to PRIMORDIA stage**
- **Record environmental data**:
  - Temperature: 65°F
  - Humidity: 85%
  - Fresh air exchanges: 4/day

```typescript
// A stage change is a new value of the specimen (a platform such as WeMush
// records it for you when you scan). Re-serialize or re-print as needed.
const pinning = {
  ...block,
  stage: "PRIMORDIA" as const,
  custom: {
    sarah: {
      ...block.custom.sarah,
      pinningDate: "2026-01-19",
      notes: "Beautiful pins! More than usual",
      environment: {
        temperature: { value: 65, unit: "F", timestamp: "2026-01-19T08:00:00Z" },
        humidity: { value: 85, timestamp: "2026-01-19T08:00:00Z" },
        co2: { value: 800, timestamp: "2026-01-19T08:00:00Z" }
      }
    }
  }
};
```

#### Step 5: Harvest & Record Yields

First flush ready after 1 week:

```typescript
const harvested = {
  ...pinning,
  stage: "HARVEST" as const,
  custom: {
    sarah: {
      ...pinning.custom.sarah,
      // WOLS 1.2 has no standard yield field, so yields live in custom too.
      yields: [
        {
          date: "2026-01-26T09:00:00Z",
          weight: { value: 1.2, unit: "lbs" },
          quality: "EXCELLENT",
          notes: "Large clusters, perfect coloring"
        }
      ],
      photoUrl: "photo-2026-01-26.jpg",
      sold: "Farmers market - $20"
    }
  }
};
```

**Continue logging** second and third flushes.

## The Results

### After 6 Months

Sarah has tracked 12 complete grows with WOLS:

**Data Insights**:

1. **Best substrate**: 70% hardwood + 25% bran + 5% gypsum
   - Average yield: 1.8 lbs per 5lb block
   - Best of 5 recipes tested

2. **Temperature matters**: Blocks at 65°F yield 30% more than 70°F
   - Discovered by comparing identical genetics at different temps

3. **Genetics**: "Friend's Strain" consistently outperforms commercial cultures
   - 1.5x yield on average
   - Subcultured through 4 clonal generations (still strong)

4. **Timing**: Inoculating blocks on Friday = weekend pinning
   - Can harvest Monday morning for farmers market

**Benefits**:

✅ **Higher yields**: 40% increase from baseline
✅ **Consistency**: Can reproduce best results
✅ **Confidence**: Knows exactly what works
✅ **Traceability**: Can trace any flush back to original culture
✅ **Learning**: Clear data to experiment scientifically
✅ **Sales**: Customers love scanning QR codes on bags

### Customer Transparency

Sarah sells at farmers markets:

**Before WOLS**:

- "These are oyster mushrooms"
- Some customers skeptical

**With WOLS**:

- QR code on every bag
- Customers scan and see:
  - Species: *Pleurotus ostreatus*
  - Grown in: "Sarah's Basement"
  - Substrate: Organic hardwood sawdust
  - Harvest date: Yesterday
  - No pesticides, local, sustainable

**Result**: Premium pricing ($16/lb vs $12/lb), loyal customers, word-of-mouth growth

## Implementation Cost

**One-time**:

- Label printer: $150
- Initial supplies (labels, jars): $50
- **Total**: $200

**Ongoing**:

- Labels: ~$0.05 per label
- Time: ~5 minutes per grow cycle
- Software: Free (WeMush free tier)

**ROI**: Pays for itself in first month from yield improvement and premium pricing

## Code Example: Complete Workflow

```typescript
import {
  createSpecimen,
  serializeSpecimen,
  toQRCodeDataURL,
  type Specimen,
} from '@wemush/wols';

// printLabel() is your own code: send a PNG data URL to your label printer.
async function label(specimen: Specimen) {
  printLabel(await toQRCodeDataURL(specimen, { size: 300, errorCorrection: 'M' }));
}

const now = () => new Date().toISOString();

// 1. Culture
const culture = {
  ...createSpecimen({
    species: "Pleurotus ostreatus",
    strain: { name: "Blue Oyster" },
    type: "CULTURE",
    stage: "COLONIZATION",
  }),
  created: now(),
};
await label(culture);

// 2. Spawn (2 weeks later): same genetics, linked by lineage
const spawn = {
  ...createSpecimen({
    species: culture.species,
    type: "SPAWN",
    stage: "INOCULATION",
    strain: { name: culture.strain!.name, lineage: culture.id },
  }),
  created: now(),
};
await label(spawn);

// 3. Substrate (2 weeks later)
const substrate = {
  ...createSpecimen({
    species: spawn.species,
    type: "SUBSTRATE",
    stage: "INOCULATION",
    strain: { name: spawn.strain!.name, lineage: spawn.id },
    custom: {
      sarah: {
        substrate: {
          components: [
            { ingredient: "Hardwood sawdust", percentage: 70 },
            { ingredient: "Wheat bran", percentage: 25 },
            { ingredient: "Gypsum", percentage: 5 }
          ],
          hydration: 60
        }
      }
    },
  }),
  created: now(),
};
await label(substrate);

// 4. Stage changes as the grow progresses (new values of the same specimen;
//    the ID stays the same, so the printed label keeps working)
const colonizing = { ...substrate, stage: "COLONIZATION" as const }; // Day 7
const pinning = { ...colonizing, stage: "PRIMORDIA" as const };      // Day 21
const fruiting = { ...pinning, stage: "FRUITING" as const };         // Day 24

// 5. Record harvest (no standard yield field in 1.2, so it goes in custom)
const harvested = {
  ...fruiting,
  stage: "HARVEST" as const,
  custom: {
    sarah: {
      ...substrate.custom!.sarah as object,
      yields: [{
        date: now(),
        weight: { value: 1.2, unit: "lbs" },
        quality: "EXCELLENT"
      }]
    }
  },
};
console.log(serializeSpecimen(harvested)); // Full JSON-LD record
```

## Tips for Success

### Start Simple

Don't try to track everything at once:

1. **Week 1**: Just label specimens
2. **Week 2**: Add stage updates
3. **Week 3**: Start recording yields
4. **Month 2+**: Add environmental data

### What to Track

**Essential**:

- Species/strain
- Dates (inoculation, harvest)
- Yields

**Nice to have**:

- Substrate recipe
- Environmental conditions
- Photos
- Notes

**Optional**:

- Detailed genetics
- Cost tracking
- Customer info (if selling)

### Make it a Habit

- **Label immediately** when starting new specimens
- **Update weekly** (or whenever changing stages)
- **Review monthly** to spot patterns
- **Experiment systematically** - change one variable at a time

## Common Questions

**Q: Do I need a label printer?**
A: No, you can print on regular paper and tape to containers. But a label printer is more convenient.

**Q: What if I forget to update labels?**
A: Not a problem. Update whenever you remember. Some data is better than no data.

**Q: Can I track multiple batches at once?**
A: Yes! Each label has unique ID. Track as many as you want.

**Q: Do I need internet to scan labels?**
A: Depends on format. Embedded JSON works offline. Server-referenced IDs need internet.

**Q: What happens to old data?**
A: Keep it forever! Historical data helps identify long-term trends.

## Next Steps

1. **Get started**: [Getting Started Guide](../docs/getting-started.md)
2. **See the spec**: [SPECIFICATION.md](../SPECIFICATION.md)
3. **Join community**: [GitHub Discussions](https://github.com/wemush/open-standard/discussions)
4. **Share results**: Post your success story!

---

**Ready to optimize your grows?** Start with one label today! 🍄
