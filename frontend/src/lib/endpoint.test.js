import test from 'node:test'
import assert from 'node:assert/strict'
import { resolveEndpoint } from './endpoint.js'

test('build endpoint is used when no query override is present', () => {
  assert.equal(resolveEndpoint('', 'https://api.example.test/scan'), 'https://api.example.test/scan')
  assert.equal(resolveEndpoint('?other=1', 'https://api.example.test/scan'), 'https://api.example.test/scan')
})
test('query override wins so a demo can change backend without a rebuild', () => {
  assert.equal(
    resolveEndpoint('?api=https://tiga-kata.trycloudflare.com/api/recognize', 'https://old.example.test/scan'),
    'https://tiga-kata.trycloudflare.com/api/recognize',
  )
})
test('unsafe or malformed overrides fall back to the build endpoint', () => {
  const build = 'https://api.example.test/scan'
  assert.equal(resolveEndpoint('?api=javascript:alert(1)', build), build)
  assert.equal(resolveEndpoint('?api=ftp://example.test/scan', build), build)
  assert.equal(resolveEndpoint('?api=not-a-url', build), build)
  assert.equal(resolveEndpoint('?api=', build), build)
})
