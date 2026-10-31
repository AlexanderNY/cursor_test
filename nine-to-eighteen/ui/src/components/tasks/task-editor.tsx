import { FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  displayNotes,
  learnEpisodePath,
  learnTargetFromNotes,
  notesWithLearnTarget,
} from '@/components/tasks/learn-link'
import type {
  SiteTaskBoard,
  SiteTaskChecklistItem,
  SiteTaskPriority,
  SiteTaskRepeat,
  SiteUserTask,
} from '@/data/site/site-api'
import { newChecklistId, TAG_PRESETS } from '@/components/tasks/task-utils'

type TaskEditorProps = {
  task: SiteUserTask
  busy?: boolean
  onClose: () => void
  onSave: (
    taskId: number,
    patch: {
      title?: string
      notes?: string
      tag?: string
      due_at?: string | null
      due_time?: string | null
      remind_at?: string | null
      priority?: SiteTaskPriority
      board?: SiteTaskBoard
      checklist?: SiteTaskChecklistItem[]
      repeat_rule?: SiteTaskRepeat
      completed?: boolean
    },
  ) => Promise<void>
  onDelete: (task: SiteUserTask) => Promise<void>
  onAddSubtask: (parentId: number, title: string) => Promise<void>
  onFocus?: (task: SiteUserTask) => void
}

