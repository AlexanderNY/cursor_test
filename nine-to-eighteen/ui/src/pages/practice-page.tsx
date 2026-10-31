import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import { TrainerTabs } from '@/components/trainer-tabs'

type TaskId =
  | 'list-keys'
  | 'extra-render'
  | 'single-state'
  | 'broken-api'
  | 'brief-sort'
  | 'keep-criteria'
  | 'rest-or-queue'
  | 'star'

const TASKS: Array<{ id: TaskId; label: string; specialty: string }> = [
  { id: 'list-keys', label: 'Ключ списка', specialty: 'Разработчик' },
  { id: 'extra-render', label: 'Лишний рендер', specialty: 'Разработчик' },
  { id: 'single-state', label: 'Один источник', specialty: 'Разработчик' },
  { id: 'broken-api', label: 'Сломанный API', specialty: 'Тестировщик' },
  { id: 'brief-sort', label: 'Разложи бриф', specialty: 'Аналитик' },
  { id: 'keep-criteria', label: 'Оставь критерий', specialty: 'Аналитик и владелец продукта' },
  { id: 'rest-or-queue', label: 'REST или очередь', specialty: 'Аналитик' },
  { id: 'star', label: 'STAR 90 секунд', specialty: 'Все' },
]

const TASK_ALIASES: Record<string, TaskId> = {
  'user-story': 'brief-sort',
}

function isTaskId(value: string | null): value is TaskId {
  return TASKS.some((task) => task.id === value)
}

function words(value: string): number {
  return value.trim().split(/\s+/).filter(Boolean).length
}

export function PracticePage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const requested = searchParams.get('task')
  const aliased = requested ? TASK_ALIASES[requested] : undefined
  const taskId: TaskId = aliased || (isTaskId(requested) ? requested : 'list-keys')

  useEffect(() => {
    if (!aliased) {
      return
    }
    const params = new URLSearchParams(searchParams)
    params.set('task', aliased)
    setSearchParams(params, { replace: true })
  }, [aliased, searchParams, setSearchParams])

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
      {taskId === 'brief-sort' ? <BriefSortTask /> : null}
      {taskId === 'keep-criteria' ? <KeepCriteriaTask /> : null}
      {taskId === 'rest-or-queue' ? <RestOrQueueTask /> : null}
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

type BriefBucket = 'fr' | 'nfr' | 'transitional' | 'wish'

const BRIEF_BUCKETS: Array<{ id: BriefBucket; label: string }> = [
  { id: 'fr', label: 'FR' },
  { id: 'nfr', label: 'NFR' },
  { id: 'transitional', label: 'Переходное' },
  { id: 'wish', label: 'Пожелание' },
]

const BRIEF_LINES: Array<{ id: string; text: string; bucket: BriefBucket }> = [
  { id: 'pay', text: 'Покупатель оплачивает заказ с телефона', bucket: 'fr' },
  { id: 'latency', text: 'Экран ответа банка появляется быстрее 300 мс', bucket: 'nfr' },
  {
    id: 'dual',
    text: 'Неделю старая и новая касса работают параллельно, суммы сверяют',
    bucket: 'transitional',
  },
  { id: 'nice', text: 'Чтобы было удобно', bucket: 'wish' },
  {
    id: 'decline',
    text: 'Если банк отказал, заказ не оплачен и деньги не списаны',
    bucket: 'fr',
  },
  { id: 'sla', text: 'Оплата доступна 99.9% времени за месяц', bucket: 'nfr' },
  {
    id: 'migrate',
    text: 'Один раз перенести сохранённые карты из старого биллинга',
    bucket: 'transitional',
  },
  { id: 'fast', text: 'Система должна быть быстрой', bucket: 'wish' },
]

