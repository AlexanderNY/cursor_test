/** Путь фото с API в адрес, который открывает браузер через прокси /api. */
export function avatarPublicSrc(path?: string | null, cacheKey?: number): string | null {
  if (!path) return null
  const absolute = path.startsWith('http://') || path.startsWith('https://') || path.startsWith('/api/')
    ? path
    : path.startsWith('/')
      ? `/api${path}`
      : path
  if (cacheKey == null) return absolute
  const join = absolute.includes('?') ? '&' : '?'
  return `${absolute}${join}v=${cacheKey}`
}
