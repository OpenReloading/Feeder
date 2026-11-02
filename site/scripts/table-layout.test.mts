import assert from 'node:assert/strict'
import { test } from 'node:test'
import tableLayout, { type Node } from './table-layout.mts'

const el = (tagName: string, children: Node[] = [], properties = {}): Node => ({
  type: 'element',
  tagName,
  properties,
  children,
})
const txt = (value: string): Node => ({ type: 'text', value })
const run = (tree: Node): Node => {
  tableLayout()(tree)
  return tree
}

test('inline code breaks after a dot between names, code blocks and numbers do not', () => {
  const inline = el('code', [txt('case_plate.pocket_clearance 0.6')])
  const block = el('pre', [el('code', [txt('a.b')])])
  run(el('root', [el('p', [inline]), block]))
  assert.deepEqual(inline.children, [txt('case_plate.'), el('wbr'), txt('pocket_clearance 0.6')])
  assert.deepEqual(block.children?.[0]?.children, [txt('a.b')])
})

const table = (cell: string): Node =>
  el('table', [
    el('thead', [el('tr', [el('th', [txt('Symptom')]), el('th', [txt('Fix')])])]),
    el('tbody', [el('tr', [el('td', [txt('jam')]), el('td', [txt(cell)])])]),
  ])

test('a table with a 60 character cell stacks on a phone, with the column header on each cell', () => {
  const long = run(table('x'.repeat(60)))
  assert.equal(long.properties?.dataStack, '')
  const row = long.children?.[1]?.children?.[0]?.children ?? []
  assert.deepEqual(
    row.map((td) => td.properties?.dataLabel),
    ['Symptom', 'Fix'],
  )
  assert.equal(run(table('x'.repeat(59))).properties?.dataStack, undefined)
})