function BriefSortTask() {
  const [picked, setPicked] = useState<Partial<Record<string, BriefBucket>>>({})
  const [verdict, setVerdict] = useState<{ passed: boolean; text: string } | null>(null)

  function choose(lineId: string, bucket: BriefBucket) {
    setPicked((prev) => ({ ...prev, [lineId]: bucket }))
    setVerdict(null)
  }

  function check() {
    const missing = BRIEF_LINES.some((line) => !picked[line.id])
    if (missing) {
      setVerdict({
        passed: false,
        text: 'Разложите все восемь фраз. Пустая корзина не считается ответом.',
      })
      return
    }
    const wrong = BRIEF_LINES.some((line) => picked[line.id] !== line.bucket)
    if (wrong) {
      setVerdict({
        passed: false,
        text: 'FR — что система делает. NFR — порог качества. Переходное нужно только на запуск и потом закрывается. «Удобно» и «быстро» без числа — пожелание.',
      })
      return
    }
    setVerdict({
      passed: true,
      text: 'Функция, порог, разовый перенос и голое пожелание разложены по разным корзинам.',
    })
  }

  return (
    <section className="quiz-question">
      <h2 className="quiz-setup-title">Разложи бриф</h2>
      <p className="learn-lead">
        Заказчик сказал: «хочу оплачивать заказ с телефона и понимать, если банк отказал». Каждую
        фразу положите в одну корзину.
      </p>
      <div className="practice-lines">
        {BRIEF_LINES.map((line) => (
          <div key={line.id}>
            <p className="practice-line-text">{line.text}</p>
            <div className="practice-buckets" role="group" aria-label={line.text}>
              {BRIEF_BUCKETS.map((bucket) => (
                <button
                  key={bucket.id}
                  type="button"
                  className={`quiz-choice practice-bucket${picked[line.id] === bucket.id ? ' is-active' : ''}`}
                  aria-pressed={picked[line.id] === bucket.id}
                  onClick={() => choose(line.id, bucket.id)}
                >
                  {bucket.label}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
      <button type="button" className="learn-admin-btn learn-admin-btn-primary" onClick={check}>
        Проверить
      </button>
      <Verdict passed={verdict?.passed ?? null} text={verdict?.text || ''} />
    </section>
  )
}

const CRITERIA: Array<{ id: string; text: string; keep: boolean }> = [
  {
    id: 'paid',
    text: 'После успеха статус заказа «оплачен», сумма заказа равна сумме списания',
    keep: true,
  },
  { id: 'fast', text: 'Оплата должна быть удобной и быстрой', keep: false },
  { id: 'address', text: 'Покупатель видит сохранённые адреса доставки', keep: false },
  {
    id: 'decline',
    text: 'Если банк отказал, заказ не оплачен и на экране есть причина',
    keep: true,
  },
  { id: 'zero', text: 'Кнопка «Оплатить» недоступна, пока сумма заказа 0', keep: true },
  { id: 'blue', text: 'Кнопка фирменного синего цвета', keep: false },
  { id: 'retry', text: 'Повторное нажатие не создаёт второе списание', keep: true },
  { id: 'credit', text: 'Приложение само предлагает кредит на покупку', keep: false },
]

function KeepCriteriaTask() {
  const [selected, setSelected] = useState<string[]>([])
  const [verdict, setVerdict] = useState<{ passed: boolean; text: string } | null>(null)

  function toggle(id: string) {
    setSelected((prev) => (prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]))
    setVerdict(null)
  }

  function check() {
    const keepIds = CRITERIA.filter((item) => item.keep).map((item) => item.id)
    const same = selected.length === keepIds.length && keepIds.every((id) => selected.includes(id))
    if (!same) {
      setVerdict({
        passed: false,
        text: 'В приёмке остаются наблюдаемые исходы и негативный путь. «Удобно», чужой сценарий и цвет кнопки туда не входят.',
      })
      return
    }
    setVerdict({
      passed: true,
      text: 'Четыре критерия можно проверить на экране. Пожелание, чужой scope и оформление отсечены.',
    })
  }

  return (
    <section className="quiz-question">
      <h2 className="quiz-setup-title">Оставь критерий</h2>
      <p className="learn-lead">
        История уже есть: «Как покупатель, я хочу оплатить заказ с телефона, чтобы не вводить карту
        на кассе». Отметьте, что остаётся в приёмке.
      </p>
      <div className="practice-lines" role="group" aria-label="Кандидаты в приёмку">
        {CRITERIA.map((item) => {
          const isOn = selected.includes(item.id)
          return (
            <button
              key={item.id}
              type="button"
              className={`quiz-choice${isOn ? ' is-active' : ''}`}
              aria-pressed={isOn}
              onClick={() => toggle(item.id)}
            >
              <span className="quiz-choice-label">{item.text}</span>
              <span className="quiz-choice-meta">{isOn ? 'В приёмке' : 'Не брать'}</span>
            </button>
          )
        })}
      </div>
      <button type="button" className="learn-admin-btn learn-admin-btn-primary" onClick={check}>
        Проверить
      </button>
      <Verdict passed={verdict?.passed ?? null} text={verdict?.text || ''} />
    </section>
  )
}

const PAY_CHANNELS = [
  {
    id: 'rest',
    label: 'Синхронный REST и Idempotency-Key',
    meta: 'Ответ нужен на телефоне сразу',
  },
  {
    id: 'queue',
    label: 'Очередь, ответ придёт позже',
    meta: 'Дедупликация съест повтор',
  },
  {
    id: 'repost',
    label: 'Повторить тот же POST без ключа',
    meta: 'Клиент нажал ещё раз после таймаута',
  },
] as const

const DECLINE_SCREENS = [
  { id: 'reason', label: 'Заказ не оплачен, деньги не списаны, на экране причина отказа' },
  { id: 'ok', label: 'Показать успех: с банком разберёмся потом' },
  { id: 'empty', label: 'Пустая страница и код 500' },
  { id: 'charged', label: 'Деньги списаны, заказ отменён' },
] as const

function RestOrQueueTask() {
  const [channel, setChannel] = useState('')
  const [screen, setScreen] = useState('')
  const [verdict, setVerdict] = useState<{ passed: boolean; text: string } | null>(null)

  function check() {
    if (!channel || !screen) {
      setVerdict({
        passed: false,
        text: 'Выберите и канал списания, и то, что человек видит при отказе банка.',
      })
      return
    }
    if (channel !== 'rest' || screen !== 'reason') {
      setVerdict({
        passed: false,
        text: 'Покупатель ждёт ответ сейчас, цепочка короткая. Повтор POST без ключа списывает второй раз. Очередь сглаживает долгую работу, а не экран оплаты. При отказе заказ не оплачен, деньги на месте, причина на экране.',
      })
      return
    }
    setVerdict({
      passed: true,
      text: 'Ответ нужен сразу, повтор с тем же ключом не создаёт второе списание, отказ банка виден человеку.',
    })
  }

  return (
    <section className="quiz-question">
      <h2 className="quiz-setup-title">REST или очередь</h2>
      <p className="learn-lead">
        Покупатель ждёт на телефоне. После таймаута он нажимает «Оплатить» ещё раз. Второго
        списания быть не должно. Если банк отказал, человек должен это понять.
      </p>
      <div className="practice-groups">
        <div>
          <p className="practice-line-text">Как списывать</p>
          <div className="practice-lines" role="group" aria-label="Как списывать">
            {PAY_CHANNELS.map((item) => (
              <button
                key={item.id}
                type="button"
                className={`quiz-choice${channel === item.id ? ' is-active' : ''}`}
                aria-pressed={channel === item.id}
                onClick={() => {
                  setChannel(item.id)
                  setVerdict(null)
                }}
              >
                <span className="quiz-choice-label">{item.label}</span>
                <span className="quiz-choice-meta">{item.meta}</span>
              </button>
            ))}
          </div>
        </div>
        <div>
          <p className="practice-line-text">Что видит человек при отказе банка</p>
          <div className="practice-lines" role="group" aria-label="Экран при отказе банка">
            {DECLINE_SCREENS.map((item) => (
              <button
                key={item.id}
                type="button"
                className={`quiz-choice${screen === item.id ? ' is-active' : ''}`}
                aria-pressed={screen === item.id}
                onClick={() => {
                  setScreen(item.id)
                  setVerdict(null)
                }}
              >
                <span className="quiz-choice-label">{item.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
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
