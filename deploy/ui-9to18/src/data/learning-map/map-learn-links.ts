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
    mapTitle: 'информационная безопасность',
    description:
      'Шифрование, аутентификация, доступ и сетевые инструменты защиты. В Learn отдельного трека пока нет — опирайтесь на карту и смежные инструменты.',
    rubricIds: ['tools'],
    episodeSlugs: [],
    tags: ['security', 'https', 'auth', 'vpn'],
  },
  {
    mapTitle: 'базы данных',
    description:
      'Реляционные БД, SQL, нормализация, транзакции и индексы. В курсе — PostgreSQL и JOIN на сезонах B и S01.',
    rubricIds: ['data'],
    episodeSlugs: ['s01e07-postgres', 's01e08-sql'],
    tags: ['sql', 'postgresql', 'acid', 'индексы'],
  },
  {
    mapTitle: 'разработка',
    description:
      'ООП, архитектура слоёв, API и фронт. Основные лекции Learn по сборке сервиса: слои, FastAPI, React, склейка.',
    rubricIds: ['architecture', 'api', 'frontend'],
    episodeSlugs: [
      'b01-karta',
      'b03-python',
      'b04-fastapi-health',
      'b07-notes-api',
      'b08-react-list',
      'b09-react-form',
      'b12-sklejka',
      's01e01-sloi',
      's01e02-karta',
      's01e05-fastapi',
      's01e10-react',
    ],
    tags: ['архитектура', 'fastapi', 'python', 'react', 'oop'],
  },
  {
    mapTitle: 'аналитика',
    description:
      'Требования, моделирование и контракт API. В Learn — системный анализ: от боли пользователя к контракту.',
    rubricIds: ['api'],
    episodeSlugs: ['s01e04-sa'],
    tags: ['требования', 'sa', 'api', 'контракт', 'babok'],
  },
  {
    mapTitle: 'регулярные выражения',
    description:
      'Паттерны поиска и разбора текста. В Learn — отдельный выпуск по regex с практикой.',
    rubricIds: ['tools'],
    episodeSlugs: ['s01e09-regex'],
    tags: ['regex', 'парсинг', 'валидация'],
  },
  {
    mapTitle: 'soft skills',
    description:
      'Поведенческие вопросы, командная работа и самопрезентация на собеседовании. В Learn отдельного трека нет — готовьтесь по узлам карты.',
    rubricIds: [],
    episodeSlugs: [],
    tags: ['интервью', 'команда', 'самопрезентация'],
  },
  {
    mapTitle: 'прочее',
    description:
      'Документация, ГОСТ и вспомогательные темы. В Learn можно опереться на выпуски про карту системы и README.',
    rubricIds: ['architecture', 'tools'],
    episodeSlugs: ['b01-karta', 'b06-git-branch', 's01e02-karta'],
    tags: ['документация', 'markdown', 'gost'],
  },
  {
    mapTitle: 'тестирование',
    description:
      'SDLC, кейсы, регресс и API-тесты. В Learn пока нет отдельного сезона QA — проверяйте API через инструменты курса.',
    rubricIds: ['tools'],
    episodeSlugs: ['b05-api-check', 's01e06-insomnia'],
    tags: ['qa', 'регресс', 'api-test'],
  },
  {
    mapTitle: 'сети передачи данных',
    description:
      'OSI, DNS, IP и путь запроса в браузере. В Learn сеть даётся косвенно через HTTP API и проверку запросов.',
    rubricIds: ['tools', 'api'],
    episodeSlugs: ['b05-api-check', 's01e06-insomnia'],
    tags: ['http', 'dns', 'osi', 'tcp'],
  },
  {
    mapTitle: 'git',
    description:
      'VCS, ветки и GitHub flow. В Learn — базовый репозиторий и ветка с README на сезонах B и S01.',
    rubricIds: ['tools'],
    episodeSlugs: ['b02-git', 'b06-git-branch', 's01e03-git'],
    tags: ['git', 'vcs', 'github'],
  },
  {
    mapTitle: 'docker',
    description:
      'Образы, Dockerfile и Compose. В Learn — упаковка API в образ и связка сервисов через Compose.',
    rubricIds: ['tools'],
    episodeSlugs: ['b10-docker', 'b11-compose'],
    tags: ['docker', 'containers', 'compose'],
  },
  {
    mapTitle: 'kubernetes',
    description:
      'Оркестрация контейнеров и модель сервисов. В Learn прямых лекций пока нет; рядом — Docker/Compose как подготовка к k8s.',
    rubricIds: ['tools'],
    episodeSlugs: ['b10-docker', 'b11-compose'],
    tags: ['kubernetes', 'оркестрация', 'containers'],
  },
  {
    mapTitle: 'jenkins',
    description:
      'CI-пайплайны и автоматизация сборки. В Learn отдельного выпуска нет — смотрите смежные инструменты DevOps на карте.',
    rubricIds: ['tools'],
    episodeSlugs: [],
    tags: ['ci', 'jenkins', 'pipeline'],
  },
  {
    mapTitle: 'kafka',
    description:
      'Очереди сообщений и потоковая обработка. В Learn пока нет лекций — тема для самостоятельного углубления по карте.',
    rubricIds: ['architecture'],
    episodeSlugs: [],
    tags: ['kafka', 'messaging', 'streaming'],
  },
  {
    mapTitle: 'devops',
    description:
      'Конфигурация, доставка и инфраструктура вокруг приложения. В Learn — Docker/Compose как первый шаг к воспроизводимому стенду.',
    rubricIds: ['tools'],
    episodeSlugs: ['b10-docker', 'b11-compose', 'b12-sklejka'],
    tags: ['devops', 'ci-cd', 'infra'],
  },
  {
    mapTitle: 'machine learning',
    description:
      'Базовые идеи ML для собеседования. В учебном контуре Learn отдельного трека нет.',
    rubricIds: [],
    episodeSlugs: [],
    tags: ['ml', 'данные', 'модели'],
  },
  {
    mapTitle: 'redis',
    description:
      'In-memory кэш и структуры данных Redis. В Learn прямых лекций нет; рядом — блок данных PostgreSQL/SQL.',
    rubricIds: ['data'],
    episodeSlugs: ['s01e07-postgres'],
    tags: ['redis', 'cache', 'nosql'],
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
  return 'Learn'
}

export const mapLearnLinks = LINKS
