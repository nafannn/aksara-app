import test from 'node:test'
import assert from 'node:assert/strict'
import { normalizeResult, safeAudioUrl } from './result.js'
import { recognizePhoto } from './recognition.js'

test('missing result fields produce safe defaults and retain learning units', () => {
  assert.deepEqual(normalizeResult(null), { success: false, aksara: null, latin: null, meaning: null, meaning_source: null, matched_latin: null, confidence: null, uncertain: false, audio_url: null, character_details: [] })
  const result = normalizeResult({ success: true, aksara: 'ᮘ', character_details: [null, { aksara: 'ᮘ', reading: 'ba' }] })
  assert.equal(result.character_details.length, 1)
  assert.equal(result.character_details[0].explanation, null)
  assert.equal(result.success, true)
})
test('meaning provenance is whitelisted so a guess is never shown as a dictionary fact', () => {
  const fuzzy = normalizeResult({ success: true, aksara: 'ᮘᮢᮌ᮪', meaning: 'Nama kawasan di Bandung', meaning_source: 'mirip', matched_latin: 'braga' })
  assert.equal(fuzzy.meaning_source, 'mirip')
  assert.equal(fuzzy.matched_latin, 'braga')
  assert.equal(normalizeResult({ success: true, aksara: 'ᮘ', meaning_source: 'pasti' }).meaning_source, null)
  assert.equal(normalizeResult({ success: true, aksara: 'ᮘ', matched_latin: '   ' }).matched_latin, null)
})
test('low-confidence readings are flagged instead of shown as certain', () => {
  const unsure = normalizeResult({ success: true, aksara: 'ᮨᮡᮨᮘᮡ', latin: 'bya', confidence: 0.42 })
  assert.equal(unsure.confidence, 0.42)
  assert.equal(unsure.uncertain, true)
  const sure = normalizeResult({ success: true, aksara: 'ᮠᮁᮒ', latin: 'harta', confidence: 0.97 })
  assert.equal(sure.uncertain, false)
  assert.equal(normalizeResult({ success: true, aksara: 'ᮘ', confidence: 1.7 }).confidence, 1)
  assert.equal(normalizeResult({ success: true, aksara: 'ᮘ', confidence: '0.9' }).confidence, null)
  assert.equal(normalizeResult({ success: false, confidence: 0.2 }).uncertain, false)
})
test('audio references resolve relative to backend and reject unsafe schemes', () => {
  assert.equal(safeAudioUrl('/audio/bandung.mp3', 'https://api.example.test/scan'), 'https://api.example.test/audio/bandung.mp3')
  assert.equal(safeAudioUrl('javascript:alert(1)', 'https://example.test'), null)
  assert.equal(safeAudioUrl(null), null)
})
test('API posts the image without a hardcoded multipart boundary and normalizes response', async () => {
  const oldFetch = globalThis.fetch
  globalThis.fetch = async (endpoint, options) => {
    assert.equal(endpoint, 'https://api.example.test/scan')
    assert.equal(options.method, 'POST')
    assert.equal(options.body.get('image').name, 'test.jpg')
    assert.equal(options.headers, undefined)
    return { ok: true, url: endpoint, json: async () => ({ success: true, aksara: 'ᮘ', audio_url: '/audio/ba.mp3' }) }
  }
  try {
    const result = await recognizePhoto(new File(['pixels'], 'test.jpg', { type: 'image/jpeg' }), { endpoint: 'https://api.example.test/scan' })
    assert.equal(result.audio_url, 'https://api.example.test/audio/ba.mp3')
  } finally { globalThis.fetch = oldFetch }
})
test('unconfigured and unsuccessful API never substitute demo data', async () => {
  const file = new File(['pixels'], 'test.jpg')
  await assert.rejects(recognizePhoto(file), /belum dikonfigurasi/)
  const oldFetch = globalThis.fetch
  globalThis.fetch = async () => ({ ok: false })
  try { await assert.rejects(recognizePhoto(file, { endpoint: '/scan' }), /Server/) }
  finally { globalThis.fetch = oldFetch }
})
