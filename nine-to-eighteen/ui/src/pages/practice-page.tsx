import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import { TrainerTabs } from '@/components/trainer-tabs'

type TaskId = 'list-keys' | 'extra-render' | 'single-state' | 'broken-api' | 'user-story' | 'star'

const TASKS: Array<{ id: TaskId; label: string; specialty: string }> = [
  { id: 'list-keys', label: 'Ключ списка', specialty: 'Разработчик' },
  { id: 'extra-render', label: 'Лишний рендер', specialty: 'Разработчик' },
  { id: 'single-state', label: 'Один источник', specialty: 'Разработчик' },
  { id: 'broken-api', label: 'Сломанный API', specialty: 'Тестировщик' },
  { id: 'user-story', label: 'История и приёмка', specialty: 'Аналитик и владелец продукта' },
  { id: 'star', label: 'STAR 90 секунд', specialty: 'Все' },
]

function isTaskId(value: string | null): value is TaskId {
  return TASKS.some((task) => task.id === value)
}

function words(value: string): number {
  return value.trim().split(/\s+/).filter(Boolean).length
}

export function PracticePage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const requested = searchParams.get('task')
  const taskId: TaskId = isTaskId(requested) ? requested : 'list-keys'

  function choose(next: TaskId) {
    const params = new URLSearchParams(searchParams)
    params.set('task', next)
    setSearchParams(params, { replace: true })
  }

  return (
    <PageShell content="article">
      <Link to="/game/learn" className="back-link">
        ← Learn
      </Link>
      <header className="learn-header">
        <p className="learn-eyebrow">Тренажёр</p>
        <h1 className="learn-title">Практика к собеседованию</h1>
        <p className="learn-lead">
          Короткие задачи без отдельного проекта. Python, SQL и Git остаются в своих песочницах.
          Здесь — то, что спрашивают руками на React, в тестировании, у аналитика и в поведенческом
          блоке.
        </p>
      </header>
      <TrainerTabs />
      <div className="quiz-choice-grid" role="tablist" aria-label="Задачи">
        {TASKS.map((task) => (
          <button
            key={task.id}
            type="button"
            className={`quiz-choice${task.id === taskId ? ' is-active' : ''}`}
            onClick={() => choose(task.id)}
          >
            <span className="quiz-choice-label">{task.label}</span>
            <span className="quiz-choice-meta">{task.specialty}</span>
          </button>
        ))}
      </div>
      {taskId === 'list-keys' ? <ListKeysTask /> : null}
      {taskId === 'extra-render' ? <ExtraRenderTask /> : null}
      {taskId === 'single-state' ? <SingleStateTask /> : null}
      {taskId === 'broken-api' ? <BrokenApiTask /> : null}
      {taskId === 'user-story' ? <UserStoryTask /> : null}
      {taskId === 'star' ? <StarTask /> : null}
    </PageShell>
  )
}

function Verdict({ passed, text }: { passed: boolean | null; text: string }) {
  if (passed === null) {
    return null
  }
  return (
    <p className="learn-section-note" role="status">
      {passed ? 'Сошлось. ' : 'Пока нет. '}
      {text}
    </p>
  )
}

