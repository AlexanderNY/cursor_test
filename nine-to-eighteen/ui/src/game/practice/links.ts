export type PracticeLink = {
  href: string
  label: string
}

/** Задача тренажёра, которая проверяет мысль выпуска, а не соседний чеклист. */
export const PRACTICE_BY_SLUG: Record<string, PracticeLink> = {
  'py-intro-python': {
    href: '/game/code?tab=tasks&task=mutable-default',
    label: 'Python: общий список по умолчанию',
  },
  'py-sqlalchemy': {
    href: '/game/code?tab=tasks&task=n-plus-one',
    label: 'Python: один запрос вместо N',
  },
  'py-code-review': {
    href: '/game/code?tab=tasks&task=review-split',
    label: 'Python: разнести сохранение и письмо',
  },
  'fe-event-loop': {
    href: '/game/practice?task=list-keys',
    label: 'React: ключ списка',
  },
  'fe-render-perf': {
    href: '/game/practice?task=extra-render',
    label: 'React: лишний рендер',
  },
  'fe-state-libraries': {
    href: '/game/practice?task=single-state',
    label: 'React: один источник состояния',
  },
  'qa-api-contract-perf': {
    href: '/game/practice?task=broken-api',
    label: 'QA: сломанный ответ API',
  },
  'qa-sql-db-basics': {
    href: '/game/sql?task=inner-join-orders',
    label: 'SQL: сверить заказ и клиента',
  },
  'sa-requirements-basics': {
    href: '/game/practice?task=brief-sort',
    label: 'Аналитик: FR, NFR и пожелание',
  },
  'pm-acceptance': {
    href: '/game/practice?task=keep-criteria',
    label: 'Что оставить в приёмке',
  },
  'sa-rest-basics': {
    href: '/game/practice?task=rest-or-queue',
    label: 'Аналитик: REST или очередь',
  },
  'sa-sync-async-queues': {
    href: '/game/practice?task=rest-or-queue',
    label: 'Аналитик: REST или очередь',
  },
  'beh-star': {
    href: '/game/practice?task=star',
    label: 'STAR за 90 секунд',
  },
}

export function practiceForSlug(slug: string): PracticeLink | undefined {
  return PRACTICE_BY_SLUG[slug]
}
