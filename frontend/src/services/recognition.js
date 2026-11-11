import { saveHistory } from '../lib/history.js'
import { normalizeResult } from './result.js'

// Inactive until explicitly called with the endpoint agreed with the Flask team.
// Proposed multipart field: image. No mock fallback for failed real requests.
export async function recognizePhoto(file, { endpoint, signal } = {}) {
  if (!(file instanceof Blob) || !file.size) throw new Error('Pilih foto yang valid terlebih dahulu.')
  if (!endpoint) throw new Error('Layanan pengenalan belum dikonfigurasi.')
  const body = new FormData()
  body.append('image', file, file.name || 'aksara.jpg')
  const response = await fetch(endpoint, { method: 'POST', body, signal })
  if (!response.ok) throw new Error('Server belum dapat memproses foto. Silakan coba lagi.')
  let data
  try { data = await response.json() } catch { throw new Error('Format jawaban server belum dapat dibaca.') }
  const result = normalizeResult(data, response.url || new URL(endpoint, window.location.href).href)
  if (!result.success || !result.aksara) throw new Error('Aksara belum berhasil dikenali. Coba foto yang lebih jelas.')
  saveHistory(result)
  return result
}


