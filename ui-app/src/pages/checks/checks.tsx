import { NavLink, Outlet, Navigate } from 'react-router-dom'
import { PageContainer, PageHeader } from '@/components/ui'
import { ChecksInfraProvider } from './checks-infra-context'

const subsections = [
  { path: 'services-status', label: 'Состояние сервисов' },
  { path: 'processor', label: 'Processor' },
  { path: 'collector', label: 'Collector' },
  { path: 'scheduler', label: 'Scheduler' },
  { path: 'posting-diagnostics', label: 'Диагностика постинга' },
  { path: 'ai', label: 'проверка AI' },
] as const

export function ChecksPage() {
  return (
    <PageContainer maxWidth="wide">
      <PageHeader
        title="Диагностика"
        description="Мониторинг сервисов, принудительный запуск процессов и тестовые проверки. Доступно только администратору."
      />

      <div className="flex border-b border-[var(--border-color)] mb-6 overflow-x-auto">
        {subsections.map((item) => (
          <NavLink
            key={item.path}
            to={`/checks/${item.path}`}
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

      <ChecksInfraProvider>
        <Outlet />
      </ChecksInfraProvider>
    </PageContainer>
  )
}

export function ChecksIndexRedirect() {
  return <Navigate to="services-status" replace />
}
