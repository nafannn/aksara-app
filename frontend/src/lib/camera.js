export const cameraMessages = {
  insecure: 'Kamera memerlukan koneksi aman. Buka melalui localhost di laptop atau HTTPS di HP. Alamat HTTP Network tidak mendukung kamera.',
  unsupported: 'Browser ini belum mendukung kamera. Coba Chrome, Edge, atau Safari versi terbaru.',
  NotAllowedError: 'Izin kamera ditolak. Izinkan kamera pada pengaturan situs di browser, lalu coba lagi.',
  NotFoundError: 'Kamera tidak ditemukan. Sambungkan atau aktifkan kamera, lalu coba lagi.',
  NotReadableError: 'Kamera tidak dapat digunakan. Tutup aplikasi lain yang memakai kamera, lalu coba lagi.',
  AbortError: 'Kamera terputus saat dibuka. Silakan coba lagi.',
  default: 'Kamera belum dapat dibuka. Periksa kamera dan izin browser, lalu coba lagi.',
}

export function cameraProblem(error) {
  return cameraMessages[error?.name] || cameraMessages.default
}

// Each session owns its stream, including streams resolved after the page is left.
export function createCameraSession({ video, mediaDevices, onEnded }) {
  let stream
  let disposed = false
  const stopTracks = (value) => value?.getTracks().forEach((track) => track.stop())
  return {
    async start() {
      stream = await mediaDevices.getUserMedia({ audio: false, video: { facingMode: { ideal: 'environment' }, width: { ideal: 1920 }, height: { ideal: 1080 } } })
      if (disposed) { stopTracks(stream); return false }
      stream.getVideoTracks().forEach((track) => track.addEventListener('ended', () => { if (!disposed) onEnded() }))
      video.srcObject = stream
      try { await video.play() } catch (error) { stopTracks(stream); throw error }
      return !disposed
    },
    stop() {
      disposed = true
      stopTracks(stream)
      video.srcObject = null
    },
  }
}

export function capturePhoto(video, canvas) {
  if (video.readyState < 2 || !video.videoWidth || !video.videoHeight) throw new Error('Kamera belum siap. Tunggu sebentar, lalu coba lagi.')
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  const context = canvas.getContext('2d')
  if (!context) throw new Error('Foto belum dapat diambil. Coba lagi atau gunakan browser lain.')
  context.drawImage(video, 0, 0, canvas.width, canvas.height)
  return canvas.toDataURL('image/jpeg', 0.9)
}
