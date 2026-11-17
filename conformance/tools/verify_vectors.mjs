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
import { createHash, createPrivateKey, createPublicKey, sign as edSign, verify as edVerify } from 'node:crypto';
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
    if (st.generation !== undefined) {
      // A JSON integer is read as its decimal string, with a warning (1.4.0, SHOULD).
      const numeric = Number.isSafeInteger(st.generation);
      if (numeric) warnings.push('strain.generation');
      if (!GENERATION.test(numeric ? String(st.generation) : st.generation)) errors.push('strain.generation');
    }
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

// --- Decoding ---------------------------------------------------------------
// Decoders read a JSON integer `strain.generation` as its decimal string (1.4.0, SHOULD).
function decoded(s) {
  const st = s?.strain;
  if (st === null || typeof st !== 'object' || !Number.isSafeInteger(st.generation)) return s;
  return { ...s, strain: { ...st, generation: String(st.generation) } };
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
  // `sig` is reserved: preserved as received, never verified.
  const result = { success: true, plaintext, specimen: decoded(specimen) };
  if (q.has('sig')) Object.assign(result, { sig: q.get('sig'), sigVerified: false });
  return result;
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
  return { success: true, specimen: decoded(out) };
}

// --- Signatures (1.4.0) -----------------------------------------------------
// Ed25519 through node:crypto (OpenSSL), keys imported as JWK from raw bytes.
const ENCRYPTED_PREFIX = 'wemush://v1/encrypted/';
const KID = /^[A-Za-z0-9_-]{1,64}$/;
const SIG = /^[A-Za-z0-9_-]{86}$/;
class Malformed extends Error {}

function jcs(v) {
  if (v === null || typeof v === 'boolean') return JSON.stringify(v);
  if (typeof v === 'number') {
    if (!Number.isFinite(v)) throw new Malformed('non-finite number');
    return JSON.stringify(v); // Number::toString; -0 becomes "0"
  }
  if (typeof v === 'string') {
    if (!v.isWellFormed()) throw new Malformed('lone surrogate');
    return JSON.stringify(v); // escapes exactly what RFC 8785 escapes
  }
  if (Array.isArray(v)) return `[${v.map(jcs).join(',')}]`;
  // Array.prototype.sort compares UTF-16 code units, as RFC 8785 requires.
  const keys = Object.keys(v).sort();
  return `{${keys.map((k) => `${jcs(k)}:${jcs(v[k])}`).join(',')}}`;
}

function signingInput(form, kid, body) {
  return Buffer.concat([Buffer.from(`WOLS-SIG-v1\n${form}\n${kid}\n`, 'ascii'), Buffer.from(body, 'utf8')]);
}

function parseToken(tok) {
  if (typeof tok !== 'string') throw new Malformed('not a string');
  const parts = tok.split('.');
  if (parts.length !== 2 || !KID.test(parts[0]) || !SIG.test(parts[1])) throw new Malformed('bad token');
  const raw = Buffer.from(parts[1], 'base64url');
  if (raw.length !== 64 || raw.toString('base64url') !== parts[1]) throw new Malformed('non-canonical');
  return { kid: parts[0], raw };
}

const pubKey = (b64) => createPublicKey({ key: { kty: 'OKP', crv: 'Ed25519', x: b64 }, format: 'jwk' });

function check(kid, raw, message, store) {
  if (!Object.hasOwn(store, kid)) return 'unknown-kid';
  const entry = store[kid];
  // An unusable entry is a configuration error: the kid was found, so the result is invalid.
  if (entry.alg !== 'Ed25519' || Buffer.from(entry.publicKeyBase64url, 'base64url').length !== 32) return 'invalid';
  try {
    return edVerify(null, message, pubKey(entry.publicKeyBase64url), raw) ? 'valid' : 'invalid';
  } catch {
    return 'invalid'; // the key doesn't decode to a point
  }
}

