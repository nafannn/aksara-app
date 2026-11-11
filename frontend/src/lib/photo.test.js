import test from 'node:test'
import assert from 'node:assert/strict'
import { adjustCrop, cropPixels, photoFile, cropPhoto } from './photo.js'

test('moving crop remains within all four image edges', () => {
  const rect = { x: .2, y: .3, width: .5, height: .4 }
  assert.deepEqual(adjustCrop(rect, 'move', 10, -10), { x: .5, y: 0, width: .5, height: .4 })
  assert.deepEqual(adjustCrop(rect, 'move', -10, 10), { x: 0, y: .6, width: .5, height: .4 })
})
test('resize clamps edges and prevents inverted or empty selections', () => {
  const rect = { x: .2, y: .3, width: .5, height: .4 }
  const expanded = adjustCrop(rect, 'se', 10, 10)
  assert.equal(expanded.x + expanded.width, 1)
  assert.equal(expanded.y + expanded.height, 1)
  const shrunk = adjustCrop(rect, 'nw', 10, 10)
  assert.ok(shrunk.width >= .019999 && shrunk.height >= .019999)
})
test('maps fractional coordinates to original landscape and portrait pixels without stretching', () => {
  const rect = { x: .25, y: .25, width: .5, height: .5 }
  assert.deepEqual(cropPixels(rect, 1920, 1080), { x: 480, y: 270, width: 960, height: 540 })
  assert.deepEqual(cropPixels(rect, 1080, 1920), { x: 270, y: 480, width: 540, height: 960 })
  assert.throws(() => cropPixels({ ...rect, width: 0 }, 100, 100), /tidak valid/)
  assert.throws(() => cropPixels({ ...rect, x: -.1 }, 100, 100), /tidak valid/)
})
test('exports bytes without re-encoding, suitable for FormData', async () => {
  const file = photoFile('data:image/png;base64,aGVsbG8=')
  assert.equal(file.type, 'image/png')
  assert.equal(file.name, 'aksara.png')
  assert.equal(await file.text(), 'hello')
  const form = new FormData()
  form.append('image', file)
  assert.equal(form.get('image').size, 5)
  assert.throws(() => photoFile(null), /belum siap/)
})
test('crop uses original pixels, handles canvas failure, and frees canvas memory', async () => {
  const oldImage = globalThis.Image
  const oldDocument = globalThis.document
  let args
  const canvas = { width: 0, height: 0, getContext: () => ({ drawImage: (...values) => { args = values } }), toDataURL: (type) => { assert.equal(type, 'image/png'); return 'data:image/png;base64,aA==' } }
  globalThis.Image = class { naturalWidth = 1200; naturalHeight = 800; set src(value) { this.source = value; this.onload() } }
  globalThis.document = { createElement: () => canvas }
  try {
    assert.equal(await cropPhoto('original', { x: .25, y: 0, width: .5, height: 1 }), 'data:image/png;base64,aA==')
    assert.deepEqual(args.slice(1), [300, 0, 600, 800, 0, 0, 600, 800])
    assert.equal(canvas.width, 0)
    canvas.getContext = () => null
    await assert.rejects(cropPhoto('original', { x: 0, y: 0, width: 1, height: 1 }), /tidak tersedia/)
    await assert.rejects(cropPhoto(null, {}), /belum tersedia/)
  } finally { globalThis.Image = oldImage; globalThis.document = oldDocument }
})
