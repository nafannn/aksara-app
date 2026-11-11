import { useRef, useState } from 'react'
import './App.css'
import GuidedCamera from './components/GuidedCamera'
import PhotoPreview from './components/PhotoPreview'
import PhotoCrop from './components/PhotoCrop'
import PhotoReady from './components/PhotoReady'
import { photoFile } from './lib/photo'

function Icon({ name, ...props }) {
  const paths = {
    scan: <><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="3" /></>,
    discover: <><path d="m12 3 3 6 6 3-6 3-3 6-3-6-6-3 6-3Z" /><path d="M12 8v8M8 12h8" /></>,
    learn: <><path d="M4 4h16v16H4zM7 8h10M7 12h10M7 16h10" /></>,
    history: <><path d="M4 10a8 8 0 1 1 1 8M4 4v6h6" /><path d="M12 7v5l3 2" /></>,
    arrow: <path d="M5 12h14m-6-6 6 6-6 6" />,
  }
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>{paths[name]}</svg>
}

const steps = [
  { icon: 'discover', title: 'Temukan', text: 'Lihat aksara di sekitarmu' },
  { icon: 'scan', title: 'Pindai', text: 'Ambil foto tulisannya' },
  { icon: 'learn', title: 'Pelajari', text: 'Kenali bunyi & makna' },
]

function App() {
  const [page, setPage] = useState('home')
  const [photo, setPhoto] = useState(null)
  const [croppedPhoto, setCroppedPhoto] = useState(null)
  const [crop, setCrop] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const dialog = useRef(null)
  const [panel, setPanel] = useState('scan')

  function clearPhoto() { setPhoto(null); setCroppedPhoto(null); setCrop(null); setSelectedFile(null) }
  function goHome() { clearPhoto(); setPage('home') }
  function retake() { clearPhoto(); setPage('camera') }
  function usePhoto() { setSelectedFile(photoFile(croppedPhoto || photo)); setPage('ready') }

  if (page === 'camera') return <GuidedCamera onBack={goHome} onCapture={(image) => { clearPhoto(); setPhoto(image); setPage('preview') }} />
  if (page === 'crop') return <PhotoCrop original={photo} initialCrop={crop} onCancel={() => setPage('preview')} onDone={(image, area) => { setCroppedPhoto(image); setCrop(area); setSelectedFile(null); setPage('preview') }} />
  if (page === 'preview') return <PhotoPreview key={croppedPhoto || photo || 'empty'} image={croppedPhoto || photo} cropped={Boolean(croppedPhoto)} onCrop={() => setPage('crop')} onReset={() => { setCroppedPhoto(null); setCrop(null); setSelectedFile(null) }} onUse={usePhoto} onRetake={retake} />
  if (page === 'ready') return <PhotoReady file={selectedFile} onBack={() => setPage('preview')} onHome={goHome} />

  function openPanel(nextPanel) {
    setPanel(nextPanel)
    dialog.current.showModal()
  }

  return (
    <main className="home-shell">
      <header className="brand-row">
        <a className="brand" href="./" aria-label="AKSARA, halaman utama">
          <span className="brand-mark" aria-hidden="true">✦</span>
          <span>AKSARA</span>
        </a>
        <button className="icon-button" aria-label="Buka riwayat belajar" title="Riwayat belajar" onClick={() => openPanel('history')}>
          <Icon name="history" />
        </button>
      </header>

      <section className="hero" aria-labelledby="hero-title">
        <div className="corner-lines" aria-hidden="true" />
        <div className="hero-leaf" aria-hidden="true" />
        <div className="hero-diamond" aria-hidden="true" />
        <div className="hero-content">
          <p className="eyebrow">Warisan Aksara Sunda</p>
          <span className="gold-rule" aria-hidden="true" />
          <h1 id="hero-title">Kenali Aksara,<br /><em>Temukan Maknanya.</em></h1>
          <p className="hero-description">Setiap tulisan menyimpan cerita. Temukan, pindai, dan pelajari Aksara Sunda yang kamu jumpai.</p>
          <div className="hero-art">
            <span className="sundanese" lang="su" aria-label="Sunda dalam Aksara Sunda">ᮞᮥᮔ᮪ᮓ</span>
            <span className="sparkle" aria-hidden="true">✧</span>
          </div>
          <div className="ornament" aria-hidden="true"><span />✥<span /></div>
          <button className="scan-button" onClick={() => setPage('camera')}>
            <Icon name="scan" /><span>Mulai Scan</span><Icon name="arrow" />
          </button>
        </div>
      </section>

      <section className="guide" aria-labelledby="guide-title">
        <div className="section-heading">
          <h2 id="guide-title">Bagaimana Caranya?</h2>
          <span aria-hidden="true">❧</span>
        </div>
        <ol className="steps">
          {steps.map((step) => <li className="step" key={step.title}>
            <span className="step-icon"><Icon name={step.icon} /></span>
            <h3>{step.title}</h3>
            <p>{step.text}</p>
          </li>)}
        </ol>
      </section>
      <footer className="home-footer"><span aria-hidden="true">✧</span><p>Satu tulisan, satu langkah mengenal budaya.</p><span aria-hidden="true">✧</span></footer>

      <dialog ref={dialog} className="info-dialog" aria-labelledby="dialog-title" onClick={(event) => { if (event.target === event.currentTarget) dialog.current.close() }}>
        <span className="dialog-symbol" aria-hidden="true">✦</span>
        <h2 id="dialog-title">{panel === 'scan' ? 'Mulai dari satu tulisan' : 'Riwayat Belajar'}</h2>
        <p>{panel === 'scan' ? 'Halaman pengambilan foto akan hadir di tahap berikutnya. Siapkan foto satu baris Aksara Sunda dengan tulisan yang jelas.' : 'Belum ada riwayat belajar. Fitur ini akan tersedia setelah pemindaian terhubung.'}</p>
        <form method="dialog"><button className="close-button">Kembali ke Home</button></form>
      </dialog>
    </main>
  )
}

export default App


