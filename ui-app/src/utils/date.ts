/** Display dates as DD.MM.YYYY HH:MM in local time. */

export function formatDateTime(
  value?: string | number | Date | null,
  empty: string = '—',
): string {
  if (value === null || value === undefined || value === '') return empty
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) {
    return typeof value === 'string' ? value : empty
  }
  const dd = String(date.getDate()).padStart(2, '0')
  const mm = String(date.getMonth() + 1).padStart(2, '0')
  const yyyy = String(date.getFullYear())
  const hh = String(date.getHours()).padStart(2, '0')
  const min = String(date.getMinutes()).padStart(2, '0')
  return `${dd}.${mm}.${yyyy} ${hh}:${min}`
}

/** Date only: DD.MM.YYYY */
export function formatDateOnly(
  value?: string | number | Date | null,
  empty: string = '—',
): string {
  const full = formatDateTime(value, '')
  if (!full) return empty
  return full.slice(0, 10)
}
