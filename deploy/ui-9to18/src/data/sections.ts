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

/** Fallback home tiles when /site/apps is empty or unreachable.
 *  Only live product surfaces — no stub LMS tiles. */
export const sections: Section[] = [
  {
    slug: 'bowl',
    title: 'Bowl',
    subtitle: 'Игра · перки · заказы',
    description:
      '2D-игра на Python в браузере: выживание в чаше, перки, боссы и внутриигровые заказы между матчами.',
    accent: '#34d399',
    emoji: '🎳',
    appPath: '/game/bowl',
  },
  {
    slug: 'learn',
    title: 'Learn',
    subtitle: 'Статьи · Anki · лабы',
    description:
      'Единый формат учебных статей: введение, разделы, схемы, тест и Anki-карты; лаба опционально.',
    accent: '#2dd4bf',
    emoji: '📚',
    appPath: '/game/learn',
  },
  {
    slug: 'learning-map',
    title: 'Карта обучения',
    subtitle: 'Профили · статьи Learn',
    description:
      'Mind map к собеседованию: профили (аналитик, DevOps, разработчик, QA, PO). Каждый лист — статья Learn с Anki.',
    accent: '#2dd4bf',
    emoji: '🗺️',
    appPath: '/game/learning-map',
  },
  {
    slug: 'code',
    title: 'Code',
    subtitle: 'Python в браузере',
    description:
      'Песочница Pyodide: короткие упражнения и эксперименты без установки IDE. Лабы Learn можно запускать здесь.',
    accent: '#2dd4bf',
    emoji: '⌨️',
    appPath: '/game/code',
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
    slug: 'tasks',
    title: 'Tasks',
    subtitle: 'Чек-лист Learn',
    description: 'Личные задачи и прогресс по выпускам Learn.',
    accent: '#4ade80',
    emoji: '✅',
    appPath: '/game/tasks',
  },
  {
    slug: 'quiz',
    title: 'Quiz',
    subtitle: 'Закрепление теории',
    description: 'Вопросы из тестов статей Learn (structured.quiz).',
    accent: '#f59e0b',
    emoji: '🧠',
    appPath: '/game/quiz',
  },
  {
    slug: 'cert',
    title: 'Cert',
    subtitle: 'Сертификаты',
    description: 'Сертификат о прохождении сезона Learn (печать / PDF).',
    accent: '#eab308',
    emoji: '🎓',
    appPath: '/game/cert',
  },
]

const sectionBySlug = new Map(sections.map((section) => [section.slug, section]))

export function getSectionBySlug(slug: string): Section | undefined {
  return sectionBySlug.get(slug)
}