// Parse label text as an I-JSON object: JSON.parse, then reject duplicate member names (which
// JSON.parse silently collapses), lone surrogates, and numbers that overflowed to Infinity.
function parseIJsonObject(text) {
  let label;
  try { label = JSON.parse(text); } catch { throw new Malformed('not JSON'); }
  if (label === null || typeof label !== 'object' || Array.isArray(label)) throw new Malformed('not an object');
  // The text is valid JSON here, so a small scanner can find object member names.
  const stack = [];
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch === '{') stack.push({ keys: new Set(), expectKey: true });
    else if (ch === '[') stack.push(null);
    else if (ch === '}' || ch === ']') stack.pop();
    else if (ch === ',') { if (stack.at(-1)) stack.at(-1).expectKey = true; }
    else if (ch === ':') stack.at(-1).expectKey = false;
    else if (ch === '"') {
      let j = i + 1;
      while (text[j] !== '"') j += text[j] === '\\' ? 2 : 1;
      const top = stack.at(-1);
      if (top && top.expectKey) {
        const name = JSON.parse(text.slice(i, j + 1));
        if (top.keys.has(name)) throw new Malformed('duplicate member name');
        top.keys.add(name);
      }
      i = j;
    }
  }
  jcs(label); // lone surrogates, non-finite numbers
  return label;
}

const detectForm = (text) => (/^[A-Za-z][A-Za-z0-9+.-]*:/.test(text) ? 'encrypted-url' : 'embedded');

function signableUrl(url) {
  const q = url.indexOf('?');
  if (q === -1 || q === url.length - 1) return false;
  if (url.slice(q + 1).split('&').some((p) => p.split('=')[0] === 'sig')) return false;
  return /^[\x21-\x7e]*$/.test(url) && !url.includes('#') && url.startsWith(ENCRYPTED_PREFIX);
}

function verifySignature(input, store) {
  let kid, raw, message;
  try {
    if (input.form === 'embedded') {
      const label = parseIJsonObject(input.label);
      if (!Object.hasOwn(label, 'signature')) return { status: 'unsigned' };
      ({ kid, raw } = parseToken(label.signature));
      const { signature: _, ...body } = label;
      message = signingInput('embedded', kid, jcs(body));
    } else if (input.form === 'encrypted-url') {
      const url = input.url;
      const q = url.indexOf('?');
      const params = q === -1 ? [] : url.slice(q + 1).split('&');
      const names = params.map((p) => p.split('=')[0]);
      if (!names.includes('sig')) return { status: 'unsigned' };
      if (!/^[\x21-\x7e]*$/.test(url) || url.includes('#') || !url.startsWith(ENCRYPTED_PREFIX)) throw new Malformed('url');
      if (names.filter((n) => n === 'sig').length !== 1 || names.at(-1) !== 'sig' || params.length < 2 ||
          !params.at(-1).startsWith('sig=')) throw new Malformed('sig position');
      const last = params.at(-1);
      ({ kid, raw } = parseToken(last.slice(4)));
      message = signingInput('encrypted-url', kid, url.slice(0, url.length - last.length - 1));
    } else {
      throw new Malformed('unknown form');
    }
  } catch (e) {
    if (e instanceof Malformed) return { status: 'malformed' };
    throw e;
  }
  const status = check(kid, raw, message, store);
  return status === 'valid' ? { status, kid, signingInput: message.toString('utf8') } : { status };
}

function signSignature(input, keys) {
  const k = keys[input.key];
  const priv = createPrivateKey({ key: { kty: 'OKP', crv: 'Ed25519', d: k.seedBase64url, x: k.publicKeyBase64url }, format: 'jwk' });
  let message;
  if (input.form === 'embedded') {
    let parsed;
    try { parsed = parseIJsonObject(input.label); } catch (e) {
      if (e instanceof Malformed) return { refused: true };
      throw e;
    }
    const { signature: _, ...body } = parsed;
    message = signingInput('embedded', input.kid, jcs(body));
  } else {
    if (!signableUrl(input.url)) return { refused: true };
    message = signingInput('encrypted-url', input.kid, input.url);
  }
  const signature = `${input.kid}.${edSign(null, message, priv).toString('base64url')}`;
  const out = { signingInput: message.toString('utf8'), signature };
  if (input.form === 'encrypted-url') out.url = `${input.url}&sig=${signature}`;
  return out;
}

