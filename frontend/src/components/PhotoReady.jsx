import Button from './Button'
import { ScanHeader } from './GuidedCamera'

export default function PhotoReady({ file, onBack, onHome, onDemo }) {
  return <main className="home-shell scan-flow">
    <ScanHeader title="Foto Siap" onBack={onBack} />
    <h2 className="preview-heading">Siap untuk langkah berikutnya</h2>
    <div className="preview-notice" role="status">{file ? <><strong>Foto pilihan sudah disiapkan.</strong><p>{file.name} · {Math.ceil(file.size / 1024)} KB</p><p>Foto tersimpan sementara selama sesi ini. Halaman pemrosesan belum tersedia; foto belum dikirim atau dikenali.</p></> : <p>Foto belum tersedia. Kembali untuk memilih foto.</p>}</div>
    <div className="action-stack"><Button variant="secondary" onClick={onDemo}>Lihat Contoh Hasil Bandung</Button><p className="scan-note">Contoh pembelajaran, bukan hasil OCR foto kamu.</p>
    <Button variant="primary" onClick={onBack}>Kembali ke Foto</Button>
    <Button variant="tertiary" onClick={onHome}>Kembali ke Home</Button></div>
  </main>
}



