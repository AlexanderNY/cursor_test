import CodeMirror from '@uiw/react-codemirror'
import { python } from '@codemirror/lang-python'
import { sql } from '@codemirror/lang-sql'
import { EditorView, keymap } from '@codemirror/view'
import { Prec } from '@codemirror/state'

/** VS Code–ish dark palette for the Code IDE shell. */
const ideEditorTheme = EditorView.theme(
  {
    '&': {
      backgroundColor: '#0d1117',
      color: '#e6edf3',
    },
    '.cm-content': {
      caretColor: '#58a6ff',
      fontFamily:
        '"JetBrains Mono", "Cascadia Code", "Fira Code", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
      fontSize: '13px',
      lineHeight: '1.55',
      padding: '0.5rem 0',
    },
    '.cm-cursor, .cm-dropCursor': {
      borderLeftColor: '#58a6ff',
    },
    '&.cm-focused .cm-selectionBackground, .cm-selectionBackground, .cm-content ::selection':
      {
        backgroundColor: 'rgba(56, 139, 253, 0.35)',
      },
    '.cm-activeLine': {
      backgroundColor: 'rgba(110, 118, 129, 0.12)',
    },
    '.cm-gutters': {
      backgroundColor: '#0d1117',
      color: '#484f58',
      border: 'none',
      borderRight: '1px solid #21262d',
      minWidth: '2.75rem',
    },
    '.cm-activeLineGutter': {
      backgroundColor: 'rgba(110, 118, 129, 0.12)',
      color: '#8b949e',
    },
    '.cm-lineNumbers .cm-gutterElement': {
      padding: '0 0.65rem 0 0.4rem',
    },
  },
  { dark: true },
)

type CodeSandboxEditorProps = {
  id?: string
  value: string
  onChange: (value: string) => void
  onRun?: () => void
  disabled?: boolean
  minHeight?: string
  language?: 'python' | 'sql' | 'shell'
}

export function CodeSandboxEditor({
  id,
  value,
  onChange,
  onRun,
  disabled = false,
  minHeight = '18rem',
  language = 'python',
}: CodeSandboxEditorProps) {
  const runKeymap = Prec.highest(
    keymap.of([
      {
        key: 'Ctrl-Enter',
        run: () => {
          onRun?.()
          return true
        },
      },
      {
        key: 'Mod-Enter',
        run: () => {
          onRun?.()
          return true
        },
      },
    ]),
  )

  const languageExtensions =
    language === 'sql'
      ? [sql()]
      : language === 'shell'
        ? []
        : [python()]

  return (
    <div
      id={id}
      className={`code-sandbox-cm${disabled ? ' code-sandbox-cm--disabled' : ''}`}
    >
      <CodeMirror
        value={value}
        height={minHeight}
        theme="none"
        editable={!disabled}
        basicSetup={{
          lineNumbers: true,
          foldGutter: false,
          highlightActiveLine: true,
          autocompletion: false,
          tabSize: 4,
        }}
        extensions={[
          ...languageExtensions,
          runKeymap,
          EditorView.lineWrapping,
          ideEditorTheme,
        ]}
        onChange={onChange}
      />
    </div>
  )
}
