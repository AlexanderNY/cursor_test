export type Section = {
  slug: string
  title: string
  subtitle: string
  description: string
  accent: string
  emoji?: string
  href?: string
  appPath?: string
}

export const sections: Section[] = [
  {
    slug: 'bowl',
    title: 'Bowl',
    subtitle: 'Игра и заказы',
    description:
      '2D-игра на Python в браузере: сражения, прокачка персонажа и внутриигровые заказы.',
    accent: '#34d399',
    emoji: '🎳',
    appPath: '/game/bowl',
  },
  {
    slug: 'learn',
    title: 'Learn',
    subtitle: 'Теория, лабы, шпаргалки',
    description:
      'Учебные материалы по сборке сервисов: теория, лабораторные работы и краткие шпаргалки.',
    accent: '#2dd4bf',
    emoji: '📚',
    appPath: '/game/learn',
  },
  {
    slug: 'learning-map',
    title: 'Карта обучения',
    subtitle: 'Mind map · собеседование',
    description:
      'Интерактивная карта подготовки к собеседованию: ветки тем и конспект из Markdown.',
    accent: '#2dd4bf',
    emoji: '🗺️',
    appPath: '/game/learning-map',
  },
  {
    slug: 'e2e-tester',
    title: 'E2E Tester',
    subtitle: 'Playwright · сценарии',
    description:
      'On-demand браузерные E2E против живого стека: YAML/JSON шаги, Playwright-скрипты, креды и артефакты прогонов.',
    accent: '#f43f5e',
    emoji: '🧪',
    href: 'http://127.0.0.1:8300',
  },
  {
    slug: 'menu',
    title: 'Menu',
    subtitle: 'Каталог и корзина',
    description:
      'Каталог материалов и позиций с корзиной — удобный обзор и оформление заказов.',
    accent: '#fbbf24',
    emoji: '📋',
  },
  {
    slug: 'rating',
    title: 'Rating',
    subtitle: 'Таблица лидеров',
    description:
      'Рейтинг участников: результаты игр, тестов и активности в учебных модулях.',
    accent: '#a78bfa',
    emoji: '🏆',
  },
  {
    slug: 'events',
    title: 'Events',
    subtitle: 'Мероприятия',
    description:
      'Календарь событий: стримы, воркшопы, дедлайны домашних заданий и офлайн-встречи.',
    accent: '#f472b6',
    emoji: '📅',
  },
  {
    slug: 'copyparse',
    title: 'CopyParse',
    subtitle: 'SaaS · copyparse.ru',
    description:
      'Платформа кросспостинга и SMM — рабочий стенд из учебного курса: бренды, каналы, календарь, inbox.',
    accent: '#fb923c',
    emoji: '🚀',
    href: 'https://www.copyparse.ru',
  },
  {
    slug: 'profile',
    title: 'Profile',
    subtitle: 'Личный кабинет',
    description: 'Прогресс Learn, настройки и доступы.',
    accent: '#38bdf8',
    emoji: '👤',
    appPath: '/account',
  },
  {
    slug: 'help',
    title: 'Help',
    subtitle: 'Помощь и FAQ',
    description:
      'Справка по платформе: частые вопросы, инструкции и подсказки по разделам.',
    accent: '#94a3b8',
    emoji: '💬',
  },
  {
    slug: 'tasks',
    title: 'Tasks',
    subtitle: 'Чек-лист Learn',
    description: 'Личные задачи и прогресс по выпускам Learn.',
    accent: '#4ade80',
    emoji: '✅',
    appPath: '/game/tasks',
  },
  {
    slug: 'chat',
    title: 'Chat',
    subtitle: 'Чат группы',
    description:
      'Чат учебной группы для вопросов, быстрых ответов и неформального общения.',
    accent: '#22d3ee',
    emoji: '💭',
  },
  {
    slug: 'cert',
    title: 'Cert',
    subtitle: 'Сертификаты',
    description: 'Сертификат о прохождении сезона Learn.',
    accent: '#eab308',
    emoji: '🎓',
    appPath: '/game/cert',
  },
  {
    slug: 'quiz',
    title: 'Quiz',
    subtitle: 'Закрепление теории',
    description: 'Короткие вопросы по выпускам Learn.',
    accent: '#f59e0b',
    emoji: '🧠',
    appPath: '/game/quiz',
  },
  {
    slug: 'stream',
    title: 'Stream',
    subtitle: 'Стримы и эфиры',
    description:
      'Прямые эфиры, записи разборов лаб и Q&A-сессии с преподавателем.',
    accent: '#ef4444',
    emoji: '📺',
  },
  {
    slug: 'news',
    title: 'News',
    subtitle: 'Новости',
    description:
      'Новости платформы, анонсы выпусков, обновлений и важных изменений.',
    accent: '#818cf8',
    emoji: '📰',
  },
  {
    slug: 'forum',
    title: 'Forum',
    subtitle: 'Форум',
    description:
      'Форум для развёрнутых обсуждений, разборов ошибок и обмена опытом.',
    accent: '#c084fc',
    emoji: '🗣️',
  },
  {
    slug: 'code',
    title: 'Code',
    subtitle: 'Редактор кода',
    description:
      'Онлайн-редактор для коротких упражнений и экспериментов без установки IDE.',
    accent: '#2dd4bf',
    emoji: '⌨️',
  },
  {
    slug: 'map',
    title: 'Map',
    subtitle: 'Карта курса',
    description:
      'Интерактивная карта курса: сезоны, выпуски и связи между темами.',
    accent: '#14b8a6',
    emoji: '🧭',
  },
  {
    slug: 'team',
    title: 'Team',
    subtitle: 'Команды',
    description:
      'Рабочие группы и команды для совместных проектов, соревнований и парного обучения.',
    accent: '#f97316',
    emoji: '👥',
  },
]

const sectionBySlug = new Map(sections.map((section) => [section.slug, section]))

export function getSectionBySlug(slug: string): Section | undefined {
  return sectionBySlug.get(slug)
}
