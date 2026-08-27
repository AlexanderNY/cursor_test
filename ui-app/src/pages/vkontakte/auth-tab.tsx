import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import type { VKAuthStatus, VKSubscriptionItem } from '@/types/vkontakte'

export interface AuthTabProps {
  authStatus: VKAuthStatus | null
  vkAppId: string
  onVkAppIdChange: (v: string) => void
  vkAppSecret: string
  onVkAppSecretChange: (v: string) => void
  vkFrontendUrl: string
  onVkFrontendUrlChange: (v: string) => void
  vkPublicGatewayUrl: string
  onVkPublicGatewayUrlChange: (v: string) => void
  vkOAuthRedirectUri: string
  accessToken: string
  onAccessTokenChange: (v: string) => void
  isSavingProfile: boolean
  onSaveOAuthSettings: () => void
  onSaveTokenSettings: () => void
  onRefreshAuthStatus: () => void
  onConnectVk: () => void
  loadingSubscriptions: boolean
  onLoadSubscriptions: () => void
  subscriptions: VKSubscriptionItem[]
  subscriptionsSource: string | null
  subscriptionsHint: string | null
  vkSeleniumOpen: boolean
  onToggleSelenium: () => void
  vkSeleniumLogin: string
  onVkSeleniumLoginChange: (v: string) => void
  vkSeleniumPassword: string
  onVkSeleniumPasswordChange: (v: string) => void
  loadingSeleniumVerify: boolean
  onVerifySelenium: () => void
}

