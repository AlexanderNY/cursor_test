import {
  compareRows,
  queryResultToRows,
  type CompareRowsOptions,
  type SqlRow,
} from '@/game/sql/compare-rows'

const DEFAULT_WALL_MS = 8000
const MAX_SQL_CHARS = 20_000

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

export type SandboxProgress = (value: number, label: string) => void

type WorkerCell = string | number | null

type WorkerResult = {
  type: 'result'
  id: number
  error: string | null
  columns: string[]
  values: WorkerCell[][]
  emptyOk: boolean
  truncated: boolean
  blank: boolean
  verifyError: string | null
  verifyColumns: string[]
  verifyValues: WorkerCell[][]
}

let sqlWorker: Worker | null = null
let loadPromise: Promise<void> | null = null
let nextRunId = 1
const pendingRuns = new Map<number, (value: WorkerResult | { timedOut: true }) => void>()

function dropWorker(): void {
  sqlWorker?.terminate()
  sqlWorker = null
  loadPromise = null
  for (const [id, resolve] of pendingRuns) {
    pendingRuns.delete(id)
    resolve({ timedOut: true })
  }
}

function ensureSqlWorker(): Promise<void> {
  if (loadPromise && sqlWorker) return loadPromise
  const worker = new Worker(new URL('./sandbox-sqlite.worker.ts', import.meta.url), {
    type: 'module',
  })
  sqlWorker = worker
  loadPromise = new Promise<void>((resolve, reject) => {
    const onMessage = (event: MessageEvent) => {
      const data = event.data as
        | { type: 'ready' }
        | { type: 'load-error'; message: string }
        | WorkerResult
      if (data.type === 'ready') {
        resolve()
        return
      }
      if (data.type === 'load-error') {
        reject(new Error(data.message))
        return
      }
      if (data.type === 'result') {
        const pending = pendingRuns.get(data.id)
        if (!pending) return
        pendingRuns.delete(data.id)
        pending(data)
      }
    }
    worker.addEventListener('message', onMessage)
    worker.postMessage({ type: 'load' })
  }).catch((err) => {
    dropWorker()
    throw err
  })
  return loadPromise
}

/**
 * Load sql.js in a worker (public/sqljs artifacts copied at predev/build).
 */
export async function loadSandboxSqlJs(onProgress?: SandboxProgress): Promise<void> {
  onProgress?.(0.1, 'sql.js')
  await ensureSqlWorker()
  onProgress?.(1, 'sql.js')
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

function resultText(
  columns: string[],
  rows: SqlRow[],
  emptyOk: boolean,
  truncated: boolean,
  blank: boolean,
): string {
  if (blank) return '(пусто)'
  if (emptyOk) return 'OK (нет результирующего набора)'
  const table = formatResultTable(columns, rows)
  return truncated ? `${table}\n(показаны первые 200 строк)` : table
}

async function runInWorker(
  studentSql: string,
  schemaSql: string,
  verifySql: string | undefined,
  wallMs: number,
): Promise<WorkerResult | { timedOut: true }> {
  if (studentSql.length > MAX_SQL_CHARS || (verifySql && verifySql.length > MAX_SQL_CHARS)) {
    return {
      type: 'result',
      id: -1,
      error: 'Запрос слишком длинный',
      columns: [],
      values: [],
      emptyOk: false,
      truncated: false,
      blank: false,
      verifyError: null,
      verifyColumns: [],
      verifyValues: [],
    }
  }
  await ensureSqlWorker()
  const worker = sqlWorker
  if (!worker) return { timedOut: true }
  const id = nextRunId
  nextRunId += 1
  return new Promise((resolve) => {
    const timer = window.setTimeout(() => {
      pendingRuns.delete(id)
      dropWorker()
      resolve({ timedOut: true })
    }, wallMs)
    pendingRuns.set(id, (value) => {
      window.clearTimeout(timer)
      resolve(value)
    })
    worker.postMessage({
      type: 'run',
      id,
      schemaSql,
      studentSql,
      verifySql,
    })
  })
}

function toRows(columns: string[], values: WorkerCell[][]): SqlRow[] {
  return queryResultToRows(columns, values)
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
  const outcome = await runInWorker(studentSql, schemaSql, undefined, wallMs)
  if ('timedOut' in outcome) {
    return {
      rows: [],
      columns: [],
      text: '',
      error: `Timeout ${wallMs}ms`,
      timedOut: true,
    }
  }
  if (outcome.error) {
    return {
      rows: [],
      columns: [],
      text: '',
      error: outcome.error,
      timedOut: false,
    }
  }
  const rows = toRows(outcome.columns, outcome.values)
  return {
    rows,
    columns: outcome.columns,
    text: resultText(outcome.columns, rows, outcome.emptyOk, outcome.truncated, outcome.blank),
    error: null,
    timedOut: false,
  }
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
  const outcome = await runInWorker(
    studentSql,
    schemaSql,
    check.mode === 'verify' ? check.verifySql : undefined,
    wallMs,
  )
  if ('timedOut' in outcome) {
    const error = `Timeout ${wallMs}ms`
    return {
      rows: [],
      columns: [],
      text: '',
      error,
      timedOut: true,
      passed: false,
      feedback: `FAIL: ${error}`,
    }
  }
  if (outcome.error) {
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
  const rows = toRows(outcome.columns, outcome.values)
  const run: SqlRunResult = {
    rows,
    columns: outcome.columns,
    text: resultText(outcome.columns, rows, outcome.emptyOk, outcome.truncated, outcome.blank),
    error: null,
    timedOut: false,
  }

  if (check.mode === 'query') {
    const cmp = compareRows(run.rows, check.expectedRows, check.compare)
    return {
      ...run,
      passed: cmp.equal,
      feedback: cmp.equal ? `PASS: ${cmp.message}` : `FAIL: ${cmp.message}`,
    }
  }

  if (outcome.verifyError) {
    return {
      ...run,
      passed: false,
      feedback: `FAIL: ${outcome.verifyError}`,
    }
  }
  const verifyRows = toRows(outcome.verifyColumns, outcome.verifyValues)
  if (verifyRows.length === 0) {
    return {
      ...run,
      passed: false,
      feedback: 'FAIL: verifySql не вернул строк',
    }
  }
  const ok =
    verifyRows[0].ok === 1 ||
    verifyRows[0].ok === '1' ||
    String(verifyRows[0].pass || '')
      .toUpperCase()
      .startsWith('PASS')
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
      formatResultTable(outcome.verifyColumns, verifyRows),
    passed: Boolean(ok),
    feedback: ok ? `PASS: ${detail}` : `FAIL: ${detail}`,
  }
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
