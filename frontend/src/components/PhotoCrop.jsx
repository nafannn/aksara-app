import { useEffect, useRef, useState } from 'react'
import { ScanHeader } from './GuidedCamera'
import { adjustCrop, cropPhoto, fullCrop } from '../lib/photo'

const corners = [['nw', 'kiri atas'], ['ne', 'kanan atas'], ['sw', 'kiri bawah'], ['se', 'kanan bawah']]

export default function PhotoCrop({ original, initialCrop, onCancel, onDone }) {
  const [rect, setRect] = useState(initialCrop || { x: .08, y: .25, width: .84, height: .5 })
  const [ready, setReady] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const surface = useRef(null)
  const drag = useRef(null)
  const alive = useRef(true)
  const pending = useRef(false)
  useEffect(() => { alive.current = true; return () => { alive.current = false; drag.current = null } }, [])

  function cancel() { alive.current = false; onCancel() }
  function start(event) {
    const mode = event.currentTarget.dataset.mode
    if (!ready || busy || (event.pointerType === 'mouse' && event.button !== 0)) return
    event.preventDefault()
    const bounds = surface.current.getBoundingClientRect()
    drag.current = { id: event.pointerId, x: event.clientX, y: event.clientY, rect, mode, bounds }
    event.currentTarget.setPointerCapture(event.pointerId)
  }
  function move(event) {
    const gesture = drag.current
    if (!gesture || gesture.id !== event.pointerId) return
    setRect(adjustCrop(gesture.rect, gesture.mode, (event.clientX - gesture.x) / gesture.bounds.width, (event.clientY - gesture.y) / gesture.bounds.height))
  }
  function keyboard(event) {
    const mode = event.currentTarget.dataset.mode
    const directions = { ArrowLeft: [-.01, 0], ArrowRight: [.01, 0], ArrowUp: [0, -.01], ArrowDown: [0, .01] }
    if (!directions[event.key] || busy || !ready) return
    event.preventDefault()
    const [x, y] = directions[event.key]
    setRect((current) => adjustCrop(current, mode, x, y))
  }

  async function finish() {
    if (pending.current) return
    pending.current = true
    setBusy(true); setError('')
    try {
      const image = await cropPhoto(original, rect)
      if (alive.current) onDone(image, rect)
    } catch (reason) { if (alive.current) setError(reason.message || 'Crop gagal. Coba pilih area kembali.') }
    finally { pending.current = false; if (alive.current) setBusy(false) }
  }

  return <main className="home-shell scan-flow">
    <ScanHeader title="Crop Foto" onBack={cancel} />
    <h2 className="preview-heading">Fokuskan pada aksara</h2>
    <p className="scan-intro" id="crop-help">Geser area pilihan dan tarik sudutnya untuk memilih satu baris aksara. Tombol panah pada keyboard juga dapat digunakan.</p>
    <div className="crop-stage"><div className="crop-surface" ref={surface}>
      {original && <img src={original} alt="Foto asli untuk dipotong" draggable={false} onLoad={() => setReady(true)} onError={() => { setReady(false); setError('Foto tidak dapat dibuka. Kembali dan ambil ulang foto.') }} />}
      {ready && <div className="crop-selection" style={{ left: `${rect.x * 100}%`, top: `${rect.y * 100}%`, width: `${rect.width * 100}%`, height: `${rect.height * 100}%` }}>
        <button type="button" className="crop-mover" aria-label="Geser area crop" aria-describedby="crop-help" disabled={busy} data-mode="move" onPointerDown={start} onPointerMove={move} onPointerUp={() => { drag.current = null }} onPointerCancel={() => { drag.current = null }} onLostPointerCapture={() => { drag.current = null }} onKeyDown={keyboard} />
        {corners.map(([mode, label]) => <button key={mode} type="button" className={`crop-handle ${mode}`} aria-label={`Ubah sudut ${label}`} disabled={busy} data-mode={mode} onPointerDown={start} onPointerMove={move} onPointerUp={() => { drag.current = null }} onPointerCancel={() => { drag.current = null }} onLostPointerCapture={() => { drag.current = null }} onKeyDown={keyboard} />)}
      </div>}
    </div></div>
    {(!original || error) && <p role="alert" className="capture-error">{error || 'Foto belum tersedia. Kembali dan ambil foto terlebih dahulu.'}</p>}
    <p className="scan-note">Crop selalu memakai foto asli; hasil tidak diregangkan atau diperkecil.</p>
    <button className="scan-action" disabled={!ready || busy} onClick={finish}>{busy ? 'Menyimpan Crop…' : 'Selesai Crop'}</button>
    <button className="scan-action secondary" disabled={busy || !ready} onClick={() => setRect({ ...fullCrop })}>Reset Area Crop</button>
    <button className="scan-action secondary" onClick={cancel}>Batalkan</button>
  </main>
}