// Key set document -> trust store. Unsupported algorithms are skipped; anything wrong with the
// document's shape or with an Ed25519 entry is a configuration error (thrown).
class ConfigError extends Error {}
// RFC 8032 section 5.1.3 point decoding (OpenSSL doesn't check this when importing a key).
const P = 2n ** 255n - 19n;
const modPow = (b, e) => { let r = 1n; b %= P; for (; e > 0n; e >>= 1n, b = b * b % P) if (e & 1n) r = r * b % P; return r; };
const D = (-121665n * modPow(121666n, P - 2n) % P + P) % P;
function onCurve(bytes) {
  const n = BigInt(`0x${Buffer.from(bytes).reverse().toString('hex')}`);
  const y = n & ((1n << 255n) - 1n), sign = n >> 255n;
  if (y >= P) return false;
  const x2 = ((y * y - 1n) % P + P) % P * modPow((D * y * y + 1n) % P, P - 2n) % P;
  return x2 === 0n ? sign === 0n : modPow(x2, (P - 1n) / 2n) === 1n;
}
const isObject = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);

function loadKeySet(doc) {
  if (!isObject(doc) || !Array.isArray(doc.keys)) throw new ConfigError('not an object with a keys array');
  const store = {};
  let skipped = 0;
  for (const entry of doc.keys) {
    if (!isObject(entry) || typeof entry.alg !== 'string') throw new ConfigError('entry needs a string alg');
    if (entry.alg !== 'Ed25519') { skipped++; continue; }
    const { kid, publicKey } = entry;
    if (typeof kid !== 'string' || !KID.test(kid)) throw new ConfigError('bad kid');
    if (typeof publicKey !== 'string' || !/^[A-Za-z0-9_-]{43}$/.test(publicKey) ||
        Buffer.from(publicKey, 'base64url').toString('base64url') !== publicKey) throw new ConfigError('bad publicKey');
    if (!onCurve(Buffer.from(publicKey, 'base64url'))) throw new ConfigError('not a curve point');
    if (Object.hasOwn(store, kid)) throw new ConfigError('duplicate kid');
    store[kid] = { alg: 'Ed25519', publicKeyBase64url: publicKey };
  }
  return { store, skipped };
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
      ok = x.success ? r.success && r.plaintext === x.plaintext && eq(r.specimen, x.specimen) &&
                       (x.sig === undefined || (r.sig === x.sig && r.sigVerified === x.sigVerified))
                     : !r.success && r.reason === x.reason;
      detail = JSON.stringify({ success: r.success, reason: r.reason });
    } else if (c.operation === 'decryptFields') {
      const r = await decryptFields(c.input.specimen, c.input.secret);
      ok = x.success ? r.success && eq(r.specimen, x.specimen) : !r.success && r.reason === x.reason;
      detail = JSON.stringify({ success: r.success, reason: r.reason });
    } else if (c.operation === 'verify') {
      // A case may supply its own trust store (unusable-entry cases); otherwise use the file's.
      const r = verifySignature(c.input, c.input.trustStore ?? doc.trustStore);
      const { configError: _, ...want } = x;
      // Callers that take a single string pick the form by its URI scheme; it must agree.
      ok = eq(r, want) && detectForm(c.input.label ?? c.input.url) === c.input.form;
      detail = JSON.stringify(r.status);
    } else if (c.operation === 'sign') {
      const r = signSignature(c.input, doc.testKeys);
      ok = eq(r, x);
      if (x.refused) {
        if (ok) pass++; else { fail++; console.log(`FAIL ${file} ${c.id}: ${JSON.stringify(r)}`); }
        continue;
      }
      // A signature this verifier made must also verify.
      const back = c.input.form === 'embedded'
        ? verifySignature({ form: 'embedded', label: JSON.stringify({ ...JSON.parse(c.input.label), signature: r.signature }) }, doc.trustStore)
        : verifySignature({ form: 'encrypted-url', url: r.url }, doc.trustStore);
      ok = ok && back.status === 'valid';
      detail = JSON.stringify(r);
    } else if (c.operation === 'loadKeySet') {
      let loaded;
      try { loaded = loadKeySet(c.input.keySet); } catch (e) {
        if (!(e instanceof ConfigError)) throw e;
        loaded = null;
      }
      if (loaded === null) {
        ok = x.configError === true; detail = 'configuration error';
      } else {
        const r = verifySignature(c.input, loaded.store);
        const got = { kids: Object.keys(loaded.store).sort(), skipped: loaded.skipped, status: r.status,
          ...(r.kid ? { kid: r.kid } : {}) };
        ok = !x.configError && eq(got, x);
        detail = JSON.stringify(got);
      }
    } else {
      ok = false; detail = `unknown operation ${c.operation}`;
    }
    if (ok) pass++; else { fail++; console.log(`FAIL ${file} ${c.id}: ${detail}`); }
  }
}

