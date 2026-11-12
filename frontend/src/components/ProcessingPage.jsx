import { ScanHeader } from './GuidedCamera'
import './ScanFlow.css'

export default function ProcessingPage({ error, recognizing, onBack }) {
  return <main className="home-shell scan-flow processing-page">
    <ScanHeader title="Memproses" onBack={onBack} />
    {error ? <section className="processing-error" role="alert">
      <h2 className="preview-heading">Pemindaian Gagal</h2>
      <p className="scan-intro">{error}</p>
    </section> : <section className="processing-state" aria-live="polite">
      <div className="processing-ring" aria-hidden="true"><span>ᮞ</span></div>
      <h2 className="preview-heading">Sedang Mengenali<br />Aksara...</h2>
      <p className="scan-intro">Gambar sedang diproses untuk mengenali tulisan Aksara Sunda.</p>
      <div className="processing-line"><span /></div>
      <span className="processing-label">{recognizing ? 'Memproses gambar' : 'Menyiapkan hasil'}</span>
    </section>}
  </main>
}
