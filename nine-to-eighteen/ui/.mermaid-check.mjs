// Usage: node .mermaid-check.mjs diagrams.json  — [{id, mermaid}] → prints failures
import { readFileSync } from 'node:fs'

globalThis.window = globalThis
globalThis.addEventListener = () => {}
globalThis.document = { createElement: () => ({ style: {}, setAttribute() {}, appendChild() {} }), querySelector: () => null }
const { default: DOMPurify } = await import('dompurify')
DOMPurify.addHook = () => {}
DOMPurify.removeHook = () => {}
DOMPurify.removeAllHooks = () => {}
DOMPurify.sanitize = (value) => value
const { default: mermaid } = await import('mermaid')
mermaid.initialize({ startOnLoad: false })

const items = JSON.parse(readFileSync(process.argv[2], 'utf8'))
let failed = 0
for (const item of items) {
  try {
    await mermaid.parse(item.mermaid)
  } catch (error) {
    failed += 1
    console.log(`FAIL ${item.id}: ${String(error?.message || error).split('\n').slice(0, 3).join(' | ')}`)
  }
}
console.log(`checked ${items.length}, failed ${failed}`)
process.exit(failed ? 1 : 0)
