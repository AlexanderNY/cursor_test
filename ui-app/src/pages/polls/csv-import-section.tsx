import { useRef, useState, type ChangeEvent } from 'react'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { gameService } from '@/services/game-service'
import {
  CSV_QUESTIONS_COLUMNS,
  CSV_QUESTIONS_EXAMPLE,
  downloadCsvTemplate,
  parseQuestionsCsv,
  type CsvParseError,
  type CsvQuestionDraft,
} from '@/utils/csv-questions-parser'

interface CsvImportSectionProps {
  modeId: number | null
  modeTitle?: string
  onImported: () => Promise<void>
}

export function CsvImportSection({ modeId, modeTitle, onImported }: CsvImportSectionProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [fileName, setFileName] = useState('')
  const [parsedQuestions, setParsedQuestions] = useState<CsvQuestionDraft[]>([])
  const [parseErrors, setParseErrors] = useState<CsvParseError[]>([])
  const [importErrors, setImportErrors] = useState<string[]>([])
  const [isParsing, setIsParsing] = useState(false)
  const [isImporting, setIsImporting] = useState(false)
  const [importProgress, setImportProgress] = useState('')
  const [importSuccess, setImportSuccess] = useState('')

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = ''
    setImportSuccess('')
    setImportErrors([])
    setImportProgress('')
    setParseErrors([])
    setParsedQuestions([])
    setFileName('')

    if (!file || !modeId) return

    setIsParsing(true)
    setFileName(file.name)
    try {
      const text = await file.text()
      const result = parseQuestionsCsv(text, modeId)
      setParseErrors(result.errors)
      setParsedQuestions(result.errors.length > 0 ? [] : result.questions)

      if (result.questions.length > 0 && result.errors.length === 0) {
        setImportSuccess(`Готово к импорту: ${result.questions.length} вопрос(ов)`)
      } else if (result.errors.length > 0) {
        setImportSuccess('')
      }
    } catch (e) {
      setParseErrors([
        { line: 0, message: e instanceof Error ? e.message : 'Не удалось прочитать файл' },
      ])
    } finally {
      setIsParsing(false)
    }
  }

  async function handleImport() {
    if (!modeId || parsedQuestions.length === 0) {
      setImportErrors(['Нет валидных строк для импорта'])
      return
    }

    setIsImporting(true)
    setImportErrors([])
    setImportSuccess('')
    setImportProgress('')

    const failed: string[] = []
    let imported = 0

    for (let i = 0; i < parsedQuestions.length; i += 1) {
      const item = parsedQuestions[i]
      setImportProgress(`Импорт ${i + 1} из ${parsedQuestions.length}…`)
      try {
        await gameService.createQuestionWithRetry(item.body)
        imported += 1
        if (i < parsedQuestions.length - 1) {
          await new Promise((resolve) => setTimeout(resolve, 50))
        }
      } catch (e) {
        const message = e instanceof Error ? e.message : 'Ошибка создания'
        failed.push(`Строка ${item.line}: ${message}`)
      }
    }

    setImportProgress('')
    setIsImporting(false)

    if (imported > 0) {
      setImportSuccess(`Импортировано вопросов: ${imported}`)
      await onImported()
    }
    if (failed.length > 0) {
      setImportErrors(failed)
    }

    setParsedQuestions([])
    setFileName('')
  }

  return (
    <div className="space-y-4 rounded-xl border border-[var(--border-color)] p-4">
      <div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">Импорт из CSV</h3>
        <p className="mt-1 text-xs text-[var(--text-secondary)]">
          Массовая загрузка вопросов в режим{modeTitle ? ` «${modeTitle}»` : ''}.
        </p>
      </div>

      <div className="rounded-lg bg-[var(--bg-tertiary)]/60 p-3 text-xs text-[var(--text-secondary)] space-y-2">
        <p className="font-medium text-[var(--text-primary)]">Правила заполнения CSV</p>
        <ul className="list-disc space-y-1 pl-4">
          <li>Кодировка UTF-8 (рекомендуется сохранять из Excel/LibreOffice как «CSV UTF-8»).</li>
          <li>
            Разделитель: <strong>точка с запятой (;)</strong> или запятая. Если в тексте есть запятые —
            возьмите поле в кавычки: <code className="text-[var(--text-primary)]">"Париж, Франция"</code>.
          </li>
          <li>
            Первая строка — заголовок (рекомендуется):{' '}
            <code className="text-[var(--text-primary)]">{CSV_QUESTIONS_COLUMNS.join(';')}</code>
          </li>
          <li>Одна строка = один вопрос с ровно <strong>6 вариантами</strong> ответа.</li>
          <li>
            Колонка <code className="text-[var(--text-primary)]">correct</code> — номер правильного
            варианта от <strong>1</strong> до <strong>6</strong> (по порядку option1…option6).
          </li>
          <li>
            Колонка <code className="text-[var(--text-primary)]">image_url</code> необязательна — URL
            из медиатеки (<code className="text-[var(--text-primary)]">public_url</code>) или внешняя
            ссылка.
          </li>
          <li>Строки, начинающиеся с <code className="text-[var(--text-primary)]">#</code>, игнорируются.</li>
          <li>Пустые строки пропускаются.</li>
        </ul>
        <div>
          <p className="mb-1 font-medium text-[var(--text-primary)]">Пример</p>
          <pre className="overflow-x-auto rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] p-2 text-[11px] leading-relaxed text-[var(--text-primary)]">
            {CSV_QUESTIONS_EXAMPLE.trimEnd()}
          </pre>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button type="button" variant="secondary" size="sm" onClick={() => downloadCsvTemplate()}>
          Скачать шаблон
        </Button>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          disabled={!modeId || isParsing || isImporting}
          onClick={() => fileInputRef.current?.click()}
        >
          {isParsing ? 'Чтение…' : 'Выбрать CSV'}
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,text/csv"
          className="hidden"
          onChange={handleFileChange}
        />
        <Button
          type="button"
          size="sm"
          disabled={!modeId || parsedQuestions.length === 0 || isImporting || parseErrors.length > 0}
          isLoading={isImporting}
          onClick={handleImport}
        >
          Импортировать{parsedQuestions.length > 0 ? ` (${parsedQuestions.length})` : ''}
        </Button>
      </div>

      {fileName && (
        <p className="text-xs text-[var(--text-secondary)]">
          Файл: <span className="text-[var(--text-primary)]">{fileName}</span>
        </p>
      )}
      {importProgress && (
        <p className="text-xs text-[var(--text-secondary)]">{importProgress}</p>
      )}
      {importSuccess && (
        <Alert variant="success">{importSuccess}</Alert>
      )}
      {parseErrors.length > 0 && (
        <Alert variant="error">
          <p className="font-medium">Ошибки в CSV</p>
          <ul className="mt-2 list-disc space-y-1 pl-4 text-sm">
            {parseErrors.map((item) => (
              <li key={`${item.line}-${item.message}`}>
                {item.line > 0 ? `Строка ${item.line}: ` : ''}
                {item.message}
              </li>
            ))}
          </ul>
        </Alert>
      )}
      {importErrors.length > 0 && (
        <Alert variant="warning">
          <p className="font-medium">Часть вопросов не импортирована</p>
          <ul className="mt-2 list-disc space-y-1 pl-4 text-sm max-h-40 overflow-y-auto">
            {importErrors.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </Alert>
      )}
      {!modeId && (
        <p className="text-xs text-[var(--text-secondary)]">Сначала выберите режим слева.</p>
      )}
    </div>
  )
}
