import { useRef, useState } from 'react'
import { MarkdownBody } from '@/components/learn-markdown'

type MarkdownFieldProps = {
  label: string
  value: string
  onChange: (next: string) => void
  rows?: number
  placeholder?: string
}

type ToolbarAction =
  | { id: string; label: string; title: string; run: () => void }
  | { id: string; label: string; separator: true }

function applyWrap(
  value: string,
  start: number,
  end: number,
  before: string,
  after: string,
  placeholder: string,
): { next: string; selectStart: number; selectEnd: number } {
  const selected = value.slice(start, end)
  const inner = selected || placeholder
  const next = `${value.slice(0, start)}${before}${inner}${after}${value.slice(end)}`
  if (selected) {
    return {
      next,
      selectStart: start + before.length,
      selectEnd: start + before.length + inner.length,
    }
  }
  return {
    next,
    selectStart: start + before.length,
    selectEnd: start + before.length + inner.length,
  }
}

function applyLinePrefix(
  value: string,
  start: number,
  end: number,
  prefix: string,
): { next: string; selectStart: number; selectEnd: number } {
  const lineStart = value.lastIndexOf('\n', Math.max(0, start - 1)) + 1
  let lineEnd = value.indexOf('\n', end)
  if (lineEnd < 0) {
    lineEnd = value.length
  }
  const block = value.slice(lineStart, lineEnd)
  const lines = block.split('\n')
  const rewritten = lines
    .map((line) => {
      if (!line.trim()) {
        return line
      }
      if (line.startsWith(prefix)) {
        return line
      }
      return `${prefix}${line}`
    })
    .join('\n')
  const next = `${value.slice(0, lineStart)}${rewritten}${value.slice(lineEnd)}`
  return {
    next,
    selectStart: lineStart,
    selectEnd: lineStart + rewritten.length,
  }
}

export function MarkdownField({
  label,
  value,
  onChange,
  rows = 6,
  placeholder,
}: MarkdownFieldProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [mode, setMode] = useState<'edit' | 'preview'>('edit')

  const commit = (next: string, selectStart: number, selectEnd: number): void => {
    onChange(next)
    requestAnimationFrame(() => {
      const el = textareaRef.current
      if (!el) {
        return
      }
      el.focus()
      el.setSelectionRange(selectStart, selectEnd)
    })
  }

  const withSelection = (
    transform: (
      value: string,
      start: number,
      end: number,
    ) => { next: string; selectStart: number; selectEnd: number },
  ): void => {
    const el = textareaRef.current
    const start = el?.selectionStart ?? value.length
    const end = el?.selectionEnd ?? value.length
    const result = transform(value, start, end)
    commit(result.next, result.selectStart, result.selectEnd)
  }

  const insertLink = (): void => {
    const href = window.prompt('URL ссылки', 'https://')
    if (!href) {
      return
    }
    withSelection((text, start, end) => {
      const selected = text.slice(start, end) || 'текст'
      const before = '['
      const after = `](${href})`
      return applyWrap(text, start, end, before, after, selected)
    })
  }

  const actions: ToolbarAction[] = [
    {
      id: 'h2',
      label: 'H2',
      title: 'Заголовок ##',
      run: () => withSelection((text, start, end) => applyLinePrefix(text, start, end, '## ')),
    },
    {
      id: 'h3',
      label: 'H3',
      title: 'Заголовок ###',
      run: () => withSelection((text, start, end) => applyLinePrefix(text, start, end, '### ')),
    },
    { id: 'sep1', label: '|', separator: true },
    {
      id: 'b',
      label: 'B',
      title: 'Жирный',
      run: () =>
        withSelection((text, start, end) => applyWrap(text, start, end, '**', '**', 'жирный')),
    },
    {
      id: 'i',
      label: 'I',
      title: 'Курсив',
      run: () =>
        withSelection((text, start, end) => applyWrap(text, start, end, '*', '*', 'курсив')),
    },
    {
      id: 'code',
      label: '</>',
      title: 'Инлайн-код',
      run: () =>
        withSelection((text, start, end) => applyWrap(text, start, end, '`', '`', 'code')),
    },
    { id: 'sep2', label: '|', separator: true },
    {
      id: 'ul',
      label: '•',
      title: 'Маркированный список',
      run: () => withSelection((text, start, end) => applyLinePrefix(text, start, end, '- ')),
    },
    {
      id: 'ol',
      label: '1.',
      title: 'Нумерованный список',
      run: () => withSelection((text, start, end) => applyLinePrefix(text, start, end, '1. ')),
    },
    {
      id: 'quote',
      label: '«»',
      title: 'Цитата',
      run: () => withSelection((text, start, end) => applyLinePrefix(text, start, end, '> ')),
    },
    { id: 'sep3', label: '|', separator: true },
    {
      id: 'a',
      label: 'A',
      title: 'Ссылка',
      run: insertLink,
    },
    {
      id: 'fence',
      label: '```',
      title: 'Блок кода',
      run: () =>
        withSelection((text, start, end) => {
          const selected = text.slice(start, end) || 'code'
          const before = '```\n'
          const after = '\n```'
          return applyWrap(text, start, end, before, after, selected)
        }),
    },
  ]

  return (
    <div className="markdown-field">
      <div className="markdown-field-head">
        <span className="markdown-field-label">{label}</span>
        <div className="markdown-field-modes" role="group" aria-label="Режим поля">
          <button
            type="button"
            className={
              mode === 'edit' ? 'markdown-field-mode markdown-field-mode-active' : 'markdown-field-mode'
            }
            onClick={() => setMode('edit')}
          >
            Редактор
          </button>
          <button
            type="button"
            className={
              mode === 'preview'
                ? 'markdown-field-mode markdown-field-mode-active'
                : 'markdown-field-mode'
            }
            onClick={() => setMode('preview')}
          >
            Превью
          </button>
        </div>
      </div>

      {mode === 'edit' ? (
        <>
          <div className="markdown-field-toolbar" role="toolbar" aria-label={label}>
            {actions.map((action) =>
              'separator' in action ? (
                <span key={action.id} className="markdown-field-sep" aria-hidden>
                  |
                </span>
              ) : (
                <button
                  key={action.id}
                  type="button"
                  className="markdown-field-btn"
                  title={action.title}
                  onMouseDown={(event) => {
                    event.preventDefault()
                    action.run()
                  }}
                >
                  {action.label}
                </button>
              ),
            )}
          </div>
          <textarea
            ref={textareaRef}
            className="learn-admin-textarea markdown-field-textarea"
            rows={rows}
            value={value}
            placeholder={placeholder}
            onChange={(event) => onChange(event.target.value)}
            spellCheck={false}
          />
        </>
      ) : (
        <div className="markdown-field-preview">
          {value.trim() ? (
            <MarkdownBody content={value} />
          ) : (
            <p className="learn-section-note">Пусто — нечего показывать.</p>
          )}
        </div>
      )}
    </div>
  )
}
