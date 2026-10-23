import { safeHref } from '@/data/safe-url'

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
    slug: 'hh-resume',
    title: 'Резюме',
    subtitle: 'Опросник · HH · навыки Learn',
    description:
      'Отдельный сервис: опросник «идеальное резюме», шаблон в стиле HeadHunter, правка текста и навыки из пройденных выпусков Learn.',
    accent: '#d6001c',
    emoji: '📄',
    appPath: '/game/hh-resume',
  },
  {
    slug: 'portfolio',
    title: 'Портфолио',
    subtitle: 'Кейсы · публичная страница',
    description:
      'Страница, которую можно отправить: задача, что сделано, результат, стек, выпуски Learn и сертификат сезона.',
    accent: '#38bdf8',
    emoji: '🗂️',
    appPath: '/game/portfolio',
  },
  {
    slug: 'code',
    title: 'Code',
    subtitle: 'Песочница · задачи PY',
    description:
      'Pyodide в браузере: редактор, каталог задач junior (PY02–PY08) с проверкой и заготовки из лаб Learn.',
    accent: '#2dd4bf',
    emoji: '⌨️',
    appPath: '/game/code',
  },
  {
    slug: 'sql',
    title: 'SQL',
    subtitle: 'Песочница · задачи SQL',
    description:
      'SQLite в браузере (sql.js): редактор, каталог задач по лекциям SQL01–SQL13 с проверкой и блоки ```sql из Learn.',
    accent: '#f59e0b',
    emoji: '🗄️',
    appPath: '/game/sql',
  },
  {
    slug: 'git',
    title: 'Git',
    subtitle: 'Симулятор · задачи Git',
    description:
      'Команды Git в браузере без диска: status/add/commit/branch/stash/merge и Check по состоянию репозитория.',
    accent: '#f97316',
    emoji: '🌿',
    appPath: '/game/git',
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
    slug: 'mnemonics',
    title: 'Мнемотехники',
    subtitle: 'Акронимы · цепочки · крючки',
    description:
      'Тренажёр кодирования для собеса: акронимы, акростихи, чанкинг, цепочки и система крючков. Дриллы из статей Learn и с карты знаний.',
    accent: '#a78bfa',
    emoji: '🧩',
    appPath: '/game/mnemonics',
  },
]

const sectionBySlug = new Map(sections.map((section) => [section.slug, section]))

export function getSectionBySlug(slug: string): Section | undefined {
  return sectionBySlug.get(slug)
}

export function blogHref(slug: string): string {
  return `/blog/${slug}`
}

export function blogPostHref(slug: string, postSlug: string): string {
  return `/blog/${slug}/${postSlug}`
}

/** Article links. Rewrites the old `/app/:slug/:post` shape onto the blog. */
export function publicPostHref(href: string, appSlug = '', postSlug = ''): string {
  const raw = href.trim()
  const legacy = /^\/app\/([^/]+)\/([^/]+)\/?$/.exec(raw)
  if (legacy) {
    return blogPostHref(decodeURIComponent(legacy[1]), decodeURIComponent(legacy[2]))
  }
  if (raw) {
    const safe = safeHref(raw)
    if (safe && (safe.startsWith('/') || safe.startsWith('http://') || safe.startsWith('https://'))) {
      return safe
    }
  }
  if (appSlug && postSlug) {
    return blogPostHref(appSlug, postSlug)
  }
  return raw
}

export type ServiceOpenTarget = {
  href: string
  external: boolean
}

function isAbsoluteHttp(href: string): boolean {
  return /^https?:\/\//i.test(href)
}

/** Tile and title clicks open the product. The blog is a separate page. */
export function serviceOpenTarget(
  section: Pick<Section, 'slug' | 'href' | 'appPath'>,
): ServiceOpenTarget {
  const appPath = (section.appPath || '').trim()
  const safeApp = safeHref(appPath)
  if (safeApp && isAbsoluteHttp(safeApp)) {
    return { href: safeApp, external: true }
  }
  if (appPath.startsWith('/') && !appPath.startsWith('//')) {
    return { href: appPath, external: false }
  }
  const externalHref = (section.href || '').trim()
  const safeExternal = safeHref(externalHref)
  if (safeExternal && isAbsoluteHttp(safeExternal)) {
    return { href: safeExternal, external: true }
  }
  return { href: blogHref(section.slug), external: false }
}