export function TaskEditor({
  task,
  busy,
  onClose,
  onSave,
  onDelete,
  onAddSubtask,
  onFocus,
}: TaskEditorProps) {
  const learnTarget = learnTargetFromNotes(task.notes)
  const [title, setTitle] = useState(task.title)
  const [notes, setNotes] = useState(displayNotes(task.notes))
  const [tag, setTag] = useState(task.tag)
  const [dueAt, setDueAt] = useState(task.dueAt || '')
  const [dueTime, setDueTime] = useState(task.dueTime || '')
  const [remindAt, setRemindAt] = useState(
    task.remindAt ? task.remindAt.slice(0, 16) : '',
  )
  const [priority, setPriority] = useState<SiteTaskPriority>(task.priority)
  const [board, setBoard] = useState<SiteTaskBoard>(task.board)
  const [repeatRule, setRepeatRule] = useState<SiteTaskRepeat>(task.repeatRule)
  const [checklist, setChecklist] = useState<SiteTaskChecklistItem[]>(
    task.checklist || [],
  )
  const [newCheck, setNewCheck] = useState('')
  const [subTitle, setSubTitle] = useState('')

  useEffect(() => {
    setTitle(task.title)
    setNotes(displayNotes(task.notes))
    setTag(task.tag)
    setDueAt(task.dueAt || '')
    setDueTime(task.dueTime || '')
    setRemindAt(task.remindAt ? task.remindAt.slice(0, 16) : '')
    setPriority(task.priority)
    setBoard(task.board)
    setRepeatRule(task.repeatRule)
    setChecklist(task.checklist || [])
  }, [task])

  async function handleSave(event: FormEvent) {
    event.preventDefault()
    const nextTitle = title.trim()
    if (!nextTitle || busy) {
      return
    }
    const hasSteps = checklist.some((item) => item.id.startsWith('step-'))
    const stepsDone = checklist.length > 0 && checklist.every((item) => item.done)
    await onSave(task.id, {
      title: nextTitle,
      notes: learnTarget
        ? notesWithLearnTarget(learnTarget.slug, learnTarget.kind, notes)
        : notes.trim(),
      tag: tag.trim(),
      due_at: dueAt.trim() || null,
      due_time: dueTime.trim() || null,
      remind_at: remindAt.trim() ? new Date(remindAt).toISOString() : null,
      priority,
      board,
      checklist,
      repeat_rule: task.parentId ? 'none' : repeatRule,
      ...(hasSteps ? { completed: stepsDone } : {}),
    })
    onClose()
  }

  function addCheckItem() {
    const value = newCheck.trim()
    if (!value) {
      return
    }
    setChecklist((prev) => [
      ...prev,
      { id: newChecklistId(), title: value, done: false },
    ])
    setNewCheck('')
  }

  return (
    <aside className="tasks-editor" aria-labelledby="tasks-editor-title">
      <header className="tasks-editor-head">
        <h2 id="tasks-editor-title">Карточка</h2>
        <div className="tasks-today-actions">
          {onFocus ? (
            <button type="button" className="learn-admin-btn" onClick={() => onFocus(task)}>
              Фокус
            </button>
          ) : null}
          <button type="button" className="learn-admin-btn" onClick={onClose}>
            Закрыть
          </button>
        </div>
      </header>
      {learnTarget ? (
        <p className="tasks-learn-links">
          {learnTarget.kind === 'quiz' ? (
            <Link to={learnEpisodePath(learnTarget.slug, 'quiz')}>Тест</Link>
          ) : (
            <Link to={learnEpisodePath(learnTarget.slug)}>Статья</Link>
          )}
          <Link to={learnEpisodePath(learnTarget.slug, 'lab')}>Лаба</Link>
          {learnTarget.kind === 'quiz' ? (
            <Link to={learnEpisodePath(learnTarget.slug)}>Статья</Link>
          ) : (
            <Link to={learnEpisodePath(learnTarget.slug, 'quiz')}>Тест</Link>
          )}
        </p>
      ) : null}
      <form className="tasks-editor-form" onSubmit={(event) => void handleSave(event)}>
        <label className="learn-admin-field">
          <span>Название</span>
          <input
            type="text"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            maxLength={512}
            required
          />
        </label>
        <label className="learn-admin-field">
          <span>Заметки</span>
          <textarea
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            rows={4}
            maxLength={8000}
          />
        </label>
        <div className="tasks-editor-grid">
          <label className="learn-admin-field">
            <span>Метка</span>
            <input
              type="text"
              value={tag}
              onChange={(event) => setTag(event.target.value)}
              list="tasks-editor-tags"
              maxLength={64}
              placeholder="работа, дом…"
            />
            <datalist id="tasks-editor-tags">
              {TAG_PRESETS.map((preset) => (
                <option key={preset} value={preset} />
              ))}
            </datalist>
          </label>
          <label className="learn-admin-field">
            <span>Приоритет</span>
            <select
              value={priority}
              onChange={(event) =>
                setPriority(event.target.value as SiteTaskPriority)
              }
            >
              <option value="low">Низкий</option>
              <option value="normal">Обычный</option>
              <option value="high">Высокий</option>
            </select>
          </label>
          <label className="learn-admin-field">
            <span>Колонка</span>
            <select
              value={board}
              onChange={(event) => setBoard(event.target.value as SiteTaskBoard)}
            >
              <option value="inbox">Разобрать</option>
              <option value="backlog">Бэклог</option>
              <option value="week">На эту неделю</option>
              <option value="today">Сегодня</option>
              <option value="done">Сделано</option>
            </select>
          </label>
          {!task.parentId ? (
            <label className="learn-admin-field">
              <span>Повтор</span>
              <select
                value={repeatRule}
                onChange={(event) =>
                  setRepeatRule(event.target.value as SiteTaskRepeat)
                }
              >
                <option value="none">Нет</option>
                <option value="daily">Ежедневно</option>
                <option value="weekly">Еженедельно</option>
                <option value="monthly">Ежемесячно</option>
              </select>
            </label>
          ) : null}
          <label className="learn-admin-field">
            <span>Срок</span>
            <input
              type="date"
              value={dueAt}
              onChange={(event) => setDueAt(event.target.value)}
            />
          </label>
          <label className="learn-admin-field">
            <span>Время</span>
            <input
              type="time"
              value={dueTime}
              onChange={(event) => setDueTime(event.target.value)}
            />
          </label>
          <label className="learn-admin-field">
            <span>Напоминание</span>
            <input
              type="datetime-local"
              value={remindAt}
              onChange={(event) => setRemindAt(event.target.value)}
            />
          </label>
        </div>

        <fieldset className="tasks-editor-checklist">
          <legend>Чек-лист</legend>
          <ul>
            {checklist.map((item) => (
              <li key={item.id}>
                <label>
                  <input
                    type="checkbox"
                    checked={item.done}
                    onChange={() =>
                      setChecklist((prev) =>
                        prev.map((row) =>
                          row.id === item.id ? { ...row, done: !row.done } : row,
                        ),
                      )
                    }
                  />
                  <span className={item.done ? 'is-done' : undefined}>{item.title}</span>
                </label>
                <button
                  type="button"
                  className="learn-admin-link"
                  onClick={() =>
                    setChecklist((prev) => prev.filter((row) => row.id !== item.id))
                  }
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
          <div className="tasks-editor-inline">
            <input
              type="text"
              value={newCheck}
              onChange={(event) => setNewCheck(event.target.value)}
              placeholder="Пункт чек-листа"
              maxLength={256}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  event.preventDefault()
                  addCheckItem()
                }
              }}
            />
            <button type="button" className="learn-admin-btn" onClick={addCheckItem}>
              +
            </button>
          </div>
        </fieldset>

        {!task.parentId ? (
          <fieldset className="tasks-editor-checklist">
            <legend>Подзадачи</legend>
            <ul>
              {(task.subtasks || []).map((sub) => (
                <li key={sub.id}>
                  <span className={sub.completed ? 'is-done' : undefined}>
                    {sub.completed ? '✓ ' : ''}
                    {sub.title}
                  </span>
                </li>
              ))}
            </ul>
            <div className="tasks-editor-inline">
              <input
                type="text"
                value={subTitle}
                onChange={(event) => setSubTitle(event.target.value)}
                placeholder="Новая подзадача"
                maxLength={512}
              />
              <button
                type="button"
                className="learn-admin-btn"
                disabled={busy || !subTitle.trim()}
                onClick={() => {
                  const value = subTitle.trim()
                  if (!value) {
                    return
                  }
                  void onAddSubtask(task.id, value).then(() => setSubTitle(''))
                }}
              >
                +
              </button>
            </div>
          </fieldset>
        ) : null}

        <div className="tasks-editor-actions">
          <button
            type="submit"
            className="learn-admin-btn learn-admin-btn-primary"
            disabled={busy || !title.trim()}
          >
            Сохранить
          </button>
          <button
            type="button"
            className="learn-admin-btn"
            disabled={busy}
            onClick={() => void onSave(task.id, { completed: !task.completed })}
          >
            {task.completed ? 'Открыть снова' : 'Готово'}
          </button>
          <button
            type="button"
            className="learn-admin-link"
            disabled={busy}
            onClick={() => void onDelete(task)}
          >
            Удалить
          </button>
        </div>
      </form>
    </aside>
  )
}
