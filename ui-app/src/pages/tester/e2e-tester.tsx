import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { PageHeader, PageContainer } from '@/components/ui'

const TESTER_PANEL_URL = 'http://127.0.0.1:8300'

const TOC = [
  { id: 'requirements', label: 'Требования' },
  { id: 'start', label: 'Запуск' },
  { id: 'suites', label: 'Наборы сценариев' },
  { id: 'usage', label: 'Использование' },
  { id: 'yaml', label: 'YAML actions' },
  { id: 'playwright', label: 'Playwright .py' },
  { id: 'notes', label: 'Важно' },
] as const

const SCENARIO_SUITES: {
  file: string
  ids: string
  creds: string
  covers: string
}[] = [
  {
    file: 'suite_smoke.yaml',
    ids: 'S00, S01, S02, S10–S12, S20, S27',
    creds: 'admin (password или JWT)',
    covers: 'login, nav, Checks health, Brands/Channels/Posts, Telegram, Custom URL',
  },
  {
    file: 'suite_platforms.yaml',
    ids: 'S20–S27',
    creds: 'любой пользователь',
    covers: 'TG, VK, IG, Threads, WP, Dzen, Twitter, Custom URL',
  },
  {
    file: 'suite_checks.yaml',
    ids: 'S02, S30–S37',
    creds: 'admin',
    covers: 'Administration, Polls, Collector/Processor/Scheduler/AI, posting diag, docs',
  },
]

const YAML_ACTIONS: { action: string; fields: string }[] = [
  { action: 'goto', fields: 'path или url' },
  {
    action: 'fill',
    fields:
      'selector, value или value_from (credentials.username / password / access_token / refresh_token)',
  },
  { action: 'click', fields: 'selector' },
  { action: 'wait', fields: 'ms' },
  { action: 'wait_url', fields: 'contains, опционально timeout_ms' },
  { action: 'assert_text', fields: 'selector, contains' },
  { action: 'assert_url', fields: 'contains' },
  { action: 'screenshot', fields: 'name' },
  { action: 'login_form', fields: 'password-креды и форма /sign-in' },
]

function CodeBlock({ children }: { children: string }) {
  return (
    <pre className="mt-3 overflow-x-auto rounded-xl border border-[var(--border-color)] bg-[var(--bg-tertiary)] p-4 text-xs leading-relaxed text-[var(--text-primary)] font-mono whitespace-pre">
      {children}
    </pre>
  )
}

function InlineCode({ children }: { children: string }) {
  return (
    <code className="rounded-md border border-[var(--border-color)] bg-[var(--bg-tertiary)] px-1.5 py-0.5 text-[0.8rem] font-mono text-[var(--text-primary)]">
      {children}
    </code>
  )
}

