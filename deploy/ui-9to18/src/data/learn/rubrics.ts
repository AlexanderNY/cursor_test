import type { LearnRubric } from './types'

export const learnRubrics: LearnRubric[] = [
  {
    id: 'architecture',
    title: 'Архитектура',
    subtitle: 'Карта системы без кода',
    order: 1,
  },
  {
    id: 'api',
    title: 'Анализ и API',
    subtitle: 'Боль → контракт → роутер',
    order: 2,
  },
  {
    id: 'data',
    title: 'Данные',
    subtitle: 'PostgreSQL и SQL',
    order: 3,
  },
  {
    id: 'frontend',
    title: 'Frontend',
    subtitle: 'UI поверх готового API',
    order: 4,
  },
  {
    id: 'tools',
    title: 'Инструменты',
    subtitle: 'Git, проверка API, regex',
    order: 5,
  },
]
