/** Cell value from a SQL result set (sql.js / checker expectations). */
export type SqlCell = string | number | null | boolean

export type SqlRow = Record<string, SqlCell>

export type CompareRowsOptions = {
  /** When true, row order must match. Default: false (multiset compare). */
  ordered?: boolean
}

function normalizeCell(value: unknown): SqlCell {
  if (value === undefined || value === null) {
    return null
  }
  if (typeof value === 'boolean') {
    return value ? 1 : 0
  }
  if (typeof value === 'number') {
    if (Number.isNaN(value)) {
      return null
    }
    return value
  }
  if (typeof value === 'bigint') {
    return Number(value)
  }
  if (typeof value === 'string') {
    return value
  }
  return String(value)
}

function cellKey(value: SqlCell): string {
  if (value === null) {
    return '∅'
  }
  if (typeof value === 'number') {
    if (Object.is(value, -0)) {
      return '0'
    }
    return `n:${value}`
  }
  if (typeof value === 'boolean') {
    return value ? 'n:1' : 'n:0'
  }
  return `s:${value}`
}

function rowKey(row: SqlRow, columns: string[]): string {
  return columns.map((col) => cellKey(normalizeCell(row[col]))).join('|')
}

function sortedColumns(rows: SqlRow[]): string[] {
  const keys = new Set<string>()
  for (const row of rows) {
    for (const key of Object.keys(row)) {
      keys.add(key)
    }
  }
  return [...keys].sort()
}

function normalizeRows(rows: SqlRow[]): SqlRow[] {
  return rows.map((row) => {
    const next: SqlRow = {}
    for (const [key, value] of Object.entries(row)) {
      next[key] = normalizeCell(value)
    }
    return next
  })
}

export type CompareRowsResult = {
  equal: boolean
  message: string
}

/**
 * Compare two result sets. Column names must match (case-sensitive).
 * NULL matches NULL. Numbers compared numerically. Order ignored unless ordered.
 */
export function compareRows(
  actual: SqlRow[],
  expected: SqlRow[],
  options: CompareRowsOptions = {},
): CompareRowsResult {
  const ordered = options.ordered === true
  const actualNorm = normalizeRows(actual)
  const expectedNorm = normalizeRows(expected)

  if (actualNorm.length !== expectedNorm.length) {
    return {
      equal: false,
      message: `ожидалось ${expectedNorm.length} строк(и), получено ${actualNorm.length}`,
    }
  }

  const columns = sortedColumns([...actualNorm, ...expectedNorm])
  if (columns.length === 0 && actualNorm.length === 0) {
    return { equal: true, message: 'пустое множество' }
  }

  for (const row of expectedNorm) {
    for (const col of columns) {
      if (!(col in row) && actualNorm.some((a) => col in a)) {
        return {
          equal: false,
          message: `в ожидаемом результате нет столбца ${col}`,
        }
      }
    }
  }

  const actualCols = sortedColumns(actualNorm)
  const expectedCols = sortedColumns(expectedNorm)
  if (actualCols.join(',') !== expectedCols.join(',')) {
    return {
      equal: false,
      message: `столбцы: ожидали [${expectedCols.join(', ')}], получили [${actualCols.join(', ')}]`,
    }
  }

  if (ordered) {
    for (let index = 0; index < expectedNorm.length; index += 1) {
      const want = rowKey(expectedNorm[index], columns)
      const got = rowKey(actualNorm[index], columns)
      if (want !== got) {
        return {
          equal: false,
          message: `строка ${index + 1}: ожидали ${formatRow(expectedNorm[index], columns)}, получили ${formatRow(actualNorm[index], columns)}`,
        }
      }
    }
    return { equal: true, message: 'совпало (с порядком)' }
  }

  const bag = new Map<string, number>()
  for (const row of expectedNorm) {
    const key = rowKey(row, columns)
    bag.set(key, (bag.get(key) || 0) + 1)
  }
  for (const row of actualNorm) {
    const key = rowKey(row, columns)
    const left = bag.get(key) || 0
    if (left === 0) {
      return {
        equal: false,
        message: `лишняя или неверная строка: ${formatRow(row, columns)}`,
      }
    }
    if (left === 1) {
      bag.delete(key)
    } else {
      bag.set(key, left - 1)
    }
  }
  if (bag.size > 0) {
    const missing = [...bag.keys()][0]
    return {
      equal: false,
      message: `не хватает строки (ключ): ${missing}`,
    }
  }
  return { equal: true, message: 'совпало' }
}

function formatRow(row: SqlRow, columns: string[]): string {
  return `{${columns.map((col) => `${col}=${JSON.stringify(normalizeCell(row[col]))}`).join(', ')}}`
}

/** Convert sql.js QueryExecResult rows into objects. */
export function queryResultToRows(
  columns: string[],
  values: unknown[][],
): SqlRow[] {
  return values.map((tuple) => {
    const row: SqlRow = {}
    columns.forEach((col, index) => {
      row[col] = normalizeCell(tuple[index])
    })
    return row
  })
}
