export type Section = {
  slug: string
  title: string
  subtitle: string
  accent: string
  emoji?: string
}

export const sections: Section[] = [
  {
    slug: 'bowl',
    title: 'Bowl',
    subtitle: 'Игра и заказы',
    accent: '#34d399',
    emoji: '🎳',
  },
  {
    slug: 'learn',
    title: 'Learn',
    subtitle: 'Теория, лабы, шпаргалки',
    accent: '#2dd4bf',
    emoji: '📚',
  },
  {
    slug: 'quiz',
    title: 'Quiz',
    subtitle: 'Викторины и опросы',
    accent: '#60a5fa',
    emoji: '❓',
  },
  {
    slug: 'menu',
    title: 'Menu',
    subtitle: 'Каталог и корзина',
    accent: '#fbbf24',
    emoji: '📋',
  },
  {
    slug: 'rating',
    title: 'Rating',
    subtitle: 'Таблица лидеров',
    accent: '#a78bfa',
    emoji: '🏆',
  },
  {
    slug: 'events',
    title: 'Events',
    subtitle: 'Мероприятия',
    accent: '#f472b6',
    emoji: '📅',
  },
  {
    slug: 'shop',
    title: 'Shop',
    subtitle: 'Магазин',
    accent: '#fb923c',
    emoji: '🛒',
  },
  {
    slug: 'profile',
    title: 'Profile',
    subtitle: 'Личный кабинет',
    accent: '#38bdf8',
    emoji: '👤',
  },
  {
    slug: 'help',
    title: 'Help',
    subtitle: 'Помощь и FAQ',
    accent: '#94a3b8',
    emoji: '💬',
  },
]

const sectionBySlug = new Map(sections.map((section) => [section.slug, section]))

export function getSectionBySlug(slug: string): Section | undefined {
  return sectionBySlug.get(slug)
}
