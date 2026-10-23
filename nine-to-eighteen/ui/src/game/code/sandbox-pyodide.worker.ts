/// <reference lib="webworker" />

type PyodideInterface = import('pyodide').PyodideInterface

type LoadRequest = { type: 'load'; indexURL: string }
type RunRequest = {
  type: 'run'
  id: number
  code: string
  traceLimit: number
  isolate: boolean
}

let pyodide: PyodideInterface | null = null

const RUNNER = `
import ast as __ast
import builtins as __builtins_mod
import sys as __sys
import traceback as __tb

__trace_count = 0
__trace_limit = int(__sandbox_trace_limit)
__blocked_roots = {"js", "pyodide", "pyodide_js", "micropip"}

def __sandbox_trace(frame, event, arg):
    global __trace_count
    __trace_count += 1
    if __trace_count > __trace_limit:
        raise TimeoutError(
            "Превышен лимит выполнения (возможный бесконечный цикл). "
            "Упростите код или уберите while True."
        )
    return __sandbox_trace

def __sandbox_import(name, globals=None, locals=None, fromlist=(), level=0):
    root = name.split(".")[0]
    if root in __blocked_roots or name in __blocked_roots:
        raise ImportError("import disabled: " + name)
    return __builtins_mod.__import__(name, globals, locals, fromlist, level)

__hidden_modules = {}
for __mod_name in list(__sys.modules):
    if __mod_name.split(".")[0] in __blocked_roots:
        __hidden_modules[__mod_name] = __sys.modules.pop(__mod_name)

__safe_builtins = vars(__builtins_mod).copy()
__safe_builtins["__import__"] = __sandbox_import
if __sandbox_isolate or __sandbox_ns is None:
    __user_ns = {"__name__": "__main__", "__builtins__": __safe_builtins}
else:
    __user_ns = __sandbox_ns
    __user_ns["__builtins__"] = __safe_builtins

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
    __sys.modules.update(__hidden_modules)
`

self.onmessage = async (event: MessageEvent<LoadRequest | RunRequest>) => {
  const data = event.data
  if (data.type === 'load') {
    try {
      self.postMessage({ type: 'progress', value: 0.1, label: 'Загрузка Pyodide…' })
      const { loadPyodide } = await import('pyodide')
      pyodide = await loadPyodide({ indexURL: data.indexURL })
      self.postMessage({ type: 'progress', value: 1, label: 'Готово' })
      self.postMessage({ type: 'ready' })
    } catch (err) {
      self.postMessage({
        type: 'load-error',
        message: err instanceof Error ? err.message : String(err),
      })
    }
    return
  }

  if (!pyodide) {
    self.postMessage({
      type: 'result',
      id: data.id,
      stdout: '',
      stderr: 'Pyodide is not loaded',
      result: '',
      timedOut: false,
    })
    return
  }

  const stdout: string[] = []
  const stderr: string[] = []
  pyodide.setStdout({ batched: (text: string) => stdout.push(text) })
  pyodide.setStderr({ batched: (text: string) => stderr.push(text) })
  pyodide.globals.set('__sandbox_source', data.code)
  pyodide.globals.set('__sandbox_trace_limit', data.traceLimit)
  pyodide.globals.set('__sandbox_isolate', data.isolate)
  if (data.isolate || pyodide.globals.get('__sandbox_ns') === undefined) {
    pyodide.globals.set('__sandbox_ns', null)
  }

  try {
    await pyodide.runPythonAsync(RUNNER)
    if (!data.isolate) {
      pyodide.globals.set('__sandbox_ns', pyodide.globals.get('__user_ns'))
    }
    const timedOut = Boolean(pyodide.globals.get('__sandbox_timed_out'))
    const err = pyodide.globals.get('__sandbox_error')
    let result = ''
    if (err !== undefined && err !== null && String(err) !== 'None') {
      stderr.push(String(err).trimEnd())
    } else {
      const raw = pyodide.globals.get('__sandbox_result')
      if (raw !== undefined && raw !== null && String(raw) !== 'None') {
        result = String(raw)
      }
    }
    self.postMessage({
      type: 'result',
      id: data.id,
      stdout: stdout.join('\n'),
      stderr: stderr.join('\n'),
      result,
      timedOut,
    })
  } catch (err) {
    self.postMessage({
      type: 'result',
      id: data.id,
      stdout: stdout.join('\n'),
      stderr: err instanceof Error ? err.message : String(err),
      result: '',
      timedOut: false,
    })
  }
}
