import { NavLink, Outlet, Navigate } from 'react-router-dom'
import { PageContainer, PageHeader } from '@/components/ui'
import { PollsProvider, usePollsContext } from './polls-context'

const subsections = [
  { path: 'content', label: 'Контент' },
  { path: 'bots', label: 'Настройки Telegram-ботов' },
  { path: 'diagnostics', label: 'Диагностика бота' },
  { path: 'rating', label: 'Рейтинг и прохождения' },
  { path: 'orders', label: 'Заказы' },
] as const

function PollsLayoutInner() {
  const { bots, selectedBotId, setSelectedBotId } = usePollsContext()
  const selectedBot = bots.find((bot) => bot.id === selectedBotId) ?? null

  return (
    <PageContainer>
      <PageHeader
        title="Polls"
        description="Контент, настройки ботов, диагностика, рейтинг и заказы — на отдельных вкладках. Состав опроса открывается по клику на него."
      />

      {bots.length > 0 && (
        <label className="mt-4 flex flex-wrap items-center gap-2 text-sm">
          <span className="text-[var(--text-secondary)]">Бот</span>
          <select
            className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]"
            value={selectedBotId ?? ''}
            onChange={(event) => setSelectedBotId(Number(event.target.value))}
          >
            {bots.map((bot) => (
              <option key={bot.id} value={bot.id}>
                {bot.name}
                {bot.username ? ` (@${bot.username})` : ''}
              </option>
            ))}
          </select>
          {selectedBot && !selectedBot.is_active && (
            <span className="text-xs text-[var(--text-secondary)]">выключен</span>
          )}
        </label>
      )}

      <div className="mt-6 flex border-b border-[var(--border-color)] mb-6 overflow-x-auto">
        {subsections.map((item) => (
          <NavLink
            key={item.path}
            to={`/polls/${item.path}`}
            className={({ isActive }) =>
              `px-6 py-3 text-sm font-medium transition-all relative whitespace-nowrap shrink-0 ${
                isActive
                  ? 'text-primary-400'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
              }`
            }
          >
            {({ isActive }) => (
              <>
                {item.label}
                {isActive && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500" />
                )}
              </>
            )}
          </NavLink>
        ))}
      </div>

      <Outlet />
    </PageContainer>
  )
}

export function PollsPage() {
  return (
    <PollsProvider>
      <PollsLayoutInner />
    </PollsProvider>
  )
}

export function PollsIndexRedirect() {
  return <Navigate to="content" replace />
}
