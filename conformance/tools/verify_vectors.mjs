#!/usr/bin/env node
/**
 * Independent check of the WOLS conformance vectors.
 *
 * Implements the minimum of SPECIFICATION.md needed to evaluate every case,
 * using only Node.js built-ins (WebCrypto). It is a cross-check for the
 * vectors, not a reference library.
 *
 * Usage: node conformance/tools/verify_vectors.mjs
 */
import { readFileSync, readdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const { subtle } = globalThis.crypto;
const VECTORS = join(dirname(fileURLToPath(import.meta.url)), '..', 'vectors');
const CONTEXT = 'https://wemush.com/wols/v1';
const TYPES = ['CULTURE', 'SPAWN', 'SUBSTRATE', 'FRUITING', 'HARVEST'];
const STAGES = ['INOCULATION', 'INCUBATION', 'COLONIZATION', 'PRIMORDIA', 'FRUITING', 'SENESCENCE', 'HARVEST'];
const ALIASES = { PINNING: 'FRUITING', FLUSH: 'FRUITING', FRUIT: 'FRUITING', FIRST_FLUSH: 'FRUITING' };
const KNOWN = new Set(['@context', '@type', 'id', 'version', 'type', 'species', 'strain', 'stage', 'created',
  'batch', 'organization', 'creator', 'custom', '_meta', 'signature']);
const GENERATION = /^(P|P\d+|F\d+|G\d+|\d+)$/;

// --- Validation -------------------------------------------------------------
function validate(s) {
  const errors = [], warnings = [];
  if (s['@context'] !== CONTEXT) errors.push('@context');
  if (s['@type'] !== 'Specimen') errors.push('@type');
  if (typeof s.id !== 'string' || !s.id.startsWith('wemush:') || s.id.length === 'wemush:'.length) errors.push('id');
  if (!TYPES.includes(s.type)) errors.push('type');
  if (typeof s.species !== 'string' || !s.species) errors.push('species');
  if (s.stage !== undefined && !STAGES.includes(s.stage)) errors.push('stage');
  const st = s.strain;
  if (st !== undefined) {
    if (typeof st?.name !== 'string') errors.push('strain.name');
    if (st.generation !== undefined && !GENERATION.test(st.generation)) errors.push('strain.generation');
    for (const k of ['clonalGeneration', 'transferDepth']) {
      if (st[k] !== undefined && !(Number.isInteger(st[k]) && st[k] >= 0)) errors.push(`strain.${k}`);
    }
    if (Number.isInteger(st.transferDepth) && Number.isInteger(st.clonalGeneration) &&
        st.transferDepth < st.clonalGeneration) warnings.push('strain.transferDepth');
  }
  for (const k of Object.keys(s)) if (!KNOWN.has(k)) warnings.push(k);
  return { valid: errors.length === 0, errors, warnings };
}

// --- Creation (type alias handling) ----------------------------------------
function create(input) {
  const upper = String(input.type).toUpperCase();
  let type = upper, stage = input.stage ?? null, warning = false;
  if (upper === 'PRIMORDIA') {
    type = 'FRUITING'; warning = true;
    if (stage === null) stage = 'PRIMORDIA';
  } else if (ALIASES[upper]) {
    type = ALIASES[upper];
  }
  return { type, stage, warning };
}

// --- Encrypted format -------------------------------------------------------
const fromB64url = (v) => Buffer.from(v.replace(/-/g, '+').replace(/_/g, '/'), 'base64');
const MIN_ITERATIONS = 10_000, MAX_ITERATIONS = 10_000_000;
const IDENTIFYING = ['@context', '@type', 'id', 'version', 'type', 'species'];

async function deriveKey(passphrase, salt, iterations) {
  const material = await subtle.importKey('raw', new TextEncoder().encode(passphrase.normalize('NFC')), 'PBKDF2', false, ['deriveBits']);
  return new Uint8Array(await subtle.deriveBits({ name: 'PBKDF2', hash: 'SHA-256', salt, iterations }, material, 256));
}

async function decrypt(url, secret) {
  const m = /^wemush:\/\/v1\/encrypted\/([^?]+)\?(.*)$/.exec(url);
  if (!m) return { success: false, reason: 'invalid-url' };
  const [, rawId, query] = m;
  let id;
  try {
    // decodeURIComponent throws on malformed escapes and on invalid UTF-8.
    id = decodeURIComponent(rawId);
  } catch {
    return { success: false, reason: 'invalid-encoding' };
  }
  if (!id) return { success: false, reason: 'invalid-url' };
  const q = new URLSearchParams(query);
  const kdf = q.get('kdf');
  if (q.get('e') && !kdf) return { success: false, reason: 'legacy-format' };
  if (!q.get('e') || !q.get('iv')) return { success: false, reason: 'missing-parameter' };
  let keyBytes;
  if (kdf === 'pbkdf2') {
    if (!q.get('salt') || !q.get('i')) return { success: false, reason: 'missing-parameter' };
    if (!/^[0-9]+$/.test(q.get('i'))) return { success: false, reason: 'invalid-parameter' };
    const iterations = Number(q.get('i'));
    if (iterations < MIN_ITERATIONS) return { success: false, reason: 'insufficient-iterations' };
    if (iterations > MAX_ITERATIONS) return { success: false, reason: 'excessive-iterations' };
    keyBytes = await deriveKey(secret.passphrase, fromB64url(q.get('salt')), iterations);
  } else if (kdf === 'raw') {
    if (q.has('salt') || q.has('i')) return { success: false, reason: 'unexpected-parameter' };
    keyBytes = fromB64url(secret.keyBase64url);
    if (keyBytes.length !== 32) return { success: false, reason: 'invalid-key' };
  } else {
    return { success: false, reason: 'unsupported-kdf' };
  }
  const key = await subtle.importKey('raw', keyBytes, 'AES-GCM', false, ['decrypt']);
  let plaintext;
  try {
    const buf = new Uint8Array(await subtle.decrypt({ name: 'AES-GCM', iv: fromB64url(q.get('iv')) }, key, fromB64url(q.get('e'))));
    if (buf[0] === 0xef && buf[1] === 0xbb && buf[2] === 0xbf) return { success: false, reason: 'invalid-plaintext' };
    plaintext = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(buf);
  } catch {
    return { success: false, reason: 'authentication-failed' };
  }
  let specimen;
  try {
    specimen = JSON.parse(plaintext);
  } catch {
    return { success: false, reason: 'invalid-plaintext' };
  }
  if (specimen.id !== `wemush:${id}`) return { success: false, reason: 'id-mismatch' };
  return { success: true, plaintext, specimen };
}

// --- Field-level encryption -------------------------------------------------
const isEncrypted = (v) => v !== null && typeof v === 'object' && v.encrypted === true;

async function decryptFields(label, secret) {
  if (IDENTIFYING.some((k) => isEncrypted(label[k]))) return { success: false, reason: 'identifying-field' };
  const fields = Object.keys(label).filter((k) => isEncrypted(label[k]));
  // Total cost check before any derivation: sum iterations over distinct (salt, iterations) pairs.
  const derivations = new Map();
  for (const k of fields) {
    const o = label[k];
    if (o.kdf === 'pbkdf2') derivations.set(`${o.salt}:${o.iterations}`, o);
  }
  let total = 0;
  for (const o of derivations.values()) {
    if (!Number.isInteger(o.iterations) || o.iterations < MIN_ITERATIONS) return { success: false, reason: 'insufficient-iterations' };
    total += o.iterations;
  }
  if (total > MAX_ITERATIONS) return { success: false, reason: 'excessive-iterations' };
  const out = { ...label };
  for (const k of fields) {
    const o = label[k];
    let keyBytes;
    if (o.kdf === 'pbkdf2') keyBytes = await deriveKey(secret.passphrase, fromB64url(o.salt), o.iterations);
    else if (o.kdf === 'raw') keyBytes = fromB64url(secret.keyBase64url);
    else return { success: false, reason: 'unsupported-kdf' };
    const key = await subtle.importKey('raw', keyBytes, 'AES-GCM', false, ['decrypt']);
    try {
      const buf = await subtle.decrypt({
        name: 'AES-GCM', iv: fromB64url(o.iv),
        additionalData: new TextEncoder().encode(`${label.id}\n${k}`),
      }, key, fromB64url(o.payload));
      out[k] = JSON.parse(new TextDecoder().decode(buf));
    } catch {
      return { success: false, reason: 'authentication-failed' };
    }
  }
  return { success: true, specimen: out };
}

// --- Runner -----------------------------------------------------------------
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);
let pass = 0, fail = 0;

