import Button from './Button'
import { useEffect, useRef, useState } from 'react'
import { cameraMessages, cameraProblem, capturePhoto, createCameraSession } from '../lib/camera'
import './ScanFlow.css'

export function ScanHeader({ title, onBack }) {
  const heading = useRef(null)
  useEffect(() => { heading.current?.focus() }, [])
  return <header className="scan-header"><button type="button" className="scan-back" onClick={onBack} aria-label="Kembali">‹</button><h1 tabIndex={-1} ref={heading}>{title}</h1><span aria-hidden="true">✧</span></header>
}

export default function GuidedCamera({ onBack, onCapture }) {
  const videoRef = useRef(null)
  const [attempt, setAttempt] = useState(0)
  const [status, setStatus] = useState('starting')
  const [error, setError] = useState('')
  const [captureError, setCaptureError] = useState('')
  const secure = window.isSecureContext
  const supported = Boolean(navigator.mediaDevices?.getUserMedia)

  useEffect(() => {
    if (!secure || !supported) return
    let active = true
    const session = createCameraSession({
      video: videoRef.current,
      mediaDevices: navigator.mediaDevices,
      onEnded: () => { session.stop(); setError('Kamera terputus. Pastikan kamera tersedia, lalu coba lagi.'); setStatus('error') },
    })
    session.start().then((started) => { if (active && started) setStatus('ready') }).catch((reason) => {
      session.stop()
      if (active) { setError(cameraProblem(reason)); setStatus('error') }
    })
    const suspend = () => { session.stop(); if (active) { setStatus('error'); setError('Kamera dihentikan saat halaman ditinggalkan. Tekan Coba Lagi untuk melanjutkan.') } }
    const visibility = () => { if (document.hidden) suspend() }
    window.addEventListener('pagehide', suspend)
    document.addEventListener('visibilitychange', visibility)
    return () => {
      active = false
      session.stop()
      window.removeEventListener('pagehide', suspend)
      document.removeEventListener('visibilitychange', visibility)
    }
  }, [attempt, secure, supported])

  const problem = !secure ? cameraMessages.insecure : !supported ? cameraMessages.unsupported : status === 'error' ? error : ''

  function retry() { setError(''); setCaptureError(''); setStatus('starting'); setAttempt((value) => value + 1) }
  function capture() {
    try { onCapture(capturePhoto(videoRef.current, document.createElement('canvas'))) }
    catch (reason) { setCaptureError(reason.message) }
  }

  return <main className="home-shell scan-flow">
    <ScanHeader title="Scan Aksara" onBack={onBack} />
    <p className="scan-intro" id="camera-instruction">Posisikan tulisan Aksara Sunda di dalam bingkai.</p>
    <div className="camera-stage">
      <video ref={videoRef} autoPlay muted playsInline aria-label="Pratinjau kamera langsung" />
      {!problem && <>
        <div className="camera-guide" aria-hidden="true"><i /><i /><i /><i />{status === 'ready' && <span className="camera-sweep-track"><span className="camera-sweep-line" /></span>}</div>
        <p className="camera-hint">Pastikan seluruh tulisan Aksara Sunda terlihat jelas dan tidak terpotong</p>
      </>}
      {status === 'starting' && !problem && <p className="camera-wait" role="status">Menunggu izin dan membuka kamera…</p>}
      {problem && <div className="camera-problem" role="alert"><span aria-hidden="true">✧</span><h2>Kamera belum tersedia</h2><p>{problem}</p>{secure && supported && <Button variant="primary" onClick={retry}>Coba Lagi</Button>}</div>}
    </div>
    <div className="capture-controls"><button type="button" className="shutter-button" aria-label="Ambil foto Aksara Sunda" aria-describedby="camera-instruction" disabled={status !== 'ready' || Boolean(problem)} onClick={capture}><span /></button><span>Ambil Foto</span></div>
    {captureError && <p className="capture-error" role="alert">{captureError}</p>}
    <p className="scan-note">Bingkai hanya panduan posisi, bukan deteksi otomatis.</p>
  </main>
}




