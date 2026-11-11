import test from 'node:test'
import assert from 'node:assert/strict'
import { HISTORY_KEY, getHistory, getHistoryItem, saveHistory, clearHistory, readHistory, historyTextKey } from './history.js'
import { bandungDemo } from '../data/resultMock.js'

function storage() {
  const values = new Map()
  globalThis.localStorage = { getItem: (key) => values.get(key) ?? null, setItem: (key, value) => values.set(key, value), removeItem: (key) => values.delete(key) }
}
test('empty history, save, reread persistence and complete result reopening', () => {
  storage()
  assert.deepEqual(getHistory(), [])
  const saved = saveHistory({ ...bandungDemo, photo: 'must not store' }, { source: 'demo' })
  assert.equal(saved.saved, true)
  const item = getHistoryItem(saved.item.id)
  assert.deepEqual(item.result, bandungDemo)
  assert.equal(item.source, 'demo')
  assert.equal(item.result.photo, undefined)
  assert.equal(JSON.parse(localStorage.getItem(HISTORY_KEY)).length, 1)
  assert.equal(clearHistory().cleared, true)
  assert.deepEqual(getHistory(), [])
})
test('normalized duplicates update timestamps and move to top', () => {
  storage()
  saveHistory(bandungDemo, { now: new Date('2026-01-01') })
  saveHistory({ ...bandungDemo, aksara: 'ᮘ' }, { now: new Date('2026-01-02') })
  saveHistory({ ...bandungDemo, aksara: `  ${bandungDemo.aksara}\u200b ` }, { now: new Date('2026-01-03') })
  assert.equal(getHistory().length, 2)
  assert.equal(getHistory()[0].id, historyTextKey(bandungDemo.aksara))
  assert.equal(getHistory()[0].lastLearnedAt, '2026-01-03T00:00:00.000Z')
})
test('failed and invalid scans never save', () => {
  storage()
  for (const result of [{ ...bandungDemo, success: false }, { ...bandungDemo, aksara: '' }, { ...bandungDemo, aksara: 'Bandung' }, { ...bandungDemo, latin: null }]) assert.equal(saveHistory(result).saved, false)
  assert.deepEqual(getHistory(), [])
})
test('malformed storage and blocked/quota failures are graceful', () => {
  storage()
  localStorage.setItem(HISTORY_KEY, '{')
  assert.deepEqual(getHistory(), [])
  assert.ok(readHistory().error)
  globalThis.localStorage = { getItem() { throw new Error('blocked') }, setItem() { throw new Error('quota') }, removeItem() { throw new Error('blocked') } }
  assert.deepEqual(getHistory(), [])
  assert.equal(saveHistory(bandungDemo).saved, false)
  assert.equal(clearHistory().cleared, false)
})
test('demo cannot replace real meaning or remove real audio reference', () => {
  storage()
  saveHistory({ ...bandungDemo, meaning: 'Verified', audio_url: 'https://example.test/audio.mp3' })
  saveHistory(bandungDemo, { source: 'demo' })
  assert.equal(getHistory()[0].result.meaning, 'Verified')
  assert.equal(getHistory()[0].result.audio_url, 'https://example.test/audio.mp3')
  assert.equal(getHistory()[0].source, 'recognition')
})
test('future API automatically persists successful recognition and ignores failed response', async () => {
  storage()
  const { recognizePhoto } = await import('../services/recognition.js')
  const oldFetch = globalThis.fetch
  const endpoint = 'https://api.example.test/scan'
  globalThis.fetch = async () => ({ ok: true, url: endpoint, json: async () => bandungDemo })
  try {
    await recognizePhoto(new File(['pixels'], 'test.jpg'), { endpoint })
    assert.equal(getHistory().length, 1)
    assert.equal(getHistory()[0].source, 'recognition')
    clearHistory()
    globalThis.fetch = async () => ({ ok: true, url: endpoint, json: async () => ({ ...bandungDemo, success: false }) })
    await assert.rejects(recognizePhoto(new File(['pixels'], 'test.jpg'), { endpoint }), /belum berhasil/)
    assert.deepEqual(getHistory(), [])
  } finally { globalThis.fetch = oldFetch }
})
