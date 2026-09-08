import type { LearnRubricId } from '@/data/learn'
import type { MindNode } from '@/data/learning-map/parse-outline'

export type MapLearnLink = {
  mapTitle: string
  description: string
  rubricIds: LearnRubricId[]
  episodeSlugs: string[]
  tags: string[]
}

export function normalizeMapTitle(title: string): string {
  return title.replace(/\u00a0/g, ' ').replace(/\s+/g, ' ').trim().toLowerCase()
}

const LINKS: MapLearnLink[] = [
  {
    mapTitle: 'разработка',
    description: 'Слои, API, React и склейка учебного стенда.',
    rubricIds: ['architecture', 'api', 'frontend'],
    episodeSlugs: [
      's01e01-sloi',
      's01e02-karta',
      'b01-karta',
      'b03-python',
      'b04-fastapi-health',
      's01e05-fastapi',
      'b07-notes-api',
      'b08-react-list',
      'b09-react-form',
      's01e10-react',
      'b12-sklejka',
    ],
    tags: ['fastapi', 'react', 'архитектура'],
  },
  {
    mapTitle: 'аналитика и продукт',
    description: 'Требования, SA и приоритизация бэклога.',
    rubricIds: ['api'],
    episodeSlugs: ['s01e04-sa', 'map-requirements', 'map-product-backlog'],
    tags: ['sa', 'product', 'требования'],
  },
  {
    mapTitle: 'данные',
    description: 'PostgreSQL, SQL, моделирование, Redis.',
    rubricIds: ['data'],
    episodeSlugs: [
      's01e07-postgres',
      's01e08-sql',
      'map-normalization',
      'map-sql-nosql',
      'map-redis',
    ],
    tags: ['sql', 'postgresql', 'redis'],
  },
  {
    mapTitle: 'инструменты',
    description: 'Git, regex и проверка HTTP API.',
    rubricIds: ['tools'],
    episodeSlugs: [
      's01e03-git',
      'b02-git',
      'b06-git-branch',
      's01e09-regex',
      's01e06-insomnia',
      'b05-api-check',
    ],
    tags: ['git', 'regex', 'api-test'],
  },
  {
    mapTitle: 'devops',
    description: 'Docker, Compose, CI/CD, k8s и сети.',
    rubricIds: ['tools'],
    episodeSlugs: [
      'b10-docker',
      'b11-compose',
      'map-cicd',
      'map-k8s',
      'map-networking',
    ],
    tags: ['docker', 'ci', 'kubernetes'],
  },
  {
    mapTitle: 'безопасность',
    description: 'JWT, HTTPS и разграничение доступа.',
    rubricIds: ['tools'],
    episodeSlugs: ['map-auth-jwt', 'map-https-access'],
    tags: ['security', 'jwt', 'https'],
  },
  {
    mapTitle: 'тестирование',
    description: 'Тест-дизайн и локальные E2E.',
    rubricIds: ['tools'],
    episodeSlugs: ['map-qa', 'map-e2e'],
    tags: ['qa', 'e2e'],
  },
  {
    mapTitle: 'soft skills',
    description: 'Поведенческие вопросы на собеседовании.',
    rubricIds: [],
    episodeSlugs: ['map-soft-skills'],
    tags: ['интервью'],
  },
]

const byTitle = new Map(LINKS.map((link) => [normalizeMapTitle(link.mapTitle), link]))

export function getMapLearnLink(title: string): MapLearnLink | undefined {
  return byTitle.get(normalizeMapTitle(title))
}

/** Прямой потомок корня = ветка 1 уровня; для любого узла возвращает L1-предка. */
export function findL1Ancestor(root: MindNode, selectedId: string): MindNode | null {
  if (root.id === selectedId) {
    return null
  }
  for (const branch of root.children) {
    if (branch.id === selectedId) {
      return branch
    }
    if (containsNode(branch, selectedId)) {
      return branch
    }
  }
  return null
}

function containsNode(node: MindNode, targetId: string): boolean {
  if (node.id === targetId) {
    return true
  }
  return node.children.some((child) => containsNode(child, targetId))
}

export function seasonLabel(episode: string): string {
  if (episode.startsWith('B')) {
    return 'Сезон B'
  }
  if (episode.startsWith('S01')) {
    return 'Сезон 1'
  }
  if (episode.startsWith('MAP')) {
    return 'Карта'
  }
  return 'Learn'
}

export const mapLearnLinks = LINKS
