import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageContainer, PageHeader, DataTable, type DataTableColumn } from '@/components/ui'
import { Alert } from '@/components/ui/alert'
import { Card, CardContent } from '@/components/ui/card'
import { notificationsService } from '@/services/notifications-service'
import type { Notification } from '@/types/core'

const NOTIFICATIONS_FETCH_LIMIT = 500

function NotificationTypeBadge({ type }: { type?: string | null }) {
  const label = type || 'general'
  const isAuthType = label.startsWith('tg_auth')

  return (
    <span
      className={`inline-block px-2 py-0.5 rounded-md text-xs font-medium ${
        isAuthType
          ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
          : 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)] border border-[var(--border-color)]'
      }`}
    >
      {label}
    </span>
  )
}

function NotificationMessageCell({
  message,
  onInternalLinkClick,
}: {
  message: string
  onInternalLinkClick: (e: React.MouseEvent<HTMLDivElement>) => void
}) {
  return (
    <div
      onClick={onInternalLinkClick}
      className="notification-content text-[var(--text-primary)] text-sm"
      dangerouslySetInnerHTML={{ __html: message }}
    />
  )
}

export function NewsPage() {
  const navigate = useNavigate()
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const handleInternalLinkClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const target = e.target as HTMLElement
      const anchor = target.closest('a')
      if (!anchor) return
      const href = anchor.getAttribute('href')
      if (href && href.startsWith('/')) {
        e.preventDefault()
        navigate(href)
      }
    },
    [navigate]
  )

  useEffect(() => {
    async function loadNotifications() {
      setError('')
      setIsLoading(true)
      try {
        const response = await notificationsService.getNotifications({ limit: NOTIFICATIONS_FETCH_LIMIT })
        setNotifications(response.notifications || [])
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load notifications')
        setNotifications([])
      } finally {
        setIsLoading(false)
      }
    }

    loadNotifications()
  }, [])

  const columns: DataTableColumn<Notification>[] = [
    {
      key: 'created_at',
      header: 'Date',
      render: (value) => (
        <span className="text-sm whitespace-nowrap">
          {value ? new Date(String(value)).toLocaleString() : '—'}
        </span>
      ),
    },
    {
      key: 'type',
      header: 'Type',
      render: (_, row) => <NotificationTypeBadge type={row.type} />,
    },
    {
      key: 'message',
      header: 'Message',
      render: (_, row) => (
        <NotificationMessageCell message={row.message} onInternalLinkClick={handleInternalLinkClick} />
      ),
    },
  ]

  return (
    <PageContainer maxWidth="wide">
      <PageHeader
        title="News"
        description="System notifications and announcements for your account"
      />

      {error && (
        <Alert variant="error" className="animate-slide-down">
          {error}
        </Alert>
      )}

      <Card className="animate-slide-up">
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={notifications}
            keyExtractor={(row) => row.id}
            isLoading={isLoading}
            emptyMessage="No notifications yet"
          />
        </CardContent>
      </Card>
    </PageContainer>
  )
}
