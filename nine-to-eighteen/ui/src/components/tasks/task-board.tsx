import { useState } from 'react'
import type { SiteTaskBoard, SiteUserTask } from '@/data/site/site-api'
import { TaskCard } from '@/components/tasks/task-card'
import { BOARD_COLUMNS } from '@/components/tasks/task-utils'

type TaskBoardProps = {
  items: SiteUserTask[]
  onToggle: (task: SiteUserTask) => void
  onOpen: (task: SiteUserTask) => void
  onMove: (task: SiteUserTask, board: SiteTaskBoard) => void
  onFocus?: (task: SiteUserTask) => void
}

export function TaskBoard({ items, onToggle, onOpen, onMove, onFocus }: TaskBoardProps) {
  const [draggingId, setDraggingId] = useState<number | null>(null)

  function tasksFor(board: SiteTaskBoard): SiteUserTask[] {
    return items.filter((task) => {
      if (board === 'done') {
        return task.completed || task.board === 'done'
      }
      return !task.completed && task.board === board
    })
  }

  return (
    <div className="tasks-board" role="list">
      {BOARD_COLUMNS.map((column) => {
        const columnTasks = tasksFor(column.id)
        return (
          <section
            key={column.id}
            className="tasks-board-column"
            onDragOver={(event) => event.preventDefault()}
            onDrop={() => {
              const task = items.find((item) => item.id === draggingId)
              setDraggingId(null)
              if (task && task.board !== column.id) {
                onMove(task, column.id)
              }
            }}
          >
            <header className="tasks-board-head">
              <h3>{column.label}</h3>
              <span>{columnTasks.length}</span>
            </header>
            <div className="tasks-board-body">
              {columnTasks.length === 0 ? (
                <p className="tasks-board-empty">Перетащите сюда</p>
              ) : (
                columnTasks.map((task) => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    compact
                    draggable
                    onToggle={onToggle}
                    onOpen={onOpen}
                    onDragStart={(item) => setDraggingId(item.id)}
                    onFocus={onFocus}
                  />
                ))
              )}
            </div>
          </section>
        )
      })}
    </div>
  )
}
