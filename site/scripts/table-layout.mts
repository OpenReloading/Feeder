// Phone layout for tables and inline code, a rehype plugin of the docs (docusaurus.config.ts). Inline code gets a <wbr>
// after each dot between names (`case_plate.pocket_clearance`), so it wraps there and not mid-word. A Markdown table with
// a long cell gets data-stack and a data-label (its column header) on every cell: src/css/feeder.css shows it as one
// block per row on a phone.

/** The part of a hast node this plugin reads and writes. */
export interface Node {
  type: string
  tagName?: string
  value?: string
  properties?: Record<string, unknown>
  children?: Node[]
}

const STACK_FROM = 60 // characters in the longest cell
const DOT = /(?<=[A-Za-z_])\.(?=[A-Za-z_])/

const text = (node: Node): string => node.value ?? (node.children ?? []).map(text).join('')
const all = (node: Node, tag: string): Node[] =>
  (node.children ?? []).flatMap((c) => [...(c.tagName === tag ? [c] : []), ...all(c, tag)])

function wrapDots(code: Node): void {
  code.children = (code.children ?? []).flatMap((child): Node[] => {
    if (child.type !== 'text') return [child]
    const parts = (child.value ?? '').split(DOT)
    return parts.flatMap((part, i): Node[] =>
      i < parts.length - 1
        ? [{ type: 'text', value: `${part}.` }, { type: 'element', tagName: 'wbr', properties: {}, children: [] }]
        : [{ type: 'text', value: part }],
    )
  })
}

function stack(table: Node): void {
  const labels = all(table, 'thead').flatMap((head) => all(head, 'th')).map((th) => text(th).trim())
  const rows = all(table, 'tbody').flatMap((body) => all(body, 'tr'))
  const cells = rows.flatMap((row) => all(row, 'td'))
  if (!labels.length || Math.max(0, ...cells.map((c) => text(c).trim().length)) < STACK_FROM) return
  table.properties = { ...table.properties, dataStack: '' }
  for (const row of rows)
    all(row, 'td').forEach((td, i) => {
      td.properties = { ...td.properties, dataLabel: labels[i] ?? '' }
    })
}

function walk(node: Node, parent?: Node): void {
  if (node.tagName === 'code' && parent?.tagName !== 'pre') wrapDots(node)
  if (node.tagName === 'table') stack(node)
  for (const child of node.children ?? []) walk(child, node)
}

export default function tableLayout() {
  return (tree: Node): void => walk(tree)
}
