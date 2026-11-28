# WOLS JSON Schemas

**Status**: Normative for WOLS 1.5.0. Where a schema and the prose of the specification differ, the schema wins. See [Schema and Data Model](../SPECIFICATION.md#schema-and-data-model-v150) and [Records Bundle](../SPECIFICATION.md#records-bundle-v150) in the specification, and the [data model proposal](../proposals/wols-1.5-data-model.md) for the background.

| File | Validates |
| ---- | --------- |
| `1.5/label.schema.json` | One embedded-format Specimen label (what goes in a QR code). A valid 1.4.x label validates, except the few cases listed under [Compatibility](../SPECIFICATION.md#compatibility). |
| `1.5/bundle.schema.json` | A records bundle for exchange: specimens, strains, recipes, observations, harvests. |

Check the schemas against the conformance vectors and the examples:

```bash
python3 conformance/tools/validate_schema.py
```

It needs `jsonschema` 4.18 or later. Rules a schema can't express (references resolve, `strain.lineage` equals `derivedFrom[0].id`) are checked in the same script.

The `$id` URLs under `https://wemush.com/wols/schema/` resolve: `https://wemush.com/wols/schema/1.5/label.schema.json` and `.../bundle.schema.json` serve these files as `application/schema+json`. The published copies follow this directory.
