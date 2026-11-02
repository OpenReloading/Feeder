// biome-ignore lint/correctness/noUndeclaredDependencies: Docusaurus alias for the theme's own component
import Code from '@theme-original/MDXComponents/Code'
import CodeInline from '@theme/CodeInline'
import type { ComponentProps, ReactNode } from 'react'
import { Children, isValidElement } from 'react'

const wbr = (part: unknown): boolean => isValidElement(part) && part.type === 'wbr'

/**
 * The theme's code component, which takes code as inline only when it is all text on one line. Inline code with the
 * <wbr> of scripts/table-layout.mts would become a code block, so text and <wbr> stay inline here.
 */
export default function MDXCode(props: ComponentProps<typeof Code>): ReactNode {
  const parts = Children.toArray(props.children)
  const inline = parts.some(wbr) && parts.every((p) => wbr(p) || (typeof p === 'string' && !p.includes('\n')))
  return inline ? <CodeInline {...props} /> : <Code {...props} />
}
