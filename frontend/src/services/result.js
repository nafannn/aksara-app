/**
 * Proposed Flask response schema; must be agreed with the backend team.
 * @typedef {Object} ScanResult
 * @property {boolean} success
 * @property {string|null} aksara
 * @property {string|null} latin
 * @property {string|null} meaning
 * @property {string|null} audio_url
 * @property {Array<{aksara: string|null, reading: string|null, category: string|null, explanation: string|null}>} character_details
 */
const text = (value) => typeof value === 'string' && value.trim() ? value.trim() : null

// Server hanya boleh menandai asal makna dengan nilai yang dikenal; nilai lain
// diabaikan supaya UI tidak pernah menampilkan tebakan seolah makna pasti.
const MEANING_SOURCES = new Set(['kamus', 'mirip', 'terjemahan', 'bacaan'])

// Di bawah ambang ini bacaan dianggap belum layak dipercaya. Pada data asli,
// confidence bacaan benar ~0,97 dan bacaan salah ~0,72 (lihat docs/dataset-notes.md).
export const MIN_CONFIDENCE = 0.8

export function safeAudioUrl(value, baseUrl) {
  if (!text(value)) return null
  try {
    const url = new URL(value, baseUrl)
    return ['http:', 'https:'].includes(url.protocol) ? url.href : null
  } catch { return null }
}

/** @returns {ScanResult} */
export function normalizeResult(value, baseUrl = 'http://localhost/') {
  const data = value && typeof value === 'object' ? value : {}
  const success = data.success === true || ['ok', 'not_found'].includes(data.status)
  const rawCharacters = Array.isArray(data.character_details) ? data.character_details : data.chars
  const characterDetails = Array.isArray(rawCharacters)
    ? rawCharacters.filter((item) => item && typeof item === 'object').map((item) => ({
      aksara: text(item.aksara ?? item.glyph),
      reading: text(item.reading ?? item.latin),
      category: text(item.category),
      explanation: text(item.explanation ?? item.note),
    }))
    : []
  const confidence = typeof data.confidence === 'number' && Number.isFinite(data.confidence)
    ? Math.min(1, Math.max(0, data.confidence)) : null
  return {
    success,
    aksara: text(data.aksara), latin: text(data.latin), meaning: text(data.meaning),
    meaning_source: MEANING_SOURCES.has(data.meaning_source) ? data.meaning_source : null,
    matched_latin: text(data.matched_latin),
    confidence,
    // Bacaan berkeyakinan rendah tetap ditampilkan, tetapi ditandai agar tidak
    // terbaca sebagai hasil yang pasti.
    uncertain: success && confidence !== null && confidence < MIN_CONFIDENCE,
    audio_url: safeAudioUrl(data.audio_url, baseUrl),
    character_details: characterDetails,
  }
}
