/** Lightweight Pyodide loader for Code sandbox (independent of Bowl game VFS). */

type PyodideInterface = import('pyodide').PyodideInterface

let sandboxInstance: PyodideInterface | null = null
let loadPromise: Promise<PyodideInterface> | null = null

const DEFAULT_TIMEOUT_MS = 5000
const DEFAULT_TRACE_LIMIT = 2_000_000

function pyodideIndexUrl(): string {
  const base = import.meta.env.BASE_URL || '/'
  return `${base}pyodide/`
}

export type SandboxProgress = (value: number, label: string) => void

export type SandboxRunOptions = {
  onProgress?: SandboxProgress
  /** Wall-clock limit; default 5000ms. */
  timeoutMs?: number
  /** Max Python trace events before abort; default 2_000_000. */
  traceLimit?: number
  /** When false, reuse globals between runs (REPL). Default true = clean namespace. */
  isolate?: boolean
}

export type SandboxRunResult = {
  stdout: string
  stderr: string
  result: string
  timedOut?: boolean
}

export async function loadSandboxPyodide(
  onProgress?: SandboxProgress,
): Promise<PyodideInterface> {
  if (sandboxInstance) {
    return sandboxInstance
  }
  if (loadPromise) {
    return loadPromise
  }
  loadPromise = (async () => {
    onProgress?.(0.1, 'Загрузка Pyodide…')
    const { loadPyodide } = await import('pyodide')
    const pyodide = await loadPyodide({
      indexURL: pyodideIndexUrl(),
    })
    onProgress?.(1, 'Готово')
    sandboxInstance = pyodide
    return pyodide
  })()
  try {
    return await loadPromise
  } catch (err) {
    loadPromise = null
    throw err
  }
}

function readPyString(value: unknown): string {
  if (value === undefined || value === null) {
    return ''
  }
  return String(value)
}

/**
 * Run user Python in an isolated namespace (by default) with a soft timeout.
 * Pure-Python infinite loops are stopped via sys.settrace; wall-clock race covers
 * long-running work that still yields to the event loop.
 */
