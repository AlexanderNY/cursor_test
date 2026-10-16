import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import ts from 'typescript'

const here = path.dirname(fileURLToPath(import.meta.url))
const sourcePath = path.join(here, '../src/data/learn/interview-quiz.ts')
const source = fs.readFileSync(sourcePath, 'utf8')
const js = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2022,
  },
}).outputText
const moduleUrl = `data:text/javascript,${encodeURIComponent(js)}`
const quiz = await import(moduleUrl)

function assert(condition, message) {
  if (!condition) {
    throw new Error(message)
  }
}

const article = {
  slug: 'sql-joins',
  title: 'JOIN',
  episode: 'SQL08',
  tags: ['sql', 'собеседование'],
  theory: '',
  structured: {
    intro: 'Соединения таблиц.',
    sections: [
      {
        heading: 'Частые вопросы с собеседования',
        body: [
          '**Вопрос.** Почему фильтр в WHERE ломает LEFT JOIN?',
          '',
          '**Ответ.** NULL из несовпавших строк отфильтровывается предикатом на правые столбцы.',
          '',
          '**Вопрос.** Чем опасен случайный CROSS JOIN?',
          '',
          '**Ответ.** Декартово произведение раздувает число строк до произведения размеров таблиц.',
        ].join('\n'),
      },
    ],
  },
}

const other = {
  ...article,
  slug: 'py-types',
  title: 'Коллекции',
  episode: 'PY02',
  tags: ['python'],
  structured: {
    intro: '',
    sections: [
      {
        heading: 'Частые вопросы с собеседования',
        body: [
          '**Вопрос.** Почему список нельзя положить ключом в dict?',
          '',
          '**Ответ.** Ключ должен быть hashable, а список изменяемый и хеш ему не гарантируют.',
          '',
          '**Вопрос.** Когда выбрать tuple вместо list?',
          '',
          '**Ответ.** Когда нужен неизменяемый контракт: ключ словаря или фиксированная запись.',
        ].join('\n'),
      },
    ],
  },
}

const outside = {
  ...article,
  slug: 'orphan',
  tags: ['qa'],
  theory: 'В теории этого ответа нет.',
  structured: {
    intro: '',
    sections: [
      {
        heading: 'Основная часть',
        body: '**Вопрос.** Это не раздел собеседования?\n\n**Ответ.** Ответ лежит в другом разделе и в квиз попасть не должен.',
      },
    ],
  },
}

const items = quiz.collectInterviewItems([article, other, outside])
assert(items.length === 4, `expected 4 interview pairs, got ${items.length}`)
assert(items.every((item) => quiz.textAppearsIn(
  `${item.answer}`,
  item.quote,
)), 'quote must be inside the article answer')

const sqlQuiz = quiz.buildInterviewQuiz(items, { track: 'sql', size: 10, seed: 2 })
assert(sqlQuiz.length === 2, `sql quiz size ${sqlQuiz.length}`)
for (const question of sqlQuiz) {
  assert(question.options.includes(question.options[question.correctIndex]), 'correct option exists')
  const correct = question.options[question.correctIndex]
  assert(quiz.textAppearsIn(question.answer, correct), 'correct option is a quote of the article answer')
  assert(
    items.some((item) => item.quote === correct && item.episodeSlug === 'sql-joins'),
    'correct quote comes from the SQL article',
  )
  for (const option of question.options) {
    assert(items.some((item) => item.quote === option), `option is not from an article: ${option}`)
  }
}

const pyQuiz = quiz.buildInterviewQuiz(items, { track: 'python', size: 10, seed: 2 })
assert(pyQuiz.length === 2, 'python track')
assert(quiz.buildInterviewQuiz(items, { track: 'qa', size: 10, seed: 1 }).length === 0, 'qa empty')

const counts = quiz.countByTrack(items)
assert(counts.all === 4 && counts.sql === 2 && counts.python === 2 && counts.qa === 0, 'counts')

console.log('interview quiz checks ok', { pairs: items.length, sql: sqlQuiz.length })
