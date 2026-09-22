/** Lightweight Pyodide loader for Code sandbox (independent of Bowl game VFS). */

type PyodideInterface = import('pyodide').PyodideInterface

let sandboxInstance: PyodideInterface | null = null
let loadPromise: Promise<PyodideInterface> | null = null

function pyodideIndexUrl(): string {
  const base = import.meta.env.BASE_URL || '/'
  return `${base}pyodide/`
}

export type SandboxProgress = (value: number, label: string) => void

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

export async function runPythonInSandbox(
  code: string,
  onProgress?: SandboxProgress,
): Promise<{ stdout: string; stderr: string; result: string }> {
  const pyodide = await loadSandboxPyodide(onProgress)
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
  let result = ''
  try {
    const raw = await pyodide.runPythonAsync(code)
    if (raw !== undefined && raw !== null) {
      result = String(raw)
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    stderr.push(message)
  }
  return {
    stdout: stdout.join('\n'),
    stderr: stderr.join('\n'),
    result,
  }
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
