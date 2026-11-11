import { useId, useState } from 'react'

export default function CharacterLearning({ characters }) {
  const [open, setOpen] = useState(false)
  const [selected, setSelected] = useState(null)
  const id = useId()
  return <section className="character-learning" aria-label="Pembelajaran karakter">
    <button className="learn-toggle" aria-expanded={open} aria-controls={`${id}-cards`} onClick={() => setOpen(!open)}>
      <span><strong>Pelajari Karakter</strong><small>Kenali karakter pembentuk kata ini.</small></span><span aria-hidden="true">{open ? '⌃' : '⌄'}</span>
    </button>
    {open && <div id={`${id}-cards`} className="learning-body">
      {!characters.length ? <p className="learn-empty">Rincian karakter belum tersedia.</p> : <>
        <div className="character-grid">{characters.map((item, index) => <button key={index} className={`character-card ${selected === index ? 'selected' : ''}`} aria-expanded={selected === index} aria-controls={`${id}-detail`} onClick={() => setSelected(selected === index ? null : index)}>
          <span className="sundanese" lang="su">{item.aksara || '—'}</span><strong>{item.reading || 'Bacaan belum tersedia'}</strong><small>{item.category || 'Kategori belum tersedia'}</small>
        </button>)}</div>
        {selected !== null && characters[selected] && <div id={`${id}-detail`} className="character-explanation" role="region" aria-label="Penjelasan karakter" aria-live="polite"><strong><span className="sundanese" lang="su">{characters[selected].aksara || '—'}</span> · {characters[selected].reading || 'Bacaan belum tersedia'}</strong><p>{characters[selected].explanation || 'Penjelasan belum tersedia.'}</p></div>}
        <p className="learning-caption">Pilih karakter untuk melihat penjelasannya. Aksara dan rarangkén dipelajari sebagai satu unit baca.</p>
      </>}
    </div>}
  </section>
}
