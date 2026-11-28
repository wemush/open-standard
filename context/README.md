# WOLS JSON-LD context

`v1.jsonld` is the document every WOLS label names in `"@context": "https://wemush.com/wols/v1"`. Publishers serve it at that URL as `application/ld+json`.

It is deliberately small:

- `@vocab` maps every WOLS member, from 1.0 through 1.5.0, to `https://wemush.com/wols/v1#<member>`, so a JSON-LD processor never drops a field. New members need no change here.
- Timestamps (`created` and the `…At` members) are typed `xsd:dateTime`.
- `custom` and `_meta` are `@json`, so vendor extensions stay as opaque JSON instead of being read as linked data.
- `id` is not aliased to `@id`, because 1.3.0 IDs can contain characters that aren't valid IRIs.

Check it against every conformance vector and example record:

```bash
python3 -m pip install PyLD
python3 conformance/tools/check_context.py
```

Each document must expand without losing a member and compact back to itself. The check runs offline.

Like `schema/` and `conformance/`, this directory is dedicated to the public domain under CC0 1.0.