function ListKeysTask() {
  const seed = useMemo(
    () => [
      { id: 'a', name: 'Чай' },
      { id: 'b', name: 'Кофе' },
      { id: 'c', name: 'Вода' },
    ],
    [],
  )
  const [items, setItems] = useState(seed)
  const [keyMode, setKeyMode] = useState<'index' | 'id'>('index')
  const [notes, setNotes] = useState<Record<string, string>>({})
  const [moved, setMoved] = useState(false)
  const [verdict, setVerdict] = useState<{ passed: boolean; text: string } | null>(null)

  function noteKey(itemId: string, index: number): string {
    return keyMode === 'id' ? itemId : `i${index}`
  }

  function move(index: number, direction: -1 | 1) {
    const next = index + direction
    if (next < 0 || next >= items.length) {
      return
    }
    const copy = [...items]
    const current = copy[index]
    copy[index] = copy[next]
    copy[next] = current
    setItems(copy)
    setMoved(true)
    setVerdict(null)
  }

  function check() {
    const typed = Object.values(notes).some((value) => value.trim().length > 0)
    if (keyMode !== 'id' || !moved || !typed) {
      setVerdict({
        passed: false,
        text: 'Наберите заметку, переставьте строку при ключе index и посмотрите, что текст остался на месте. Затем переключите ключ на id и переставьте ещё раз: заметка должна уехать вместе с названием.',
      })
      return
    }
    setVerdict({
      passed: true,
      text: 'Ключ — устойчивый id записи. Индекс говорит React, что это «третья строка», и состояние инпута прилипает к месту.',
    })
  }

  return (
    <section className="quiz-question">
      <h2 className="quiz-setup-title">Ключ списка</h2>
      <p className="learn-lead">
        У каждой строки есть заметка. Переставьте строки. При ключе по индексу заметка остаётся на
        месте. При ключе по id она едет с товаром.
      </p>
      <label className="learn-filter-field">
        <span>Ключ</span>
        <select
          value={keyMode}
          onChange={(event) => {
            setKeyMode(event.target.value === 'id' ? 'id' : 'index')
            setNotes({})
            setVerdict(null)
          }}
        >
          <option value="index">index</option>
          <option value="id">id</option>
        </select>
      </label>
      <ul className="quiz-options">
        {items.map((item, index) => (
          <li key={noteKey(item.id, index)}>
            {item.name}{' '}
            <input
              aria-label={`Заметка для ${item.name}`}
              value={notes[noteKey(item.id, index)] || ''}
              onChange={(event) =>
                setNotes((prev) => ({ ...prev, [noteKey(item.id, index)]: event.target.value }))
              }
            />{' '}
            <button type="button" className="learn-admin-btn" onClick={() => move(index, -1)}>
              Вверх
            </button>{' '}
            <button type="button" className="learn-admin-btn" onClick={() => move(index, 1)}>
              Вниз
            </button>
          </li>
        ))}
      </ul>
      <button type="button" className="learn-admin-btn learn-admin-btn-primary" onClick={check}>
        Проверить
      </button>
      <Verdict passed={verdict?.passed ?? null} text={verdict?.text || ''} />
    </section>
  )
}

function ExtraRenderTask() {
  const [count, setCount] = useState(0)
  const [memoOn, setMemoOn] = useState(false)
  const [childRenders, setChildRenders] = useState(1)
  const [seenCount, setSeenCount] = useState(0)
  const [verdict, setVerdict] = useState<{ passed: boolean; text: string } | null>(null)

  function bump() {
    const nextCount = count + 1
    const nextRenders = memoOn ? childRenders : childRenders + 1
    const nextSeen = memoOn ? seenCount : nextCount
    setCount(nextCount)
    setChildRenders(nextRenders)
    setSeenCount(nextSeen)
    setVerdict(
      memoOn
        ? {
            passed: true,
            text: `Счётчик родителя стал ${nextCount}, ребёнок остался на ${nextRenders} пересчётах и всё ещё видел ${nextSeen}. memo помогает, только если пропсы ребёнка не менялись.`,
          }
        : {
            passed: false,
            text: `Без memo ребёнок пересчитался (${nextRenders}) вместе со счётчиком ${nextCount}, хотя его текст от счётчика не зависит. Включите memo и нажмите ещё раз.`,
          },
    )
  }

  return (
    <section className="quiz-question">
      <h2 className="quiz-setup-title">Лишний рендер</h2>
      <p className="learn-lead">
        Родитель считает клики. Подпись ребёнка от счётчика не зависит. Последний пересчёт ребёнка
        видел счётчик {seenCount}, всего пересчётов: {childRenders}. Memo сейчас{' '}
        {memoOn ? 'включён' : 'выключен'}.
      </p>
      <button type="button" className="learn-admin-btn" onClick={() => setMemoOn((value) => !value)}>
        {memoOn ? 'Выключить memo' : 'Включить memo'}
      </button>{' '}
      <button type="button" className="learn-admin-btn learn-admin-btn-primary" onClick={bump}>
        Счётчик: {count}
      </button>
      <Verdict passed={verdict?.passed ?? null} text={verdict?.text || ''} />
    </section>
  )
}

