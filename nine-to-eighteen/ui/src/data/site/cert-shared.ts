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
