import Button from './Button'
import { useState } from 'react'
import { saveHistory } from '../lib/history'
import { ScanHeader } from './GuidedCamera'
import CharacterLearning from './CharacterLearning'
import PronunciationPlayer from './PronunciationPlayer'
import { normalizeResult } from '../services/result'
import './ResultPage.css'

export default function ResultPage({ data, isDemo = false, allowDemoSave = false, onBack, onScanAgain }) {
  const [saveMessage, setSaveMessage] = useState('')
  function saveDemo() {
    const outcome = saveHistory(data, { source: 'demo' })
    setSaveMessage(outcome.saved ? 'Contoh demo tersimpan di Riwayat Belajar.' : outcome.error)
  }
  const result = normalizeResult(data, window.location.href)
  return <main className="home-shell scan-flow result-page">
    <ScanHeader title="Hasil Pemindaian" onBack={onBack} />
    {isDemo && <aside className="demo-notice"><strong>Contoh Pembelajaran · Bandung</strong><p>Data contoh untuk mencoba tampilan. Ini bukan hasil pembacaan foto kamu.</p></aside>}
    {!result.success && <p className="capture-error" role="alert">Hasil pengenalan belum tersedia. Kamu dapat memindai ulang.</p>}
    <section className="result-card" aria-label="Tulisan dan makna">
      <p className="result-label section-label">Aksara Sunda</p>
      <div className="result-script sundanese" lang="su">{result.aksara || 'Aksara belum tersedia'}</div>
      <p className="result-label section-label">Transliterasi Latin</p>
      <h2 className="result-latin">{result.latin || 'Bacaan belum tersedia'}</h2>
      <div className="result-divider" aria-hidden="true"><span />✧<span /></div>
      <h3 className="meaning-label section-label">Makna</h3><p className="result-meaning">{result.meaning || 'Makna belum tersedia dalam kamus.'}</p>
      <PronunciationPlayer source={result.audio_url} />
    </section>
    {isDemo && allowDemoSave && <div><Button variant="tertiary" onClick={saveDemo}>Simpan Contoh Demo ke Riwayat</Button><p className="history-save-status" role="status">{saveMessage}</p></div>}
    <CharacterLearning characters={result.character_details} />
    <Button variant="primary" className="result-scan" onClick={onScanAgain}>↻ &nbsp; Scan Ulang</Button>
    <p className="scan-note">Satu tulisan, satu langkah mengenal budaya.</p>
  </main>
}



