# WOLS Registries

Machine-readable registries that the [specification](../SPECIFICATION.md) refers to.

| File | Registry | Defined in |
| ---- | -------- | ---------- |
| [`species-codes.json`](./species-codes.json) | Compact URL species codes, and the legacy codes decoders still read | [Species Code Registry](../SPECIFICATION.md#species-code-registry-v150) |

Registries are append-only. A code, once registered, keeps its meaning and is never removed or reassigned, so a label printed today decodes the same way with every later version. To register a code, open a pull request that adds one entry to `codes` with the scientific name, a code that matches `codePattern` and isn't already used (as a code or a legacy code), and `since` set to the next release. The [conformance vectors](../conformance/vectors/compact.json) copy the registry, so run `python3 conformance/tools/generate_vectors.py` in the same pull request.

Like `schema/` and `conformance/`, this directory is dedicated to the public domain under CC0 1.0.
