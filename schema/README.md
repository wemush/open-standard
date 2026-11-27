# WOLS JSON Schemas

**Status**: Draft for WOLS 1.5. See [proposals/wols-1.5-data-model.md](../proposals/wols-1.5-data-model.md).

| File | Validates |
| ---- | --------- |
| `1.5/label.schema.json` | One embedded-format Specimen label (what goes in a QR code). Every valid 1.4.0 label validates. |
| `1.5/bundle.schema.json` | A records bundle for exchange: specimens, strains, recipes, observations, harvests. |

Check the schemas against the conformance vectors and the examples:

```bash
python3 conformance/tools/validate_schema.py
```

It needs `jsonschema` 4.18 or later. Rules a schema can't express (references resolve, `strain.lineage` equals `derivedFrom[0].id`) are checked in the same script.

The `$id` URLs under `https://wemush.com/wols/schema/` resolve: `https://wemush.com/wols/schema/1.5/label.schema.json` and `.../bundle.schema.json` serve these files as `application/schema+json`. They are still drafts, and the published copies follow this directory.