// --- Interop corpora (conformance/interop) -------------------------------------
// Labels generated by real implementations from interop/matrix.json. Each one
// must decrypt here to the matrix document, with every listed passphrase.
const INTEROP = join(VECTORS, '..', 'interop');
for (const line of readFileSync(join(INTEROP, 'SHA256SUMS'), 'utf8').trim().split('\n')) {
  const [hash, name] = line.split(/\s+/);
  const actual = createHash('sha256').update(readFileSync(join(INTEROP, name))).digest('hex');
  if (actual === hash) pass++; else { fail++; console.log(`FAIL interop/SHA256SUMS ${name}`); }
}
const sortedJson = (v) => Array.isArray(v) ? `[${v.map(sortedJson).join(',')}]`
  : v !== null && typeof v === 'object'
    ? `{${Object.keys(v).sort().map((k) => `${JSON.stringify(k)}:${sortedJson(v[k])}`).join(',')}}`
    : JSON.stringify(v);
const matrix = JSON.parse(readFileSync(join(INTEROP, 'matrix.json'), 'utf8'));
const matrixHash = createHash('sha256').update(readFileSync(join(INTEROP, 'matrix.json'))).digest('hex');
for (const file of readdirSync(join(INTEROP, 'corpus')).filter((f) => f.endsWith('.json')).sort()) {
  const corpus = JSON.parse(readFileSync(join(INTEROP, 'corpus', file), 'utf8'));
  if (corpus.matrixSha256 !== matrixHash) { fail++; console.log(`FAIL interop/corpus/${file}: made from another matrix.json`); continue; }
  for (const c of matrix.cases) {
    const entry = corpus.cases[c.id];
    const expected = decoded({ ...matrix.specimens[c.specimen], id: c.specimenId });
    const secrets = c.kdf === 'raw' ? [{ keyBase64url: c.key }] : c.decryptPassphrases.map((passphrase) => ({ passphrase }));
    let ok = entry !== undefined, detail = ok ? '' : 'missing';
    for (const secret of ok ? secrets : []) {
      const r = c.form === 'url' ? await decrypt(entry.url, secret) : await decryptFields(entry.document, secret);
      if (!r.success || sortedJson(r.specimen) !== sortedJson(expected)) { ok = false; detail = JSON.stringify({ success: r.success, reason: r.reason }); }
    }
    if (ok && c.form === 'url') {
      const sig = new URLSearchParams(entry.url.split('?')[1]).get('sig');
      if (sig !== (c.sig ?? null)) { ok = false; detail = `sig ${JSON.stringify(sig)}`; }
    }
    for (const passphrase of ok ? c.rejectPassphrases ?? [] : []) {
      const r = c.form === 'url' ? await decrypt(entry.url, { passphrase }) : await decryptFields(entry.document, { passphrase });
      if (r.success || r.reason !== 'authentication-failed') { ok = false; detail = `wrong passphrase ${JSON.stringify(passphrase)} accepted`; }
    }
    if (ok) pass++; else { fail++; console.log(`FAIL interop/corpus/${file} ${c.id}: ${detail}`); }
  }
}
console.log(`${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
