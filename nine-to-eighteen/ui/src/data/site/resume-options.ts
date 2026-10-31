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

/** Подписи, которые распознаёт импорт файла на hh.ru. */
export const EMPLOYMENT_HH_LABEL: Record<string, string> = {
  full: 'полная занятость',
  part: 'частичная занятость',
  project: 'проектная работа',
  volunteer: 'волонтерство',
  internship: 'стажировка',
}

export const SCHEDULE_HH_LABEL: Record<string, string> = {
  office: 'полный день',
  remote: 'удаленная работа',
  hybrid: 'гибкий график',
  travel: 'вахтовый метод',
}

export const EDUCATION_LEVEL_OPTIONS: Array<{ id: string; label: string }> = [
  { id: 'secondary', label: 'Среднее' },
  { id: 'special_secondary', label: 'Среднее специальное' },
  { id: 'unfinished_higher', label: 'Неоконченное высшее' },
  { id: 'higher', label: 'Высшее' },
  { id: 'bachelor', label: 'Бакалавр' },
  { id: 'master', label: 'Магистр' },
  { id: 'candidate', label: 'Кандидат наук' },
  { id: 'doctor', label: 'Доктор наук' },
]

const MONTHS_NOM = [
  '',
  'январь',
  'февраль',
  'март',
  'апрель',
  'май',
  'июнь',
  'июль',
  'август',
  'сентябрь',
  'октябрь',
  'ноябрь',
  'декабрь',
]

export const HH_UPLOAD_HINT =
  'На hh.ru: Создать резюме → Загрузить файл. Выберите DOCX — его сайт разбирает точнее, чем PDF. После загрузки проверьте должность, опыт, образование и навыки.'

function monthLabel(yearMonth: string): string {
  const match = /^(\d{4})-(\d{2})$/.exec(yearMonth)
  if (!match) return ''
  const month = Number(match[2])
  if (month < 1 || month > 12) return ''
  const name = MONTHS_NOM[month]
  return `${name.charAt(0).toUpperCase()}${name.slice(1)} ${match[1]}`
}

export function hhPeriodLabel(start: string, end: string): string {
  const startLabel = monthLabel(start)
  if (!startLabel) return ''
  const endLabel = monthLabel(end)
  return endLabel ? `${startLabel} — ${endLabel}` : `${startLabel} — настоящее время`
}

export function hhSalaryLabel(amount: number | null | undefined): string {
  if (amount == null || Number.isNaN(amount) || amount <= 0) return ''
  return `${new Intl.NumberFormat('ru-RU').format(amount)} руб.`
}

export function educationLevelLabel(id: string): string {
  return EDUCATION_LEVEL_OPTIONS.find((option) => option.id === id)?.label || ''
}

export function hhListLabel(ids: string[], labels: Record<string, string>): string {
  return ids
    .map((id) => labels[id] || '')
    .filter(Boolean)
    .join(', ')
}

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
