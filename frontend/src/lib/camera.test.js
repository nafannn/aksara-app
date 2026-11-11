import test from 'node:test'
import assert from 'node:assert/strict'
import { createCameraSession, capturePhoto, cameraProblem } from './camera.js'

function fixture(getStream) {
  let stopped = 0
  const track = { stop() { stopped++ }, addEventListener() {} }
  const stream = { getTracks: () => [track], getVideoTracks: () => [track] }
  const video = { srcObject: null, play: async () => {} }
  let constraints
  const session = createCameraSession({ video, mediaDevices: { getUserMedia: async (value) => { constraints = value; return getStream ? getStream(stream) : stream } }, onEnded() {} })
  return { session, video, stream, stopped: () => stopped, constraints: () => constraints }
}

test('requests rear camera without audio, attaches it and releases it on exit', async () => {
  const f = fixture()
  assert.equal(await f.session.start(), true)
  assert.equal(f.video.srcObject, f.stream)
  assert.equal(f.constraints().audio, false)
  assert.equal(f.constraints().video.facingMode.ideal, 'environment')
  f.session.stop()
  assert.equal(f.stopped(), 1)
  assert.equal(f.video.srcObject, null)
})

test('late permission approval cannot leak a stream after navigation', async () => {
  let resolve
  const f = fixture(() => new Promise((done) => { resolve = done }))
  const pending = f.session.start()
  f.session.stop()
  resolve(f.stream)
  assert.equal(await pending, false)
  assert.equal(f.stopped(), 1)
  assert.equal(f.video.srcObject, null)
})

test('failed video playback releases camera', async () => {
  const f = fixture()
  f.video.play = async () => { throw new Error('playback failed') }
  await assert.rejects(f.session.start(), /playback failed/)
  assert.equal(f.stopped(), 1)
})

test('captures actual video dimensions and JPEG pixels', () => {
  const video = { readyState: 2, videoWidth: 1920, videoHeight: 1080 }
  let drawArgs
  const canvas = { getContext: () => ({ drawImage: (...args) => { drawArgs = args } }), toDataURL: (type, quality) => { assert.equal(type, 'image/jpeg'); assert.equal(quality, .9); return 'data:image/jpeg;base64,photo' } }
  assert.equal(capturePhoto(video, canvas), 'data:image/jpeg;base64,photo')
  assert.equal(canvas.width, 1920)
  assert.equal(canvas.height, 1080)
  assert.deepEqual(drawArgs, [video, 0, 0, 1920, 1080])
  assert.throws(() => capturePhoto({ readyState: 0 }, canvas), /belum siap/)
})

test('camera errors have actionable Indonesian messages', () => {
  assert.match(cameraProblem({ name: 'NotAllowedError' }), /pengaturan situs/)
  assert.match(cameraProblem({ name: 'NotFoundError' }), /tidak ditemukan/)
  assert.match(cameraProblem({ name: 'NotReadableError' }), /aplikasi lain/)
  assert.match(cameraProblem({ name: 'UnexpectedError' }), /Periksa kamera/)
})
