let assetsPrefetched = false

function getPyodideIndexUrl(): string {
  const base = import.meta.env.BASE_URL ?? '/'
  return `${base}pyodide/`
}

/** Прогревает HTTP-кэш браузера для тяжёлых артефактов WASM (~13 МБ). */
export function prefetchPyodideAssets(): void {
  if (assetsPrefetched) return
  assetsPrefetched = true
  const base = getPyodideIndexUrl()
  for (const fileName of [
    'pyodide.asm.wasm',
    'python_stdlib.zip',
    'pyodide.asm.mjs',
    'pyodide-lock.json',
  ]) {
    void fetch(`${base}${fileName}`)
  }
}

/** Запускает полную загрузку Pyodide в фоне (динамический import, не тянет код игры в главный бандл). */
export function prefetchPyodideRuntime(): void {
  prefetchPyodideAssets()
  void import('./pyodide-loader').then((module) => module.prefetchPyodideRuntime())
}
