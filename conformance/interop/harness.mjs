#!/usr/bin/env node
/**
 * WOLS cross-library round-trip harness (TypeScript/JavaScript side).
 *
 * Generates a corpus of encrypted labels from `matrix.json` with an installed
 * `@wemush/wols`, and verifies a corpus produced by any implementation
 * (normally the Python `wols` package) by decrypting it with `@wemush/wols`.
 *
 * Usage:
 *
 *   node harness.mjs generate matrix.json corpus.json
 *   node harness.mjs verify matrix.json corpus.json
 *
 * `@wemush/wols` is resolved from this file's location (copy the file next to
 * a node_modules that has the package), or from WOLS_JS_MODULE if set.
 * `verify` exits non-zero if any case fails, or if a case listed in the
 * matrix's `expectedFailures` unexpectedly passes.
 *
 * The canonical copy is `conformance/interop/` in the WOLS specification
 * repository. wemush/specimen-labels-js and wemush/specimen-labels-py carry
 * byte-identical copies in `tests/interop/`. It uses only the public
 * `@wemush/wols` API, so it also runs against a published release.
 */

import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const DECODER = 'typescript';
const IDENTIFYING = ['@context', '@type', 'id', 'version', 'type', 'species'];

// RFC 3986 pchar minus pct-encoded: unreserved / sub-delims / ":" / "@".
const PCHAR_RE = /^(?:[A-Za-z0-9\-._~!$&'()*+,;=:@]|%[0-9A-Fa-f]{2})*$/;
// Characters a generator MUST percent-encode (SPECIFICATION.md 1.3.0).
// eslint-disable-next-line no-control-regex
const MUST_ENCODE_RE = /[%/?# +\x00-\x1f\x7f]|[^\x00-\x7f]/;
const B64URL_RE = /^[A-Za-z0-9_-]*$/;
// Query parameters of the encrypted URL (SPECIFICATION.md, Wire format).
const URL_PARAMS = new Set(['e', 'iv', 'kdf', 'salt', 'i', 'sig']);
// Spaces, controls and non-ASCII characters must be percent-encoded.
const PRINTABLE_ASCII_RE = /^[\x21-\x7e]*$/;

class CheckError extends Error {
  constructor(message) {
    super(message);
    this.name = 'CheckError';
  }
}

function check(condition, message) {
  if (!condition) throw new CheckError(message);
}

/** Key-sorted JSON, so documents compare independently of member order. */
function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (value !== null && typeof value === 'object') {
    const keys = Object.keys(value).sort();
    return `{${keys.map(k => `${JSON.stringify(k)}:${canonical(value[k])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

function sameDoc(actual, expected) {
  return typeof actual === 'object' && actual !== null && canonical(actual) === canonical(expected);
}

function b64urlDecode(value) {
  return new Uint8Array(Buffer.from(value, 'base64url'));
}

function canonicalB64url(name, value) {
  check(typeof value === 'string', `${name} must be a string`);
  check(B64URL_RE.test(value), `${name} must be base64url without padding`);
  const raw = b64urlDecode(value);
  check(
    Buffer.from(raw).toString('base64url') === value,
    `${name} is not canonical base64url (non-zero trailing bits)`
  );
  return raw;
}

/** Strict UTF-8 percent-decoding; '+' is literal. */
function percentDecode(name, value) {
  try {
    return decodeURIComponent(value);
  } catch {
    throw new CheckError(`${name} ${JSON.stringify(value)} is not valid UTF-8 percent-encoding`);
  }
}

export function loadJson(path) {
  return JSON.parse(readFileSync(path, 'utf8'));
}

export function matrixSha256(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex');
}

/**
 * The document for a case: `specimens[name]` with `id` set to `specimenId`.
 * `name` defaults to the case's input `specimen`.
 */
export function expectedDocument(matrix, c, name = c.specimen) {
  const template = matrix.specimens[name];
  const doc = {};
  for (const [key, value] of Object.entries(template)) {
    doc[key] = structuredClone(value);
    if (key === '@type') doc.id = c.specimenId;
  }
  if (!('id' in doc)) doc.id = c.specimenId;
  return doc;
}

/**
 * What a decoder must return (`expectSpecimen`, else the input), and, for a
 * `legacyPlaintext` case, the input document that a 1.3.0 generator wrote
 * unchanged and that is also accepted on the wire.
 */
function expectations(matrix, c) {
  const expected = expectedDocument(matrix, c, c.expectSpecimen ?? c.specimen);
  const legacy = c.legacyPlaintext ? expectedDocument(matrix, c) : undefined;
  return { expected, legacy };
}

/** Match `value` against the expected value, then the legacy one. */
function matchWritten(value, expected, legacy) {
  if (canonical(value) === canonical(expected)) return 'current';
  if (legacy !== undefined && canonical(value) === canonical(legacy)) return 'legacy';
  return undefined;
}

function secretFor(c, passphrase) {
  if (c.kdf === 'raw') return b64urlDecode(c.key);
  return passphrase ?? c.passphrase;
}

function withIterations(c, options) {
  if (c.iterations !== undefined) options.iterations = c.iterations;
  return options;
}

// =============================================================================
// GENERATE
// =============================================================================

export async function generateCase(wols, matrix, c) {
  const doc = expectedDocument(matrix, c);
  const key = secretFor(c);
  if (c.form === 'url') {
    const enc = await wols.encryptSpecimen(doc, withIterations(c, { key }));
    let url = enc.url;
    if (c.sig !== undefined) url = wols.toEncryptedUrl({ ...enc, signature: c.sig });
    return { url };
  }
  if (c.form === 'fields') {
    const document = await wols.encryptFields(doc, withIterations(c, { key, fields: c.fields }));
    return { document };
  }
  throw new Error(`unknown form ${c.form}`);
}

export async function generate(wols, matrix, matrixHash, version) {
  const cases = {};
  for (const c of matrix.cases) cases[c.id] = await generateCase(wols, matrix, c);
  return {
    corpusVersion: 1,
    matrixVersion: matrix.matrixVersion,
    matrixSha256: matrixHash,
    generator: { implementation: '@wemush/wols', language: 'typescript', version },
    cases,
  };
}

// =============================================================================
// VERIFY
// =============================================================================

function checkKdfParams(c, salt, iterations, saltName, iName) {
  if (c.kdf === 'pbkdf2') {
    check(canonicalB64url(saltName, salt).length >= 16, 'salt under 16 bytes');
    let n = iterations;
    if (typeof n === 'string') {
      check(
        /^[1-9][0-9]*$/.test(n),
        `${iName} ${JSON.stringify(n)} must be decimal digits without a leading zero`
      );
      n = Number(n);
    }
    check(
      typeof n === 'number' && Number.isInteger(n) && n === c.expectIterations,
      `${iName} is ${JSON.stringify(iterations)}, expected ${c.expectIterations}`
    );
  } else {
    check(salt === undefined, `${saltName} must be omitted for kdf=raw`);
    check(iterations === undefined, `${iName} must be omitted for kdf=raw`);
  }
}

function checkUrlWire(c, url) {
  const prefix = 'wemush://v1/encrypted/';
  check(url.startsWith(prefix), `URL must start with ${prefix}`);
  const rest = url.slice(prefix.length);
  check(!rest.includes('#'), 'URL must not contain a fragment');
  const q = rest.indexOf('?');
  check(q !== -1, 'URL has no query');
  const segment = rest.slice(0, q);
  const query = rest.slice(q + 1);
  check(
    PCHAR_RE.test(segment),
    `ID path segment ${JSON.stringify(segment)} is not a valid RFC 3986 segment`
  );
  check(
    !MUST_ENCODE_RE.test(segment.replace(/%[0-9A-Fa-f]{2}/g, '')),
    `ID path segment ${JSON.stringify(segment)} leaves a character unencoded that MUST be encoded`
  );
  const suffix = c.specimenId.slice('wemush:'.length);
  check(
    percentDecode('ID path segment', segment) === suffix,
    `ID path segment ${JSON.stringify(segment)} does not percent-decode to ${JSON.stringify(suffix)}`
  );
  if (c.expectPathSegment !== undefined) {
    check(
      segment === c.expectPathSegment,
      `ID path segment ${JSON.stringify(segment)} != expected ${JSON.stringify(c.expectPathSegment)}`
    );
  }
  check(
    PRINTABLE_ASCII_RE.test(query),
    'URL query must be printable ASCII (spaces, controls and non-ASCII must be percent-encoded)'
  );

  const params = new Map();
  for (const pair of query.split('&')) {
    const eq = pair.indexOf('=');
    const key = eq === -1 ? pair : pair.slice(0, eq);
    check(URL_PARAMS.has(key), `unknown parameter ${JSON.stringify(key)}`);
    check(!params.has(key), `duplicate parameter ${key}`);
    params.set(key, eq === -1 ? '' : pair.slice(eq + 1));
  }
  check(params.get('kdf') === c.kdf, `kdf must be ${c.kdf}`);
  check(canonicalB64url('e', params.get('e')).length >= 16, 'e is shorter than the tag');
  check(canonicalB64url('iv', params.get('iv')).length === 12, 'iv must be 12 bytes');
  checkKdfParams(c, params.get('salt'), params.get('i'), 'salt', 'i');
  check(
    params.has('sig') === (c.sig !== undefined),
    c.sig === undefined ? 'unexpected sig parameter' : 'sig parameter missing'
  );
  if (c.sig !== undefined) {
    // The raw query value, percent-decoded ('+' literal), must be the input.
    const sig = percentDecode('sig', params.get('sig'));
    check(
      sig === c.sig,
      `sig parameter ${JSON.stringify(params.get('sig'))} decodes to ${JSON.stringify(sig)}, ` +
        `expected ${JSON.stringify(c.sig)}`
    );
  }
}

function unwrap(result, what) {
  if (!result.success) {
    throw new CheckError(`${what}: ${result.error.reason}: ${result.error.message}`);
  }
  return result.data;
}

function expectAuthFailure(result, what) {
  check(!result.success, `${what}: decryption unexpectedly succeeded`);
  check(
    result.error.reason === 'authentication-failed',
    `${what}: expected authentication-failed, got ${result.error.reason}`
  );
}

/** @returns {Promise<boolean>} whether the label carried legacy plaintext */
async function verifyUrl(wols, c, { expected, legacy }, url) {
  check(typeof url === 'string', 'corpus entry has no url');
  checkUrlWire(c, url);

  const parsed = unwrap(wols.parseEncryptedUrl(url), 'parseEncryptedUrl');
  check(parsed.id === c.specimenId, `parsed id ${JSON.stringify(parsed.id)}`);
  check(parsed.kdf === c.kdf, 'parsed kdf differs');
  check(
    parsed.signature === c.sig,
    `sig not preserved: got ${JSON.stringify(parsed.signature)}, expected ${JSON.stringify(c.sig)}`
  );
  if (c.kdf === 'pbkdf2') check(parsed.iterations === c.expectIterations, 'iterations');

  const passphrases = c.decryptPassphrases ?? [undefined];
  let written;
  for (const passphrase of passphrases) {
    const text = unwrap(
      await wols.decryptPlaintext(url, { key: secretFor(c, passphrase) }),
      `decryptPlaintext (passphrase=${JSON.stringify(passphrase)})`
    );
    const plaintext = JSON.parse(text);
    written = typeof plaintext === 'object' ? matchWritten(plaintext, expected, legacy) : undefined;
    check(
      written !== undefined,
      `decrypted document differs (passphrase=${JSON.stringify(passphrase)}): ${text}`
    );
  }
  const specimen = unwrap(
    await wols.decryptSpecimen(url, { key: secretFor(c, passphrases[0]) }),
    'decryptSpecimen'
  );
  check(specimen.id === c.specimenId, 'decryptSpecimen id differs');
  check(specimen.species === expected.species, 'decryptSpecimen species differs');
  if (expected.strain?.generation !== undefined) {
    check(
      specimen.strain?.generation === expected.strain.generation,
      `decryptSpecimen strain.generation is ${JSON.stringify(specimen.strain?.generation)}, ` +
        `expected ${JSON.stringify(expected.strain.generation)}`
    );
  }

  for (const wrong of c.rejectPassphrases ?? []) {
    expectAuthFailure(
      await wols.decryptPlaintext(url, { key: wrong }),
      `passphrase ${JSON.stringify(wrong)}`
    );
  }
  return written === 'legacy';
}

/** @returns {Promise<boolean>} whether the label carried legacy plaintext */
async function verifyFields(wols, c, { expected, legacy }, doc) {
  check(typeof doc === 'object' && doc !== null, 'corpus entry has no document');
  check(
    canonical(Object.keys(doc).sort()) === canonical(Object.keys(expected).sort()),
    `document keys differ: ${Object.keys(doc).sort().join(',')}`
  );
  let sawLegacy = false;
  const written = (value, key, what) => {
    const match = matchWritten(value, expected[key], legacy?.[key]);
    check(match !== undefined, what);
    if (match === 'legacy') sawLegacy = true;
  };
  const ivs = new Set();
  const allowed = new Set(['encrypted', 'algorithm', 'payload', 'iv', 'kdf', 'salt', 'iterations']);
  for (const key of Object.keys(expected)) {
    if (!c.fields.includes(key)) {
      written(doc[key], key, `cleartext field ${key} changed`);
      continue;
    }
    check(!IDENTIFYING.includes(key), `identifying field ${key} encrypted`);
    const obj = doc[key];
    check(typeof obj === 'object' && obj !== null, `field ${key} is not an encryption object`);
    check(obj.encrypted === true, `${key}.encrypted must be true`);
    check(obj.algorithm === 'AES-256-GCM', `${key}.algorithm`);
    check(obj.kdf === c.kdf, `${key}.kdf must be ${c.kdf}`);
    check(canonicalB64url(`${key}.payload`, obj.payload).length >= 16, 'tag');
    check(canonicalB64url(`${key}.iv`, obj.iv).length === 12, 'iv length');
    check(!ivs.has(obj.iv), `${key}.iv reused across fields`);
    ivs.add(obj.iv);
    checkKdfParams(c, obj.salt, obj.iterations, `${key}.salt`, `${key}.iterations`);
    const extra = Object.keys(obj).filter(k => !allowed.has(k));
    check(extra.length === 0, `${key} has unexpected members ${extra.join(',')}`);
  }

  for (const passphrase of c.decryptPassphrases ?? [undefined]) {
    const options = { key: secretFor(c, passphrase) };
    // decryptField must return each value exactly as encrypted ...
    for (const field of c.fields) {
      const value = unwrap(
        await wols.decryptField(doc[field], options, { id: doc.id, field }),
        `decryptField(${field})`
      );
      written(value, field, `decryptField(${field}) differs: ${JSON.stringify(value)}`);
    }
    // ... and decryptFields restores and validates the whole label, which
    // must equal expectSpecimen even when the label carries legacy values.
    const restored = unwrap(
      await wols.decryptFields(doc, options),
      `decryptFields (passphrase=${JSON.stringify(passphrase)})`
    );
    check(
      sameDoc(restored, expected),
      `restored document differs (passphrase=${JSON.stringify(passphrase)}): ${JSON.stringify(restored)}`
    );
  }
  for (const wrong of c.rejectPassphrases ?? []) {
    expectAuthFailure(
      await wols.decryptFields(doc, { key: wrong }),
      `passphrase ${JSON.stringify(wrong)}`
    );
  }
  return sawLegacy;
}

function expectedFailure(matrix, caseId, generator) {
  return (matrix.expectedFailures ?? []).find(
    e =>
      e.case === caseId &&
      (e.generator ?? generator) === generator &&
      (e.decoder ?? DECODER) === DECODER
  );
}

/**
 * `legacy` is true when a `legacyPlaintext` case's label carried the input
 * unchanged (as a 1.3.0 generator wrote it) and decoded to `expectSpecimen`.
 *
 * @returns {Promise<{caseId: string, status: 'pass'|'fail'|'xfail'|'xpass', detail: string, legacy: boolean}[]>}
 */
export async function verify(wols, matrix, corpus) {
  const generator = corpus.generator.language;
  const results = [];
  for (const c of matrix.cases) {
    const entry = corpus.cases[c.id];
    let ok = true;
    let detail = '';
    let legacy = false;
    try {
      check(entry !== undefined, 'case missing from corpus');
      const exp = expectations(matrix, c);
      legacy =
        c.form === 'url'
          ? await verifyUrl(wols, c, exp, entry.url)
          : await verifyFields(wols, c, exp, entry.document);
    } catch (err) {
      ok = false;
      detail =
        err instanceof CheckError ? `${err.name}: ${err.message}` : String(err?.stack ?? err);
    }
    const xfail = expectedFailure(matrix, c.id, generator);
    let status;
    if (xfail === undefined) {
      status = ok ? 'pass' : 'fail';
    } else if (ok) {
      status = 'xpass';
      detail = `listed in expectedFailures but passed: ${xfail.reason}`;
    } else {
      status = 'xfail';
      detail = `${xfail.reason} (${xfail.reference}): ${detail}`;
    }
    if (ok && legacy && status === 'pass') {
      detail =
        'legacy plaintext (the input unchanged, as 1.3.0 wrote it) decoded to expectSpecimen';
    }
    results.push({ caseId: c.id, status, detail, legacy: ok && legacy });
  }
  return results;
}

export function summarize(corpus, results, decoderVersion) {
  const gen = corpus.generator;
  const lines = [
    `interop: ${gen.implementation} ${gen.version} (${gen.language}) -> @wemush/wols ${decoderVersion} (typescript)`,
  ];
  for (const r of results) {
    lines.push(`  ${r.status.toUpperCase().padEnd(5)} ${r.caseId}`);
    if (r.status !== 'pass' || r.legacy) lines.push(`        ${r.detail}`);
  }
  const count = s => results.filter(r => r.status === s).length;
  lines.push(
    `interop: ${results.length} cases: ${count('pass')} pass, ${count('fail')} fail, ` +
      `${count('xfail')} xfail, ${count('xpass')} xpass, ` +
      `${results.filter(r => r.legacy).length} legacy`
  );
  return { text: lines.join('\n'), failed: count('fail') + count('xpass') > 0 };
}

/** Version of the resolved @wemush/wols package (its package.json, found by walking up). */
function packageVersion(entryUrl) {
  let dir = dirname(fileURLToPath(entryUrl));
  for (;;) {
    const candidate = join(dir, 'package.json');
    if (existsSync(candidate)) {
      const pkg = JSON.parse(readFileSync(candidate, 'utf8'));
      if (pkg.name === '@wemush/wols') return pkg.version;
    }
    const parent = dirname(dir);
    if (parent === dir) return 'unknown';
    dir = parent;
  }
}

async function main(argv) {
  const [command, matrixPath, corpusPath] = argv;
  if (argv.length !== 3 || !['generate', 'verify'].includes(command)) {
    process.stderr.write('usage: node harness.mjs generate|verify matrix.json corpus.json\n');
    return 2;
  }
  const specifier = process.env.WOLS_JS_MODULE
    ? pathToFileURL(process.env.WOLS_JS_MODULE).href
    : import.meta.resolve('@wemush/wols');
  const wols = await import(specifier);
  const version = packageVersion(specifier);
  const matrix = loadJson(matrixPath);
  if (command === 'generate') {
    const corpus = await generate(wols, matrix, matrixSha256(matrixPath), version);
    writeFileSync(corpusPath, JSON.stringify(corpus, null, 2) + '\n');
    process.stdout.write(
      `interop: wrote ${Object.keys(corpus.cases).length} cases to ${corpusPath}\n`
    );
    return 0;
  }
  const corpus = loadJson(corpusPath);
  const { text, failed } = summarize(corpus, await verify(wols, matrix, corpus), version);
  process.stdout.write(text + '\n');
  return failed ? 1 : 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exitCode = await main(process.argv.slice(2));
}
