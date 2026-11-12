import { useState } from 'react'
import './App.css'
import Button from './components/Button'
import aksaraLogo from './assets/logo-aksara.png'
import GuidedCamera from './components/GuidedCamera'
import PhotoPreview from './components/PhotoPreview'
import PhotoCrop from './components/PhotoCrop'
import ResultPage from './components/ResultPage'
import HistoryPage from './components/HistoryPage'
import { bandungDemo } from './data/resultMock'
import { photoFile } from './lib/photo'
import { recognizePhoto } from './services/recognition'
import ProcessingPage from './components/ProcessingPage'

function Icon({ name, ...props }) {
  const paths = {
    scan: <><path d="M8 3H5a2 2 0 0 0-2 2v3m13-5h3a2 2 0 0 1 2 2v3M3 16v3a2 2 0 0 0 2 2h3m8 0h3a2 2 0 0 0 2-2v-3" /><path d="M7 12h10" /></>,
    discover: <><circle cx="10.5" cy="10.5" r="6.5" /><path d="m15.1 15.1 5.4 5.4" /></>,
    learn: <><path d="M12 6C9.5 4.3 6 4 2.5 5v15C6 19 9.5 19.3 12 21c2.5-1.7 6-2 9.5-1V5C18 4 14.5 4.3 12 6Zm0 0v15" /><path d="M6 8.5c1.1-.1 2.2.1 3 .5m-3 3c1.1-.1 2.2.1 3 .5m6-3.5c.8-.4 1.9-.6 3-.5m-3 4c.8-.4 1.9-.6 3-.5" /></>,
    history: <><path d="M3 10a9 9 0 1 1 2.6 8.4M3 4v6h6" /><path d="M12 7v5l3 2" /></>,
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
  const [historyRecord, setHistoryRecord] = useState(null)
  const [recognitionResult, setRecognitionResult] = useState(null)
  const [recognitionError, setRecognitionError] = useState('')
  const [recognizing, setRecognizing] = useState(false)

  function clearPhoto() { setPhoto(null); setCroppedPhoto(null); setCrop(null) }
  function goHome() { clearPhoto(); setPage('home') }
  function retake() { clearPhoto(); setPage('camera') }
  async function recognizeSelectedPhoto(file) {
    setRecognitionError('')
    setRecognizing(true)
    setPage('processing')
    try {
      const endpoint = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000/api/recognize'
      const result = await recognizePhoto(file, { endpoint })
      setRecognitionResult(result)
      setPage('result')
    } catch (error) {
      setRecognitionError(error instanceof Error ? error.message : 'Foto belum berhasil diproses.')
      setPage('preview')
    } finally {
      setRecognizing(false)
    }
  }
  function usePhoto() { recognizeSelectedPhoto(photoFile(croppedPhoto || photo)) }

  if (page === 'camera') return <GuidedCamera onBack={goHome} onCapture={(image) => { clearPhoto(); setPhoto(image); setPage('preview') }} />
  if (page === 'crop') return <PhotoCrop original={photo} initialCrop={crop} onCancel={() => setPage('preview')} onDone={(image, area) => { setCroppedPhoto(image); setCrop(area); setPage('preview') }} />
  if (page === 'preview') return <PhotoPreview key={croppedPhoto || photo || 'empty'} image={croppedPhoto || photo} cropped={Boolean(croppedPhoto)} onCrop={() => setPage('crop')} onReset={() => { setCroppedPhoto(null); setCrop(null) }} onUse={usePhoto} onRetake={retake} error={recognitionError} />
  if (page === 'processing') return <ProcessingPage error={recognitionError} recognizing={recognizing} onBack={() => setPage('preview')} />

  if (page === 'result' && recognitionResult) return <ResultPage data={recognitionResult} onBack={goHome} onScanAgain={retake} />

  if (page === 'result-demo') return <ResultPage data={bandungDemo} isDemo allowDemoSave onBack={() => setPage('ready')} onScanAgain={retake} />

  if (page === 'history') return <HistoryPage onBack={() => setPage('home')} onScan={retake} onSelect={(record) => { setHistoryRecord(record); setPage('history-result') }} />
  if (page === 'history-result' && historyRecord) return <ResultPage key={historyRecord.id} data={historyRecord.result} isDemo={historyRecord.source === 'demo'} onBack={() => setPage('history')} onScanAgain={retake} />

  return (
    <main className="home-shell">
      <header className="brand-row">
        <a className="brand" href="./" aria-label="AKSARA, halaman utama">
          <img className="brand-logo" src={aksaraLogo} alt="" width="66" height="44" />
          <span>AKSARA</span>
        </a>
        <button className="icon-button" aria-label="Buka riwayat belajar" title="Riwayat belajar" onClick={() => setPage('history')}>
          <Icon name="history" />
        </button>
      </header>

      <section className="hero" aria-labelledby="hero-title">
        <div className="corner-lines" aria-hidden="true" />
        <div className="hero-leaf" aria-hidden="true" />
        <div className="hero-diamond" aria-hidden="true" />
        <div className="hero-content">
          <p className="eyebrow section-label">Warisan Aksara Sunda</p>
          <span className="gold-rule" aria-hidden="true" />
          <h1 id="hero-title">Kenali Aksara,<br /><em>Temukan Maknanya.</em></h1>
          <p className="hero-description">Setiap tulisan menyimpan cerita. Temukan, pindai, dan pelajari Aksara Sunda yang kamu jumpai.</p>
          <div className="hero-art">
            <span className="sundanese" lang="su" aria-label="Sunda dalam Aksara Sunda">ᮞᮥᮔ᮪ᮓ</span>
            <span className="sparkle" aria-hidden="true">✧</span>
          </div>
          <div className="ornament" aria-hidden="true"><span />✥<span /></div>
          <Button className="home-start" onClick={() => setPage('camera')}>
            <Icon name="scan" /><span>Mulai Scan</span><Icon name="arrow" />
          </Button>
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


    </main>
  )
}

export default App