// Check SHA256SUMS first, so a stale or edited vector file is reported.
for (const line of readFileSync(join(VECTORS, 'SHA256SUMS'), 'utf8').trim().split('\n')) {
  const [hash, name] = line.split(/\s+/);
  const actual = createHash('sha256').update(readFileSync(join(VECTORS, name))).digest('hex');
  if (actual === hash) pass++; else { fail++; console.log(`FAIL SHA256SUMS ${name}`); }
}

for (const file of readdirSync(VECTORS).filter((f) => f.endsWith('.json')).sort()) {
  const doc = JSON.parse(readFileSync(join(VECTORS, file), 'utf8'));
  for (const c of doc.cases) {
    let ok, detail = '';
    const x = c.expected;
    if (c.operation === 'validate') {
      const r = validate(c.input);
      ok = r.valid === x.valid &&
        (!x.errorField || r.errors.includes(x.errorField)) &&
        (!x.warningField || r.warnings.includes(x.warningField));
      detail = JSON.stringify(r);
    } else if (c.operation === 'create') {
      const r = create(c.input);
      ok = eq(r, x);
      detail = JSON.stringify(r);
    } else if (c.operation === 'derive') {
      const k = await deriveKey(c.input.passphrase, fromB64url(c.input.saltBase64url), c.input.iterations);
      ok = Buffer.from(k).toString('base64url') === x.keyBase64url;
    } else if (c.operation === 'decrypt') {
      const r = await decrypt(c.input.url, c.input.secret);
      ok = x.success ? r.success && r.plaintext === x.plaintext && eq(r.specimen, x.specimen)
                     : !r.success && r.reason === x.reason;
      detail = JSON.stringify({ success: r.success, reason: r.reason });
    } else if (c.operation === 'decryptFields') {
      const r = await decryptFields(c.input.specimen, c.input.secret);
      ok = x.success ? r.success && eq(r.specimen, x.specimen) : !r.success && r.reason === x.reason;
      detail = JSON.stringify({ success: r.success, reason: r.reason });
    } else {
      ok = false; detail = `unknown operation ${c.operation}`;
    }
    if (ok) pass++; else { fail++; console.log(`FAIL ${file} ${c.id}: ${detail}`); }
  }
}
console.log(`${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
