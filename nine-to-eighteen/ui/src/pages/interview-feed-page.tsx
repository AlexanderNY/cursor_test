import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import { collectInterviewItems } from '@/data/learn/interview-quiz'
import { postsWithBundledEpisodes } from '@/data/learn/learn-store'
import {
  LEARN_LEVELS,
  LEARN_PROFILES,
  isLearnLevelId,
  isLearnProfileId,
  type LearnLevelId,
  type LearnProfileId,
} from '@/data/learn/labels'
import {
  LEARN_LEVEL_FILTER_KEY,
  LEARN_PROFILE_FILTER_KEY,
  RECALL_NEW_LIMIT,
  buildRecallSession,
  interviewRecallId,
  formatRecallDay,
  readRecallStore,
  recallSessionStats,
  writeRecallMark,
  type RecallEntry,
  type RecallMark,
  type RecallStore,
} from '@/data/learn/recall'
import { getPublishedPosts, useLearnPosts } from '@/data/learn/use-learn-posts'
import { learnAnkiCards } from '@/data/site/structured-post'

type DeckId = 'questions' | 'cards'
type ViewId = 'session' | 'all'

type QueueCard = {
  id: string
  prompt: string
  answer: string
  episodeSlug: string
  episodeTitle: string
  episodeCode: string
}

const MARKS: Array<{ id: RecallMark; label: string; when: string }> = [
  { id: 'missed', label: 'Не знал', when: 'завтра' },
  { id: 'stumbled', label: 'Запнулся', when: 'через 3 дня' },
  { id: 'said', label: 'Сказал', when: 'через 7 дней' },
]

function ankiCardId(slug: string, index: number, front: string): string {
  return `anki:${slug}:${index}:${front.trim()}`
}

