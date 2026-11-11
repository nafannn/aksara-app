import { ScanHeader } from './GuidedCamera'

export default function PhotoReady({ file, onBack, onHome }) {
  return <main className="home-shell scan-flow">
    <ScanHeader title="Foto Siap" onBack={onBack} />
    <h2 className="preview-heading">Siap untuk langkah berikutnya</h2>
    <div className="preview-notice" role="status">{file ? <><strong>Foto pilihan sudah disiapkan.</strong><p>{file.name} · {Math.ceil(file.size / 1024)} KB</p><p>Foto tersimpan sementara selama sesi ini. Halaman pemrosesan belum tersedia; foto belum dikirim atau dikenali.</p></> : <p>Foto belum tersedia. Kembali untuk memilih foto.</p>}</div>
    <button className="scan-action" onClick={onBack}>Kembali ke Foto</button>
    <button className="scan-action secondary" onClick={onHome}>Kembali ke Home</button>
  </main>
}
