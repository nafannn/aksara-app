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
  return {
    success: data.success === true,
    aksara: text(data.aksara), latin: text(data.latin), meaning: text(data.meaning),
    audio_url: safeAudioUrl(data.audio_url, baseUrl),
    character_details: Array.isArray(data.character_details) ? data.character_details.filter((item) => item && typeof item === 'object').map((item) => ({ aksara: text(item.aksara), reading: text(item.reading), category: text(item.category), explanation: text(item.explanation) })) : [],
  }
}
