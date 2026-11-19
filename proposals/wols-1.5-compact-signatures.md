# Proposal: Compact URL Signatures (WOLS 1.5)

**Status**: Draft (non-normative). Nothing in this document changes the 1.4.0 specification.
**Target**: WOLS 1.5.0, a minor release, shipped first as `1.5.0-rc.1`
**Depends on**: the compact URL parameter registry, the species code registry, and the compact URL conformance vectors ([ROADMAP.md, v1.5.0 goals 4 and 5](../ROADMAP.md#v150-goals))
**Date**: November 19, 2026
**Discussion**: To be opened in [GitHub Discussions](https://github.com/wemush/open-standard/discussions), as [GOVERNANCE.md](../GOVERNANCE.md#types-of-decisions) requires for RFCs. This file is the draft for that discussion.

> The repository had no proposals directory before this one. This proposal starts `proposals/`, named `wols-{version}-{topic}.md`. If the project prefers to keep RFCs only in Discussions, this file can move there unchanged.

---

## Summary

WOLS 1.4.0 signs embedded labels and encrypted URLs, but not compact URLs ([SPECIFICATION.md, Cryptographic Signatures](../SPECIFICATION.md#cryptographic-signatures) and [Not in 1.4.0](../SPECIFICATION.md#not-in-140)). This proposal adds a third signed form, `compact-url`. It reuses everything 1.4.0 already defines (Ed25519, the `kid "." sig` token, the `WOLS-SIG-v1` signing input, the trust store and the five statuses), and it signs the **exact printed URL bytes before `&sig=`**, as encrypted URLs already do.

It also states what a signed compact label costs in QR modules. That is the reason compact signing matters: on the small thermal labels where compact URLs are used, a signed embedded label doesn't scan. The honest result: a signed compact URL is about 190 to 210 bytes. That **brings the smallest signable QR from 40 mm down to about 23 mm** at ECC M. It **does not reliably fit the 20 mm QR on the default 40×30 mm label** with today's payloads. It fits there only with a trimmed payload, ECC L, and a print-and-scan test that hasn't been done yet.

---

## 1. Problem and goals

### 1.1 Why compact signing is the only option for small labels

The WeMush Platform signs labels with the 1.4.0 scheme today. Its renderer draws the QR at ECC M with a 2-module quiet zone inside the QR edge. Thermal printers print at 203 dpi.

A signed embedded label is 450 to 530 bytes, which is QR v16 to v18 at ECC M. This is what it would get on each label size:

| Label | QR edge | Format printed today | Signed embedded would get |
| ----- | ------- | -------------------- | ------------------------- |
| 40×30 mm (default) | 20.0 mm | Compact, unsigned | 1.7 to 1.9 dots per module |
| 2×1″ | 21.3 mm | Compact, unsigned | 1.8 to 2.0 dots per module |
| 60×40 mm | 25.2 mm | Compact, unsigned | 2.2 to 2.4 dots per module |
| 3×2″, 40×60 mm | 32.0, 33.0 mm | Compact, unsigned | 2.75 to 2.96 dots per module (measured) |
| 4×2″ (ZD220) | 42.7 mm | Signed embedded | 3.7 to 3.8 dots per module (3.4 at a 40 mm edge) |

The platform upgrades a compact label to signed embedded only when the QR edge is at least 40 mm. Below that, labels print compact and unsigned. Embedded labels can't get much smaller: the `signature` member alone costs about 113 bytes, and the label body is the rest. So for every label under 40 mm, compact signing is the only way to sign at all.

### 1.2 Goals

1. **Sign small labels.** A signed compact URL fits a QR that scans reliably on the smallest label it can.
2. **Verify offline.** Verification needs only the scanned text and a trust store, with no network access. That is the 1.4.0 rule, unchanged.
3. **Keep 1.4 readers working.** A 1.4.0 decoder must still parse and resolve a signed compact URL and ignore the signature. Section 7.3 shows what both 1.4.0 libraries do today.
4. **Reuse 1.4.0.** Same algorithm, same token grammar, same signing-input structure, same trust store, same statuses and check order. Only the form tag and body are new.

### 1.3 Non-goals

- Binding a label to a physical item. A signature authenticates bytes, not bags (section 5.4).
- Authenticating resolver data. Data fetched by ID from an API isn't covered by the signature (section 5.4).
- A new signature algorithm. Section 3.4 explains why.
- Signing the HTTPS resolver form. It isn't defined yet (open question 4).

---

## 2. What must be normative so there are fixed bytes to sign

1.4.0 says compact URLs "can't be signed in 1.4.0. Their parameter set and code registries aren't normative yet, so there are no fixed bytes to sign" (SPECIFICATION.md lines 551 and 742). That sentence covers two different problems:

- **What is signed**: Which bytes go into the signing input. Signing the exact received bytes fixes this without any registry.
- **What it means**: What a verified `s=PO` or `st=COL` says. Only the registries can fix this, whichever option below is chosen.

### 2.1 Option A: a canonical compact form

The verifier parses the URL, rebuilds a canonical form, and verifies that. The spec would have to fix:

- **Parameter set and order**: A fixed set of names in a fixed order, and a rule for parameters outside it.
- **Percent-encoding**: Which characters are encoded, the case of hex digits, and whether `+` means space.
- **Value spelling**: Full stage names or 3-letter codes, species codes or full names, leading zeros in `t`.
- **Registry versioning**: If the canonical form is semantic (`s=POSTR` and `s=Pleurotus%20ostreatus` canonicalize to the same thing), the code registry must be frozen or versioned, and the body must say which version.
- **Unknown parameters**: Either sign them, which needs a generic canonicalization for them too, or leave them out. Leaving them out lets anyone add unsigned parameters next to signed ones, and a reader could show them as if they were signed. The platform already prints one such extension, `td` (transfer depth).

**Failure modes**:

- **Divergent canonicalizers**: Every implementation needs a byte-identical canonicalizer. The JCS rules in 1.4.0 show how many details that takes for JSON. Every divergence is a `valid` label that one library reports as `invalid`.
- **Rebuilt-model trap**: Libraries rebuild compact refs today. TypeScript re-adds `wemush:`, resolves codes, and reports `1.1.0` for any `v1` path. Python drops a full stage name it doesn't recognize (`st=COLONIZATION` becomes `stage=None`). The 1.4.0 rule "canonicalize what was received, not your model" would have to be restated for URLs, and it would be just as easy to get wrong.
- **Registry coupling**: Adding or changing a code changes the canonical form of existing labels, which can't be recalled.

**Advantage**: A canonical form survives a reader that re-serializes a URL, for example by reordering parameters or turning `%20` into `+`.

### 2.2 Option B: the exact received bytes, minus `sig`

The body is the URL exactly as scanned, with the trailing `&sig=…` removed, as 1.4.0 already defines for encrypted URLs ([Encrypted URL body](../SPECIFICATION.md#encrypted-url-body)). Nothing is decoded, re-encoded, or reordered.

**What must still be normative**:

- **The URL shape a verifier accepts**: The prefix, a single path segment, and the rules in section 4.
- **Parameter value decoding**: How a verified value is decoded for display. This matters only for showing what was verified, not for checking the signature.
- **Registries that only grow**: The species code and parameter registries never reassign a code or name. Exact bytes fix what was signed, not what it means. A signed `s=PO` (the Python 2-letter table) and a signed `s=POSTR` (the TypeScript 5-letter table) both verify. If `PO` is later assigned to another species, an old signed label would display the wrong species with a `valid` badge. So assignments must be append-only.
- **Generation profile (SHOULD, not MUST)**: Signers SHOULD emit one recommended spelling (registry parameter order, extensions last, uppercase hex in escapes). This is for interoperability and smaller output. Verification never depends on it.

**Failure modes**:

- **Re-serialization**: A reader that rebuilds the URL makes the signature fail. It fails as `invalid`, the same status as tampering, which is confusing but fail-closed. Mitigation: verify the string the scanner returned. 1.4.0 already says to re-emit signed URLs as received.
- **Wrappers**: `web+wemush://…` and `https://{host}/wols/…` don't start with the signed prefix. Section 4.4 handles them with an unwrap step outside verification.
- **Display ambiguity**: `sn=Blue+Oyster` can be read as `Blue Oyster` or `Blue+Oyster`. Section 4.3 fixes this for display without touching the body.

### 2.3 Recommendation: option B

Sign the exact received bytes, with a new form tag.

- **Already built**: Both 1.4.0 libraries already implement this body rule for encrypted URLs and pass its vectors. Compact signing reuses that code and changes only the prefix check and the form tag.
- **Printed bytes don't change**: The QR payload is fixed when printed, so the bytes a scanner reads are the bytes that were signed. Re-serialization happens only in software that ignores "re-emit as received", and the fix there is to keep the raw string.
- **Covers extensions**: Extension parameters such as `td`, and future registered parameters, are covered without a generic canonicalizer.
- **Registries can still change**: Signing doesn't wait for, or freeze, registry contents. Registries only have to be append-only.

The registries still have to be settled in 1.5, as the roadmap plans, so that verified values have one meaning. That is a requirement for displaying values, not for checking signatures.

---

## 3. Signature placement and encoding

### 3.1 Placement

The token goes in a trailing `sig` parameter, exactly as for encrypted URLs:

```text
wemush://v1/{id}?{params}&sig={kid}.{86 base64url chars}
```

- `sig` is the last parameter, appears once, and nothing follows it.
- The token grammar is the 1.4.0 grammar, unchanged (`kid = 1*64(ALPHA / DIGIT / "-" / "_")`, `sig = 86` base64url characters with zero unused bits).
- **Why the name `sig`**: The 1.3.x and 1.4.0 decoders already treat it as reserved. A new parameter name would gain nothing (`&z=` would save 2 bytes) and wouldn't have that history.

### 3.2 Domain separation

The signing input is the 1.4.0 structure with a third form tag:

```text
signing input = "WOLS-SIG-v1" LF "compact-url" LF kid LF body
```

`compact-url` keeps a compact signature from verifying as `embedded` or `encrypted-url`, and the reverse, even over identical body bytes. The domain stays `WOLS-SIG-v1`, because the algorithm and token don't change. 1.4.0 reserves a new domain tag for a new scheme, and this isn't one.

### 3.3 Kid size

The token costs `5 + len(kid) + 1 + 86` bytes (`&sig=`, kid, `.`, signature), so 92 bytes plus the kid. The kid is the only part an issuer controls.

- **Short kids**: Compact-label kids SHOULD be 1 to 3 characters, such as `w1`. The 1.4.0 grammar already allows them. Each character saved is one byte, and section 6.2 shows that a few bytes can decide the QR version.
- **Collisions**: Short kids collide more easily in a trust store that holds several issuers. A kid is unique only within a trust store, as in 1.4.0. A store that loads several issuers must refuse duplicate kids, which key set loading already does.
- **Aliases**: An issuer MAY register a short compact kid and a long embedded kid for the same key. Several kids may map to one key, and the kid is signed, so moving a signature between them fails.
- **Rotation**: Never reuse a retired kid for a new key (section 5.3).
- **Omitting the kid** (rejected): Trying every key in the store saves about 3 bytes. It breaks the token grammar, makes verification cost grow with the store, and leaves `unknown-kid` undefined.

### 3.4 Can the signature be shorter?

No. **The signature is the floor.**

- **Ed25519**: Signatures are always 64 bytes. Verification needs both halves (`R` and `S`), so there's no truncated form.
- **Truncated MACs are not acceptable.** An HMAC or other MAC, truncated or not, is symmetric: anyone who can verify can also forge. That breaks the 1.4.0 trust model, where public keys are distributed in trust stores and key set documents and anyone can verify offline. A scanner holding a shared MAC key could mint labels for any issuer. 1.5 MUST NOT define a MAC as a compact signature.
- **Shorter public-key signatures exist but aren't advisable for 1.5.**
  - **BLS12-381**: Minimal-signature-size BLS is 48 bytes, 64 base64url characters, which saves 22 characters. It needs pairing libraries that aren't in WebCrypto or the Python `cryptography` package, subgroup checks, new key types, a new domain tag, and slower verification on phones.
  - **Short Schnorr variants**: Variants with a truncated challenge reach 48 bytes, but they aren't standardized.
  - Either could come later, under a new domain tag, if label sizes still don't fit.

### 3.5 Could a different text encoding of the 64 bytes help?

QR codes have modes that pack characters more densely than byte mode (8 bits per character):

- **Alphanumeric mode**: 11 bits per 2 characters, over `0-9 A-Z space $ % * + - . / :`
- **Numeric mode**: 10 bits per 3 digits

An encoder can switch mode partway through a payload. Each switch costs a 4-bit mode indicator plus a character count (11 or 12 bits at versions 10 to 26). The cost of the 64 signature bytes in each encoding:

| Encoding of the 64 bytes | Characters | URL-safe | QR bits | Saving vs base64url |
| ------------------------ | ---------- | -------- | ------- | ------------------- |
| base64url, byte mode (1.4.0 token) | 86 | Yes | 86 × 8 = **688** | — |
| base45 (RFC 9285), alphanumeric segment | 96 | **No** (space, `%`, `+`) | 48 × 11 + 15 = **543** before escaping; about **590 to 615** with escapes | About 75 to 100 bits (9 to 12 B) after escaping |
| base32, alphanumeric segment | 103 | Yes (uppercase only) | 51 × 11 + 6 + 15 = **582** | 106 bits (13 B) |
| Decimal, numeric segment | 155 | Yes | 51 × 10 + 7 + 16 = **533** | 155 bits (19 B) |
| Decimal, encoder without mode switching | 155 | Yes | 155 × 8 = 1240 | **−552 bits (−69 B)** |

Effect on QR version, measured with `qrcode` 1.5.4 (section 6.1). The kid is `wm1`, and the body is the unsigned URL:

| Unsigned body | base64url (byte) | base45 | base32 | decimal (numeric) | decimal, byte-only encoder |
| ------------- | ---------------- | ------ | ------ | ----------------- | -------------------------- |
| 59 B | L v7 / M v9 | L v7 / M v8 | L v7 / M v8 | L v6 / M v8 | L v9 / M v11 |
| 95 B | L v8 / M v10 | L v8 / M v9 | L v8 / M v9 | L v8 / M v9 | L v10 / M v12 |
| 106 B | L v9 / M v10 | L v8 / M v10 | L v8 / M v10 | L v8 / M v10 | L v10 / M v12 |

**Base45 doesn't help in a URL.**

- **Escaping**: Space, `%`, and `+` must be percent-encoded in a URL. `+` would decode as a space (section 4.3).
- **Cost of escapes**: An escape with uppercase hex (`%20`) is still three alphanumeric characters, so it stays in the segment. That turns one character into three.
- **Expected count**: About 6.4 of the 96 characters need escaping (3/45 of them). One sample with 4 escapes came to 104 characters and 587 bits.
- **Result**: That is about the same as base32, with none of base32's simplicity. The table's QR versions are before escaping, so they flatter base45.

**Decimal saves about 19 bytes, one QR version in some cases**, but it has real costs:

- **Second token encoding**: A second token syntax (155 digits) only for compact URLs, which every verifier must implement.
- **Encoder dependence**: The saving exists only if the QR encoder switches to numeric mode for the digits. `qrcode` (npm) does this automatically. Many encoders, including some printer firmware and label-design tools, use byte mode for the whole payload. In byte mode a decimal signature costs **69 bytes more** than base64url, two QR versions worse. A spec can't require segmentation from every encoder.
- **Uncertain gain**: The gain appears only at a few payload sizes (95 B at M, 106 B at L).

**Recommendation**: Keep the 1.4.0 base64url token for compact URLs in 1.5. Decimal encoding is open question 2, to revisit only if a print-and-scan test shows that one version decides whether 20 mm labels work.

---

## 4. Verification

### 4.1 Which URLs are compact URLs (for signing)

A signable compact URL:

- **Prefix**: Starts with exactly `wemush://v1/`, lowercase.
- **Path**: Then one non-empty path segment (the percent-encoded ID suffix) containing no `/`.
- **Query**: Then `?` and a non-empty query.
- **Exclusions**: Isn't an encrypted URL (`wemush://v1/encrypted/…`), which keeps its 1.4.0 rules.

Other routes, such as the platform's `v1/batch/`, `v1/c/`, and `v1/scan/`, are not signable. With a `sig` they are `malformed`. A compact ID that is literally `encrypted` (`wemush://v1/encrypted?…`) has no `/` after the segment, so it is a compact URL.

### 4.2 Algorithm

The steps and their order follow 1.4.0, and each status means the same thing.

1. **Form**: A string that starts with a URI scheme takes the URL rules, as in 1.4.0. Starting with `wemush://v1/encrypted/` selects `encrypted-url`, unchanged from 1.4.0. Matching section 4.1 selects `compact-url`. Anything else is `unsigned` without a `sig` parameter and `malformed` with one, as in 1.4.0.
2. **Find `sig`**: Split at the first `?`, then on `&`. A name is the text before its first `=`. Names are compared as exact text. No parameter named `sig` means `unsigned`.
3. **Malformed**: The URL is `malformed` if any of these hold:
   - **Copied from the 1.4.0 encrypted URL rules**: A character outside U+0021 to U+007E; a `#`; more than one `sig`; `sig` not last, or the only parameter (see open question 9); `sig` without `=`.
   - **New for compact**: An empty parameter (`&&`, or `?&`). Any parameter name, other than `sig`, that appears more than once, so that `s=POSTR&s=AMANI` can't display differently in first-wins and last-wins readers. A parameter name that doesn't match `1*(ALPHA / DIGIT / "_" / "-")`, so that `%73` can't be read as `s` by a decoding reader. A malformed percent escape, or an escape that decodes to invalid UTF-8, in the path segment or any value.
   - **Token**: A token that breaks the 1.4.0 grammar.
4. **Trust store**: The kid isn't in the trust store, which gives `unknown-kid`. An unusable entry gives `invalid`, as in 1.4.0.
5. **Signature**: Verify Ed25519 (RFC 8032 §5.1.7, rejecting `S ≥ L`) over `"WOLS-SIG-v1\ncompact-url\n" + kid + "\n" + body`. The body is the first `len(url) − len("&sig=" + token)` characters, as ASCII bytes. The result is `valid` or `invalid`.

The new malformed rules apply only to signed compact URLs. They don't change how unsigned compact URLs decode.

### 4.3 What a verifier returns

- **Verified parameters**: For `valid`, the result reports the kid, as in 1.4.0, and SHOULD also report the parameters decoded from the verified body. Applications display those, not a second parse. That is the 1.4.0 rule "display what you verified", applied to URLs.
- **Value decoding**: Percent-decode as UTF-8. In query values, `+` decodes to space. That is what both 1.4.0 libraries and the platform's parser already do: tested, `sn=Blue+Oyster` and `sr=Blue+Oyster` both read as `Blue Oyster`. The platform parser reads the strain from `sr` or `strain`, not `sn`, which is another registry divergence for 1.5 to settle. In the ID path segment, `+` is a literal character, as in the encrypted URL rules. This makes today's `toCompactUrl` output signable as is. The stricter alternative, where signers must write `%20` and a `+` is `malformed`, would make existing generator output unsignable without a change. It is not recommended.
- **Unknown parameters**: Parameters the verifier doesn't recognize, such as the platform's `td`, are covered by the signature. A verifier SHOULD return them separately, marked unrecognized, so an application doesn't present a value it can't interpret as a verified fact.

### 4.4 Wrapped URLs: `web+wemush://` and the PWA handler form

Labels SHOULD print the signed `wemush://v1/` form. In 1.4.0, both signed URL forms use only that prefix, and the `verify-url-other-scheme` vector holds a `web+wemush://` URL with `sig` to `malformed`. This proposal keeps that. The verifier itself accepts only `wemush://v1/`, and wrappers are removed by a separate, optional step before verification, like key fetching in 1.4.0:

- **Unwrap function**: Libraries SHOULD provide `unwrapWolsUrl(text)` with exactly two transforms, applied in this order:
  1. For `https://{host}/wols/{x}`, percent-decode `{x}` exactly once.
  2. Remove a leading `web+` from `web+wemush://v1/…`.

  The transforms chain. The platform's PWA manifest registers the `web+wemush` protocol, so its handler URL decodes to `web+wemush://…`, which step 2 then turns into `wemush://…`. The result is accepted only if it starts with `wemush://v1/`. Nothing else is rewritten. In particular, the outer query isn't merged in. The platform's handler currently does merge it, which is a heuristic.
- **Fail-closed**: An unwrap that changes any other byte makes the signature fail as `invalid`, not `valid`. So the unwrap step can cause false failures but never a false `valid`.
- **Decode once**: Percent-decoding once is exact for any signable URL, because `encodeURIComponent` followed by one `decodeURIComponent` gives back the original. A second decode would turn `%2520` into a space, so decoding twice is forbidden.

### 4.5 Signing

- **Input**: The signer builds the complete unsigned URL as it will be printed. The signed URL is that URL, then `&sig=`, then the token.
- **Refusals**: Signers MUST refuse:
  - A URL without a query.
  - A URL that already has `sig`. To re-sign, remove it first.
  - A URL that breaks any section 4.2 rule: non-ASCII, a `#`, a duplicate name, an empty parameter, a bad name, or a bad escape.
  - A URL that doesn't match section 4.1.
- **Recommended spelling**: Signers SHOULD emit the recommended spelling (section 2.2).

---

## 5. Keys, rotation, and security considerations

### 5.1 Trust store and key set documents

No changes:

- A compact kid resolves only through the caller's trust store, never from the label. Compact labels carry `o` (organization) and similar parameters, and those MUST NOT be used to choose a key or a key set host.
- `/.well-known/wols-keys.json` already holds `Ed25519` keys with any valid kid, including short ones.
- No network access during verification.

### 5.2 Kid and issuer policy

A `valid` result means the holder of the kid's key signed these bytes. Any trusted kid can sign any ID. In a store with several issuers, issuer A can sign a label whose ID or `o` belongs to issuer B, and it verifies `valid` under A's kid. Applications SHOULD check that the kid is one they expect for the label's ID namespace or organization, and SHOULD always show the signer.

### 5.3 Rotation and retired keys

As in 1.4.0:

- **Rotate**: Rotate with a new kid, and keep retired public keys in trust stores while labels signed with them are in circulation. Compact labels are often reprinted at each stage, but not always, so assume years.
- **Never reuse a kid**: Never reassign a retired kid to a new key. Short kids make reuse tempting, because `w1` to `w9` run out. A trust store maps a kid to one key, so reuse would force verifiers to drop the old key, and every old label would become `invalid`. Use a kid scheme with room to grow, such as `w1`…`w9`, then `wa`…`wz`.
- **Compromise**: Remove the kid from every trust store. Every label under it then verifies as `unknown-kid`, including genuine ones. A stolen key can backdate labels, so there is no way to separate them.

### 5.4 Threats

- **Cloning and replay**: A signature authenticates content, not physical binding. A valid label can be copied onto another bag and still verifies. Compact labels are references, so a clone resolves to the genuine record, and it is indistinguishable from the original. An older signed label for the same ID, from an earlier stage, also stays `valid` (rollback). `t` is whatever the signer wrote, not a trusted time. Mitigations are outside the label: tamper-evident label stock, and resolver-side detection of one ID scanned in two places.
- **Resolver data is not signed**: The signature covers only the printed parameters. Data fetched from an API by ID is authenticated by TLS and the resolver, not by the label signature. Applications MUST NOT present resolved data as verified by the label.
- **Downgrade by stripping**: Removing `&sig=…` leaves a valid unsigned compact URL, `unsigned`, not `invalid`. The kid goes with it, so a verifier can't tell from a stripped label who should have signed it. A policy that requires signatures has to come from context: this station, this organization's ID namespace, or every label from a given resolver.
- **Parameter injection**:
  - **Before `sig`**: Parameters before `sig` are in the signed bytes.
  - **After `sig`**: Parameters after it are `malformed`.
  - **Duplicates**: Duplicate names are `malformed`, so first-wins and last-wins readers can't show different values for a `valid` label.
  - **Escaped names**: Escaped parameter names are `malformed`, so a decoding reader can't see a second `s`.
  - **Fragments**: A fragment is `malformed`.
  - **What remains**: A decoder that ignores verification still decodes whatever it is given. That is why applications display the verified parameters (section 4.3).
- **Cross-form reuse**: Signatures don't move between forms, because of the `compact-url` tag. Vectors cover both directions.
- **Meaning drift**: Covered by append-only registries (section 2.2). A verifier that doesn't recognize a code shows it raw, and doesn't guess.
- **Linkability**: The kid is cleartext. Every compact label signed with one key links to its issuer. Issuers who care SHOULD use separate keys for separate purposes, as in 1.4.0.

---

## 6. Size budget

### 6.1 Method

**Geometry**: 20 mm at 203 dpi is 20 / 25.4 × 203 = **159.84 dots**.

- **Modules**: A version-*v* QR has 17 + 4*v* modules per side. The platform adds a 2-module quiet zone on each side, inside the edge, so the edge holds 21 + 4*v* modules.
- **Dots per module**: 159.84 / (21 + 4*v*).
- **Example**: v8 is 49 modules, so 53 with the quiet zone, and 159.84 / 53 = **3.02** dots per module.
- **Integer dots**: A 203 dpi printer can't print fractional dots. 3 dots × 53 = 159 dots = 19.9 mm, so v8 fits a 20 mm edge at exactly 3 dots, with less than one dot to spare. v9 needs 3 × 57 = 171 dots = 21.4 mm.

**Tools**: QR versions were computed with `qrcode` 1.5.4 (the platform's encoder) in pure byte mode. Byte mode is the baseline because a spec can't require an encoder to segment. Where `qrcode`'s automatic segmentation gives a smaller version, it is noted. The signature is a real Ed25519 signature, 86 base64url characters. The label QR edges come from the platform's own label geometry. The measurement scripts aren't part of this proposal; every input is shown below, so the numbers can be reproduced with any ISO/IEC 18004 encoder.

**Caveat**: These numbers are geometry, not scan tests. They show which QR version a payload needs and how many dots each module gets. Whether 3.02 dots scans reliably on worn thermal stock in a grow room is an open question that only a print-and-scan test can answer (open question 1).

**Byte-mode capacity, and dots per module at 203 dpi with the quiet zone included** (matches the budget measured on the platform: 152 B at M and 192 B at L for 3 or more dots on a 20 mm QR; 362 B at M and 458 B at L for 2 or more dots):

| Version | Modules | Cap L | Cap M | 20 mm | 21.3 mm (2×1″) | 25.2 mm (60×40) | 32 mm (3×2″) |
| ------- | ------- | ----- | ----- | ----- | -------------- | --------------- | ------------ |
| 6 | 41 | 134 | 106 | 3.55 | 3.78 | 4.48 | 5.68 |
| 7 | 45 | 154 | 122 | 3.26 | 3.47 | 4.11 | 5.22 |
| 8 | 49 | 192 | 152 | **3.02** | 3.22 | 3.80 | 4.83 |
| 9 | 53 | 230 | 180 | 2.80 | 2.99 | 3.53 | 4.49 |
| 10 | 57 | 271 | 213 | 2.62 | 2.80 | **3.30** | 4.19 |
| 11 | 61 | 321 | 251 | 2.46 | 2.62 | 3.10 | 3.93 |
| 12 | 65 | 367 | 287 | 2.32 | 2.47 | 2.92 | 3.71 |
| 14 | 73 | 458 | 362 | 2.08 | — | — | — |

ECC L recovers about 7% of the codewords, M about 15%, and Q about 25%.

### 6.2 Payloads

The signature overhead is `&sig=` + kid + `.` + 86 characters, which is 92 + kid bytes: 94 for `w1`, 95 for `wm1`, 103 for `mushoh-2026`.

The samples spell the space in `Blue Oyster` as `%20`. Today's generators write `+`, which is 2 bytes shorter per space. No verdict below changes.

| Payload | Unsigned | Unsigned QR (L / M) | Signed, `wm1` | Signed QR (L / M) | Signed, `mushoh-2026` | Signed QR (L / M) |
| ------- | -------- | ------------------- | ------------- | ----------------- | --------------------- | ----------------- |
| Spec example `wemush://v1/clx1a2b3c4?s=POSTR&st=COLONIZATION&t=1734307200` | 59 B | v4 / v4 | 154 B | v7 / v9 (v8 auto) | 162 B | v8 / v9 |
| TypeScript library, cuid ID, `s ty st sn sg` | 95 B | v5 / v6 | 190 B | **v8** / v10 | 198 B | v9 / v10 |
| Platform, `WM-LC-…` ID, `s ty st b sn sg td` | 106 B | v5 / v6 | 201 B | v9 / v10 | 209 B | v9 / v10 |

The largest unsigned URL that still fits a target version once signed:

| Target | ECC | Kid 2 chars | Kid 3 chars | Kid 11 chars |
| ------ | --- | ----------- | ----------- | ------------ |
| v8 (3.02 dots at 20 mm) | L | 98 B | 97 B | 89 B |
| v8 | M | 58 B | 57 B | 49 B |
| v9 | L | 136 B | 135 B | 127 B |
| v9 | M | 86 B | 85 B | 77 B |
| v10 | L | 177 B | 176 B | 168 B |
| v10 | M | 119 B | 118 B | 110 B |

### 6.3 Verdict

- **20 mm QR (40×30 mm default): not reliably with today's payloads.** A typical signed compact URL (190 to 209 B) needs v10 at ECC M, which is 2.62 dots per module. That is below the 3-dot floor, so modules print 2 or 3 dots wide. At ECC L it needs v8 or v9 (3.02 or 2.80). It reaches v8, exactly 3 dots, only in one of these cases:
  - **ECC L with a trimmed payload**: ECC L and an unsigned URL of 98 B or less with a 2-character kid. The 95-byte TypeScript sample just fits, and the 106-byte platform sample doesn't. ECC L recovers only about 7%, and the platform renderer is hard-coded to M today, so this needs a renderer change plus a scan test.
  - **ECC M with a minimal profile**: ECC M and an unsigned URL of 58 B or less with a 2-character kid. That is roughly `wemush://v1/{id}?s={code}&st={stage}` alone. A 19-character `WM-LC-250114-000001` ID with `s=POSTR&st=COLONIZATION` is 55 B and fits. A 24-character cuid with the same parameters is 60 B and doesn't fit, unless the registry adopts 3-letter stage codes (`st=COL`, 51 B).

  Either way the margin is less than one dot. Treat 20 mm as **marginal, pending a print-and-scan test**, not as supported.
- **2×1″ (21.3 mm)**: v8 gets 3.22 dots and v9 gets 2.99, just under 3. A typical payload fits v9 at ECC L (unsigned URL of 136 B or less). At ECC M only a minimal profile fits v9 (86 B or less). Marginal: test it alongside 20 mm.
- **60×40 mm (25.2 mm)**: **Yes, at ECC M**, with typical payloads. v10 gets 3.30 dots, and even v11 (up to 251 B) gets 3.10.
- **3×2″ and 40×60 mm (32 to 33 mm)**: **Comfortable at ECC M** (4.2 to 4.3 dots at v10), and even at ECC Q (v12, 3.7 dots).
- **300 dpi printers**: At 300 dpi a 20 mm edge is 236 dots, so v10 gets 3.87 dots per module. A typical signed compact URL at ECC M works on a 20 mm QR.

**Net effect**: Signed compact lowers the smallest signable QR edge at 203 dpi from **40 mm** (signed embedded) to about **23 mm** at ECC M (v10 at 3 dots is 22.9 mm). The 60×40 mm, 3×2″, and 40×60 mm labels, which print unsigned today, could all be signed. The 40×30 mm default stays unsigned unless a scan test supports a trimmed payload at ECC L or a minimal profile at ECC M. A 300 dpi printer also solves it.

**ID-only signed labels**: Section 4.2 copies the 1.4.0 rule that `sig` can't be the only parameter. Without that rule, the smallest signed label is `wemush://v1/{id}?sig=w1.…`. It is 125 B for a 19-character ID and 131 B for a 25-character cuid, which is **v8 at ECC M (3.02 dots on 20 mm)**. It would sign only "this issuer printed this ID", not species or stage, but it is the one signed form that fits the default label at ECC M with any ID. See open question 9.

---

## 7. Conformance vectors and library impact

### 7.1 New vectors

The prerequisite is a new `compact.json` file for parsing compact URLs. The roadmap already plans it, with the registries. Signing vectors are added to `signatures.json` with `input.form: "compact-url"`, in the existing case format. The descriptions are marked "(1.5.0)", the way 1.4.0 marked its additions to the 1.3.0 files. They use the existing test keys. A short test kid, for example `w1` mapped to the `mushoh-2026` key, is added to `trustStore`.

| Case id | Op | Expected |
| ------- | -- | -------- |
| `sign-compact-url` | `sign` | Exact `signingInput` (`…\ncompact-url\n…`), token, and `url` |
| `sign-compact-url-short-kid` | `sign` | The same URL under `w1`; a different token |
| `sign-compact-url-plus` | `sign` | `sn=Blue+Oyster` is signed as is |
| `sign-refuse-compact-*` | `sign` | `{ "refused": true }` for: no query, empty query, existing `sig`, duplicate name, empty parameter, non-ASCII, `#`, bad escape, bad name, two path segments |
| `verify-compact-valid` | `verify` | `valid`, kid |
| `verify-compact-short-kid` | `verify` | `valid`, kid `w1` |
| `verify-compact-tampered-param` / `-added-param` / `-removed-param` / `-reordered` | `verify` | `invalid` |
| `verify-compact-reencoded` | `verify` | `invalid` (`%20` changed to `+`, and `%2F` to `%2f`: exact bytes) |
| `verify-compact-extension-param` | `verify` | `valid`, with `td` covered (a tampered `td` is `invalid`) |
| `verify-compact-unsigned` | `verify` | `unsigned` |
| `verify-compact-unknown-kid` | `verify` | `unknown-kid` |
| `verify-compact-kid-swapped` | `verify` | `invalid` (`w1` and `mushoh-2026` share a key) |
| `verify-compact-encrypted-url-signature-replayed` and `verify-encrypted-url-compact-signature-replayed` | `verify` | `invalid`, both directions |
| `verify-compact-embedded-prefix` | `verify` | `invalid` (signed with the `embedded` tag) |
| `verify-compact-malformed-*` | `verify` | `malformed` for: `sig` not last, two `sig`, duplicate name, empty parameter, `%73` name, bad escape, invalid UTF-8 escape, `#`, non-ASCII, `WEMUSH://` uppercase, two path segments, `v1/batch/` route |
| `verify-compact-web-plus-wrapper` | `verify` | `malformed` (same rule as `verify-url-other-scheme`) |
| `unwrap-compact-*` (new operation `unwrap`, SHOULD) | `unwrap` | `web+wemush://` and the handler form give the exact signed URL, and then `valid`. Double-encoded input isn't unwrapped twice |
| `parse-compact-signed` (in `compact.json`) | `parse` | Decodes exactly as the unsigned URL; `sig` kept unchanged; not reported as verified |

No existing vector changes. The only vector about a non-encrypted URL with `sig` is `verify-url-other-scheme`, a `web+wemush://` encrypted URL, and it stays `malformed`.

### 7.2 Library API (design only)

The shapes extend the 1.4.0 [Library API Reference](../SPECIFICATION.md#signatures-v140):

```typescript
// Unsigned compact URL, as it will be printed. Returns it with `&sig=` and the token appended.
signCompactUrl(url: string, options: { privateKey: Uint8Array; kid: string }): Promise<string>

// verifySpecimen gains the compact form; its single-string form detection follows section 4.2.
interface VerificationResult {
  status: SignatureStatus;
  kid?: string;
  reason?: string;
  form?: 'embedded' | 'encrypted-url' | 'compact-url';    // new, optional
  params?: Record<string, string>;                         // compact-url + valid: verified, decoded
  unrecognizedParams?: string[];                           // compact-url + valid
}

// Optional pre-step (section 4.4). Returns the wemush://v1/ URL, or null if it can't unwrap exactly.
unwrapWolsUrl(text: string): string | null

// parseCompactUrl keeps the raw token (today the TypeScript SpecimenRef drops it).
interface SpecimenRef { /* … */ signature?: string }
```

- **TypeScript (`@wemush/wols`)**: Reuse the encrypted URL body code, adding the section 4.1 prefix check and the new malformed rules. `parseCompactUrl` should keep `sig` in `SpecimenRef`. 1.4.0 drops it, so a re-emitted URL becomes unsigned. `toCompactUrl` doesn't need to change.
- **Python (`wols`)**: The same. `parse_compact_url` already keeps `sig` in `params`. Its default `web+wemush://` prefix is fine for unsigned output, but `sign_compact_url` must emit `wemush://`.
- **Platform**: `parseWOLSUrl` already keeps `signature` and `raw` for compact URLs. Verification should take `raw` (the scanned string), not a rebuilt URL. The handler unwrap that merges the outer query must not feed the verifier.

### 7.3 What 1.4.0 readers do with a signed compact URL (tested)

The test URLs carried a well-formed 1.4.0 token, `wm1.` plus 86 characters.

| Reader | Parse | Keeps `sig` | `verifySpecimen` |
| ------ | ----- | ----------- | ---------------- |
| `@wemush/wols` 1.4.0 `parseCompactUrl` | Succeeds, same result as unsigned | No (dropped from `SpecimenRef`) | `malformed` ("does not start with `wemush://v1/encrypted/`") |
| `wols` 1.4.0 (Python) `parse_compact_url` | Succeeds, same result as unsigned | Yes (`params['sig']`) | `malformed` ("URL doesn't start with wemush://v1/encrypted/") |
| Platform `parseWOLSUrl` | Succeeds (`valid: true`) | Yes (`signature`, `raw`) | — |

Goal 3 holds for parsing and resolving: both 1.4.0 libraries decode a signed compact URL exactly as the unsigned one. "Ignore the signature" holds for decoding, but a 1.4.0 **verifier** returns `malformed`, not `unsigned`. That is safe, because it is never `valid`, but an application that shows `malformed` as an alarm will alarm. That is the reason for the readers-before-writers order in section 8.

The `web+wemush://` form is parsed by Python and rejected by TypeScript 1.4.0, with or without a signature. That gap already exists in 1.4.0 and is another reason signed compact labels print `wemush://`.

---

## 8. Migration and version plan

The change ships as WOLS **1.5.0**, a minor release, through the [pre-release process](../GOVERNANCE.md#pre-releases).

1. **`1.5.0-rc.1`**: The specification adds, together:
   - The compact parameter and species code registries (append-only).
   - The `compact.json` parse vectors.
   - The `compact-url` signing form and its vectors.

   The 1.4.0 text says compact signing "will be defined with the compact URL conformance vectors", so they ship together.
2. **Readers first**: Release `@wemush/wols` and `wols` 1.5.0 with `verify` for `compact-url`, and `parseCompactUrl` keeping `sig`. Update the platform scanner to verify `raw` with the 1.5.0 libraries. Applications on 1.4.0 libraries should show `malformed` on a compact URL as "signature not verifiable by this app", not as tampering. That needs only a UI change, not a spec change.
3. **Final `1.5.0`**: Once one library passes every `MUST` vector, per GOVERNANCE.md.
4. **Writers second**: Start signing compact labels where section 6.3 says they fit: 60×40 mm, 3×2″, and 40×60 mm at ECC M, with a short kid. Keep signed embedded at 40 mm and above, since it carries the full data offline.
5. **20 mm and 2×1″ labels**: These stay unsigned until a print-and-scan test on real thermal stock decides between a minimal profile at ECC M and ECC L with a trimmed payload (open question 1). 300 dpi printers can sign them right away.

**Wire-format compatibility** ([GOVERNANCE.md](../GOVERNANCE.md#wire-format-compatibility)): Nothing here changes how any label decodes. Signed compact URLs decode as unsigned ones in 1.4.0 and 1.5.0. The new malformed rules apply only to verification of signed compact URLs. The one 1.4.0 rule that changes is "a URL that isn't a `wemush://v1/encrypted/` URL is `malformed` with a `sig` parameter". It narrows to exclude section 4.1 compact URLs, which 1.4.0 generators never signed.

---

## 9. Open questions

1. **Print-and-scan test for 20 mm and 2×1″**: Does v8 at 3.02 dots (ECC L, or ECC M with a minimal profile) scan reliably on worn thermal stock? Test with phone cameras and the station scanner. Does v9 or v10 at 2.6 to 2.8 dots scan at all? The answer decides whether 1.5 recommends a minimal signed-compact profile for small labels.
2. **Decimal signature encoding**: Is a second, numeric-mode token encoding (155 digits, about 19 bytes smaller with mixed-mode encoders and 69 bytes larger without) worth it if open question 1 shows that one version matters? This proposal says no for 1.5.
3. **Extension parameters**: How are non-registry parameters such as `td` named, for example an `x-` prefix or an organization prefix, so that a future registry name can't collide with an existing signed extension?
4. **HTTPS resolver form**: The roadmap's HTTPS form (`https://{host}/wols/v1/{id}?…`) could be defined as `https://{host}/wols/` + the exact bytes after `wemush://`. Then the signature is host-independent, and the unwrap step is a prefix swap. Browsers normalize some characters (WHATWG URL query percent-encoding), so it would need a stricter character set for signed URLs. Should it be decided in 1.5 with this proposal or later?
5. **Unwrap for encrypted URLs**: Should `unwrapWolsUrl` also apply before encrypted URL verification? The verifier wouldn't change, because unwrap is a pre-step, but the advice would.
6. **Minimal profile**: Should 1.5 define a named "signed small label" parameter profile (`s`, `st`, and possibly `t`)? That depends on the stage-code decision: 3-letter codes save 9 bytes on `COLONIZATION`.
7. **Verified parameter display**: Should `params` in the verification result be a MUST? 1.4.0 makes display-what-you-verified a SHOULD.
8. **Version signaling**: The `v1` path can't signal a minor version. Does a signed compact URL need to say which registry version its codes come from? Under append-only registries this proposal says no.
9. **ID-only signed labels**: Should the compact form allow `sig` as the only parameter (`wemush://v1/{id}?sig=…`)? The rule against it was copied from the encrypted URL rules, where a URL with no other parameters can't be decrypted anyway. Allowing it gives a signed label that fits v8 at ECC M on a 20 mm QR (section 6.3) and attests only to the ID.