export function AuthTab({
  authStatus,
  vkAppId,
  onVkAppIdChange,
  vkAppSecret,
  onVkAppSecretChange,
  vkFrontendUrl,
  onVkFrontendUrlChange,
  vkPublicGatewayUrl,
  onVkPublicGatewayUrlChange,
  vkOAuthRedirectUri,
  accessToken,
  onAccessTokenChange,
  isSavingProfile,
  onSaveOAuthSettings,
  onSaveTokenSettings,
  onRefreshAuthStatus,
  onConnectVk,
  loadingSubscriptions,
  onLoadSubscriptions,
  subscriptions,
  subscriptionsSource,
  subscriptionsHint,
  vkSeleniumOpen,
  onToggleSelenium,
  vkSeleniumLogin,
  onVkSeleniumLoginChange,
  vkSeleniumPassword,
  onVkSeleniumPasswordChange,
  loadingSeleniumVerify,
  onVerifySelenium,
}: AuthTabProps) {
  return (
    <Card className="animate-slide-up border-amber-500/30">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-amber-400">VK авторизация</CardTitle>
        <CardDescription className="space-y-2">
          <span className="block">
            {authStatus?.message ??
              'Пользовательский OAuth нужен для загрузки фото на стену сообщества (photos.getWallUploadServer). Токен сообщества (ниже) — для публикации от имени группы и сбора стены.'}
          </span>
          <span className="block text-xs text-[var(--text-muted)]">
            Запрашиваемые scope в Core: <code className="text-[var(--text-secondary)]">wall</code>,{' '}
            <code className="text-[var(--text-secondary)]">photos</code>,{' '}
            <code className="text-[var(--text-secondary)]">groups</code>,{' '}
            <code className="text-[var(--text-secondary)]">offline</code> (классический OAuth VK, не VK ID PKCE).
          </span>
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-3 p-4 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)]">
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">Приложение VK (OAuth)</h3>
          <p className="text-xs text-[var(--text-muted)]">
            Параметры из <code className="text-[var(--text-secondary)]">.env</code> перенесены сюда. Укажите данные
            приложения с{' '}
            <a href="https://dev.vk.com" target="_blank" rel="noopener noreferrer" className="text-primary-400 hover:underline">
              dev.vk.com
            </a>
            . Redirect URI в кабинете VK должен совпадать с вычисленным ниже.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <Input
              label="VK App ID (VK_APP_ID)"
              value={vkAppId}
              onChange={(e) => onVkAppIdChange(e.target.value)}
              placeholder="12345678"
            />
            <Input
              label="VK App Secret (VK_APP_SECRET)"
              type="password"
              value={vkAppSecret === '***' ? '' : vkAppSecret}
              onChange={(e) => onVkAppSecretChange(e.target.value)}
              placeholder={vkAppSecret === '***' ? 'Секрет сохранён (скрыт)' : 'Защищённый ключ приложения'}
            />
            <Input
              label="URL интерфейса (FRONTEND_URL)"
              value={vkFrontendUrl}
              onChange={(e) => onVkFrontendUrlChange(e.target.value)}
              placeholder="http://localhost:8100"
            />
            <Input
              label="Публичный URL gateway (VK_PUBLIC_GATEWAY_URL)"
              value={vkPublicGatewayUrl}
              onChange={(e) => onVkPublicGatewayUrlChange(e.target.value)}
              placeholder="http://localhost:8000"
            />
          </div>
          <p className="text-xs text-[var(--text-muted)]">
            Redirect URI для VK: <code className="text-[var(--text-secondary)] break-all">{vkOAuthRedirectUri}</code>
          </p>
          <Button type="button" variant="secondary" size="sm" onClick={onSaveOAuthSettings} isLoading={isSavingProfile}>
            Сохранить настройки OAuth
          </Button>
        </div>

        <div className="flex items-center gap-3 p-3 rounded-lg bg-[var(--bg-tertiary)]">
          <div
            className={`w-3 h-3 rounded-full ${
              authStatus?.connected ? 'bg-green-400' : 'bg-amber-400 animate-pulse'
            }`}
          />
          <span className="text-sm text-[var(--text-secondary)]">
            {authStatus?.connected ? 'Подключено' : 'Не подключено'}
            {authStatus?.vk_user_id != null && authStatus.connected && (
              <span className="ml-2 text-[var(--text-muted)]">(VK id: {authStatus.vk_user_id})</span>
            )}
          </span>
          <Button variant="ghost" size="sm" onClick={onRefreshAuthStatus} className="ml-auto">
            Обновить
          </Button>
        </div>
        {!authStatus?.connected && (
          <div className="p-4 rounded-lg border border-amber-500/30 bg-amber-500/5">
            <p className="text-sm text-[var(--text-muted)] mb-4">
              Сначала сохраните блок «Приложение VK» выше, затем нажмите кнопку и войдите в VK. После успешного входа
              токен сохранится в профиле (user_access_token).
            </p>
            <Button onClick={onConnectVk}>Подключить VK</Button>
          </div>
        )}
        {authStatus?.connected && (
          <div className="p-4 rounded-lg border border-green-500/30 bg-green-500/5">
            <p className="text-sm text-green-400">
              Пользовательский токен VK сохранён. Публикация с фото на стену группы доступна.
            </p>
          </div>
        )}

        <div className="space-y-3 pt-2 border-t border-[var(--border-color)]">
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">Токен сообщества (Access token)</h3>
          <p className="text-xs text-[var(--text-muted)]">
            Обычно это <strong className="text-[var(--text-secondary)]">токен сообщества</strong> для публикации от имени
            группы и сбора стены (<code className="text-[var(--text-muted)]">wall</code>, при необходимости{' '}
            <code className="text-[var(--text-muted)]">groups</code>). Для фото на стене группы дополнительно нужен
            пользовательский OAuth (блок выше). Подробнее: docs VK_BOT_POSTING.
          </p>
          <input
            type="password"
            value={accessToken === '***' ? '' : accessToken}
            onChange={(e) => onAccessTokenChange(e.target.value)}
            placeholder={accessToken === '***' ? 'Токен сохранён (скрыт)' : 'Оставьте пустым, чтобы не менять'}
            className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
          />
          {accessToken === '***' && (
            <p className="text-xs text-[var(--text-muted)]">Токен сохранён и скрыт. Введите новый токен, чтобы заменить.</p>
          )}
          <Button type="button" variant="secondary" onClick={onSaveTokenSettings} isLoading={isSavingProfile}>
            Сохранить токен и настройки
          </Button>
        </div>

        <div className="space-y-3 pt-2 border-t border-[var(--border-color)]">
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">Проверка авторизации</h3>
          <p className="text-xs text-[var(--text-muted)]">
            С OAuth: запрашивается список подписок на сообщества (VK API{' '}
            <code className="text-[var(--text-muted)]">users.getSubscriptions</code>). Только токен сообщества: по группам
            из «Group to post» и сбора (<code className="text-[var(--text-muted)]">groups.getById</code>).
          </p>
          <Button type="button" onClick={onLoadSubscriptions} isLoading={loadingSubscriptions}>
            Запросить список подписок
          </Button>
          {subscriptionsSource && (
            <p className="text-xs text-[var(--text-secondary)]">Источник: {subscriptionsSource}</p>
          )}
          {subscriptionsHint && <p className="text-xs text-amber-400/90">{subscriptionsHint}</p>}
          {subscriptions.length > 0 && (
            <ul className="mt-2 space-y-2 max-h-72 overflow-y-auto rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] p-3">
              {subscriptions.map((s, i) => (
                <li
                  key={`${s.id ?? 'x'}-${i}`}
                  className="flex flex-wrap gap-x-3 gap-y-1 text-sm text-[var(--text-primary)] border-b border-[var(--border-color)] border-opacity-50 pb-2 last:border-0 last:pb-0"
                >
                  {s.screen_name && <span className="font-mono text-primary-400">{s.screen_name}</span>}
                  {s.name && <span className="text-[var(--text-secondary)]">{s.name}</span>}
                  {s.id != null && <span className="text-[var(--text-muted)] text-xs">id: {s.id}</span>}
                </li>
              ))}
            </ul>
          )}

          <div className="pt-3 border-t border-[var(--border-color)] border-dashed">
            <button
              type="button"
              className="text-sm text-amber-400/90 hover:text-amber-300 underline-offset-2 hover:underline"
              onClick={onToggleSelenium}
            >
              {vkSeleniumOpen ? 'Скрыть' : 'Резервный вход'} (Selenium, логин/пароль)
            </button>
            {vkSeleniumOpen && (
              <div className="mt-3 space-y-3 rounded-lg border border-amber-500/25 bg-[var(--bg-tertiary)]/50 p-4">
                <p className="text-xs text-[var(--text-muted)]">
                  Если OAuth или API недоступны: вход через headless-браузер (vk-bot). Пароль не сохраняется в браузере и
                  передаётся только по HTTPS; на сервере не хранится после ответа. Возможны капча и 2FA — тогда используйте
                  обычный OAuth. Результат — веб-список сообществ, не API-токен.
                </p>
                <div className="grid gap-3 sm:grid-cols-2">
                  <Input
                    label="Телефон или email VK"
                    type="text"
                    autoComplete="username"
                    value={vkSeleniumLogin}
                    onChange={(e) => onVkSeleniumLoginChange(e.target.value)}
                    placeholder="Логин"
                  />
                  <Input
                    label="Пароль"
                    type="password"
                    autoComplete="current-password"
                    value={vkSeleniumPassword}
                    onChange={(e) => onVkSeleniumPasswordChange(e.target.value)}
                    placeholder="Одноразово для проверки"
                  />
                </div>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={onVerifySelenium}
                  isLoading={loadingSeleniumVerify}
                  disabled={!vkSeleniumLogin.trim() || !vkSeleniumPassword}
                >
                  Проверить через Selenium (до ~4 мин)
                </Button>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
