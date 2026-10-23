/// <reference lib="webworker" />

import type { SqlValue } from 'sql.js'

const MAX_ROWS = 200
const MAX_SQL_CHARS = 20_000
const BLOCKED_SQL =
  /\b(ATTACH|DETACH|LOAD_EXTENSION|PRAGMA\s+load_extension|VACUUM\s+INTO)\b/i

type SqlCell = string | number | null

type RunRequest = {
  type: 'run'
  id: number
  schemaSql: string
  studentSql: string
  verifySql?: string
}

type LoadRequest = { type: 'load' }

let sqlPromise: Promise<import('sql.js').SqlJsStatic> | null = null

function assertSafeSql(sql: string): void {
  if (sql.length > MAX_SQL_CHARS) {
    throw new Error('Запрос слишком длинный')
  }
  if (BLOCKED_SQL.test(sql)) {
    throw new Error(
      'Команда запрещена в песочнице (ATTACH / load_extension / VACUUM INTO)',
    )
  }
}

function cell(value: SqlValue): SqlCell {
  if (value === null || typeof value === 'number' || typeof value === 'string') {
    return value
  }
  return String(value)
}

async function loadSql(): Promise<import('sql.js').SqlJsStatic> {
  if (!sqlPromise) {
    sqlPromise = (async () => {
      const initSqlJs = (
        await import(/* @vite-ignore */ 'sql.js/dist/sql-wasm.js')
      ).default as (config?: {
        locateFile?: (file: string) => string
      }) => Promise<import('sql.js').SqlJsStatic>
      return initSqlJs({
        locateFile: (file) => {
          const name = file.endsWith('.wasm') ? 'sql-wasm.wasm' : file
          return `/sqljs/${name}`
        },
      })
    })()
  }
  return sqlPromise
}

function execLast(
  db: import('sql.js').Database,
  sql: string,
): {
  columns: string[]
  values: SqlCell[][]
  emptyOk: boolean
  truncated: boolean
  blank: boolean
} {
  assertSafeSql(sql)
  const trimmed = sql.trim()
  if (!trimmed) {
    return { columns: [], values: [], emptyOk: false, truncated: false, blank: true }
  }
  const results = db.exec(trimmed)
  if (results.length === 0) {
    return { columns: [], values: [], emptyOk: true, truncated: false, blank: false }
  }
  const last = results[results.length - 1]
  const truncated = last.values.length > MAX_ROWS
  const values = last.values.slice(0, MAX_ROWS).map((row) => row.map(cell))
  return { columns: last.columns, values, emptyOk: false, truncated, blank: false }
}

self.onmessage = async (event: MessageEvent<LoadRequest | RunRequest>) => {
  const data = event.data
  if (data.type === 'load') {
    try {
      await loadSql()
      self.postMessage({ type: 'ready' })
    } catch (err) {
      self.postMessage({
        type: 'load-error',
        message: err instanceof Error ? err.message : String(err),
      })
    }
    return
  }

  try {
    const SQL = await loadSql()
    const db = new SQL.Database()
    try {
      if (data.schemaSql.trim()) {
        assertSafeSql(data.schemaSql)
        db.run(data.schemaSql)
      }
      const student = execLast(db, data.studentSql)
      let verifyColumns: string[] = []
      let verifyValues: SqlCell[][] = []
      let verifyError: string | null = null
      if (data.verifySql?.trim()) {
        try {
          const verify = execLast(db, data.verifySql)
          verifyColumns = verify.columns
          verifyValues = verify.values
        } catch (err) {
          verifyError = err instanceof Error ? err.message : String(err)
        }
      }
      self.postMessage({
        type: 'result',
        id: data.id,
        error: null,
        columns: student.columns,
        values: student.values,
        emptyOk: student.emptyOk,
        truncated: student.truncated,
        blank: student.blank,
        verifyError,
        verifyColumns,
        verifyValues,
      })
    } finally {
      db.close()
    }
  } catch (err) {
    self.postMessage({
      type: 'result',
      id: data.id,
      error: err instanceof Error ? err.message : String(err),
      columns: [],
      values: [],
      emptyOk: false,
      truncated: false,
      blank: false,
      verifyError: null,
      verifyColumns: [],
      verifyValues: [],
    })
  }
}
