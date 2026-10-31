export type CertTone = {
  a: string
  b: string
  c: string
}

export const TRACK_TONES: Record<string, CertTone> = {
  b: { a: '#5eead4', b: '#fde68a', c: '#a5b4fc' },
  s01: { a: '#fbbf24', b: '#fb7185', c: '#fdba74' },
  py: { a: '#c4b5fd', b: '#67e8f9', c: '#f9a8d4' },
  qa: { a: '#fda4af', b: '#fde68a', c: '#fb923c' },
  map: { a: '#7dd3fc', b: '#86efac', c: '#fde68a' },
  interview: { a: '#34d399', b: '#fbbf24', c: '#67e8f9' },
  other: { a: '#cbd5e1', b: '#5eead4', c: '#a5b4fc' },
}

export const INTERVIEW_CERT_TRACK_ID = 'interview'
export const INTERVIEW_CERT_PERCENT = 100
export const INTERVIEW_CERT_MIN_TOTAL = 10

export function toneOf(trackId: string): CertTone {
  return TRACK_TONES[trackId] ?? TRACK_TONES.other
}

export function splitTrackTitle(title: string): { series: string; name: string } {
  const parts = title.split(' · ')
  if (parts.length < 2) {
    return { series: '9to18', name: title }
  }
  return { series: parts[0], name: parts.slice(1).join(' · ') }
}

export function formatCertDate(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) {
    return new Date().toLocaleDateString('ru-RU')
  }
  return date.toLocaleDateString('ru-RU')
}

const CERT_MONTHS = [
  'января',
  'февраля',
  'марта',
  'апреля',
  'мая',
  'июня',
  'июля',
  'августа',
  'сентября',
  'октября',
  'ноября',
  'декабря',
]

export function formatCertDateLong(iso: string): string {
  const date = new Date(iso)
  if (!iso || Number.isNaN(date.getTime())) {
    return ''
  }
  return `${date.getDate()} ${CERT_MONTHS[date.getMonth()]} ${date.getFullYear()} г.`
}

/** Фамилия Имя Отчество. Логин — если в профиле нет имени. */
export function certHolderName(
  firstName: string,
  lastName: string,
  patronymic = '',
  fallback = '',
): string {
  const last = lastName.trim()
  const first = firstName.trim()
  const middle = patronymic.trim()
  if (last && first) {
    return [last, first, middle].filter(Boolean).join(' ')
  }
  const partial = [last, first, middle].filter(Boolean).join(' ')
  if (partial) {
    return partial
  }
  return fallback.trim() || 'Участник'
}

export function sumDurationMinutes(episodes: { durationMin?: number }[]): number {
  return episodes.reduce((sum, episode) => sum + Math.max(0, Number(episode.durationMin) || 0), 0)
}

export function formatCourseDuration(totalMin: number): string {
  const minutes = Math.max(0, Math.round(totalMin))
  if (minutes <= 0) {
    return ''
  }
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  if (hours === 0) {
    return `около ${rest} мин`
  }
  if (rest === 0) {
    return `около ${hours} ч`
  }
  return `около ${hours} ч ${rest} мин`
}

export type CertTopicLine = {
  key: string
  code: string
  title: string
}

export function certTopicLines(
  episodes: { slug: string; episode: string; title: string }[],
  completed: ReadonlySet<string> | null,
): CertTopicLine[] {
  return episodes
    .filter((episode) => completed == null || completed.has(episode.slug))
    .map((episode) => ({
      key: episode.slug,
      code: episode.episode,
      title: episode.title,
    }))
}

export function printCertificate(trackId: string) {
  const cards = document.querySelectorAll<HTMLElement>('.cert-diploma')
  cards.forEach((card) => {
    if (card.getAttribute('data-cert-id') === trackId) {
      card.classList.add('is-print-target')
    } else {
      card.classList.add('no-print')
    }
  })
  window.print()
  cards.forEach((card) => {
    card.classList.remove('is-print-target', 'no-print')
  })
}

export function certPublicPath(code: string): string {
  return `/game/cert/${code}`
}
