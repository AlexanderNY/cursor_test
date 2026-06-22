import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { PageHeader, PageContainer } from '@/components/ui'

const APP_VERSION = '0.1.0'

export function AboutPage() {
  return (
    <PageContainer>
      <PageHeader title="About" description="Information about Control Panel" />

      <Card className="animate-slide-up">
        <CardHeader>
          <CardTitle className="text-2xl">Control Panel</CardTitle>
          <CardDescription>Version {APP_VERSION} · Project information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-[var(--text-secondary)]">
            Control Panel — панель управления для публикации контента в социальные сети и мессенджеры.
          </p>
          <p className="text-xs text-[var(--text-muted)]">
            © 2026 Control Panel. All rights reserved.
          </p>
        </CardContent>
      </Card>

      <Card className="animate-slide-up animate-stagger-1">
        <CardHeader>
          <CardTitle>Features</CardTitle>
          <CardDescription>Main capabilities</CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="list-disc list-inside space-y-2 text-sm text-[var(--text-secondary)]">
            <li>Publish posts to Telegram, Threads, Twitter, VKontakte, WordPress</li>
            <li>Custom URL scraping and content collection</li>
            <li>Unified post creation and scheduling</li>
            <li>User groups and role-based access (manager, author)</li>
            <li>Administration: users, groups, statistics, services status</li>
          </ul>
        </CardContent>
      </Card>

      <Card className="animate-slide-up animate-stagger-2">
        <CardHeader>
          <CardTitle>Links</CardTitle>
          <CardDescription>Documentation and support</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-sm text-[var(--text-secondary)]">
            Documentation and support links can be added here when available.
          </p>
        </CardContent>
      </Card>
    </PageContainer>
  )
}