function SingleStateTask() {
  const [parentQty, setParentQty] = useState(2)
  const [childQty, setChildQty] = useState(2)
  const [lifted, setLifted] = useState(false)
  const [verdict, setVerdict] = useState<{ passed: boolean; text: string } | null>(null)
  const shown = lifted ? parentQty : childQty
  const total = shown * 10

  function check() {
    if (!lifted || shown !== parentQty || total !== parentQty * 10) {
      setVerdict({
        passed: false,
        text: 'Пока сумма берётся из копии в ребёнке, правка родителя её не меняет. Оставьте одно поле.',
      })
      return
    }
    setVerdict({
      passed: true,
      text: 'Сумма считается из того же числа, которое показано в поле. Второе состояние было копией и врало.',
    })
  }

  return (
    <section className="quiz-question">
      <h2 className="quiz-setup-title">Один источник состояния</h2>
      <p className="learn-lead">
        Цена позиции 10. Сумма на экране: {total}. Пока источник не один, поле ребёнка и число
        родителя разъезжаются.
      </p>
      <label className="learn-filter-field">
        <span>Количество у родителя</span>
        <input
          type="number"
          value={parentQty}
          onChange={(event) => setParentQty(Number(event.target.value) || 0)}
        />
      </label>
      <label className="learn-filter-field">
        <span>Количество в поле</span>
        <input
          type="number"
          value={shown}
          onChange={(event) => {
            const next = Number(event.target.value) || 0
            if (lifted) {
              setParentQty(next)
            } else {
              setChildQty(next)
            }
          }}
        />
      </label>
      <button type="button" className="learn-admin-btn" onClick={() => setLifted(true)}>
        Оставить один источник
      </button>{' '}
      <button type="button" className="learn-admin-btn learn-admin-btn-primary" onClick={check}>
        Проверить
      </button>
      <Verdict passed={verdict?.passed ?? null} text={verdict?.text || ''} />
    </section>
  )
}

const API_CASES = [
  {
    id: 'empty-200',
    title: 'GET /orders вернул 200 и пустое тело',
    expectStatus: '200',
    keyword: 'тело',
    hint: 'Статус успешный, контракт тела нарушен.',
  },
  {
    id: 'email-500',
    title: 'POST /users с почтой «нет собаки» вернул 500',
    expectStatus: '400',
    keyword: 'клиент',
    hint: 'Кривой вход — ошибка клиента, не падение сервера.',
  },
  {
    id: 'sum-3',
    title: 'В заказе две позиции по 1, экран показывает сумму 3',
    expectStatus: '200',
    keyword: 'сумм',
    hint: 'Ответ мог быть 200. Ложь в правиле суммы, её надо сверить с таблицей.',
  },
] as const

function BrokenApiTask() {
  const [caseId, setCaseId] = useState<(typeof API_CASES)[number]['id']>('empty-200')
  const [status, setStatus] = useState('')
  const [note, setNote] = useState('')
  const [verdict, setVerdict] = useState<{ passed: boolean; text: string } | null>(null)
  const current = API_CASES.find((item) => item.id === caseId) || API_CASES[0]

  function check() {
    const statusOk = status.trim() === current.expectStatus
    const noteOk = note.toLowerCase().includes(current.keyword)
    setVerdict({
      passed: statusOk && noteOk,
      text: statusOk && noteOk
        ? 'Код и причина совпали с контрактом. Дальше этот случай становится одним негативным кейсом, не эссе.'
        : `${current.hint} В заметке должно быть слово про «${current.keyword}». Ожидаемый код: ${current.expectStatus}.`,
    })
  }

  return (
    <section className="quiz-question">
      <h2 className="quiz-setup-title">Сломанный API</h2>
      <p className="learn-lead">{current.title}</p>
      <label className="learn-filter-field">
        <span>Случай</span>
        <select
          value={caseId}
          onChange={(event) => {
            setCaseId(event.target.value as (typeof API_CASES)[number]['id'])
            setVerdict(null)
          }}
        >
          {API_CASES.map((item) => (
            <option key={item.id} value={item.id}>
              {item.title}
            </option>
          ))}
        </select>
      </label>
      <label className="learn-filter-field">
        <span>Какой код вы ожидали</span>
        <input value={status} onChange={(event) => setStatus(event.target.value)} placeholder="400" />
      </label>
      <label className="learn-filter-field">
        <span>Что именно сломано</span>
        <input
          value={note}
          onChange={(event) => setNote(event.target.value)}
          placeholder="пустое тело / ошибка клиента / сумма"
        />
      </label>
      <button type="button" className="learn-admin-btn learn-admin-btn-primary" onClick={check}>
        Проверить
      </button>
      <Verdict passed={verdict?.passed ?? null} text={verdict?.text || ''} />
    </section>
  )
}

