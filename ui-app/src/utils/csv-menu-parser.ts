import type { GameMenuNodeCreate } from '@/types/game'

export const CSV_MENU_COLUMNS = [
  'parent_title',
  'title',
  'description',
  'price',
  'sort_order',
  'image_url',
] as const

export const CSV_MENU_EXAMPLE = `parent_title;title;description;price;sort_order;image_url
;Услуги;Раздел услуг;;0;
Услуги;Консультации;Подраздел консультаций;;1;
Консультации;Онлайн 30 мин;Видеозвонок с специалистом;500;0;
Консультации;Очный приём;Визит в офис;1200;1;
`

export interface CsvParseError {
  line: number
  message: string
}

export interface CsvMenuDraft {
  line: number
  parentTitle: string
  body: GameMenuNodeCreate
}

export interface CsvMenuParseResult {
  nodes: CsvMenuDraft[]
  errors: CsvParseError[]
}

const COLUMN_INDEX = {
  parent_title: 0,
  title: 1,
  description: 2,
  price: 3,
  sort_order: 4,
  image_url: 5,
} as const

type CsvColumnKey = keyof typeof COLUMN_INDEX

const HEADER_ALIASES: Record<string, CsvColumnKey> = {
  parent_title: 'parent_title',
  parent: 'parent_title',
  родитель: 'parent_title',
  title: 'title',
  название: 'title',
  description: 'description',
  описание: 'description',
  body_text: 'description',
  price: 'price',
  цена: 'price',
  sort_order: 'sort_order',
  order: 'sort_order',
  image_url: 'image_url',
  image: 'image_url',
}

function stripBom(text: string): string {
  return text.charCodeAt(0) === 0xfeff ? text.slice(1) : text
}

function detectDelimiter(line: string): ',' | ';' {
  let commas = 0
  let semicolons = 0
  let inQuotes = false
  for (const char of line) {
    if (char === '"') inQuotes = !inQuotes
    if (!inQuotes) {
      if (char === ',') commas += 1
      if (char === ';') semicolons += 1
    }
  }
  return semicolons >= commas ? ';' : ','
}

function parseCsvLine(line: string, delimiter: ',' | ';'): string[] {
  const result: string[] = []
  let current = ''
  let inQuotes = false
  for (let i = 0; i < line.length; i += 1) {
    const char = line[i]
    if (char === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"'
        i += 1
      } else {
        inQuotes = !inQuotes
      }
      continue
    }
    if (char === delimiter && !inQuotes) {
      result.push(current.trim())
      current = ''
      continue
    }
    current += char
  }
  result.push(current.trim())
  return result
}

function normalizeHeader(value: string): string {
  return value.trim().toLowerCase().replace(/\s+/g, '_')
}

function isHeaderRow(cells: string[]): boolean {
  const normalized = cells.map(normalizeHeader)
  return normalized.some((cell) => cell in HEADER_ALIASES)
}

function mapHeaderRow(cells: string[]): Array<CsvColumnKey | null> {
  return cells.map((cell) => {
    const key = HEADER_ALIASES[normalizeHeader(cell)]
    return key ?? null
  })
}

function readField(
  cells: string[],
  mapping: Array<CsvColumnKey | null> | null,
  field: CsvColumnKey,
  fallbackIndex: number,
): string {
  if (mapping) {
    const index = mapping.findIndex((item) => item === field)
    if (index >= 0) return (cells[index] ?? '').trim()
  }
  return (cells[fallbackIndex] ?? '').trim()
}

function buildNodeFromRow(
  cells: string[],
  mapping: Array<CsvColumnKey | null> | null,
  modeId: number,
  line: number,
): { node?: CsvMenuDraft; error?: CsvParseError } {
  const parentTitle = readField(cells, mapping, 'parent_title', COLUMN_INDEX.parent_title)
  const title = readField(cells, mapping, 'title', COLUMN_INDEX.title)
  const description = readField(cells, mapping, 'description', COLUMN_INDEX.description)
  const priceRaw = readField(cells, mapping, 'price', COLUMN_INDEX.price)
  const sortRaw = readField(cells, mapping, 'sort_order', COLUMN_INDEX.sort_order)
  const imageUrl = readField(cells, mapping, 'image_url', COLUMN_INDEX.image_url)

  if (!title) {
    return { error: { line, message: 'Пустое поле title (название пункта)' } }
  }

  let price = 0
  if (priceRaw) {
    const normalized = priceRaw.replace(',', '.')
    if (!/^\d+(\.\d{1,2})?$/.test(normalized) && !/^\d+$/.test(normalized)) {
      return { error: { line, message: `Некорректная цена: "${priceRaw}" (до 2 знаков после запятой)` } }
    }
    const parsed = Number.parseFloat(normalized)
    if (!Number.isFinite(parsed) || parsed < 0) {
      return { error: { line, message: `Некорректная цена: "${priceRaw}"` } }
    }
    price = Math.round(parsed * 100) / 100
  }

  let sortOrder = 0
  if (sortRaw) {
    const parsed = Number.parseInt(sortRaw, 10)
    if (!Number.isFinite(parsed)) {
      return { error: { line, message: `Некорректный sort_order: "${sortRaw}"` } }
    }
    sortOrder = parsed
  }

  return {
    node: {
      line,
      parentTitle,
      body: {
        mode_id: modeId,
        title,
        body_text: description || null,
        price,
        sort_order: sortOrder,
        image_url: imageUrl || null,
        is_active: true,
      },
    },
  }
}

export function parseMenuCsv(content: string, modeId: number): CsvMenuParseResult {
  const normalized = stripBom(content).replace(/\r\n/g, '\n').replace(/\r/g, '\n')
  const rawLines = normalized.split('\n')

  const nodes: CsvMenuDraft[] = []
  const errors: CsvParseError[] = []
  let delimiter: ',' | ';' = ';'
  let headerMapping: Array<CsvColumnKey | null> | null = null
  let dataStarted = false

  for (let i = 0; i < rawLines.length; i += 1) {
    const line = rawLines[i].trim()
    if (!line) continue

    const lineNumber = i + 1
    if (!dataStarted) {
      delimiter = detectDelimiter(line)
    }

    const cells = parseCsvLine(line, delimiter)
    if (!dataStarted && isHeaderRow(cells)) {
      headerMapping = mapHeaderRow(cells)
      dataStarted = true
      continue
    }

    dataStarted = true
    const minColumns = headerMapping ? 2 : 3
    if (cells.length < minColumns) {
      errors.push({
        line: lineNumber,
        message: `Недостаточно колонок (${cells.length})`,
      })
      continue
    }

    const result = buildNodeFromRow(cells, headerMapping, modeId, lineNumber)
    if (result.error) {
      errors.push(result.error)
      continue
    }
    if (result.node) {
      nodes.push(result.node)
    }
  }

  if (!dataStarted) {
    errors.push({ line: 0, message: 'Файл пустой' })
  }

  return { nodes, errors }
}

export function downloadMenuCsvTemplate(filename = 'polls-menu-template.csv'): void {
  const blob = new Blob([`\uFEFF${CSV_MENU_EXAMPLE}`], {
    type: 'text/csv;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}