export async function runPythonInSandbox(
  code: string,
  options: SandboxRunOptions | SandboxProgress = {},
): Promise<SandboxRunResult> {
  const opts: SandboxRunOptions =
    typeof options === 'function' ? { onProgress: options } : options
  const timeoutMs = opts.timeoutMs ?? DEFAULT_TIMEOUT_MS
  const traceLimit = opts.traceLimit ?? DEFAULT_TRACE_LIMIT
  const isolate = opts.isolate !== false

  const pyodide = await loadSandboxPyodide(opts.onProgress)
  const stdout: string[] = []
  const stderr: string[] = []
  pyodide.setStdout({
    batched: (text: string) => {
      stdout.push(text)
    },
  })
  pyodide.setStderr({
    batched: (text: string) => {
      stderr.push(text)
    },
  })

  let timedOut = false
  let result = ''

  const runIsolated = async () => {
    pyodide.globals.set('__sandbox_source', code)
    pyodide.globals.set('__sandbox_trace_limit', traceLimit)
    await pyodide.runPythonAsync(`
import ast as __ast
import sys as __sys
import traceback as __tb

__trace_count = 0
__trace_limit = int(__sandbox_trace_limit)

def __sandbox_trace(frame, event, arg):
    global __trace_count
    __trace_count += 1
    if __trace_count > __trace_limit:
        raise TimeoutError(
            "Превышен лимит выполнения (возможный бесконечный цикл). "
            "Упростите код или уберите while True."
        )
    return __sandbox_trace

__user_ns = {"__name__": "__main__", "__builtins__": __builtins__}
__sandbox_result = None
__sandbox_error = None
__sandbox_timed_out = False
__sys.settrace(__sandbox_trace)
try:
    __source = str(__sandbox_source)
    __tree = __ast.parse(__source, mode="exec")
    __last_expr = None
    if __tree.body and isinstance(__tree.body[-1], __ast.Expr):
        __last_expr = __tree.body.pop()
    exec(compile(__tree, "<sandbox>", "exec"), __user_ns)
    if __last_expr is not None:
        __sandbox_result = eval(
            compile(__ast.Expression(__last_expr.value), "<sandbox>", "eval"),
            __user_ns,
        )
except TimeoutError as __exc:
    __sandbox_timed_out = True
    __sandbox_error = str(__exc)
except Exception:
    __sandbox_error = __tb.format_exc()
finally:
    __sys.settrace(None)
`)
    timedOut = Boolean(pyodide.globals.get('__sandbox_timed_out'))
    const err = pyodide.globals.get('__sandbox_error')
    if (err !== undefined && err !== null && String(err) !== 'None') {
      stderr.push(readPyString(err).trimEnd())
    } else {
      const raw = pyodide.globals.get('__sandbox_result')
      if (raw !== undefined && raw !== null && String(raw) !== 'None') {
        result = readPyString(raw)
      }
    }
  }

  const runShared = async () => {
    try {
      const raw = await pyodide.runPythonAsync(code)
      if (raw !== undefined && raw !== null) {
        result = String(raw)
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      stderr.push(message)
    }
  }

  let timer: ReturnType<typeof setTimeout> | undefined
  const timeoutPromise = new Promise<void>((resolve) => {
    timer = setTimeout(() => {
      timedOut = true
      stderr.push(
        `Превышено время выполнения (${timeoutMs} мс). Код, возможно, всё ещё занят runtime.`,
      )
      resolve()
    }, timeoutMs)
  })

  try {
    await Promise.race([isolate ? runIsolated() : runShared(), timeoutPromise])
  } finally {
    if (timer) {
      clearTimeout(timer)
    }
  }

  return {
    stdout: stdout.join('\n'),
    stderr: stderr.join('\n'),
    result,
    timedOut,
  }
}

/**
 * Execute student code then a checker snippet that may call student functions.
 * Checker runs in the same namespace as student code (after student exec).
 */
export async function runPythonWithChecker(
  studentCode: string,
  checkerCode: string,
  options: SandboxRunOptions = {},
): Promise<SandboxRunResult & { passed: boolean; feedback: string }> {
  const combined = `${studentCode}\n\n# --- checks ---\n${checkerCode}\n`
  const run = await runPythonInSandbox(combined, {
    ...options,
    isolate: true,
  })
  const feedbackLine =
    run.stdout
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .find((line) => line.startsWith('PASS:') || line.startsWith('FAIL:')) || ''
  const passed = feedbackLine.startsWith('PASS:')
  const feedback = feedbackLine
    ? feedbackLine.replace(/^(PASS|FAIL):\s*/, '')
    : run.stderr.trim() ||
      (run.timedOut ? 'Превышено время выполнения' : 'Проверка не вернула результат')
  return { ...run, passed, feedback }
}

/** Extract fenced ```python blocks from markdown lab text. */
export function extractPythonBlocks(markdown: string): string[] {
  const blocks: string[] = []
  const pattern = /```(?:python|py)\s*\n([\s\S]*?)```/gi
  let match: RegExpExecArray | null
  while ((match = pattern.exec(markdown)) !== null) {
    const body = match[1]?.trim()
    if (body) {
      blocks.push(body)
    }
  }
  return blocks
}

/** Format sandbox channels for UI pre blocks. */
export function formatRunChannels(run: SandboxRunResult): string {
  const parts: string[] = []
  if (run.stdout.trim()) {
    parts.push(run.stdout.trimEnd())
  }
  if (run.result.trim()) {
    parts.push(`⟹ ${run.result}`)
  }
  if (run.stderr.trim()) {
    parts.push(`Error:\n${run.stderr.trimEnd()}`)
  }
  return parts.join('\n\n') || '(нет вывода)'
}
