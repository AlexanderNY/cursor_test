import type { Database, SqlJsStatic } from 'sql.js'
import {
  compareRows,
  queryResultToRows,
  type CompareRowsOptions,
  type SqlRow,
} from '@/game/sql/compare-rows'

const SQLJS_BASE = '/sqljs/'
const DEFAULT_WALL_MS = 8000

let sqlPromise: Promise<SqlJsStatic> | null = null

const BLOCKED_SQL =
  /\b(ATTACH|DETACH|LOAD_EXTENSION|PRAGMA\s+load_extension|VACUUM\s+INTO)\b/i

export type SqlRunResult = {
  rows: SqlRow[]
  columns: string[]
  text: string
  error: string | null
  timedOut: boolean
}

export type SqlCheckResult = SqlRunResult & {
  passed: boolean
  feedback: string
}

/**
 * Load sql.js against public/sqljs artifacts (copied at predev/build).
 * Prefer the wasm build; Vite may resolve either sql-wasm or sql-wasm-browser.
 */
export async function loadSandboxSqlJs(
  onProgress?: (value: number, label: string) => void,
): Promise<SqlJsStatic> {
  if (!sqlPromise) {
    onProgress?.(0.1, 'sql.js')
    sqlPromise = (async () => {
      const initSqlJs = (
        await import(/* @vite-ignore */ 'sql.js/dist/sql-wasm.js')
      ).default as (config?: {
        locateFile?: (file: string) => string
      }) => Promise<SqlJsStatic>
      const SQL = await initSqlJs({
        locateFile: (file) => {
          const name = file.endsWith('.wasm') ? 'sql-wasm.wasm' : file
          return `${SQLJS_BASE}${name}`
        },
      })
      onProgress?.(1, 'sql.js')
      return SQL
    })()
  }
  return sqlPromise
}

function assertSafeSql(sql: string): void {
  if (BLOCKED_SQL.test(sql)) {
    throw new Error(
      'Команда запрещена в песочнице (ATTACH / load_extension / VACUUM INTO)',
    )
  }
}

function openDb(SQL: SqlJsStatic): Database {
  return new SQL.Database()
}

