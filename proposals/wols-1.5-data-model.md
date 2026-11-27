# Proposal: WOLS 1.5 data model and JSON Schema

**Status**: Draft (non-normative). Nothing in this document changes the 1.4.0 specification.
**Target**: WOLS 1.5.0, a minor release, shipped first as `1.5.0-rc.1`
**Closes**: ROADMAP v1.5.0 goal 5 items "Required-field clarity", "Multiple parents", "Generation without a named strain", "Extended data attachment", "Specimen condition" and "Container/vessel", plus goals 1 to 3 at the data-model level
**Date**: November 27, 2026
**Artifacts**: [`schema/1.5/label.schema.json`](../schema/1.5/label.schema.json), [`schema/1.5/bundle.schema.json`](../schema/1.5/bundle.schema.json), [`examples/records/black-pearl-king-chain.json`](../examples/records/black-pearl-king-chain.json), [`conformance/tools/validate_schema.py`](../conformance/tools/validate_schema.py)

---

## Summary

WOLS 1.4 is a good **label** standard: three wire formats, encryption, Ed25519 signatures, and 112 MUST conformance cases. It is not yet a **data** standard. The model lives in a TypeScript interface in prose, the extended structures (environment, substrate, circular economy) attach to nothing, observations and harvests appear only in a REST example, and each library hand-writes its own model. The two libraries already disagree on `_meta` key casing, compact URLs and whether `stage` is required.

This proposal does three things:

1. **Publishes a JSON Schema (2020-12) as the normative model.** The spec prose stays, but the schema wins where they differ. Both libraries generate or check their types against it.
2. **Adds optional label members** that close the roadmap gaps: `taxon` (identifiers and hybrids), `form`, `derivedFrom` (several parents with a relation), `condition`, `container` and `lot`. All are optional, so every valid 1.4.0 label stays valid, and 1.4 decoders treat them as unknown members.
3. **Adds a records layer, the Bundle**, that carries what a label can't: strains, recipes, observations and harvests. Bundles are for exchange between systems and are never printed.

## 1. Why a schema, and why JSON Schema

The business test is whether a vendor's developer can integrate in an afternoon. A JSON Schema gives them validation in any language, editor completion, and generated types, with no WOLS library at all. It also lets the two reference libraries stop drifting: today the only thing that keeps them in sync is the vectors, and the vectors don't cover `_meta`, compact URLs or the extended data.

LinkML was considered, since MIxS is authored in it and it emits JSON Schema, a JSON-LD context, pydantic and TypeScript from one source. It is the better choice if WOLS later wants an RDF/OWL form for research data. For 1.5 it adds a toolchain neither library uses. Recommendation: hand-author the JSON Schema now, keep its `$defs` names and descriptions LinkML-friendly, and revisit at 2.0.

**Sync rule (normative for reference libraries)**: each library's CI validates every `validate` vector input against `schema/1.5/label.schema.json` and fails if the schema verdict differs from the vector's. Types are generated from the schema (json-schema-to-typescript for TS, datamodel-code-generator for Python) or checked against it in tests.

## 2. Label changes (all optional)

| Member | Why | 1.4 behaviour it replaces |
| ------ | --- | ------------------------- |
| `taxon` `{scientificName, authorship, rank, identifiers[], hybridOf[]}` | A name string can't be resolved, deduplicated or express a hybrid. Identifiers use `mycobank`, `indexfungorum`, `gbif`, `col`, `inaturalist` or `ncbi`. | `species` string only. `species` stays required. |
| `form` | `GRAIN_SPAWN`, `LIQUID_CULTURE`, `AGAR_PLATE` etc. survive the round trip. Unregistered values use `x-`. | Type aliases collapse 18 platform types into 5 and lose the rest. |
| `derivedFrom[] {id, relation, quantity}` | Combined spawn, multi-spore isolates and repacks. `relation` says which counter moves. | `strain.lineage`, one ID. Kept, and when both are present `lineage` MUST equal `derivedFrom[0].id`. |
| `condition` | `CONTAMINATED`, `EXHAUSTED`, `DISPOSED`, `ARCHIVED` are not growth stages. | Implementations map contamination onto a stage. |
| `container {format, capacity}` | Vessel words (`PETRI`, `BAG`, `BUCKET`) stop being type aliases. | Aliases only. |
| `lot` | A traceability lot code for sellable product (FSMA 204 TLC, GS1 AI 10). | `batch`, which is a production grouping. |
| `strain.accession` | Culture-collection or vendor accession. | None. |

