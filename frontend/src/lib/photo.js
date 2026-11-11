const clamp = (value, low, high) => Math.min(high, Math.max(low, value))
export const fullCrop = { x: 0, y: 0, width: 1, height: 1 }

export function adjustCrop(rect, mode, dx, dy) {
  if (mode === 'move') return { ...rect, x: clamp(rect.x + dx, 0, 1 - rect.width), y: clamp(rect.y + dy, 0, 1 - rect.height) }
  let left = rect.x, top = rect.y, right = rect.x + rect.width, bottom = rect.y + rect.height
  if (mode.includes('w')) left = clamp(left + dx, 0, right - .02)
  if (mode.includes('e')) right = clamp(right + dx, left + .02, 1)
  if (mode.includes('n')) top = clamp(top + dy, 0, bottom - .02)
  if (mode.includes('s')) bottom = clamp(bottom + dy, top + .02, 1)
  return { x: left, y: top, width: right - left, height: bottom - top }
}

export function cropPixels(rect, width, height) {
  if (!width || !height || !Object.values(rect).every(Number.isFinite) || rect.width <= 0 || rect.height <= 0 || rect.x < 0 || rect.y < 0 || rect.x + rect.width > 1.000001 || rect.y + rect.height > 1.000001) throw new Error('Area crop tidak valid. Pilih kembali area tulisan.')
  const x = Math.min(width - 1, Math.round(rect.x * width))
  const y = Math.min(height - 1, Math.round(rect.y * height))
  return { x, y, width: Math.max(1, Math.min(width, Math.round((rect.x + rect.width) * width)) - x), height: Math.max(1, Math.min(height, Math.round((rect.y + rect.height) * height)) - y) }
}

export function loadPhoto(source) {
  return new Promise((resolve, reject) => {
    if (!source) return reject(new Error('Foto belum tersedia. Silakan ambil foto kembali.'))
    const image = new Image()
    image.onload = () => { image.onload = image.onerror = null; resolve(image) }
    image.onerror = () => { image.onload = image.onerror = null; reject(new Error('Foto tidak dapat dibuka. Silakan ambil ulang.')) }
    image.src = source
  })
}

export async function cropPhoto(source, rect) {
  const image = await loadPhoto(source)
  const area = cropPixels(rect, image.naturalWidth, image.naturalHeight)
  const canvas = document.createElement('canvas')
  try {
    canvas.width = area.width
    canvas.height = area.height
    const context = canvas.getContext('2d')
    if (!context) throw new Error('Editor foto tidak tersedia pada browser ini.')
    context.drawImage(image, area.x, area.y, area.width, area.height, 0, 0, area.width, area.height)
    // PNG avoids another lossy encode after camera capture; native pixels stay intact.
    return canvas.toDataURL('image/png')
  } finally { canvas.width = canvas.height = 0 }
}

export function photoFile(source) {
  const match = /^data:(image\/(?:jpeg|png));base64,(.+)$/.exec(source || '')
  if (!match) throw new Error('Foto belum siap digunakan. Silakan ambil ulang.')
  const bytes = Uint8Array.from(atob(match[2]), (character) => character.charCodeAt(0))
  if (!bytes.length) throw new Error('Foto kosong. Silakan ambil ulang.')
  return new File([bytes], `aksara.${match[1] === 'image/png' ? 'png' : 'jpg'}`, { type: match[1] })
}
