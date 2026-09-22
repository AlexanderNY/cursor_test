/** Shared HH-resume labels and helpers. */

export const EMPLOYMENT_OPTIONS: Array<{ id: string; label: string }> = [
  { id: 'full', label: 'Полная занятость' },
  { id: 'part', label: 'Частичная занятость' },
  { id: 'project', label: 'Проектная работа' },
  { id: 'volunteer', label: 'Волонтёрство' },
  { id: 'internship', label: 'Стажировка' },
]

export const WORK_FORMAT_OPTIONS: Array<{ id: string; label: string }> = [
  { id: 'office', label: 'Офис' },
  { id: 'remote', label: 'Удалённо' },
  { id: 'hybrid', label: 'Гибрид' },
  { id: 'travel', label: 'Разъездная' },
]

export function toggleInList(list: string[], id: string): string[] {
  return list.includes(id) ? list.filter((x) => x !== id) : [...list, id]
}

export function employmentLabel(ids: string[]): string {
  return ids
    .map((id) => EMPLOYMENT_OPTIONS.find((o) => o.id === id)?.label || id)
    .join(', ')
}

export function workFormatLabel(ids: string[]): string {
  return ids
    .map((id) => WORK_FORMAT_OPTIONS.find((o) => o.id === id)?.label || id)
    .join(', ')
}