export function InterviewFeedPage() {
  const { posts, isReady } = useLearnPosts()
  const published = useMemo(
    () => postsWithBundledEpisodes(getPublishedPosts(posts)),
    [posts],
  )
  const [profile, setProfile] = useState<LearnProfileId | ''>(() => {
    const saved = window.localStorage.getItem(LEARN_PROFILE_FILTER_KEY) || ''
    return isLearnProfileId(saved) ? saved : ''
  })
  const [level, setLevel] = useState<LearnLevelId | ''>(() => {
    const saved = window.localStorage.getItem(LEARN_LEVEL_FILTER_KEY) || ''
    return isLearnLevelId(saved) ? saved : ''
  })
  const [query, setQuery] = useState('')
  const [deck, setDeck] = useState<DeckId>('questions')
  const [view, setView] = useState<ViewId>('session')
  const [openId, setOpenId] = useState<string | null>(null)
  const [records, setRecords] = useState<RecallStore>(() => readRecallStore())
  const now = useMemo(() => Date.now(), [records])

  const pool = useMemo(() => {
    const needle = query.trim().toLowerCase()
    const matched = published.filter((post) => {
      if (profile && !(post.profiles || []).includes(profile)) {
        return false
      }
      if (level && post.level !== level) {
        return false
      }
      return true
    })
    const questions: QueueCard[] = collectInterviewItems(matched).map((item) => ({
      id: interviewRecallId(item.episodeSlug, item.question),
      prompt: item.question,
      answer: item.answer,
      episodeSlug: item.episodeSlug,
      episodeTitle: item.episodeTitle,
      episodeCode: item.episodeCode,
    }))
    const cards: QueueCard[] = []
    for (const post of matched) {
      if (!post.structured?.anki?.length) {
        continue
      }
      learnAnkiCards(post.structured).forEach((card, index) => {
        cards.push({
          id: ankiCardId(post.slug, index, card.front),
          prompt: card.front,
          answer: card.back,
          episodeSlug: post.slug,
          episodeTitle: post.title,
          episodeCode: post.episode,
        })
      })
    }
    const source = deck === 'questions' ? questions : cards
    if (!needle) {
      return source
    }
    return source.filter(
      (item) =>
        item.prompt.toLowerCase().includes(needle) || item.answer.toLowerCase().includes(needle),
    )
  }, [published, profile, level, query, deck])

  const stats = useMemo(
    () => recallSessionStats(pool.map((item) => item.id), records, now),
    [pool, records, now],
  )
  const session = useMemo(
    () => buildRecallSession(pool, records, now),
    [pool, records, now],
  )
  const active = session[0]

  function chooseProfile(next: LearnProfileId | '') {
    setProfile(next)
    window.localStorage.setItem(LEARN_PROFILE_FILTER_KEY, next)
    setOpenId(null)
  }

  function chooseLevel(next: LearnLevelId | '') {
    setLevel(next)
    window.localStorage.setItem(LEARN_LEVEL_FILTER_KEY, next)
    setOpenId(null)
  }

  function mark(id: string, next: RecallMark) {
    setRecords(writeRecallMark(id, next))
    setOpenId(null)
  }

  const waitingNew = Math.max(0, stats.fresh - RECALL_NEW_LIMIT)

  return (
    <PageShell content="article">
      <Link to="/game/learn" className="back-link">
        ← Learn
      </Link>
      <header className="learn-header">
        <p className="learn-eyebrow">Лента</p>
        <h1 className="learn-title">Что спрашивают</h1>
        <p className="learn-lead">
          Сессия начинается с «не знал», затем «запнулся». Новые вопросы и карточки — после
          повторов, не больше {RECALL_NEW_LIMIT} за раз. «Не знал» вернётся завтра, «запнулся» через
          3 дня, «сказал» через 7. Отметки остаются в этом браузере. Собрать из них созвон — в{' '}
          <Link to="/game/slot">слоте на 25 минут</Link>. Квиз с вариантами — в{' '}
          <Link to="/game/quiz">проверке</Link>.
        </p>
      </header>
      <div className="quiz-choice-grid" role="tablist" aria-label="Колода">
        <button
          type="button"
          className={`quiz-choice${deck === 'questions' ? ' is-active' : ''}`}
          onClick={() => {
            setDeck('questions')
            setOpenId(null)
          }}
        >
          <span className="quiz-choice-label">Вопросы</span>
          <span className="quiz-choice-meta">из статей</span>
        </button>
        <button
          type="button"
          className={`quiz-choice${deck === 'cards' ? ' is-active' : ''}`}
          onClick={() => {
            setDeck('cards')
            setOpenId(null)
          }}
        >
          <span className="quiz-choice-label">Карточки</span>
          <span className="quiz-choice-meta">Anki выпуска</span>
        </button>
        <button
          type="button"
          className={`quiz-choice${view === 'session' ? ' is-active' : ''}`}
          onClick={() => {
            setView('session')
            setOpenId(null)
          }}
        >
          <span className="quiz-choice-label">Сессия</span>
          <span className="quiz-choice-meta">
            {stats.missed + stats.stumbled + stats.said} к повтору
          </span>
        </button>
        <button
          type="button"
          className={`quiz-choice${view === 'all' ? ' is-active' : ''}`}
          onClick={() => {
            setView('all')
            setOpenId(null)
          }}
        >
          <span className="quiz-choice-label">Вся колода</span>
          <span className="quiz-choice-meta">{pool.length}</span>
        </button>
      </div>
      <div className="learn-filters" aria-label="Фильтр ленты">
        <label className="learn-filter-field">
          <span>Специальность</span>
          <select
            value={profile}
            onChange={(event) => chooseProfile(event.target.value as LearnProfileId | '')}
          >
            <option value="">Все</option>
            {LEARN_PROFILES.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <label className="learn-filter-field">
          <span>Уровень</span>
          <select
            value={level}
            onChange={(event) => chooseLevel(event.target.value as LearnLevelId | '')}
          >
            <option value="">Все</option>
            {LEARN_LEVELS.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <label className="learn-filter-field">
          <span>Поиск</span>
          <input
            value={query}
            onChange={(event) => {
              setQuery(event.target.value)
              setOpenId(null)
            }}
            placeholder="GIL, JOIN, критерий"
          />
        </label>
      </div>
      <p className="learn-section-note">
        К повторению: {stats.missed} «не знал», {stats.stumbled} «запнулся», {stats.said} «сказал».
        Новых в колоде: {stats.fresh}
        {view === 'session' && waitingNew > 0 ? `, в эту сессию войдёт ${RECALL_NEW_LIMIT}` : ''}.
      </p>
      {!isReady ? (
        <p className="learn-section-note">Загрузка…</p>
      ) : pool.length === 0 ? (
        <p className="learn-section-note">
          Для этой специальности и уровня в опубликованных выпусках пока нет{' '}
          {deck === 'questions' ? 'пар «вопрос / ответ»' : 'карточек'}.
        </p>
      ) : view === 'session' ? (
        active ? (
          <section className="quiz-question">
            <p className="quiz-question-index">В сессии осталось {session.length}</p>
            <CardBody
              item={active}
              open={openId === active.id}
              entry={records[active.id]}
              onOpen={() => setOpenId(active.id)}
              onMark={(next) => mark(active.id, next)}
            />
          </section>
        ) : (
          <p className="learn-section-note">
            На сегодня эта колода закрыта. «Не знал» вернётся завтра, «запнулся» через 3 дня,
            «сказал» через 7.
          </p>
        )
      ) : (
        <ol className="quiz-options">
          {pool.map((item) => (
            <li key={item.id} className="quiz-question">
              <CardBody
                item={item}
                open={openId === item.id}
                entry={records[item.id]}
                onOpen={() => setOpenId(item.id)}
                onMark={(next) => mark(item.id, next)}
              />
            </li>
          ))}
        </ol>
      )}
    </PageShell>
  )
}

function CardBody({
  item,
  open,
  entry,
  onOpen,
  onMark,
}: {
  item: QueueCard
  open: boolean
  entry: RecallEntry | undefined
  onOpen: () => void
  onMark: (mark: RecallMark) => void
}) {
  return (
    <>
      {item.episodeCode ? (
        <p className="quiz-question-index">
          {item.episodeCode} · {item.episodeTitle}
        </p>
      ) : null}
      <p className="quiz-question-prompt">{item.prompt}</p>
      {open ? (
        <>
          <p className="learn-lead">{item.answer}</p>
          <div className="learn-admin-actions">
            {MARKS.map((option) => (
              <button
                key={option.id}
                type="button"
                className={`learn-admin-btn${entry?.mark === option.id ? ' learn-admin-btn-primary' : ''}`}
                onClick={() => onMark(option.id)}
              >
                {option.label} · {option.when}
              </button>
            ))}
          </div>
        </>
      ) : (
        <button type="button" className="learn-admin-btn" onClick={onOpen}>
          Показать ответ
        </button>
      )}
      {entry ? (
        <p className="learn-section-note">Вернётся {formatRecallDay(entry.dueAt)}.</p>
      ) : null}
      <p className="learn-section-note">
        <Link to={`/game/learn/${item.episodeSlug}`}>Статья-справочник</Link>
      </p>
    </>
  )
}
