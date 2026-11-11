import Button from './Button'
import { useState } from 'react'
import { ScanHeader } from './GuidedCamera'
import { getHistoryItem, readHistory } from '../lib/history'
import './HistoryPage.css'

export default function HistoryPage({ onBack, onScan, onSelect }) {
  const [snapshot] = useState(readHistory)
  const [error, setError] = useState('')
  function select(id) {
    const item = getHistoryItem(id)
    if (item) onSelect(item)
    else setError('Entri ini tidak tersedia lagi. Kembali ke Home, lalu buka riwayat kembali.')
  }
  return <main className="home-shell scan-flow history-page">
    <ScanHeader title="Riwayat Belajar" onBack={onBack} />
    <div className="history-banner"><p className="section-label">Jejak Pembelajaran</p><h2>Setiap aksara punya cerita.</h2><span className="sundanese" lang="su" aria-hidden="true">ᮞᮥᮔ᮪ᮓ</span></div>
    {(snapshot.error || error) && <p role="alert" className="capture-error">{error || snapshot.error}</p>}
    {snapshot.items.length ? <>
      <h2 className="history-heading">Yang Pernah Kamu Temui</h2>
      <p className="scan-intro">Buka kembali hasil scan untuk mengingat cara membaca dan maknanya.</p>
      <ul className="history-list">{snapshot.items.map((item) => <li key={item.id}><button className="history-card" onClick={() => select(item.id)}>
        <span className="history-card-content"><span className="sundanese history-script" lang="su">{item.result.aksara}</span><strong>{item.result.latin}</strong><span className="history-date">Terakhir dipelajari: <time dateTime={item.lastLearnedAt}>{new Intl.DateTimeFormat('id-ID', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(item.lastLearnedAt))}</time></span>{item.source === 'demo' && <span className="history-demo">Contoh demo</span>}</span><span className="history-chevron" aria-hidden="true">›</span>
      </button></li>)}</ul>
      <p className="scan-note">Tulisan yang sama digabung dalam satu entri. Riwayat tersimpan hanya di browser ini.</p>
    </> : <div className="history-empty"><span aria-hidden="true">✧</span><h2>Belum Ada Riwayat Belajar</h2><p>Mulai pindai Aksara Sunda untuk menyimpan hasil pembelajaranmu di sini.</p><Button variant="primary" onClick={onScan}>Mulai Scan</Button></div>}
  </main>
}


