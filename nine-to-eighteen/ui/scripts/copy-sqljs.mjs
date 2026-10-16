import { copyFileSync, mkdirSync, existsSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const rootDir = join(dirname(fileURLToPath(import.meta.url)), '..')
const sourceDir = join(rootDir, 'node_modules', 'sql.js', 'dist')
const targetDir = join(rootDir, 'public', 'sqljs')

const files = [
  'sql-wasm.js',
  'sql-wasm.wasm',
  'sql-wasm-browser.js',
  'sql-wasm-browser.wasm',
]

if (!existsSync(sourceDir)) {
  console.error('sql.js package not found. Run npm install first.')
  process.exit(1)
}

mkdirSync(targetDir, { recursive: true })

for (const fileName of files) {
  copyFileSync(join(sourceDir, fileName), join(targetDir, fileName))
}

console.log(`Copied ${files.length} sql.js artifacts to public/sqljs/`)
