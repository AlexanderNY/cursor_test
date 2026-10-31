import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  siteCreateFocusLog,
  siteListFocusLogs,
  type SiteFocusLog,
} from '@/data/site/site-api'

const STORAGE_KEY = '9to18-focus-timer'

type TimerMode = 'focus' | 'break'
type StoredTimer = {
  mode: TimerMode
  totalSec: number
  remainingSec: number
  running: boolean
  startedAt: number | null
}

const PRESETS = [
  { label: 'Pomodoro 25', focus: 25, brk: 5 },
  { label: 'Короткий 15', focus: 15, brk: 5 },
  { label: 'Глубокий 50', focus: 50, brk: 10 },
] as const

function loadStored(): StoredTimer {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return {
        mode: 'focus',
        totalSec: 25 * 60,
        remainingSec: 25 * 60,
        running: false,
        startedAt: null,
      }
    }
    return JSON.parse(raw) as StoredTimer
  } catch {
    return {
      mode: 'focus',
      totalSec: 25 * 60,
      remainingSec: 25 * 60,
      running: false,
      startedAt: null,
    }
  }
}

function formatClock(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

type FocusTimerProps = {
  taskTitle?: string
  onSession?: (minutes: number) => void
}

export function FocusTimer({ taskTitle = '', onSession }: FocusTimerProps) {
  const onSessionRef = useRef(onSession)
  onSessionRef.current = onSession
  const sessionLabel = taskTitle.trim() || 'Pomodoro'
  const [state, setState] = useState<StoredTimer>(() => loadStored())
  const [logs, setLogs] = useState<SiteFocusLog[]>([])
  const [immersive, setImmersive] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  }, [state])

  useEffect(() => {
    void siteListFocusLogs()
      .then(setLogs)
      .catch(() => setLogs([]))
  }, [])

  const tickRemaining = useCallback(() => {
    setState((prev) => {
      if (!prev.running || prev.startedAt == null) {
        return prev
      }
      const elapsed = Math.floor((Date.now() - prev.startedAt) / 1000)
      const remaining = Math.max(0, prev.totalSec - elapsed)
      if (remaining === prev.remainingSec) {
        return prev
      }
      return { ...prev, remainingSec: remaining }
    })
  }, [])

  useEffect(() => {
    if (!state.running) {
      return
    }
    tickRemaining()
    const id = window.setInterval(tickRemaining, 500)
    return () => window.clearInterval(id)
  }, [state.running, tickRemaining])

  useEffect(() => {
    if (!state.running || state.remainingSec > 0) {
      return
    }
    const finishedMode = state.mode
    const minutes = Math.max(1, Math.round(state.totalSec / 60))
    setState((prev) => ({
      ...prev,
      running: false,
      startedAt: null,
      remainingSec: 0,
    }))
    if (finishedMode === 'focus') {
      void siteCreateFocusLog({ minutes, label: sessionLabel })
        .then((log) => setLogs((prev) => [log, ...prev].slice(0, 50)))
        .catch((err) =>
          setError(err instanceof Error ? err.message : 'Не удалось записать фокус'),
        )
      onSessionRef.current?.(minutes)
    }
  }, [sessionLabel, state.mode, state.remainingSec, state.running, state.totalSec])

  const progress = useMemo(() => {
    if (state.totalSec <= 0) {
      return 0
    }
    return Math.round(((state.totalSec - state.remainingSec) / state.totalSec) * 100)
  }, [state.remainingSec, state.totalSec])

  function applyPreset(focusMin: number, breakMin: number) {
    setState({
      mode: 'focus',
      totalSec: focusMin * 60,
      remainingSec: focusMin * 60,
      running: false,
      startedAt: null,
    })
    sessionStorage.setItem(
      `${STORAGE_KEY}-break`,
      String(breakMin * 60),
    )
  }

  function toggleRun() {
    setState((prev) => {
      if (prev.running) {
        return {
          ...prev,
          running: false,
          startedAt: null,
          remainingSec: prev.remainingSec,
          totalSec: prev.remainingSec,
        }
      }
      return {
        ...prev,
        running: true,
        startedAt: Date.now() - (prev.totalSec - prev.remainingSec) * 1000,
      }
    })
  }

  function startBreak() {
    const raw = sessionStorage.getItem(`${STORAGE_KEY}-break`)
    const breakSec = raw ? Number(raw) : 5 * 60
    setState({
      mode: 'break',
      totalSec: breakSec,
      remainingSec: breakSec,
      running: true,
      startedAt: Date.now(),
    })
  }

  return (
    <section
      className={immersive ? 'tasks-focus is-immersive' : 'tasks-focus'}
      aria-labelledby="tasks-focus-title"
    >
      <header className="tasks-panel-head">
        <h2 id="tasks-focus-title" className="learn-section-title">
          Фокус
        </h2>
        <p className="learn-section-note">
          {taskTitle.trim()
            ? `Сессия для «${taskTitle.trim()}». Минуты запишутся в карточку.`
            : 'Таймер Pomodoro и журнал завершённых сессий.'}
        </p>
      </header>

      <div className="tasks-focus-presets">
        {PRESETS.map((preset) => (
          <button
            key={preset.label}
            type="button"
            className="learn-admin-btn"
            onClick={() => applyPreset(preset.focus, preset.brk)}
          >
            {preset.label}
          </button>
        ))}
      </div>

      <div className="tasks-focus-clock" role="timer" aria-live="polite">
        <p className="tasks-focus-mode">
          {state.mode === 'focus' ? 'Работа' : 'Перерыв'}
        </p>
        <p className="tasks-focus-time">{formatClock(state.remainingSec)}</p>
        <div className="tasks-progress" aria-hidden>
          <span className="tasks-progress-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>

      <div className="tasks-focus-actions">
        <button
          type="button"
          className="learn-admin-btn learn-admin-btn-primary"
          onClick={toggleRun}
        >
          {state.running ? 'Пауза' : 'Старт'}
        </button>
        <button
          type="button"
          className="learn-admin-btn"
          onClick={() =>
            setState((prev) => ({
              ...prev,
              running: false,
              startedAt: null,
              remainingSec: prev.totalSec,
            }))
          }
        >
          Сброс
        </button>
        <button type="button" className="learn-admin-btn" onClick={startBreak}>
          Перерыв
        </button>
        <button
          type="button"
          className="learn-admin-btn"
          onClick={() => setImmersive((value) => !value)}
        >
          {immersive ? 'Обычный вид' : 'Концентрация'}
        </button>
      </div>

      {error ? <p className="tasks-personal-error">{error}</p> : null}

      <div className="tasks-focus-logs">
        <h3>Недавние сессии</h3>
        {logs.length === 0 ? (
          <p className="learn-section-note">Пока пусто — завершите первый таймер.</p>
        ) : (
          <ul>
            {logs.slice(0, 8).map((log) => (
              <li key={log.id}>
                <span>{log.minutes} мин</span>
                <span>{log.label || 'Фокус'}</span>
                <span>
                  {new Date(log.createdAt).toLocaleString('ru-RU', {
                    day: 'numeric',
                    month: 'short',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