Also settled:

- **`stage` and `created` are optional**, as both libraries and the `embedded-minimal` vector already behave. Generators SHOULD write both.
- **`strain.name` is optional**, so `generation` and `clonalGeneration` can be recorded for an unnamed strain.
- **`version` allows pre-release suffixes** (`1.5.0-rc.1`). The TS validator rejects them today.
- **`_meta` keys are camelCase on the wire.** Decoders SHOULD accept snake_case and re-emit camelCase (the Python 1.4.0 library writes snake_case).
- **Unknown top-level members are valid** (a warning), and decoders MUST preserve them on re-serialization. Both libraries drop them today.

Why not put several IDs in `strain.lineage`, as the roadmap suggests: a 1.4 decoder that gets an array where it expects a string either rejects the label or loses it. A new member is ignored safely.

## 3. Records layer: the Bundle

A Bundle is `{"@context", "@type": "Bundle", version, publisher, license, specimens[], strains[], recipes[], observations[], harvests[]}`.

- **SpecimenRecord** is a label plus `strainRef`, `recipeRef`, `inoculatedAt`, `inoculum`, `substrateWetWeight`, `substrateDryWeight`, `location` and `circularEconomy`. Biological efficiency is derived: fresh harvest weight over substrate dry weight.
- **StrainRecord** holds the taxon, aliases, accession, origin, isolation source and growth parameter ranges.
- **Recipe** replaces `SubstrateFormula`. Ingredients are amounts with units, because that's what growers weigh; percentages are derived. Covers agar, LC, grain, substrate and casing, and the treatment (autoclave, pasteurize, lime).
- **Observation** is one dated fact about one specimen: note, measurement, environment reading, stage or condition change, contamination (agent, severity, action), photo, with `observedAt` separate from `recordedAt` and a `source` (manual, sensor, import, AI-assisted). `Environment` replaces `EnvironmentalData`: values take their time from the observation.
- **Harvest** is one flush from one specimen: fresh and dry weight, grade, lot, and the HARVEST specimen it became.

All quantities are `{value, unit}` with UCUM codes (`g`, `kg`, `mL`, `Cel`, `%`, `[ppm]`). Legacy `C` and `F` are accepted for temperature.

## 4. Mapping to other standards

| WOLS | Darwin Core | MIxS | EPCIS 2.0 / FSMA 204 |
| ---- | ----------- | ---- | -------------------- |
| Specimen | MaterialEntity (dwc:materialEntityID) | sample | EPC (object) |
| derivedFrom | ResourceRelationship; DwC-DP material derivation | source_mat_id | TransformationEvent inputs |
| taxon | Identification, taxonID, scientificName | host_taxid / samp_taxon_id | n/a |
| Observation | MeasurementOrFact, Event | environment terms (temp, rel_humidity, co2) | ObjectEvent (bizStep inspecting) |
| Harvest | Event + MeasurementOrFact | n/a | ObjectEvent (harvesting CTE), TLC at initial packing |
| lot | n/a | n/a | lot (GS1 AI 10), traceability lot code |
| Location.gln | locationID | geo_loc_name | bizLocation / readPoint |

Term names are from Darwin Core, MIxS 6 and EPCIS 2.0 as published; the DwC-DP names should be re-checked against the ratified guide before this table goes in the spec. A WOLS-to-DwC-DP export and an EPCIS event export are non-normative follow-ups.

## 5. Compatibility

- Every 1.4.0 `validate` vector passes the 1.5 label schema with the same verdict and the same `errorField` (checked by `conformance/tools/validate_schema.py`).
- New members are optional and top-level or inside `strain`, where 1.4 decoders warn, not fail.
- Signed labels: new members are part of the JCS body like any other member, so no signing change.
- The JSON-LD context must define the new terms before 1.5 is final. The context document at `https://wemush.com/wols/v1` is still an unchecked deliverable.

## 6. Open questions

1. Should `taxon` become required in 2.0, with `species` derived from it?
2. Registry for `form`, `container.format`, measurement names and contamination agents: in the spec, or a separate `registries/` folder with its own process like custom namespaces?
3. Should `Observation` and `Harvest` allow a signature, for supply-chain partners?
4. Does a Bundle need a streaming form (JSON Lines) for large exports?
5. ~~License of the schema~~ Settled in this PR: `schema/`, `conformance/` and `examples/records/` are CC0 1.0, because code generators and test suites copy them verbatim. The spec stays CC BY 4.0 and the libraries stay Apache 2.0.
