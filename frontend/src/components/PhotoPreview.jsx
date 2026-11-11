import { useState } from 'react'
import { ScanHeader } from './GuidedCamera'

export default function PhotoPreview({ image, cropped, onCrop, onReset, onUse, onRetake }) {
  const [error, setError] = useState('')
  const [loaded, setLoaded] = useState(false)
  return <main className="home-shell scan-flow">
    <ScanHeader title="Tinjau Foto" onBack={onRetake} />
    <h2 className="preview-heading">Sudah terlihat jelas?</h2>
    <p className="scan-intro">Pastikan tulisan Aksara Sunda tampak utuh dan tidak buram.</p>
    {image && <img className="captured-photo" src={image} alt={cropped ? 'Hasil crop foto Aksara Sunda' : 'Foto Aksara Sunda yang baru diambil'} onLoad={() => { setLoaded(true); setError('') }} onError={() => { setLoaded(false); setError('Foto tidak dapat ditampilkan. Silakan ambil ulang.') }} />}
    {(!image || error) && <p role="alert" className="capture-error">{error || 'Belum ada foto. Silakan ambil foto terlebih dahulu.'}</p>}
    <div className="preview-notice"><p>{cropped ? 'Area crop sudah diterapkan. Kamu dapat menyesuaikannya lagi dari foto asli.' : 'Jika ada banyak elemen lain, gunakan Crop Foto untuk memilih area aksara. Crop bersifat opsional.'}</p></div>
    <button className="scan-action" disabled={!loaded} onClick={() => { try { onUse() } catch (reason) { setError(reason.message) } }}>Gunakan Foto</button>
    <button className="scan-action secondary" disabled={!loaded} onClick={onCrop}>Crop Foto</button>
    <button className="scan-action secondary" onClick={onRetake}>Ambil Ulang</button>
    {cropped && <button className="scan-action secondary" onClick={onReset}>Kembalikan Foto Asli</button>}
  </main>
}