function execScript(db: Database, sql: string): SqlRunResult {
  assertSafeSql(sql)
  const trimmed = sql.trim()
  if (!trimmed) {
    return {
      rows: [],
      columns: [],
      text: '(пусто)',
      error: null,
      timedOut: false,
    }
  }

  try {
    const results = db.exec(trimmed)
    if (results.length === 0) {
      return {
        rows: [],
        columns: [],
        text: 'OK (нет результирующего набора)',
        error: null,
        timedOut: false,
      }
    }
    const last = results[results.length - 1]
    const rows = queryResultToRows(last.columns, last.values)
    return {
      rows,
      columns: last.columns,
      text: formatResultTable(last.columns, rows),
      error: null,
      timedOut: false,
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return {
      rows: [],
      columns: [],
      text: '',
      error: message,
      timedOut: false,
    }
  }
}

export function formatResultTable(columns: string[], rows: SqlRow[]): string {
  if (columns.length === 0) {
    return '(0 строк)'
  }
  const header = columns.join(' | ')
  const sep = columns.map(() => '---').join(' | ')
  const body = rows.map((row) =>
    columns
      .map((col) => {
        const value = row[col]
        if (value === null) return 'NULL'
        return String(value)
      })
      .join(' | '),
  )
  const lines = [header, sep, ...body, `(${rows.length} строк)`]
  return lines.join('\n')
}

async function withTimeout<T>(
  work: () => T,
  wallMs: number,
): Promise<{ value?: T; timedOut: boolean; error?: string }> {
  return new Promise((resolve) => {
    const timer = window.setTimeout(() => {
      resolve({ timedOut: true, error: `Timeout ${wallMs}ms` })
    }, wallMs)
    try {
      const value = work()
      window.clearTimeout(timer)
      resolve({ value, timedOut: false })
    } catch (err) {
      window.clearTimeout(timer)
      resolve({
        timedOut: false,
        error: err instanceof Error ? err.message : String(err),
      })
    }
  })
}

/**
 * Run student SQL against a fresh DB after optional schema seed.
 * Returns the last result set (for SELECT) or OK / error text.
 */
export async function runSqlInSandbox(
  studentSql: string,
  schemaSql = '',
  wallMs = DEFAULT_WALL_MS,
): Promise<SqlRunResult> {
  const SQL = await loadSandboxSqlJs()
  const outcome = await withTimeout(() => {
    const db = openDb(SQL)
    try {
      if (schemaSql.trim()) {
        assertSafeSql(schemaSql)
        db.run(schemaSql)
      }
      return execScript(db, studentSql)
    } finally {
      db.close()
    }
  }, wallMs)

  if (outcome.timedOut) {
    return {
      rows: [],
      columns: [],
      text: '',
      error: outcome.error || 'Timeout',
      timedOut: true,
    }
  }
  if (outcome.error && !outcome.value) {
    return {
      rows: [],
      columns: [],
      text: '',
      error: outcome.error,
      timedOut: false,
    }
  }
  return outcome.value!
}

export type QueryCheckSpec = {
  mode: 'query'
  expectedRows: SqlRow[]
  compare?: CompareRowsOptions
}

export type VerifyCheckSpec = {
  mode: 'verify'
  /** Run after student SQL; must return one row with ok=1 (or PASS text). */
  verifySql: string
}

export type SqlCheckSpec = QueryCheckSpec | VerifyCheckSpec

export async function runSqlWithCheck(
  studentSql: string,
  schemaSql: string,
  check: SqlCheckSpec,
  wallMs = DEFAULT_WALL_MS,
): Promise<SqlCheckResult> {
  const SQL = await loadSandboxSqlJs()
  const outcome = await withTimeout(() => {
    const db = openDb(SQL)
    try {
      if (schemaSql.trim()) {
        assertSafeSql(schemaSql)
        db.run(schemaSql)
      }
      const run = execScript(db, studentSql)
      if (run.error) {
        return {
          ...run,
          passed: false,
          feedback: run.error,
        } satisfies SqlCheckResult
      }

      if (check.mode === 'query') {
        const cmp = compareRows(run.rows, check.expectedRows, check.compare)
        return {
          ...run,
          passed: cmp.equal,
          feedback: cmp.equal
            ? `PASS: ${cmp.message}`
            : `FAIL: ${cmp.message}`,
        } satisfies SqlCheckResult
      }

      assertSafeSql(check.verifySql)
      const verifyResults = db.exec(check.verifySql.trim())
      if (verifyResults.length === 0) {
        return {
          ...run,
          passed: false,
          feedback: 'FAIL: verifySql не вернул строк',
        } satisfies SqlCheckResult
      }
      const last = verifyResults[verifyResults.length - 1]
      const verifyRows = queryResultToRows(last.columns, last.values)
      const ok =
        verifyRows.length > 0 &&
        (verifyRows[0].ok === 1 ||
          verifyRows[0].ok === '1' ||
          String(verifyRows[0].pass || '')
            .toUpperCase()
            .startsWith('PASS'))
      const detail =
        verifyRows[0]?.detail != null
          ? String(verifyRows[0].detail)
          : ok
            ? 'проверка схемы пройдена'
            : 'проверка схемы не пройдена'
      return {
        ...run,
        text:
          run.text +
          (run.text ? '\n\n' : '') +
          '-- verify --\n' +
          formatResultTable(last.columns, verifyRows),
        passed: Boolean(ok),
        feedback: ok ? `PASS: ${detail}` : `FAIL: ${detail}`,
      } satisfies SqlCheckResult
    } finally {
      db.close()
    }
  }, wallMs)

  if (outcome.timedOut) {
    return {
      rows: [],
      columns: [],
      text: '',
      error: outcome.error || 'Timeout',
      timedOut: true,
      passed: false,
      feedback: `FAIL: ${outcome.error || 'Timeout'}`,
    }
  }
  if (outcome.error && !outcome.value) {
    return {
      rows: [],
      columns: [],
      text: '',
      error: outcome.error,
      timedOut: false,
      passed: false,
      feedback: `FAIL: ${outcome.error}`,
    }
  }
  return outcome.value!
}

const SQL_FENCE = /```(?:sql)\s*\n([\s\S]*?)```/gi

/** Extract fenced ```sql blocks from markdown. */
export function extractSqlBlocks(markdown: string): string[] {
  const blocks: string[] = []
  const source = markdown || ''
  let match: RegExpExecArray | null
  const re = new RegExp(SQL_FENCE.source, 'gi')
  while ((match = re.exec(source)) !== null) {
    const code = match[1].replace(/\s+$/, '')
    if (code.trim()) {
      blocks.push(code)
    }
  }
  return blocks
}

export function formatSqlRunChannels(run: SqlRunResult): string {
  if (run.timedOut) {
    return run.error || 'Timeout'
  }
  if (run.error) {
    return `ERROR: ${run.error}`
  }
  return run.text || '(пусто)'
}
