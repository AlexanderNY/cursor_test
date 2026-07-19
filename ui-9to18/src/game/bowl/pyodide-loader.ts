import { prefetchPyodideAssets } from './pyodide-prefetch'
import { ENGINE_BOOTSTRAP } from './python-bootstrap'
import { loadEffectiveGameConfig } from './settings-storage'
import {
  PERKS_CONFIG_PATH,
  PY_AI_FILES,
  PY_BASE_PATH,
  PY_FILES,
  PY_VFS_PATH,
  type ProgressCallback,
} from './types'

type PyodideInterface = import('pyodide').PyodideInterface

let pyodideInstance: PyodideInterface | null = null
let loadPromise: Promise<PyodideInterface> | null = null
let progressCallback: ProgressCallback = () => {}
const PY_RUNTIME_VERSION = '22'

function getPyodideIndexUrl(): string {
  const base = import.meta.env.BASE_URL ?? '/'
  return `${base}pyodide/`
}

function reportProgress(value: number, label: string): void {
  progressCallback(value, label)
}

async function fetchPythonFile(relativePath: string): Promise<string> {
  const response = await fetch(`${PY_BASE_PATH}/${relativePath}`)
  if (!response.ok) {
    throw new Error(`Failed to load ${relativePath}: ${response.status}`)
  }
  return response.text()
}

async function fetchPerksJson(): Promise<string> {
  const response = await fetch(PERKS_CONFIG_PATH)
  if (!response.ok) {
    throw new Error(`Failed to load perks.json: ${response.status}`)
  }
  return response.text()
}

function isRuntimeCached(): boolean {
  return (
    pyodideInstance !== null &&
    sessionStorage.getItem('bowl-py-version') === PY_RUNTIME_VERSION
  )
}

async function bootPyodide(): Promise<PyodideInterface> {
  const cachedVersion = sessionStorage.getItem('bowl-py-version')
  if (pyodideInstance && cachedVersion === PY_RUNTIME_VERSION) {
    reportProgress(100, 'Готово')
    return pyodideInstance
  }
  pyodideInstance = null

  const indexURL = getPyodideIndexUrl()
  reportProgress(5, 'Загрузка Pyodide…')

  const { loadPyodide } = await import('pyodide')
  const pyodide = await loadPyodide({
    indexURL,
    packageBaseUrl: indexURL,
  })

  reportProgress(48, 'Загрузка Python-модулей…')
  pyodide.FS.mkdirTree(PY_VFS_PATH)
  pyodide.FS.mkdirTree(`${PY_VFS_PATH}/ai`)

  const allFiles = [...PY_FILES, ...PY_AI_FILES]
  const [effectiveConfig, perksJson, ...pythonSources] = await Promise.all([
    loadEffectiveGameConfig(),
    fetchPerksJson(),
    ...allFiles.map((fileName) => fetchPythonFile(fileName)),
  ])
  const configJson = JSON.stringify(effectiveConfig)

  pyodide.FS.writeFile('/bowl/game-config.json', configJson)
  for (let index = 0; index < allFiles.length; index += 1) {
    pyodide.FS.writeFile(`${PY_VFS_PATH}/${allFiles[index]}`, pythonSources[index])
  }

  reportProgress(82, 'Инициализация движка…')
  pyodide.globals.set('_bowl_config_json', configJson)
  pyodide.globals.set('_bowl_perks_json', perksJson)
  await pyodide.runPythonAsync(`
${ENGINE_BOOTSTRAP}
engine.load_config(_bowl_config_json)
engine.load_perks(_bowl_perks_json)
`)

  reportProgress(100, 'Готово')
  pyodideInstance = pyodide
  sessionStorage.setItem('bowl-py-version', PY_RUNTIME_VERSION)
  return pyodide
}

function startLoad(): Promise<PyodideInterface> {
  if (!loadPromise) {
    loadPromise = bootPyodide().catch((error) => {
      loadPromise = null
      throw error
    })
  }
  return loadPromise
}

/** Запускает полную загрузку заранее (например, при наведении на плитку Bowl). */
export function prefetchPyodideRuntime(onProgress: ProgressCallback = () => {}): Promise<PyodideInterface> {
  prefetchPyodideAssets()
  progressCallback = onProgress
  if (isRuntimeCached()) {
    reportProgress(100, 'Готово')
    return Promise.resolve(pyodideInstance!)
  }
  return startLoad()
}

export async function loadPyodideRuntime(onProgress: ProgressCallback): Promise<PyodideInterface> {
  prefetchPyodideAssets()
  progressCallback = onProgress
  if (isRuntimeCached()) {
    reportProgress(100, 'Готово')
    return pyodideInstance!
  }
  return startLoad()
}

export function getPyodide(): PyodideInterface {
  if (!pyodideInstance) {
    throw new Error('Pyodide is not loaded')
  }
  return pyodideInstance
}
