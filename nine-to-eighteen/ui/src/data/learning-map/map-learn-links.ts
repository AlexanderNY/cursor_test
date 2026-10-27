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
      's01e01-sloi',
      'b01-karta',
      'b01-karta',
      'b01-karta',
      's01e05-fastapi',
      'b05-api-check',
      'b05-api-check',
      'b05-api-check',
      's01e09-regex',
      'b10-docker',
    ],
    tags: ['fastapi', 'react', 'архитектура'],
  },
  {
    mapTitle: 'аналитика и продукт',
    description: 'Требования, SA и приоритизация бэклога.',
    rubricIds: ['api'],
    episodeSlugs: ['s01e03-git'],
    tags: ['sa', 'product', 'требования'],
  },
  {
    mapTitle: 'данные',
    description: 'PostgreSQL, SQL, моделирование, Redis.',
    rubricIds: ['data'],
    episodeSlugs: [
      's01e07-postgres',
      's01e07-postgres',
    ],
    tags: ['sql', 'postgresql', 'redis'],
  },
  {
    mapTitle: 'инструменты',
    description: 'Git, regex и проверка HTTP API.',
    rubricIds: ['tools'],
    episodeSlugs: [
      's01e03-git',
      'b01-karta',
      'b05-api-check',
      's01e09-regex',
      's01e05-fastapi',
      'b05-api-check',
    ],
    tags: ['git', 'regex', 'api-test'],
  },
  {
    mapTitle: 'devops',
    description: 'Docker, Compose, пайплайн, объекты Kubernetes и сети.',
    rubricIds: ['tools'],
    episodeSlugs: [
      'b10-docker',
      'b10-docker',
      'ops-linux-process',
      'ops-linux-process',
      'ops-linux-process',
    ],
    tags: ['docker', 'ci', 'kubernetes'],
  },
  {
    mapTitle: 'безопасность',
    description: 'JWT, HTTPS и разграничение доступа.',
    rubricIds: ['tools'],
    episodeSlugs: [
      'sec-authn-authz',
      'sec-authn-authz',
      'sec-authn-authz',
      'sec-authn-authz',
    ],
    tags: ['security', 'jwt', 'https'],
  },
  {
    mapTitle: 'тестирование',
    description: 'Тест-дизайн и локальные E2E.',
    rubricIds: ['tools'],
    episodeSlugs: ['qa-intro-testing', 'qa-aqa-principles'],
    tags: ['qa', 'e2e'],
  },
  {
    mapTitle: 'soft skills',
    description: 'Поведенческие вопросы на собеседовании.',
    rubricIds: [],
    episodeSlugs: [
      'beh-star',
      'beh-star',
      'beh-star',
      'beh-star',
    ],
    tags: ['интервью'],
  },
  {
    mapTitle: 'алгоритмы',
    description: 'Сложность, структуры и разбор задачи вслух.',
    rubricIds: ['tools'],
    episodeSlugs: [
      'algo-complexity',
      'algo-complexity',
      'algo-complexity',
      'algo-complexity',
      'algo-complexity',
      'algo-complexity',
    ],
    tags: ['algorithms'],
  },
  {
    mapTitle: 'проектирование',
    description: 'Один сервис, кэш, хранилище и отказ.',
    rubricIds: ['architecture'],
    episodeSlugs: ['sd-one-service', 'sd-one-service', 'sd-one-service', 'sd-one-service'],
    tags: ['system-design'],
  },
  {
    mapTitle: 'postgres',
    description: 'Изоляция, MVCC и молчащий индекс.',
    rubricIds: ['data'],
    episodeSlugs: ['pg-isolation', 'pg-isolation', 'pg-isolation', 'pg-isolation'],
    tags: ['postgresql'],
  },
  {
    mapTitle: 'сети',
    description: 'DNS, TCP, TLS и этаж поломки.',
    rubricIds: ['tools'],
    episodeSlugs: ['net-dns-http', 'net-dns-http', 'net-dns-http', 'net-dns-http'],
    tags: ['network'],
  },
  {
    mapTitle: 'наблюдаемость',
    description: 'Лог, хвост задержки и один запрос.',
    rubricIds: ['tools'],
    episodeSlugs: ['obs-logs', 'obs-logs', 'obs-logs'],
    tags: ['observability'],
  },
  {
    mapTitle: 'java core',
    description: 'HashMap, потоки, сборщик и граница Spring.',
    rubricIds: ['tools'],
    episodeSlugs: ['jc-collections-hashmap', 'jc-collections-hashmap', 'jc-collections-hashmap', 'jc-collections-hashmap'],
    tags: ['java'],
  },
  {
    mapTitle: 'фронтенд',
    description: 'Цикл событий, замыкание, состояние React и TypeScript.',
    rubricIds: ['frontend'],
    episodeSlugs: ['fe-event-loop', 'fe-event-loop', 'fe-event-loop', 'fe-event-loop'],
    tags: ['frontend'],
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
