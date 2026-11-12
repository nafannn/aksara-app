import Button from './Button'
import { useState } from 'react'
import { ScanHeader } from './GuidedCamera'
import './PhotoPreview.css'

export default function PhotoPreview({ image, cropped, onCrop, onReset, onUse, onRetake, error: externalError = '' }) {
  const [imageError, setImageError] = useState('')
  const [loaded, setLoaded] = useState(false)
  return <main className="home-shell scan-flow">
    <ScanHeader title="Tinjau Foto" onBack={onRetake} />
    <h2 className="preview-heading">Sudah terlihat jelas?</h2>
    <p className="scan-intro">Pastikan seluruh tulisan Aksara Sunda terlihat jelas dan tidak terpotong</p>
    {image && <img className="captured-photo" src={image} alt={cropped ? 'Hasil crop foto Aksara Sunda' : 'Foto Aksara Sunda yang baru diambil'} onLoad={() => { setLoaded(true); setImageError('') }} onError={() => { setLoaded(false); setImageError('Foto tidak dapat ditampilkan. Silakan ambil ulang.') }} />}
    {(!image || imageError || externalError) && <p role="alert" className="capture-error">{externalError || imageError || 'Belum ada foto. Silakan ambil foto terlebih dahulu.'}</p>}
    {!cropped && <div className="preview-notice"><p>Jika ada bagian foto yang tidak diperlukan, gunakan Crop Foto untuk memilih area tulisan Aksara Sunda</p></div>}
    <div className="action-stack">
      <Button variant="primary" disabled={!loaded} onClick={() => { try { onUse() } catch (reason) { setImageError(reason.message) } }}>Gunakan Foto</Button>
      <Button variant="secondary" disabled={!loaded} onClick={onCrop}>{cropped ? 'Ubah Crop' : 'Crop Foto'}</Button>
      {cropped ? <div className="preview-tertiary-actions">
        <Button variant="tertiary" fullWidth={false} onClick={onReset}>Batalkan Crop</Button>
        <span className="preview-action-divider" aria-hidden="true" />
        <Button variant="tertiary" fullWidth={false} onClick={onRetake}>Ambil Ulang</Button>
      </div> : <Button variant="tertiary" onClick={onRetake}>Ambil Ulang</Button>}
    </div>
  </main>
}
