import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import ts from 'typescript'

const here = path.dirname(fileURLToPath(import.meta.url))
const sourcePath = path.join(here, '../src/game/sql/compare-rows.ts')
const source = fs.readFileSync(sourcePath, 'utf8')
const js = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2022,
  },
}).outputText
const moduleUrl = `data:text/javascript,${encodeURIComponent(js)}`
const { compareRows, queryResultToRows } = await import(moduleUrl)

function check(condition, message) {
  assert.ok(condition, message)
}

const empty = compareRows([], [])
check(empty.equal, 'empty sets match')

const same = compareRows(
  [{ a: 1, b: null }, { a: 2, b: 'x' }],
  [{ a: 2, b: 'x' }, { a: 1, b: null }],
)
check(same.equal, 'unordered multiset matches')

const orderedFail = compareRows(
  [{ a: 1 }, { a: 2 }],
  [{ a: 2 }, { a: 1 }],
  { ordered: true },
)
check(!orderedFail.equal, 'ordered mismatch detected')

const orderedOk = compareRows(
  [{ a: 1 }, { a: 2 }],
  [{ a: 1 }, { a: 2 }],
  { ordered: true },
)
check(orderedOk.equal, 'ordered match')

const nullOk = compareRows([{ v: null }], [{ v: null }])
check(nullOk.equal, 'NULL matches NULL')

const numOk = compareRows([{ n: 1.5 }], [{ n: 1.5 }])
check(numOk.equal, 'numbers match')

const cols = queryResultToRows(['id', 'name'], [[1, 'a'], [2, null]])
check(cols.length === 2 && cols[1].name === null, 'queryResultToRows maps NULL')

const extra = compareRows([{ a: 1 }], [{ a: 1 }, { a: 2 }])
check(!extra.equal, 'length mismatch')

console.log('check-sql-compare: ok')
