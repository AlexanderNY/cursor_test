import type { SiteUserTask } from '@/data/site/site-api'
import { displayNotes, learnTargetFromNotes } from '@/components/tasks/learn-link'
import {
  checklistProgress,
  formatDue,
  isOverdue,
  priorityLabel,
  tagAccentClass,
} from '@/components/tasks/task-utils'

type TaskCardProps = {
  task: SiteUserTask
  compact?: boolean
  draggable?: boolean
  onToggle: (task: SiteUserTask) => void
  onOpen: (task: SiteUserTask) => void
  onDragStart?: (task: SiteUserTask) => void
}

export function TaskCard({
  task,
  compact,
  draggable,
  onToggle,
  onOpen,
  onDragStart,
}: TaskCardProps) {
  const overdue = isOverdue(task)
  const progress = checklistProgress(task)
  const dueLabel = formatDue(task.dueAt, task.dueTime)
  const subCount = task.subtasks?.length || 0
  const notes = displayNotes(task.notes)
  const learnTarget = learnTargetFromNotes(task.notes)

  return (
    <article
      className={[
        'tasks-card',
        tagAccentClass(task.tag),
        task.completed ? 'is-done' : '',
        overdue ? 'is-overdue' : '',
        compact ? 'is-compact' : '',
      ]
        .filter(Boolean)
        .join(' ')}
      draggable={Boolean(draggable)}
      onDragStart={() => onDragStart?.(task)}
    >
      <div className="tasks-card-main">
        <label className="tasks-card-check">
          <input
            type="checkbox"
            checked={task.completed}
            onChange={() => onToggle(task)}
            aria-label={task.completed ? 'Открыть снова' : 'Отметить готовым'}
          />
        </label>
        <button type="button" className="tasks-card-body" onClick={() => onOpen(task)}>
          <span className="tasks-card-title">{task.title}</span>
          {!compact && notes ? (
            <span className="tasks-card-notes">{notes}</span>
          ) : null}
          <span className="tasks-card-meta">
            {learnTarget ? (
              <span className="tasks-mini-badge">
                {learnTarget.kind === 'quiz' ? 'Тест' : 'Статья'}
              </span>
            ) : null}
            {task.tag.trim() ? (
              <span className="tasks-mini-badge">{task.tag.trim()}</span>
            ) : null}
            {task.priority !== 'normal' ? (
              <span className={`tasks-priority tasks-priority-${task.priority}`}>
                {priorityLabel(task.priority)}
              </span>
            ) : null}
            {dueLabel ? (
              <span className={overdue ? 'tasks-due is-overdue' : 'tasks-due'}>
                {overdue ? 'Просрочено · ' : ''}
                {dueLabel}
              </span>
            ) : null}
            {progress.total > 0 ? (
              <span className="tasks-mini-badge">
                ✓ {progress.done}/{progress.total}
              </span>
            ) : null}
            {subCount > 0 ? (
              <span className="tasks-mini-badge">Подзадачи {subCount}</span>
            ) : null}
            {task.repeatRule !== 'none' ? (
              <span className="tasks-mini-badge">↻ {task.repeatRule}</span>
            ) : null}
          </span>
        </button>
      </div>
    </article>
  )
}
