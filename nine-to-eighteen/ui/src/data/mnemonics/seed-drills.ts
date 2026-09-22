import type { MnemonicTechniqueId, StructuredMnemonicItem } from '@/data/site/structured-post'

/** Built-in examples per technique (trainer library + Learn seed fallback). */
export type SeedMnemonicDrill = StructuredMnemonicItem & {
  learnSlug: string
  learnTitle: string
  episode: string
}

export const SEED_MNEMONIC_DRILLS: SeedMnemonicDrill[] = [
  // —— Акронимы ——
  {
    technique: 'acronym',
    title: 'ACID',
    prompt: 'Четыре свойства транзакции БД.',
    items: ['Atomicity', 'Consistency', 'Isolation', 'Durability'],
    hint: 'Первые буквы → одно слово.',
    answer: 'ACID',
    learnSlug: 'sql-acid-transactions',
    learnTitle: 'ACID и транзакции',
    episode: 'SQL08',
  },
  {
    technique: 'acronym',
    title: 'SOLID',
    prompt: 'Пять принципов ООП Роберта Мартина.',
    items: [
      'Single Responsibility',
      'Open/Closed',
      'Liskov Substitution',
      'Interface Segregation',
      'Dependency Inversion',
    ],
    hint: 'S·O·L·I·D',
    answer: 'SOLID',
    learnSlug: 'mnemonics-intro',
    learnTitle: 'Мнемотехники для собеса',
    episode: 'MEM01',
  },
  {
    technique: 'acronym',
    title: 'DRY',
    prompt: 'Принцип «не повторяйся» в коде и документации.',
    items: ["Don't", 'Repeat', 'Yourself'],
    hint: 'Три слова → DRY.',
    answer: 'DRY',
    learnSlug: 'mnemonics-intro',
    learnTitle: 'Мнемотехники для собеса',
    episode: 'MEM01',
  },
  {
    technique: 'acronym',
    title: 'KISS',
    prompt: 'Принцип простоты решения.',
    items: ['Keep', 'It', 'Simple', 'Stupid'],
    hint: 'Или Keep It Short and Simple.',
    answer: 'KISS',
    learnSlug: 'mnemonics-intro',
    learnTitle: 'Мнемотехники для собеса',
    episode: 'MEM01',
  },
  {
    technique: 'acronym',
    title: 'CAP',
    prompt: 'Теорема Брюера для распределённых систем.',
    items: ['Consistency', 'Availability', 'Partition tolerance'],
    hint: 'Выбирают два из трёх при сетевом разделении.',
    answer: 'CAP',
    learnSlug: 'mnemonics-intro',
    learnTitle: 'Мнемотехники для собеса',
    episode: 'MEM01',
  },
  {
    technique: 'acronym',
    title: 'REST',
    prompt: 'Свойства архитектурного стиля REST (часто вспоминают на собесе).',
    items: [
      'Representational',
      'State',
      'Transfer',
    ],
    hint: 'Не путать с CRUD-операциями.',
    answer: 'REST',
    learnSlug: 'mnemonics-intro',
    learnTitle: 'Мнемотехники для собеса',
    episode: 'MEM01',
  },
  {
    technique: 'acronym',
    title: 'CRUD',
    prompt: 'Базовые операции над ресурсом.',
    items: ['Create', 'Read', 'Update', 'Delete'],
    hint: 'Четыре буквы → CRUD.',
    answer: 'CRUD',
    learnSlug: 'mnemonics-intro',
    learnTitle: 'Мнемотехники для собеса',
    episode: 'MEM01',
  },
  {
    technique: 'acronym',
    title: 'BASE',
    prompt: 'Альтернатива ACID для eventually consistent систем.',
    items: ['Basically Available', 'Soft state', 'Eventually consistent'],
    hint: 'B·A·S·E',
    answer: 'BASE',
    learnSlug: 'mnemonics-intro',
    learnTitle: 'Мнемотехники для собеса',
    episode: 'MEM01',
  },

  // —— Акростих ——
  {
    technique: 'acrostic',
    title: 'OSI 7 слоёв',
    prompt: 'Порядок слоёв OSI снизу вверх.',
    items: [
      'Physical',
      'Data Link',
      'Network',
      'Transport',
      'Session',
      'Presentation',
      'Application',
    ],
    hint: 'Please Do Not Throw Sausage Pizza Away',
    answer: 'Please Do Not Throw Sausage Pizza Away',
    learnSlug: 'mnemonics-intro',
    learnTitle: 'Мнемотехники для собеса',
    episode: 'MEM01',
  },
  {
    technique: 'acrostic',
    title: 'HTTP методы (безопасные)',
    prompt: 'Запомните «безопасные» методы через фразу.',
    items: ['GET', 'HEAD', 'OPTIONS'],
    hint: 'Get Hot Oatmeal — чтение без изменения ресурса.',
    answer: 'Get Hot Oatmeal',
    learnSlug: 'mnemonics-intro',
    learnTitle: 'Мнемотехники для собеса',
    episode: 'MEM01',
  },

  // —— Чанкинг ——
  {
    technique: 'chunking',
    title: 'Порт PostgreSQL',
    prompt: 'Порт PostgreSQL — разбейте на группы.',
    items: ['5432'],
    hint: '54 · 32',
    answer: '54-32',
    learnSlug: 'mnemonics-intro',
    learnTitle: 'Мнемотехники для собеса',
    episode: 'MEM01',
  },
  {
    technique: 'chunking',
    title: 'Порт Redis',
    prompt: 'Запомните порт Redis.',
    items: ['6379'],
    hint: '63 · 79',
    answer: '63-79',
    learnSlug: 'mnemonics-intro',
    learnTitle: 'Мнемотехники для собеса',
    episode: 'MEM01',
  },
  {
    technique: 'chunking',
    title: 'IPv4 loopback',
    prompt: 'Адрес loopback — по октетам.',
    items: ['127.0.0.1'],
    hint: '127 · 0 · 0 · 1',
    answer: '127.0.0.1',
    learnSlug: 'mnemonics-intro',
    learnTitle: 'Мнемотехники для собеса',
    episode: 'MEM01',
  },

  // —— Цепочка ——
  {
    technique: 'link',
    title: 'Уровни тестирования',
    prompt: 'Свяжите уровни в историю (от узкого к широкому).',
    items: ['unit', 'integration', 'system', 'acceptance'],
    hint: 'Модуль → стыки → система → приёмка.',
    answer: 'unit → integration → system → acceptance',
    learnSlug: 'qa-types-levels',
    learnTitle: 'Типы и уровни тестов',
    episode: 'QA02',
  },
  {
    technique: 'link',
    title: 'CI/CD pipeline',
    prompt: 'Порядок стадий пайплайна.',
    items: ['commit', 'build', 'test', 'deploy'],
    hint: 'Коммит толкает сборку, тесты пускают деплой.',
    answer: 'commit → build → test → deploy',
    learnSlug: 'mnemonics-intro',
    learnTitle: 'Мнемотехники для собеса',
    episode: 'MEM01',
  },

  // —— Крючки ——
  {
    technique: 'peg',
    title: 'Слои сервиса',
    prompt: 'Повесьте слои на крючки 1–4.',
    items: ['UI', 'API', 'БД', 'Деплой'],
    hint: '1=кол→UI, 2=лебедь→API, 3=трезубец→БД, 4=стул→Деплой.',
    answer: '1 UI · 2 API · 3 БД · 4 Деплой',
    learnSlug: 's01e01-sloi',
    learnTitle: 'Зачем собирать сервис слоями',
    episode: 'S01E01',
  },
  {
    technique: 'peg',
    title: 'HTTP статус-классы',
    prompt: 'Классы кодов 1xx–5xx на крючки.',
    items: ['Info', 'Success', 'Redirect', 'Client error', 'Server error'],
    hint: '1 инфо → 2 ок → 3 ушёл → 4 виноват клиент → 5 сервер.',
    answer: '1xx…5xx',
    learnSlug: 'mnemonics-intro',
    learnTitle: 'Мнемотехники для собеса',
    episode: 'MEM01',
  },

  // —— Дворец ——
  {
    technique: 'loci',
    title: 'STAR',
    prompt: 'STAR-ответ по комнатам маршрута.',
    items: ['Situation', 'Task', 'Action', 'Result'],
    hint: 'кухня → коридор → кабинет → балкон',
    answer: 'Situation → Task → Action → Result',
    learnSlug: 'mnemonics-intro',
    learnTitle: 'Мнемотехники для собеса',
    episode: 'MEM01',
  },

  // —— Major ——
  {
    technique: 'major',
    title: 'HTTPS 443',
    prompt: 'Порт HTTPS через образ.',
    items: ['443'],
    hint: '4=р, 3=м → «ром» на сервере',
    answer: '443',
    learnSlug: 'mnemonics-intro',
    learnTitle: 'Мнемотехники для собеса',
    episode: 'MEM01',
  },
  {
    technique: 'major',
    title: 'HTTP 80',
    prompt: 'Порт HTTP.',
    items: ['80'],
    hint: '8≈ф, 0≈с → «фос» / просто «восемьдесят»',
    answer: '80',
    learnSlug: 'mnemonics-intro',
    learnTitle: 'Мнемотехники для собеса',
    episode: 'MEM01',
  },

  // —— Keyword ——
  {
    technique: 'keyword',
    title: 'Idempotent',
    prompt: 'Свяжите звучание с образом и смыслом.',
    items: ['idempotent', 'повтор запроса не меняет результат'],
    hint: '«ай-дем» → один и тот же дом / тот же итог',
    answer: 'повтор без побочного эффекта',
    learnSlug: 'mnemonics-intro',
    learnTitle: 'Мнемотехники для собеса',
    episode: 'MEM01',
  },
  {
    technique: 'keyword',
    title: 'Latency',
    prompt: 'Созвучие → образ задержки.',
    items: ['latency', 'время до ответа'],
    hint: '«лейт» → опоздал / late',
    answer: 'задержка ответа',
    learnSlug: 'mnemonics-intro',
    learnTitle: 'Мнемотехники для собеса',
    episode: 'MEM01',
  },
]

export function examplesForTechnique(technique: MnemonicTechniqueId): SeedMnemonicDrill[] {
  return SEED_MNEMONIC_DRILLS.filter((item) => item.technique === technique)
}

export function toStructuredExample(seed: SeedMnemonicDrill): StructuredMnemonicItem {
  return {
    technique: seed.technique,
    title: seed.title,
    prompt: seed.prompt,
    items: [...seed.items],
    ...(seed.hint ? { hint: seed.hint } : {}),
    ...(seed.answer ? { answer: seed.answer } : {}),
  }
}
