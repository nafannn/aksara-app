import { normalizeResult } from '../services/result.js'

export const HISTORY_KEY = 'aksara.learning-history.v1'
export function historyTextKey(text) {
  return typeof text === 'string' ? text.normalize('NFC').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim() : ''
}
export function validHistoryResult(value) {
  const key = historyTextKey(value?.aksara)
  return value?.success === true && /[\u1B80-\u1BBF]/u.test(key) && /^[\u1B80-\u1BBF\s]+$/u.test(key) && typeof value.latin === 'string' && Boolean(value.latin.trim())
}
const base = () => globalThis.location?.href || 'http://localhost/'
const sort = (items) => items.sort((a, b) => Date.parse(b.lastLearnedAt) - Date.parse(a.lastLearnedAt) || a.id.localeCompare(b.id))
export function readHistory() {
  try {
    const raw = globalThis.localStorage.getItem(HISTORY_KEY)
    if (!raw) return { items: [], error: '' }
    const stored = JSON.parse(raw)
    if (!Array.isArray(stored)) throw new Error('invalid')
    const entries = new Map()
    let invalid = false
    for (const item of stored) {
      if (!validHistoryResult(item?.result) || !Number.isFinite(Date.parse(item?.lastLearnedAt))) { invalid = true; continue }
      const id = historyTextKey(item.result.aksara)
      const record = { id, lastLearnedAt: new Date(item.lastLearnedAt).toISOString(), source: item.source === 'demo' ? 'demo' : 'recognition', result: normalizeResult(item.result, base()) }
      if (!entries.has(id) || Date.parse(record.lastLearnedAt) > Date.parse(entries.get(id).lastLearnedAt)) entries.set(id, record)
    }
    return { items: sort([...entries.values()]), error: invalid ? 'Sebagian riwayat tidak dapat dibaca dan tidak ditampilkan.' : '' }
  } catch { return { items: [], error: 'Riwayat tidak dapat dibaca. Penyimpanan browser mungkin diblokir atau datanya rusak.' } }
}
export const getHistory = () => readHistory().items
export const getHistoryItem = (id) => getHistory().find((item) => item.id === id) || null
export function saveHistory(result, { source = 'recognition', now = new Date() } = {}) {
  if (!validHistoryResult(result)) return { saved: false, error: 'Hasil tidak valid atau belum berhasil dikenali.' }
  try {
    const id = historyTextKey(result.aksara)
    const items = getHistory()
    const previous = items.find((item) => item.id === id)
    // A demo must not overwrite a real recognition record for the same text.
    const keepReal = source === 'demo' && previous?.source === 'recognition'
    const record = { id, lastLearnedAt: now.toISOString(), source: keepReal ? 'recognition' : source === 'demo' ? 'demo' : 'recognition', result: keepReal ? previous.result : normalizeResult(result, base()) }
    globalThis.localStorage.setItem(HISTORY_KEY, JSON.stringify(sort([record, ...items.filter((item) => item.id !== id)])))
    return { saved: true, item: record, error: '' }
  } catch { return { saved: false, error: 'Riwayat belum tersimpan. Penyimpanan browser penuh atau tidak diizinkan.' } }
}
export function clearHistory() {
  try { globalThis.localStorage.removeItem(HISTORY_KEY); return { cleared: true, error: '' } }
  catch { return { cleared: false, error: 'Riwayat belum dapat dihapus. Periksa izin penyimpanan browser.' } }
}
