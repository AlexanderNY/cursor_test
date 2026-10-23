/** Lightweight Pyodide loader for Code sandbox (independent of Bowl game VFS). */

const DEFAULT_TIMEOUT_MS = 5000
const DEFAULT_TRACE_LIMIT = 2_000_000

type WorkerResult = {
  type: 'result'
  id: number
  stdout: string
  stderr: string
  result: string
  timedOut: boolean
}

type WorkerProgress = { type: 'progress'; value: number; label: string }
type WorkerReady = { type: 'ready' }
type WorkerLoadError = { type: 'load-error'; message: string }

let sandboxWorker: Worker | null = null
let loadPromise: Promise<void> | null = null
let nextRunId = 1
const pendingRuns = new Map<number, (value: WorkerResult) => void>()

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

function pyodideIndexUrl(): string {
  const base = import.meta.env.BASE_URL || '/'
  return new URL(`${base}pyodide/`, window.location.origin).href
}

function dropWorker(): void {
  sandboxWorker?.terminate()
  sandboxWorker = null
  loadPromise = null
  for (const [id, resolve] of pendingRuns) {
    pendingRuns.delete(id)
    resolve({
      type: 'result',
      id,
      stdout: '',
      stderr: 'Превышено время выполнения. Runtime остановлен.',
      result: '',
      timedOut: true,
    })
  }
}

function ensureWorker(onProgress?: SandboxProgress): Promise<void> {
  if (loadPromise && sandboxWorker) return loadPromise
  const worker = new Worker(new URL('./sandbox-pyodide.worker.ts', import.meta.url), {
    type: 'module',
  })
  sandboxWorker = worker
  loadPromise = new Promise<void>((resolve, reject) => {
    const onMessage = (event: MessageEvent) => {
      const data = event.data as
        | WorkerResult
        | WorkerProgress
        | WorkerReady
        | WorkerLoadError
      if (data.type === 'progress') {
        onProgress?.(data.value, data.label)
        return
      }
      if (data.type === 'result') {
        const pending = pendingRuns.get(data.id)
        if (!pending) return
        pendingRuns.delete(data.id)
        pending(data)
        return
      }
      if (data.type === 'ready') {
        resolve()
        return
      }
      if (data.type === 'load-error') {
        reject(new Error(data.message))
      }
    }
    worker.addEventListener('message', onMessage)
    worker.postMessage({ type: 'load', indexURL: pyodideIndexUrl() })
  }).catch((err) => {
    dropWorker()
    throw err
  })
  return loadPromise
}

export async function loadSandboxPyodide(onProgress?: SandboxProgress): Promise<void> {
  await ensureWorker(onProgress)
}

/**
 * Run user Python in a worker. The worker is terminated when the wall clock
 * expires, so a stuck runtime cannot keep the page busy.
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

  await loadSandboxPyodide(opts.onProgress)
  const worker = sandboxWorker
  if (!worker) {
    return { stdout: '', stderr: 'Pyodide worker is not running', result: '', timedOut: true }
  }

  const id = nextRunId
  nextRunId += 1

  return new Promise((resolve) => {
    const timer = window.setTimeout(() => {
      pendingRuns.delete(id)
      dropWorker()
      resolve({
        stdout: '',
        stderr: `Превышено время выполнения (${timeoutMs} мс). Код, возможно, всё ещё занят runtime.`,
        result: '',
        timedOut: true,
      })
    }, timeoutMs)

    pendingRuns.set(id, (data) => {
      window.clearTimeout(timer)
      resolve({
        stdout: data.stdout,
        stderr: data.stderr,
        result: data.result,
        timedOut: data.timedOut,
      })
    })

    worker.postMessage({ type: 'run', id, code, traceLimit, isolate })
  })
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
