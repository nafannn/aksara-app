/**
 * Endpoint API bisa ditimpa lewat query string `?api=...` supaya demo bisa
 * berganti backend tanpa build ulang: URL tunnel Cloudflare berubah setiap
 * sesi, sedangkan build Vercel bersifat statis.
 *
 * Hanya http/https yang diterima; nilai lain jatuh ke default.
 */
const FALLBACK_ENDPOINT = 'http://127.0.0.1:5000/api/recognize'

export function resolveEndpoint(search, buildEndpoint) {
  const fallback = buildEndpoint || FALLBACK_ENDPOINT
  if (!search) return fallback
  try {
    const value = new URLSearchParams(search).get('api')
    if (!value) return fallback
    const url = new URL(value)
    return ['http:', 'https:'].includes(url.protocol) ? url.href : fallback
  } catch {
    return fallback
  }
}