function UserStoryTask() {
  const [role, setRole] = useState('')
  const [want, setWant] = useState('')
  const [why, setWhy] = useState('')
  const [criteria, setCriteria] = useState(['', '', ''])
  const [negative, setNegative] = useState('')
  const [verdict, setVerdict] = useState<{ passed: boolean; text: string } | null>(null)

  function check() {
    const filled = [role, want, why, negative, ...criteria].every((value) => words(value) >= 2)
    const negativeMarksFailure = /не|ошиб|отказ|пуст/i.test(negative)
    setVerdict({
      passed: filled && negativeMarksFailure,
      text:
        filled && negativeMarksFailure
          ? 'История называет роль, действие и пользу. Три критерия наблюдаемы, негативный случай говорит, что будет при отказе.'
          : 'Нужны роль, действие, польза, три критерия и негативный случай. В негативном напишите, что увидит человек, если оплата или проверка не прошла.',
    })
  }

  return (
    <section className="quiz-question">
      <h2 className="quiz-setup-title">История и критерии приёмки</h2>
      <p className="learn-lead">
        Заказчик сказал: «хочу оплачивать заказ с телефона и понимать, если банк отказал». Соберите
        историю и приёмку. Разработчик этот текст не пишет вместо вас — он читает ваш выпуск про
        требования как справочник.
      </p>
      <label className="learn-filter-field">
        <span>Роль</span>
        <input value={role} onChange={(event) => setRole(event.target.value)} />
      </label>
      <label className="learn-filter-field">
        <span>Хочу</span>
        <input value={want} onChange={(event) => setWant(event.target.value)} />
      </label>
      <label className="learn-filter-field">
        <span>Чтобы</span>
        <input value={why} onChange={(event) => setWhy(event.target.value)} />
      </label>
      {criteria.map((value, index) => (
        <label key={index} className="learn-filter-field">
          <span>Критерий {index + 1}</span>
          <input
            value={value}
            onChange={(event) =>
              setCriteria((prev) => prev.map((item, itemIndex) => (itemIndex === index ? event.target.value : item)))
            }
          />
        </label>
      ))}
      <label className="learn-filter-field">
        <span>Негативный случай</span>
        <input value={negative} onChange={(event) => setNegative(event.target.value)} />
      </label>
      <button type="button" className="learn-admin-btn learn-admin-btn-primary" onClick={check}>
        Проверить
      </button>
      <Verdict passed={verdict?.passed ?? null} text={verdict?.text || ''} />
    </section>
  )
}

function StarTask() {
  const [left, setLeft] = useState(90)
  const [running, setRunning] = useState(false)
  const [situation, setSituation] = useState('')
  const [task, setTask] = useState('')
  const [action, setAction] = useState('')
  const [result, setResult] = useState('')
  const [verdict, setVerdict] = useState<{ passed: boolean; text: string } | null>(null)

  useEffect(() => {
    if (!running) {
      return
    }
    const timer = window.setInterval(() => {
      setLeft((value) => {
        if (value <= 1) {
          setRunning(false)
          return 0
        }
        return value - 1
      })
    }, 1000)
    return () => window.clearInterval(timer)
  }, [running])

  function check() {
    const actionWords = words(action)
    const situationWords = words(situation)
    const filled = [situation, task, action, result].every((value) => words(value) >= 3)
    const actionLeads = actionWords > situationWords
    setVerdict({
      passed: filled && actionLeads,
      text:
        filled && actionLeads
          ? 'Действие длиннее ситуации. На собеседовании так и отличают ваш поступок от пересказа обстоятельств.'
          : 'Заполните все четыре поля хотя бы тремя словами. Действие должно быть длиннее ситуации.',
    })
  }

  return (
    <section className="quiz-question">
      <h2 className="quiz-setup-title">STAR за {left} с</h2>
      <p className="learn-lead">
        История: на ревью нашли, что сумма заказа расходится с таблицей, релиз через два часа.
      </p>
      <button type="button" className="learn-admin-btn" onClick={() => setRunning(true)} disabled={running}>
        Старт
      </button>
      <label className="learn-filter-field">
        <span>Ситуация</span>
        <textarea value={situation} onChange={(event) => setSituation(event.target.value)} rows={2} />
      </label>
      <label className="learn-filter-field">
        <span>Задача</span>
        <textarea value={task} onChange={(event) => setTask(event.target.value)} rows={2} />
      </label>
      <label className="learn-filter-field">
        <span>Действие</span>
        <textarea value={action} onChange={(event) => setAction(event.target.value)} rows={3} />
      </label>
      <label className="learn-filter-field">
        <span>Результат</span>
        <textarea value={result} onChange={(event) => setResult(event.target.value)} rows={2} />
      </label>
      <button type="button" className="learn-admin-btn learn-admin-btn-primary" onClick={check}>
        Проверить
      </button>
      <Verdict passed={verdict?.passed ?? null} text={verdict?.text || ''} />
    </section>
  )
}
