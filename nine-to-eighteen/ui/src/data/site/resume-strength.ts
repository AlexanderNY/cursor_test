/** Клиентский пересчёт силы резюме (зеркало resume_strength.py). */
export const PHOTO_POINTS = 10
export const ABOUT_POINTS = 15
export const ABOUT_MIN_LEN = 40
export const LEARN_POINTS_PER_MODULE = 20
export const MAX_STRENGTH_SCORE = 100

export type StrengthAction = {
  id: string
  points: number
  title: string
  href?: string | null
  slug?: string
}

export type StrengthLiveInput = {
  hasPhoto: boolean
  about: string
  doneRelevantSlugs: string[]
  missingRelevantSlugs: string[]
}

export function computeStrengthLive(input: StrengthLiveInput): {
  score: number
  maxScore: number
  actions: StrengthAction[]
} {
  let score = 0
  const actions: StrengthAction[] = []
  if (input.hasPhoto) {
    score += PHOTO_POINTS
  } else {
    actions.push({
      id: 'photo',
      points: PHOTO_POINTS,
      title: `Загрузите фото в кабинете (+${PHOTO_POINTS}%)`,
      href: '/account',
    })
  }
  const aboutOk = input.about.trim().length >= ABOUT_MIN_LEN
  if (aboutOk) {
    score += ABOUT_POINTS
  } else {
    actions.push({
      id: 'about',
      points: ABOUT_POINTS,
      title: `Заполните «О себе» (≥${ABOUT_MIN_LEN} символов, +${ABOUT_POINTS}%)`,
      href: null,
    })
  }
  score += LEARN_POINTS_PER_MODULE * input.doneRelevantSlugs.length
  for (const slug of input.missingRelevantSlugs.slice(0, 5)) {
    actions.push({
      id: `learn:${slug}`,
      points: LEARN_POINTS_PER_MODULE,
      title: `Пройдите модуль (${slug}), чтобы получить +${LEARN_POINTS_PER_MODULE}%`,
      href: `/game/learn/${slug}`,
      slug,
    })
  }
  return {
    score: Math.min(MAX_STRENGTH_SCORE, score),
    maxScore: MAX_STRENGTH_SCORE,
    actions,
  }
}
