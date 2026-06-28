import type { GameOptionInput, GameQuestionCreate } from '@/types/game'

export const CSV_QUESTIONS_COLUMNS = [
  'prompt_text',
  'option1',
  'option2',
  'option3',
  'option4',
  'option5',
  'option6',
  'correct',
  'image_url',
] as const

export const CSV_QUESTIONS_EXAMPLE = `prompt_text;option1;option2;option3;option4;option5;option6;correct;image_url
Столица Франции?;Берлин;Париж;Рим;Мадрид;Вена;Прага;2;
2+2=?;3;4;5;6;22;0;2;
`

export interface CsvParseError {
  line: number
  message: string
}

export interface CsvQuestionDraft {
  line: number
  body: GameQuestionCreate
}

export interface CsvParseResult {
  questions: CsvQuestionDraft[]
  errors: CsvParseError[]
}

const COLUMN_INDEX = {
  prompt_text: 0,
  option1: 1,
  option2: 2,
  option3: 3,
  option4: 4,
  option5: 5,
  option6: 6,
  correct: 7,
  image_url: 8,
} as const

type CsvColumnKey = keyof typeof COLUMN_INDEX

const HEADER_ALIASES: Record<string, CsvColumnKey> = {
  prompt_text: 'prompt_text',
  question: 'prompt_text',
  вопрос: 'prompt_text',
  option1: 'option1',
  option2: 'option2',
  option3: 'option3',
  option4: 'option4',
  option5: 'option5',
  option6: 'option6',
  option_1: 'option1',
  option_2: 'option2',
  option_3: 'option3',
  option_4: 'option4',
  option_5: 'option5',
  option_6: 'option6',
  correct: 'correct',
  правильный: 'correct',
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
    if (char === '"') {
      inQuotes = !inQuotes
      continue
    }
    if (inQuotes) continue
    if (char === ',') commas += 1
    if (char === ';') semicolons += 1
  }

  return semicolons > commas ? ';' : ','
}

function parseCsvLine(line: string, delimiter: string): string[] {
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

function buildQuestionFromRow(
  cells: string[],
  mapping: Array<CsvColumnKey | null> | null,
  modeId: number,
  line: number,
): { question?: CsvQuestionDraft; error?: CsvParseError } {
  const promptText = readField(cells, mapping, 'prompt_text', COLUMN_INDEX.prompt_text)
  const correctRaw = readField(cells, mapping, 'correct', COLUMN_INDEX.correct)
  const imageUrl = readField(cells, mapping, 'image_url', COLUMN_INDEX.image_url)

  if (!promptText) {
    return { error: { line, message: 'Пустой prompt_text (текст вопроса)' } }
  }

  const optionTexts = ([1, 2, 3, 4, 5, 6] as const).map((index) => {
    const key = `option${index}` as CsvColumnKey
    return readField(cells, mapping, key, COLUMN_INDEX[key])
  })

  const emptyOptions = optionTexts
    .map((text, index) => ({ index: index + 1, text }))
    .filter((item) => !item.text)
  if (emptyOptions.length > 0) {
    return {
      error: {
        line,
        message: `Заполните все варианты option1–option6 (пусто: option${emptyOptions[0].index})`,
      },
    }
  }

  const correct = Number.parseInt(correctRaw, 10)
  if (!Number.isInteger(correct) || correct < 1 || correct > 6) {
    return {
      error: {
        line,
        message: `Поле correct должно быть числом от 1 до 6 (получено: "${correctRaw}")`,
      },
    }
  }

  const options: GameOptionInput[] = optionTexts.map((optionText, index) => ({
    option_index: index + 1,
    option_text: optionText,
    is_correct: index + 1 === correct,
  }))

  return {
    question: {
      line,
      body: {
        mode_id: modeId,
        prompt_text: promptText,
        image_url: imageUrl || null,
        options,
      },
    },
  }
}

export function parseQuestionsCsv(content: string, modeId: number): CsvParseResult {
  const normalized = stripBom(content).replace(/\r\n/g, '\n').replace(/\r/g, '\n')
  const rawLines = normalized.split('\n')

  const questions: CsvQuestionDraft[] = []
  const errors: CsvParseError[] = []

  let delimiter: ',' | ';' = ','
  let headerMapping: Array<CsvColumnKey | null> | null = null
  let dataStarted = false

  for (let i = 0; i < rawLines.length; i += 1) {
    const lineNumber = i + 1
    const line = rawLines[i].trim()
    if (!line || line.startsWith('#')) continue

    if (!dataStarted) {
      delimiter = detectDelimiter(line)
      dataStarted = true
    }

    const cells = parseCsvLine(line, delimiter)
    if (cells.every((cell) => !cell)) continue

    if (!headerMapping && isHeaderRow(cells)) {
      headerMapping = mapHeaderRow(cells)
      const hasPrompt = headerMapping.includes('prompt_text')
      const hasCorrect = headerMapping.includes('correct')
      const optionCount = ([1, 2, 3, 4, 5, 6] as const).filter((n) =>
        headerMapping?.includes(`option${n}` as CsvColumnKey),
      ).length
      if (!hasPrompt || !hasCorrect || optionCount !== 6) {
        errors.push({
          line: lineNumber,
          message:
            'Строка заголовка должна содержать prompt_text, option1–option6 и correct',
        })
      }
      continue
    }

    const minColumns = headerMapping ? 3 : CSV_QUESTIONS_COLUMNS.length - 1
    if (cells.length < minColumns) {
      errors.push({
        line: lineNumber,
        message: `Недостаточно колонок (${cells.length}), ожидается минимум ${minColumns}`,
      })
      continue
    }

    const result = buildQuestionFromRow(cells, headerMapping, modeId, lineNumber)
    if (result.error) {
      errors.push(result.error)
      continue
    }
    if (result.question) {
      questions.push(result.question)
    }
  }

  if (!dataStarted) {
    errors.push({ line: 0, message: 'Файл пустой' })
  }

  return { questions, errors }
}

export function downloadCsvTemplate(filename = 'polls-questions-template.csv'): void {
  const blob = new Blob([`\uFEFF${CSV_QUESTIONS_EXAMPLE}`], {
    type: 'text/csv;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}
