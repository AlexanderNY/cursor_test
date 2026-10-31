import type { SiteUserTask } from '@/data/site/site-api'
import { TaskCard } from '@/components/tasks/task-card'

type TaskListProps = {
  items: SiteUserTask[]
  onToggle: (task: SiteUserTask) => void
  onOpen: (task: SiteUserTask) => void
  onFocus?: (task: SiteUserTask) => void
}

export function TaskList({ items, onToggle, onOpen, onFocus }: TaskListProps) {
  if (items.length === 0) {
    return (
      <p className="learn-section-note">
        Пока нет задач — добавьте первую в строке выше.
      </p>
    )
  }

  return (
    <div className="tasks-list">
      {items.map((task) => (
        <div key={task.id} className="tasks-list-group">
          <TaskCard task={task} onToggle={onToggle} onOpen={onOpen} onFocus={onFocus} />
          {task.subtasks?.length ? (
            <div className="tasks-list-sub">
              {task.subtasks.map((sub) => (
                <TaskCard
                  key={sub.id}
                  task={sub}
                  compact
                  onToggle={onToggle}
                  onOpen={onOpen}
                  onFocus={onFocus}
                />
              ))}
            </div>
          ) : null}
        </div>
      ))}
    </div>
  )
}
