import { useRef, useState, type ChangeEvent } from 'react'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { gameService } from '@/services/game-service'
import type { GameMenuNode } from '@/types/game'
import {
  CSV_MENU_COLUMNS,
  CSV_MENU_EXAMPLE,
  downloadMenuCsvTemplate,
  parseMenuCsv,
  type CsvParseError,
  type CsvMenuDraft,
} from '@/utils/csv-menu-parser'

interface MenuCsvImportSectionProps {
  modeId: number | null
  modeTitle?: string
  existingNodes: GameMenuNode[]
  onImported: () => Promise<void>
}

function buildTitleMap(nodes: GameMenuNode[]): Map<string, number> {
  const map = new Map<string, number>()
  for (const node of nodes) {
    map.set(node.title.trim(), node.id)
  }
  return map
}

export function MenuCsvImportSection({
  modeId,
  modeTitle,
  existingNodes,
  onImported,
}: MenuCsvImportSectionProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [fileName, setFileName] = useState('')
  const [parsedNodes, setParsedNodes] = useState<CsvMenuDraft[]>([])
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
    setParsedNodes([])
    setFileName('')

    if (!file || !modeId) return

    setIsParsing(true)
    setFileName(file.name)
    try {
      const text = await file.text()
      const result = parseMenuCsv(text, modeId)
      setParseErrors(result.errors)
      setParsedNodes(result.errors.length > 0 ? [] : result.nodes)

      if (result.nodes.length > 0 && result.errors.length === 0) {
        setImportSuccess(`Готово к импорту: ${result.nodes.length} пункт(ов)`)
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
    if (!modeId || parsedNodes.length === 0) {
      setImportErrors(['Нет валидных строк для импорта'])
      return
    }

    setIsImporting(true)
    setImportErrors([])
    setImportSuccess('')
    setImportProgress('')

    const titleToId = buildTitleMap(existingNodes)
    const failed: string[] = []
    let imported = 0

    for (let i = 0; i < parsedNodes.length; i += 1) {
      const item = parsedNodes[i]
      setImportProgress(`Импорт ${i + 1} из ${parsedNodes.length}…`)

      const parentTitle = item.parentTitle.trim()
      let parentId: number | null = null
      if (parentTitle) {
        parentId = titleToId.get(parentTitle) ?? null
        if (parentId === null) {
          failed.push(`Строка ${item.line}: родитель «${parentTitle}» не найден`)
          continue
        }
      }

      try {
        const created = await gameService.createMenuNodeWithRetry({
          ...item.body,
          parent_id: parentId,
        })
        titleToId.set(item.body.title.trim(), created.id)
        imported += 1
        if (i < parsedNodes.length - 1) {
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
      setImportSuccess(`Импортировано пунктов: ${imported}`)
      await onImported()
    }
    if (failed.length > 0) {
      setImportErrors(failed)
    }

    setParsedNodes([])
    setFileName('')
  }

  return (
    <div className="space-y-4 rounded-xl border border-[var(--border-color)] p-4">
      <div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">Импорт меню из CSV</h3>
        <p className="mt-1 text-xs text-[var(--text-secondary)]">
          Массовая загрузка пунктов в режим{modeTitle ? ` «${modeTitle}»` : ''}.
        </p>
      </div>

      <div className="rounded-lg bg-[var(--bg-tertiary)]/60 p-3 text-xs text-[var(--text-secondary)] space-y-2">
        <p className="font-medium text-[var(--text-primary)]">Колонки CSV</p>
        <p className="font-mono text-[11px]">{CSV_MENU_COLUMNS.join('; ')}</p>
        <ul className="list-disc space-y-1 pl-4">
          <li><code>parent_title</code> — название родителя (пусто = корень). Родитель должен быть выше в файле или уже существовать.</li>
          <li><code>title</code> — заголовок кнопки.</li>
          <li><code>description</code> — описание пункта.</li>
          <li><code>price</code> — цена в рублях (для конечных позиций; у разделов можно оставить пустым).</li>
          <li><code>sort_order</code> — порядок сортировки.</li>
          <li><code>image_url</code> — URL картинки (необязательно).</li>
        </ul>
        <pre className="mt-2 overflow-x-auto rounded bg-[var(--bg-primary)] p-2 text-[11px]">
          {CSV_MENU_EXAMPLE.trim()}
        </pre>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button type="button" variant="secondary" size="sm" onClick={() => downloadMenuCsvTemplate()}>
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
        {parsedNodes.length > 0 && (
          <Button type="button" size="sm" isLoading={isImporting} onClick={handleImport}>
            Импортировать ({parsedNodes.length})
          </Button>
        )}
      </div>

      {fileName && <p className="text-xs text-[var(--text-secondary)]">Файл: {fileName}</p>}
      {importProgress && <p className="text-xs text-[var(--text-secondary)]">{importProgress}</p>}
      {importSuccess && (
        <Alert variant="success" className="text-sm">
          {importSuccess}
        </Alert>
      )}
      {parseErrors.length > 0 && (
        <ul className="space-y-1 text-xs text-red-400">
          {parseErrors.map((err) => (
            <li key={`${err.line}-${err.message}`}>
              {err.line > 0 ? `Строка ${err.line}: ` : ''}
              {err.message}
            </li>
          ))}
        </ul>
      )}
      {importErrors.length > 0 && (
        <ul className="space-y-1 text-xs text-red-400 max-h-40 overflow-y-auto">
          {importErrors.map((msg) => (
            <li key={msg}>{msg}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