export function E2eTesterPage() {
  return (
    <PageContainer>
      <PageHeader
        title="E2E Tester"
        description="On-demand сервис браузерных E2E против уже запущенного основного стека. Своя Postgres — только сценарии, креды и отчёты; Chromium ходит на ui:8100 через edge_net."
      />

      <nav className="mb-6 flex flex-wrap gap-2 text-sm">
        {TOC.map((item) => (
          <a
            key={item.id}
            href={`#${item.id}`}
            className="rounded-lg border border-[var(--border-color)] px-3 py-1.5 text-[var(--text-secondary)] hover:border-primary-500/50 hover:text-[var(--text-primary)] transition-colors"
          >
            {item.label}
          </a>
        ))}
      </nav>

      <section id="requirements" className="scroll-mt-6 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Требования</CardTitle>
            <CardDescription>Перед запуском тестера</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-[var(--text-secondary)] space-y-3">
            <ol className="list-decimal list-inside space-y-1">
              <li>
                Сеть <InlineCode>edge_net</InlineCode> существует.
              </li>
              <li>
                Основной <InlineCode>docker compose</InlineCode> поднят (
                <InlineCode>ui</InlineCode> и <InlineCode>gateway</InlineCode> на{' '}
                <InlineCode>edge_net</InlineCode>).
              </li>
            </ol>
            <CodeBlock>{`# один раз
docker network create edge_net

# основной стек (из корня репозитория)
docker compose up -d`}</CodeBlock>
          </CardContent>
        </Card>
      </section>

      <section id="start" className="scroll-mt-6 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Запуск тестера</CardTitle>
            <CardDescription>
              Панель:{' '}
              <a
                href={TESTER_PANEL_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-400 hover:text-primary-300 underline-offset-2 hover:underline"
              >
                {TESTER_PANEL_URL}
              </a>
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-[var(--text-secondary)] space-y-3">
            <CodeBlock>{`cp tester/.env.example tester/.env
# Сгенерируйте Fernet-ключ:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Впишите в TESTER_SECRET_KEY=

docker compose -f tester/docker-compose.yml --env-file tester/.env up -d --build
# или:
docker compose -f docker-compose.tester.yml --env-file tester/.env up -d --build`}</CodeBlock>
            <p>Остановка:</p>
            <CodeBlock>{`docker compose -f tester/docker-compose.yml --env-file tester/.env down`}</CodeBlock>
            <p>
              Тома <InlineCode>tester_pg_data</InlineCode> /{' '}
              <InlineCode>tester_artifacts</InlineCode> сохраняются до{' '}
              <InlineCode>down -v</InlineCode>.
            </p>
          </CardContent>
        </Card>
      </section>

      <section id="suites" className="scroll-mt-6 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Наборы сценариев</CardTitle>
            <CardDescription>
              Готовые YAML в <InlineCode>tester/examples/</InlineCode> — загрузите в панель тестера
              (:8300) с нужными credentials
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
              <table className="w-full text-sm text-left">
                <thead className="bg-[var(--bg-tertiary)] text-[var(--text-secondary)]">
                  <tr>
                    <th className="px-4 py-2.5 font-medium">Файл</th>
                    <th className="px-4 py-2.5 font-medium">ID</th>
                    <th className="px-4 py-2.5 font-medium">Креды</th>
                    <th className="px-4 py-2.5 font-medium">Покрытие</th>
                  </tr>
                </thead>
                <tbody>
                  {SCENARIO_SUITES.map((row) => (
                    <tr
                      key={row.file}
                      className="border-t border-[var(--border-color)] text-[var(--text-secondary)]"
                    >
                      <td className="px-4 py-2.5 font-mono text-[var(--text-primary)]">
                        {row.file}
                      </td>
                      <td className="px-4 py-2.5">{row.ids}</td>
                      <td className="px-4 py-2.5">{row.creds}</td>
                      <td className="px-4 py-2.5">{row.covers}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-sm text-[var(--text-secondary)]">
              Read-only smoke: без реальной публикации. Наборы <InlineCode>suite_smoke</InlineCode> и{' '}
              <InlineCode>suite_checks</InlineCode> требуют роль admin для страниц Checks /
              Administration.
            </p>
          </CardContent>
        </Card>
      </section>

      <section id="usage" className="scroll-mt-6 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Использование</CardTitle>
            <CardDescription>Credentials → Scenarios → Runs</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-[var(--text-secondary)] space-y-3">
            <ol className="list-decimal list-inside space-y-2">
              <li>
                <strong className="text-[var(--text-primary)]">Credentials</strong> — логин/пароль
                пользователя продукта или JWT (<InlineCode>access_token</InlineCode> /{' '}
                <InlineCode>refresh_token</InlineCode>). Секреты шифруются Fernet и не отдаются в
                API-списках.
              </li>
              <li>
                <strong className="text-[var(--text-primary)]">Scenarios</strong> — YAML/JSON шаги
                или <InlineCode>.py</InlineCode> Playwright-скрипт. Примеры:{' '}
                <InlineCode>tester/examples/</InlineCode>.
              </li>
              <li>
                <strong className="text-[var(--text-primary)]">Runs</strong> — Start → live-логи →
                скриншоты при ошибках.
              </li>
            </ol>
            <p>
              JWT: перед сценарием токены кладутся в <InlineCode>localStorage</InlineCode> (
              <InlineCode>access_token</InlineCode> / <InlineCode>refresh_token</InlineCode>), как в
              ui-app.
            </p>
            <p>
              Password: шаг <InlineCode>login_form</InlineCode> или ручные{' '}
              <InlineCode>fill</InlineCode> / <InlineCode>click</InlineCode>.
            </p>
          </CardContent>
        </Card>
      </section>

      <section id="yaml" className="scroll-mt-6 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>YAML actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
              <table className="w-full text-sm text-left">
                <thead className="bg-[var(--bg-tertiary)] text-[var(--text-secondary)]">
                  <tr>
                    <th className="px-4 py-2.5 font-medium">action</th>
                    <th className="px-4 py-2.5 font-medium">поля</th>
                  </tr>
                </thead>
                <tbody>
                  {YAML_ACTIONS.map((row) => (
                    <tr
                      key={row.action}
                      className="border-t border-[var(--border-color)] text-[var(--text-secondary)]"
                    >
                      <td className="px-4 py-2.5 font-mono text-[var(--text-primary)]">
                        {row.action}
                      </td>
                      <td className="px-4 py-2.5">{row.fields}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </section>

      <section id="playwright" className="scroll-mt-6 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Playwright .py</CardTitle>
            <CardDescription>
              Запрещены импорты os, subprocess, socket, httpx и т.п., а также eval / exec / open.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-[var(--text-secondary)]">
            <p className="mb-2">Скрипт должен объявить:</p>
            <CodeBlock>{`async def run(page, base_url, credentials, log):
    ...`}</CodeBlock>
          </CardContent>
        </Card>
      </section>

      <section id="notes" className="scroll-mt-6 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Важно</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-[var(--text-secondary)]">
            <ul className="list-disc list-inside space-y-2">
              <li>
                Тесты мутируют данные staging/prod-like окружения. Используйте отдельные учётки и
                cleanup-шаги.
              </li>
              <li>
                Порт панели только на <InlineCode>127.0.0.1:8300</InlineCode>.
              </li>
              <li>
                Health: <InlineCode>GET /api/health</InlineCode> на панели тестера.
              </li>
            </ul>
          </CardContent>
        </Card>
      </section>
    </PageContainer>
  )
}
