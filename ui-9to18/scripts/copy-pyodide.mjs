import { copyFileSync, mkdirSync, existsSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const rootDir = join(dirname(fileURLToPath(import.meta.url)), '..')
const sourceDir = join(rootDir, 'node_modules', 'pyodide')
const targetDir = join(rootDir, 'public', 'pyodide')

const files = [
  'pyodide.asm.mjs',
  'pyodide.asm.wasm',
  'python_stdlib.zip',
  'pyodide-lock.json',
]

if (!existsSync(sourceDir)) {
  console.error('pyodide package not found. Run npm install first.')
  process.exit(1)
}

mkdirSync(targetDir, { recursive: true })

for (const fileName of files) {
  copyFileSync(join(sourceDir, fileName), join(targetDir, fileName))
}

console.log(`Copied ${files.length} Pyodide artifacts to public/pyodide/`)
