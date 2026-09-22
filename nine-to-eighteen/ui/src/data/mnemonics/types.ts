import type {
  MnemonicTechniqueId,
  StructuredMnemonicItem,
} from '@/data/site/structured-post'
import { isMnemonicTechniqueId } from '@/data/site/structured-post'

export type { MnemonicTechniqueId, StructuredMnemonicItem }

export type MnemonicDrillCard = StructuredMnemonicItem & {
  id: string
  learnSlug: string
  learnTitle: string
  learnHref: string
  episode: string
  tags: string[]
  branchId: string
  branchTitle: string
}

export type MnemonicTechniqueMeta = {
  id: MnemonicTechniqueId
  title: string
  subtitle: string
  wave1: boolean
  howTo: string
  inputHint: string
  itemsLabel: string
  answerLabel: string
  answerPlaceholder: string
  exampleTitle: string
}

export const MNEMONIC_TECHNIQUE_META: MnemonicTechniqueMeta[] = [
  {
    id: 'acronym',
    title: 'Акроним',
    subtitle: 'Первые буквы → слово',
    wave1: true,
    howTo:
      'Введите элементы списка. Из первых букв составьте слово или аббревиатуру, затем проверьте себя.',
    inputHint: 'По одному элементу на строку (Atomicity, Consistency…)',
    itemsLabel: 'Элементы списка',
    answerLabel: 'Эталонный акроним (необязательно)',
    answerPlaceholder: 'ACID',
    exampleTitle: 'ACID',
  },
  {
    id: 'acrostic',
    title: 'Акростих',
    subtitle: 'Буквы → фраза',
    wave1: true,
    howTo:
      'Когда буквы не складываются в слово — придумайте фразу, где каждое слово начинается с нужной буквы.',
    inputHint: 'Элементы по строкам (Physical, Data Link…)',
    itemsLabel: 'Элементы списка',
    answerLabel: 'Эталонная фраза (необязательно)',
    answerPlaceholder: 'Please Do Not Throw…',
    exampleTitle: 'OSI',
  },
  {
    id: 'chunking',
    title: 'Чанкинг',
    subtitle: 'Длинная строка → группы',
    wave1: true,
    howTo:
      'Введите число, порт, UUID или команду. Разбейте на короткие группы и восстановите по памяти.',
    inputHint: 'Одна строка — то, что нужно запомнить (5432, 192.168.0.1…)',
    itemsLabel: 'Что запомнить',
    answerLabel: 'Эталон с разбиением (необязательно)',
    answerPlaceholder: '54-32',
    exampleTitle: 'Порт PostgreSQL',
  },
  {
    id: 'link',
    title: 'Цепочка',
    subtitle: 'Список → история',
    wave1: true,
    howTo:
      'Введите шаги в правильном порядке. Придумайте историю, связывающую соседние элементы, затем восстановите порядок.',
    inputHint: 'Шаги по строкам в нужном порядке',
    itemsLabel: 'Шаги цепочки',
    answerLabel: 'Эталон порядка (необязательно)',
    answerPlaceholder: 'A → B → C',
    exampleTitle: 'Уровни тестов',
  },
  {
    id: 'peg',
    title: 'Крючки',
    subtitle: 'Номер → образ → элемент',
    wave1: true,
    howTo:
      'У чисел 1–10 уже есть образы-крючки. Введите элементы по порядку — «повесьте» каждый на свой крючок и проверьте.',
    inputHint: 'Элементы по строкам (1-й, 2-й…)',
    itemsLabel: 'Элементы по номерам',
    answerLabel: 'Подсказка / эталон (необязательно)',
    answerPlaceholder: '1 UI · 2 API · …',
    exampleTitle: 'Слои сервиса',
  },
  {
    id: 'loci',
    title: 'Дворец памяти',
    subtitle: 'Элементы по «комнатам»',
    wave1: true,
    howTo:
      'Задайте маршрут «комнат» (кухня → коридор →… ) и элементы. Мысленно разложите каждый элемент по комнате, затем восстановите.',
    inputHint: 'Элементы по строкам в порядке маршрута',
    itemsLabel: 'Элементы / комнаты',
    answerLabel: 'Маршрут или эталон (необязательно)',
    answerPlaceholder: 'кухня → коридор → кабинет',
    exampleTitle: 'STAR-ответ',
  },
  {
    id: 'major',
    title: 'Major system',
    subtitle: 'Цифры → образ',
    wave1: true,
    howTo:
      'Введите число. Переведите цифры в согласные → слово-образ, запомните образ, затем восстановите число.',
    inputHint: 'Число или код (443, 8080…)',
    itemsLabel: 'Число',
    answerLabel: 'Образ / эталон (необязательно)',
    answerPlaceholder: 'ром → 43',
    exampleTitle: 'Порт HTTPS',
  },
  {
    id: 'keyword',
    title: 'Keyword',
    subtitle: 'Звук → образ термина',
    wave1: true,
    howTo:
      'Введите чужой термин. Подберите созвучный образ на родном языке и свяжите с смыслом — затем проверьте себя.',
    inputHint: 'Термин (одна строка) и при желании перевод/смысл ниже',
    itemsLabel: 'Термин (+ смысл со 2-й строки)',
    answerLabel: 'Образ / эталон (необязательно)',
    answerPlaceholder: 'звучит как… → образ',
    exampleTitle: 'Термин',
  },
]

export function techniqueLabel(id: MnemonicTechniqueId): string {
  return MNEMONIC_TECHNIQUE_META.find((item) => item.id === id)?.title || id
}

export function getTechniqueMeta(id: string): MnemonicTechniqueMeta | undefined {
  if (!isMnemonicTechniqueId(id)) {
    return undefined
  }
  return MNEMONIC_TECHNIQUE_META.find((item) => item.id === id)
}

export function parseItemsText(raw: string, technique: MnemonicTechniqueId): string[] {
  const lines = raw
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
  if (technique === 'chunking' || technique === 'major') {
    const joined = lines.join(' ').trim()
    return joined ? [joined] : []
  }
  if (technique === 'keyword') {
    return lines.slice(0, 4)
  }
  return lines
}
