import Button from './Button'
import { useEffect, useRef, useState } from 'react'

function SpeakerIcon() {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ flexShrink: 0 }}>
    <path d="M11 4 6 8H2v8h4l5 4V4Z" />
    <path d="M15 8a6 6 0 0 1 0 8m3-11a10 10 0 0 1 0 14" />
  </svg>
}
function AudioSource({ source }) {
  const player = useRef(null)
  const [status, setStatus] = useState('loading')
  useEffect(() => {
    const audio = new Audio()
    player.current = audio
    audio.preload = 'auto'
    const timeout = setTimeout(() => setStatus('error'), 15000)
    const ready = () => { clearTimeout(timeout); setStatus((current) => current === 'playing' ? current : 'ready') }
    const playing = () => setStatus('playing')
    const failed = () => setStatus('error')
    audio.addEventListener('canplay', ready)
    audio.addEventListener('playing', playing)
    audio.addEventListener('pause', ready)
    audio.addEventListener('ended', ready)
    audio.addEventListener('error', failed)
    audio.src = source
    audio.load()
    return () => {
      audio.removeEventListener('canplay', ready)
      audio.removeEventListener('playing', playing)
      audio.removeEventListener('pause', ready)
      audio.removeEventListener('ended', ready)
      audio.removeEventListener('error', failed)
      clearTimeout(timeout); audio.pause(); audio.removeAttribute('src'); audio.load()
      player.current = null
    }
  }, [source])
  async function toggle() {
    try {
      if (status === 'playing') player.current?.pause()
      else await player.current?.play()
    } catch { setStatus('error') }
  }
  return <div className="pronunciation">
    <Button variant="secondary" loading={status === 'loading'} loadingLabel="Memuat Audio…" disabled={status === 'error'} onClick={toggle} aria-pressed={status === 'playing'}>
      <SpeakerIcon />{status === 'loading' ? 'Memuat Audio…' : status === 'playing' ? 'Jeda Pengucapan' : 'Dengarkan Pengucapan'}
    </Button>
    <p role="status">{status === 'error' ? 'Audio tidak dapat diputar. Periksa koneksi atau coba muat ulang audio.' : status === 'loading' ? 'Menyiapkan berkas pengucapan.' : ''}</p>
    {status === 'error' && <Button variant="tertiary" onClick={() => { setStatus('loading'); player.current?.load() }}>Muat Ulang Audio</Button>}
  </div>
}

export default function PronunciationPlayer({ source }) {
  if (!source) return <div className="pronunciation"><Button variant="secondary" disabled><SpeakerIcon />Dengarkan Pengucapan</Button><p role="status">Audio pengucapan belum tersedia.</p></div>
  return <AudioSource key={source} source={source} />
}




