import { NavLink, Outlet, Navigate } from 'react-router-dom'
import { PageContainer, PageHeader } from '@/components/ui'
import { BotsSettingsSection } from './bots-settings-section'
import { PollsProvider, usePollsContext } from './polls-context'

const subsections = [
  { path: 'content', label: 'Контент' },
  { path: 'diagnostics', label: 'Диагностика бота' },
  { path: 'rating', label: 'Рейтинг и прохождения' },
  { path: 'orders', label: 'Заказы' },
] as const

function PollsLayoutInner() {
  const {
    selectedBotId,
    setSelectedBotId,
    handleBotsLoaded,
    loadModes,
  } = usePollsContext()

  return (
    <PageContainer>
      <PageHeader
        title="Polls"
        description="Управление Telegram-игрой: контент, диагностика бота, рейтинг и заказы."
      />

      <BotsSettingsSection
        selectedBotId={selectedBotId}
        onSelectBot={setSelectedBotId}
        onBotsLoaded={handleBotsLoaded}
        onBotsChanged={() => loadModes(selectedBotId)}
      />

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
