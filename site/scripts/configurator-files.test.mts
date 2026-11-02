import assert from 'node:assert/strict'
import { existsSync, mkdirSync, mkdtempSync, readdirSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { test } from 'node:test'
import { copyConfiguratorFiles } from './configurator-files.mts'

test('the print files and the manifest land next to the configurator page, nothing without a manifest', () => {
  const root = mkdtempSync(join(tmpdir(), 'configurator-'))
  const src = join(root, 'configurator')
  mkdirSync(src)
  writeFileSync(join(src, 'ab12.stl'), 'solid')
  writeFileSync(join(src, 'notes.txt'), 'not copied')
  assert.equal(copyConfiguratorFiles(src, join(root, 'out')), 0)
  assert.equal(existsSync(join(root, 'out')), false)
  writeFileSync(join(src, 'manifest.json'), '{}')
  assert.equal(copyConfiguratorFiles(src, join(root, 'out')), 2)
  assert.deepEqual(readdirSync(join(root, 'out', 'configurator', 'data')).sort(), ['ab12.stl', 'manifest.json'])
})
