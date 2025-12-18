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
import { generateLabel } from '@wemush/specimen-labels';

const culture = await generateLabel({
  species: "Pleurotus ostreatus",
  strain: "Blue Oyster - Friend's Strain",
  type: "CULTURE",
  stage: "COLONIZATION",
  created: "2025-12-01T10:00:00Z",
  custom: {
    sarah: {
      source: "Friend donation",
      notes: "Said this gives huge flushes"
    }
  }
});
```

**Print label**, stick on petri dish.

#### Step 2: Transfer to Grain Spawn

Two weeks later, culture is ready:

```typescript
const spawn = await generateLabel({
  species: "Pleurotus ostreatus",
  strain: "Blue Oyster - Friend's Strain",
  type: "SPAWN",
  stage: "INOCULATION",
  created: "2025-12-15T14:00:00Z",
  genetics: {
    parentId: culture.id, // Links to parent culture
    generation: 1
  },
  custom: {
    sarah: {
      substrate: "Rye grain",
      weight: "5 lbs",
      inoculationDate: "2025-12-15"
    }
  }
});
```

**Print label**, stick on spawn jar.

#### Step 3: Inoculate Fruiting Block

Spawn colonizes in 2 weeks:

```typescript
const block = await generateLabel({
  species: "Pleurotus ostreatus",
  strain: "Blue Oyster - Friend's Strain",
  type: "SUBSTRATE",
  stage: "INOCULATION",
  created: "2025-12-29T16:00:00Z",
  genetics: {
    parentId: spawn.id,
    generation: 2
  },
  substrate: {
    components: [
      { type: "Hardwood sawdust", percentage: 70 },
      { type: "Wheat bran", percentage: 25 },
      { type: "Gypsum", percentage: 5 }
    ],
    moisture: 60,
    sterilizationMethod: "Pressure cooked 2.5 hours"
  },
  custom: {
    sarah: {
      bagWeight: "5 lbs",
      room: "Basement shelf 2"
    }
  }
});
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
// Update via app or manually
{
  ...block,
  stage: "PRIMORDIA",
  environment: {
    temperature: { value: 65, unit: "F" },
    humidity: { value: 85, unit: "%" },
    co2: { value: 800, unit: "ppm" }
  },
  custom: {
    sarah: {
      pinningDate: "2026-01-19",
      notes: "Beautiful pins! More than usual"
    }
  }
}
```

#### Step 5: Harvest & Record Yields

First flush ready after 1 week:

```typescript
{
  ...block,
  stage: "HARVEST",
  yields: [
    {
      date: "2026-01-26T09:00:00Z",
      weight: { value: 1.2, unit: "lbs" },
      quality: "EXCELLENT",
      notes: "Large clusters, perfect coloring"
    }
  ],
  custom: {
    sarah: {
      photoUrl: "photo-2026-01-26.jpg",
      sold: "Farmers market - $20"
    }
  }
}
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
   - Propagated through 4 generations (still strong)

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
import { generateLabel, updateLabel } from '@wemush/specimen-labels';

// 1. Culture
const culture = await generateLabel({
  species: "Pleurotus ostreatus",
  strain: "Blue Oyster",
  type: "CULTURE",
  stage: "COLONIZATION",
  created: new Date().toISOString()
});
printLabel(culture.qrDataUrl);

// 2. Spawn (2 weeks later)
const spawn = await generateLabel({
  species: culture.species,
  strain: culture.strain,
  type: "SPAWN",
  stage: "INOCULATION",
  genetics: { parentId: culture.id, generation: 1 },
  created: new Date().toISOString()
});
printLabel(spawn.qrDataUrl);

// 3. Substrate (2 weeks later)
const substrate = await generateLabel({
  species: spawn.species,
  strain: spawn.strain,
  type: "SUBSTRATE",
  stage: "INOCULATION",
  genetics: { parentId: spawn.id, generation: 2 },
  substrate: {
    components: [
      { type: "Hardwood sawdust", percentage: 70 },
      { type: "Wheat bran", percentage: 25 },
      { type: "Gypsum", percentage: 5 }
    ],
    moisture: 60
  },
  created: new Date().toISOString()
});
printLabel(substrate.qrDataUrl);

// 4. Update stages as grow progresses
await updateLabel(substrate.id, { stage: "COLONIZATION" }); // Day 7
await updateLabel(substrate.id, { stage: "PRIMORDIA" });     // Day 21
await updateLabel(substrate.id, { stage: "FRUITING" });      // Day 24

// 5. Record harvest
await updateLabel(substrate.id, {
  stage: "HARVEST",
  yields: [{
    date: new Date().toISOString(),
    weight: { value: 1.2, unit: "lbs" },
    quality: "EXCELLENT"
  }]
});
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

1. **Get started**: [Getting Started Guide](../getting-started.md)
2. **See the spec**: [SPECIFICATION.md](../../SPECIFICATION.md)
3. **Join community**: [GitHub Discussions](https://github.com/wemush/open-standard/discussions)
4. **Share results**: Post your success story!

---

**Ready to optimize your grows?** Start with one label today! 🍄
