import { useEffect, useRef } from 'react'
import { plainTextToHtml, sanitizeLearnHtml } from '@/data/learn/sanitize-html'

interface HtmlEditorProps {
  label: string
  value: string
  onChange: (html: string) => void
}

type ToolbarAction =
  | { id: string; label: string; run: () => void }
  | { id: string; label: string; separator: true }

function exec(command: string, value?: string): void {
  document.execCommand(command, false, value)
}

export function HtmlEditor({ label, value, onChange }: HtmlEditorProps) {
  const editorRef = useRef<HTMLDivElement>(null)
  const lastValueRef = useRef<string>('')

  useEffect(() => {
    if (!editorRef.current) {
      return
    }
    const nextHtml = sanitizeLearnHtml(plainTextToHtml(value))
    if (nextHtml === lastValueRef.current) {
      return
    }
    editorRef.current.innerHTML = nextHtml
    lastValueRef.current = nextHtml
  }, [value])

  const emitChange = (): void => {
    if (!editorRef.current) {
      return
    }
    const html = sanitizeLearnHtml(editorRef.current.innerHTML)
    lastValueRef.current = html
    onChange(html)
  }

  const wrapCode = (): void => {
    const selection = window.getSelection()
    if (!selection || selection.rangeCount === 0) {
      return
    }
    const text = selection.toString() || 'code'
    exec('insertHTML', `<code>${text.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code>`)
    emitChange()
  }

  const insertLink = (): void => {
    const href = window.prompt('URL ссылки', 'https://')
    if (!href) {
      return
    }
    exec('createLink', href)
    emitChange()
  }

  const insertImage = (): void => {
    const src = window.prompt('URL картинки', 'https://')
    if (!src) {
      return
    }
    const alt = window.prompt('Alt текст', '') ?? ''
    exec('insertHTML', `<img src="${src}" alt="${alt.replace(/"/g, '&quot;')}" />`)
    emitChange()
  }

  const actions: ToolbarAction[] = [
    { id: 'h1', label: 'H1', run: () => exec('formatBlock', 'H1') },
    { id: 'h2', label: 'H2', run: () => exec('formatBlock', 'H2') },
    { id: 'h3', label: 'H3', run: () => exec('formatBlock', 'H3') },
    { id: 'sep1', label: '|', separator: true },
    { id: 'b', label: 'B', run: () => exec('bold') },
    { id: 'p', label: 'P', run: () => exec('formatBlock', 'P') },
    { id: 'li', label: 'LI', run: () => exec('insertUnorderedList') },
    { id: 'sep2', label: '|', separator: true },
    { id: 'a', label: 'A', run: insertLink },
    { id: 'img', label: 'IMG', run: insertImage },
    { id: 'code', label: '</>', run: wrapCode },
  ]

  return (
    <div className="html-editor">
      <div className="html-editor-label">{label}</div>
      <div className="html-editor-toolbar" role="toolbar" aria-label={label}>
        {actions.map((action) =>
          'separator' in action ? (
            <span key={action.id} className="html-editor-sep" aria-hidden>
              |
            </span>
          ) : (
            <button
              key={action.id}
              type="button"
              className="html-editor-btn"
              onMouseDown={(event) => {
                event.preventDefault()
                action.run()
                editorRef.current?.focus()
                emitChange()
              }}
            >
              {action.label}
            </button>
          ),
        )}
      </div>
      <div
        ref={editorRef}
        className="html-editor-surface learn-markdown"
        contentEditable
        suppressContentEditableWarning
        role="textbox"
        aria-multiline="true"
        aria-label={label}
        onInput={emitChange}
        onBlur={emitChange}
      />
    </div>
  )
}
