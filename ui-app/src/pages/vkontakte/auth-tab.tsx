import { useEffect, useState } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import type { VKAuthStatus, VKAuthVerifyResult, VKSubscriptionItem } from '@/types/vkontakte'

export type VkVerifyBlock = 'community' | 'callback' | 'app' | 'oauth'

function isMaskedSecret(value: string): boolean {
  return value === '***'
}

/** Пресеты scope для Implicit Flow — VK часто отвечает invalid_scope на wall для части приложений. */
const VK_IMPLICIT_SCOPE_PRESETS: { id: string; label: string; scope: string; hint: string }[] = [
  {
    id: 'core',
    label: 'photos + offline',
    scope: 'photos,offline',
    hint: 'Часто проходит на старых приложениях; хватает для чтения и части API.',
  },
  {
    id: 'groups',
    label: 'groups + photos + offline',
    scope: 'groups,photos,offline',
    hint: 'Для Collect / списка сообществ без scope wall.',
  },
  {
    id: 'wall',
    label: 'wall + photos + offline',
    scope: 'wall,photos,offline',
    hint: 'Нужен для личной стены и wall.post от пользователя. Может дать invalid_scope.',
  },
  {
    id: 'full',
    label: 'wall + photos + groups + offline',
    scope: 'wall,photos,groups,offline',
    hint: 'Максимум для user token (если приложение позволяет).',
  },
  {
    id: 'offline',
    label: 'только offline',
    scope: 'offline',
    hint: 'Минимум — проверить, что приложение вообще выдаёт токен.',
  },
]

function buildVkImplicitAuthUrl(appId: string, scope: string): string {
  const params = new URLSearchParams({
    client_id: appId.trim(),
    display: 'page',
    redirect_uri: 'https://oauth.vk.com/blank.html',
    scope,
    response_type: 'token',
    v: '5.199',
  })
  return `https://oauth.vk.com/authorize?${params.toString()}`
}

function oauthRedirectHostMismatch(redirectUri: string): string | null {
  if (typeof window === 'undefined' || !redirectUri) return null
  try {
    const host = new URL(redirectUri).hostname
    if (host && host !== window.location.hostname) {
      return host
    }
  } catch {
    return null
  }
  return null
}

/** Секрет: если уже в БД — не показываем в input (браузер иначе подставляет чужой пароль). */
function SecretTokenField({
  label,
  value,
  onChange,
  placeholder = 'vk1.a.xxxxxxxx…',
}: {
  label: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
}) {
  const [replacing, setReplacing] = useState(false)
  const saved = isMaskedSecret(value)

  useEffect(() => {
    if (saved) setReplacing(false)
  }, [saved])

  const showInput = !saved || replacing

  if (!showInput) {
    return (
      <div className="space-y-2">
        <label className="block text-sm font-medium text-[var(--text-secondary)]">{label}</label>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-green-400">сохранён в профиле (не показывается повторно)</span>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => {
              setReplacing(true)
              onChange('')
            }}
          >
            Заменить
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <Input
        label={label}
        type="password"
        autoComplete="new-password"
        name={`vk-secret-${label.replace(/\s+/g, '-').toLowerCase()}`}
        value={saved ? '' : value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
      {replacing && (
        <button
          type="button"
          className="text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
          onClick={() => {
            setReplacing(false)
            onChange('***')
          }}
        >
          Отмена — оставить сохранённый ключ
        </button>
      )}
    </div>
  )
}

export interface AuthTabProps {
  authStatus: VKAuthStatus | null
  groupToPost: string
  onGroupToPostChange: (v: string) => void
  accessToken: string
  onAccessTokenChange: (v: string) => void
  userAccessToken: string
  onUserAccessTokenChange: (v: string) => void
  onSaveUserToken: () => void
  vkCallbackConfirmation: string
  onVkCallbackConfirmationChange: (v: string) => void
  vkCallbackSecret: string
  onVkCallbackSecretChange: (v: string) => void
  vkCallbackApiUrl: string
  vkAppId: string
  onVkAppIdChange: (v: string) => void
  vkAppSecret: string
  onVkAppSecretChange: (v: string) => void
  vkAppServiceKey: string
  onVkAppServiceKeyChange: (v: string) => void
  vkFrontendUrl: string
  onVkFrontendUrlChange: (v: string) => void
  vkPublicGatewayUrl: string
  onVkPublicGatewayUrlChange: (v: string) => void
  vkOAuthRedirectUri: string
  isSavingProfile: boolean
  verifyResults: Partial<Record<VkVerifyBlock, VKAuthVerifyResult | null>>
  verifyingBlock: VkVerifyBlock | null
  onSaveCommunity: () => void
  onSaveCallback: () => void
  onSaveApp: () => void
  onVerify: (block: VkVerifyBlock) => void
  onTestCommunityWall: () => void
  testingCommunityWall: boolean
  communityTestPostUrl: string | null
  onLoadAdminGroups: () => void
  loadingAdminGroups: boolean
  adminGroups: VKSubscriptionItem[]
  onSelectAdminGroup: (groupId: number) => void
  onTestOwnWall: () => void
  testingOwnWall: boolean
  ownWallTestPostUrl: string | null
  onRefreshAuthStatus: () => void
  onConnectVkUser: () => void
  onConnectVkCommunity: () => void
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

function VerifyBadge({ result }: { result?: VKAuthVerifyResult | null }) {
  if (!result) {
    return <span className="text-xs text-[var(--text-muted)]">не проверялось</span>
  }
  return (
    <span className={`text-xs ${result.ok ? 'text-green-400' : 'text-amber-400'}`}>
      {result.ok ? 'OK' : 'Ошибка'}: {result.message}
    </span>
  )
}

export function AuthTab({
  authStatus,
  groupToPost,
  onGroupToPostChange,
  accessToken,
  onAccessTokenChange,
  userAccessToken,
  onUserAccessTokenChange,
  onSaveUserToken,
  vkCallbackConfirmation,
  onVkCallbackConfirmationChange,
  vkCallbackSecret,
  onVkCallbackSecretChange,
  vkCallbackApiUrl,
  vkAppId,
  onVkAppIdChange,
  vkAppSecret,
  onVkAppSecretChange,
  vkAppServiceKey,
  onVkAppServiceKeyChange,
  vkFrontendUrl,
  onVkFrontendUrlChange,
  vkPublicGatewayUrl,
  onVkPublicGatewayUrlChange,
  vkOAuthRedirectUri,
  isSavingProfile,
  verifyResults,
  verifyingBlock,
  onSaveCommunity,
  onSaveCallback,
  onSaveApp,
  onVerify,
  onTestCommunityWall,
  testingCommunityWall,
  communityTestPostUrl,
  onLoadAdminGroups,
  loadingAdminGroups,
  adminGroups,
  onSelectAdminGroup,
  onTestOwnWall,
  testingOwnWall,
  ownWallTestPostUrl,
  onRefreshAuthStatus,
  onConnectVkUser,
  onConnectVkCommunity,
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
  const [implicitScopeId, setImplicitScopeId] = useState('groups')
  const implicitPreset =
    VK_IMPLICIT_SCOPE_PRESETS.find((p) => p.id === implicitScopeId) ?? VK_IMPLICIT_SCOPE_PRESETS[0]
  const implicitAuthUrl = vkAppId.trim()
    ? buildVkImplicitAuthUrl(vkAppId, implicitPreset.scope)
    : ''
  const oauthHostMismatch = oauthRedirectHostMismatch(vkOAuthRedirectUri)

  return (
    <div className="space-y-4 animate-slide-up">
      <Card className="border-amber-500/30">
        <CardHeader>
          <CardTitle className="text-amber-400">VK авторизация — 4 блока</CardTitle>
          <CardDescription>
            {authStatus?.message ??
              'Секреты хранятся в профиле (БД). Каждый блок сохраняется и проверяется отдельно.'}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-[var(--text-secondary)]">
          <p className="text-[var(--text-muted)] text-xs">
            Что для чего (кратко). Channels → Recheck смотрит на те же токены.
          </p>
          <ul className="space-y-2 text-xs leading-relaxed">
            <li>
              <span className="text-[var(--text-primary)] font-medium">Сбор (Collect) и алерты</span>
              {' '}в Channels / Profile → Collection, а также список подписок — только{' '}
              <strong className="text-[var(--text-primary)]">блок 4 · user OAuth</strong>
              {' '}(<code className="text-[var(--text-secondary)]">user_access_token</code>).
              Токена сообщества недостаточно: <code>wall.get</code> чужих/своих стен с community
              auth даёт ошибку API [27]. Без user OAuth переключатели Collect/Alert и «Запросить
              список» подписок недоступны.
            </li>
            <li>
              <span className="text-[var(--text-primary)] font-medium">Чтение чужих групп</span>
              {' '}(Channels source/competitor, short name вроде{' '}
              <code className="text-[var(--text-secondary)]">onlinestudies</code>) —{' '}
              <strong className="text-[var(--text-primary)]">блок 4 · user OAuth</strong>
              {' '}(+ при необходимости App ID из блока 3).
            </li>
            <li>
              <span className="text-[var(--text-primary)] font-medium">Пост текстом в сообщество</span>
              {' '}(<code className="text-[var(--text-secondary)]">wall.post</code> от имени группы) —{' '}
              <strong className="text-[var(--text-primary)]">блок 1</strong>
              {' '}(Group to post + токен сообщества) или community OAuth в блоке 4.
            </li>
            <li>
              <span className="text-[var(--text-primary)] font-medium">Пост с фото в сообщество</span>
              {' '}— токен сообщества (блок 1){' '}
              <strong className="text-[var(--text-primary)]">+ user OAuth</strong> (блок 4) для{' '}
              <code className="text-[var(--text-secondary)]">photos.getWallUploadServer</code>.
            </li>
            <li>
              <span className="text-[var(--text-primary)] font-medium">Пост на личную стену</span>
              {' '}(текст / фото) — только{' '}
              <strong className="text-[var(--text-primary)]">блок 4 · user OAuth</strong>.
            </li>
            <li>
              <span className="text-[var(--text-primary)] font-medium">Callback / события группы</span>
              {' '}— блок 2 (confirmation + secret) + URL из блока 3.
            </li>
            <li>
              <span className="text-[var(--text-primary)] font-medium">OAuth «Подключить…»</span>
              {' '}— блок 3 (App ID + защищённый ключ), иначе кнопки в блоке 4 не заработают.
            </li>
          </ul>
        </CardContent>
      </Card>

      {/* 1. Community */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">1. Токен сообщества</CardTitle>
          <CardDescription>
            Ключ из «Управление → Работа с API» группы или OAuth сообщества (блок 4).{' '}
            <a
              href="https://dev.vk.ru/ru/api/community-messages/getting-started"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-400 hover:underline"
            >
              Документация
            </a>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <ul className="text-xs text-[var(--text-muted)] space-y-1 list-disc pl-4">
            <li>
              <span className="text-emerald-400/90">Нужен для:</span> постов текстом в{' '}
              <em>вашу</em> группу (<code>wall.post</code>, from_group).
            </li>
            <li>
              <span className="text-amber-400/90">Недостаточно для:</span> чтения чужих групп,
              загрузки фото на стену группы, постов на личную стену.
            </li>
            <li>
              ID группы — числовой id или <code>club…</code>; должен совпадать с каналом роли{' '}
              <code>own</code> в Channels.
            </li>
          </ul>
          <Input
            label="ID группы"
            value={groupToPost}
            onChange={(e) => onGroupToPostChange(e.target.value)}
            placeholder="club236672543"
            autoComplete="off"
          />
          <SecretTokenField
            label="Ключ доступа"
            value={accessToken}
            onChange={onAccessTokenChange}
            placeholder="vk1.a.xxxxxxxx…"
          />
          <div className="flex flex-wrap gap-2 items-center">
            <Button type="button" onClick={onSaveCommunity} isLoading={isSavingProfile}>
              Сохранить
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => onVerify('community')}
              isLoading={verifyingBlock === 'community'}
            >
              Проверить
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={onTestCommunityWall}
              isLoading={testingCommunityWall}
            >
              Отправить тестовый пост
            </Button>
            <VerifyBadge result={verifyResults.community} />
          </div>
          {communityTestPostUrl && (
            <p className="text-sm">
              <a
                href={communityTestPostUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-400 hover:underline break-all"
              >
                Открыть тестовый пост → {communityTestPostUrl}
              </a>
            </p>
          )}
        </CardContent>
      </Card>

      {/* 2. Callback */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">2. Callback API</CardTitle>
          <CardDescription>
            Адрес сервера в настройках группы и строка подтверждения.{' '}
            <a
              href="https://dev.vk.ru/ru/api/callback/getting-started"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-400 hover:underline"
            >
              Документация
            </a>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <ul className="text-xs text-[var(--text-muted)] space-y-1 list-disc pl-4">
            <li>
              <span className="text-emerald-400/90">Нужен для:</span> приёма событий группы
              (confirmation, новые сообщения и т.п. на <code>POST /vk/callback</code>).
            </li>
            <li>
              <span className="text-amber-400/90">Не нужен для:</span> обычного постинга и сбора стен
              через Channels / wall.post.
            </li>
          </ul>
          <p className="text-xs text-[var(--text-muted)]">
            URL сервера (скопировать в VK):{' '}
            <code className="text-[var(--text-secondary)] break-all">{vkCallbackApiUrl || '— сохраните gateway URL в блоке 3'}</code>
          </p>
            <Input
              label="Строка подтверждения"
              value={vkCallbackConfirmation}
              onChange={(e) => onVkCallbackConfirmationChange(e.target.value)}
              placeholder="из настроек Callback API"
              autoComplete="off"
            />
            <SecretTokenField
              label="Секретный ключ сервера"
              value={vkCallbackSecret}
              onChange={onVkCallbackSecretChange}
              placeholder="произвольная строка"
            />
          <div className="flex flex-wrap gap-2 items-center">
            <Button type="button" onClick={onSaveCallback} isLoading={isSavingProfile}>
              Сохранить
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => onVerify('callback')}
              isLoading={verifyingBlock === 'callback'}
            >
              Проверить
            </Button>
            <VerifyBadge result={verifyResults.callback} />
          </div>
        </CardContent>
      </Card>

      {/* 3. App keys */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">3. Приложение (ключи)</CardTitle>
          <CardDescription>
            App ID, защищённый и сервисный ключ из кабинета приложения.{' '}
            <a
              href="https://dev.vk.ru/ru/mini-apps/settings/development/keys"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-400 hover:underline"
            >
              Ключи доступа
            </a>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <ul className="text-xs text-[var(--text-muted)] space-y-1 list-disc pl-4">
            <li>
              <span className="text-emerald-400/90">Нужен для:</span> кнопок OAuth в блоке 4
              (обмен code → токен). Redirect URI должен совпадать с кабинетом VK.
            </li>
            <li>
              <span className="text-[var(--text-primary)]">Защищённый ключ</span> — обязателен для
              OAuth. <span className="text-[var(--text-primary)]">Сервисный</span> — опционально
              (публичные методы / resolve без user-сессии).
            </li>
            <li>
              <span className="text-amber-400/90">Сам по себе не публикует</span> и не читает стены —
              только включает OAuth и вспомогательные вызовы API.
            </li>
          </ul>
          <div className="grid gap-3 sm:grid-cols-2">
            <Input
              label="VK App ID"
              value={vkAppId}
              onChange={(e) => onVkAppIdChange(e.target.value)}
              placeholder="54497652"
              autoComplete="off"
            />
            <SecretTokenField
              label="Защищённый ключ"
              value={vkAppSecret}
              onChange={onVkAppSecretChange}
              placeholder="protected key"
            />
            <SecretTokenField
              label="Сервисный ключ"
              value={vkAppServiceKey}
              onChange={onVkAppServiceKeyChange}
              placeholder="service key (опционально)"
            />
            <Input
              label="URL интерфейса"
              value={vkFrontendUrl}
              onChange={(e) => onVkFrontendUrlChange(e.target.value)}
              placeholder="https://www.copyparse.ru"
              autoComplete="off"
            />
            <Input
              label="Публичный URL gateway"
              value={vkPublicGatewayUrl}
              onChange={(e) => onVkPublicGatewayUrlChange(e.target.value)}
              placeholder="https://www.copyparse.ru/api"
              autoComplete="off"
            />
          </div>
          <div className="flex flex-wrap gap-2 items-center">
            <Button type="button" onClick={onSaveApp} isLoading={isSavingProfile}>
              Сохранить
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => onVerify('app')}
              isLoading={verifyingBlock === 'app'}
            >
              Проверить
            </Button>
            <VerifyBadge result={verifyResults.app} />
          </div>
        </CardContent>
      </Card>

      {/* 4. OAuth */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">4. OAuth</CardTitle>
          <CardDescription>
            Два разных потока: пользователь и сообщество. Сначала сохраните ключи в блоке 3.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <ul className="text-xs text-[var(--text-muted)] space-y-1 list-disc pl-4">
            <li>
              <span className="text-[var(--text-primary)] font-medium">User token</span>
              {' '}→ Collect / Alert, чужие группы, фото на стену группы, личная стена.
            </li>
            <li>
              Если OAuth / VK ID недоступны — Implicit Flow. При{' '}
              <code>invalid_scope</code> смените набор прав ниже (часто <code>wall</code> режется).
            </li>
          </ul>
          <div className="rounded-lg border border-[var(--border-color)] p-3 space-y-3">
            <p className="text-sm text-[var(--text-primary)] font-medium">User token вручную</p>
            <p className="text-xs text-[var(--text-muted)] leading-relaxed">
              1) Выберите scope и откройте ссылку (нужен App ID из блока 3).
              <br />
              2) После входа: <code>oauth.vk.com/blank.html#access_token=…</code>
              <br />
              3) Скопируйте <code>access_token</code> (до <code>&amp;</code>) в поле ниже.
            </p>
            <div className="space-y-2">
              <label className="block text-sm font-medium text-[var(--text-secondary)]">
                Права (scope)
              </label>
              <div className="flex flex-col gap-1.5">
                {VK_IMPLICIT_SCOPE_PRESETS.map((preset) => (
                  <label
                    key={preset.id}
                    className="flex items-start gap-2 text-xs text-[var(--text-secondary)] cursor-pointer"
                  >
                    <input
                      type="radio"
                      className="mt-0.5"
                      name="vk-implicit-scope"
                      checked={implicitScopeId === preset.id}
                      onChange={() => setImplicitScopeId(preset.id)}
                    />
                    <span>
                      <span className="text-[var(--text-primary)]">{preset.label}</span>
                      <span className="text-[var(--text-muted)]"> — {preset.hint}</span>
                    </span>
                  </label>
                ))}
              </div>
            </div>
            {implicitAuthUrl ? (
              <a
                href={implicitAuthUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-primary-400 hover:underline break-all inline-block"
              >
                Открыть Implicit Flow → получить user token
                <span className="text-[var(--text-muted)]"> ({implicitPreset.scope})</span>
              </a>
            ) : (
              <p className="text-xs text-amber-400">
                Сначала сохраните VK App ID в блоке 3 — появится ссылка для получения токена.
              </p>
            )}
            <SecretTokenField
              label="User token"
              value={userAccessToken}
              onChange={onUserAccessTokenChange}
              placeholder="vk1.a.xxxxxxxx…"
            />
            <div className="flex flex-wrap gap-2 items-center">
              <Button type="button" onClick={onSaveUserToken} isLoading={isSavingProfile}>
                Сохранить user token
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => onVerify('oauth')}
                isLoading={verifyingBlock === 'oauth'}
              >
                Проверить
              </Button>
              <VerifyBadge result={verifyResults.oauth} />
            </div>
          </div>
          <div className="text-xs text-[var(--text-muted)] space-y-1">
            <p>
              Redirect URI нужно добавить в кабинет приложения VK ID → «Доверенный Redirect URI»
              <strong className="text-[var(--text-secondary)]"> один в один</strong> (https, www,
              путь). Недостаточно указать только «Публичный URL gateway».
            </p>
            <p className="flex flex-wrap items-center gap-2">
              <code className="text-[var(--text-secondary)] break-all">{vkOAuthRedirectUri}</code>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => {
                  void navigator.clipboard.writeText(vkOAuthRedirectUri)
                }}
              >
                Копировать
              </Button>
            </p>
            {oauthHostMismatch && (
              <p className="text-amber-500">
                Страница открыта на {typeof window !== 'undefined' ? window.location.host : ''}
                , а VK вернёт браузер на {oauthHostMismatch}. Для локального Docker в блоке 3
                поставьте gateway <code>http://localhost:8000</code> и сохраните; в кабинете VK
                добавьте <code>http://localhost:8000/vk/oauth/callback</code>.
              </p>
            )}
          </div>
          <div className="flex flex-wrap gap-3 text-sm text-[var(--text-secondary)]">
            <span>
              Сообщество: {authStatus?.community_connected ? 'токен есть' : 'нет'}
            </span>
            <span>
              Пользователь: {authStatus?.connected ? 'токен есть' : 'нет'}
              {authStatus?.vk_user_id != null && authStatus.connected
                ? ` (id ${authStatus.vk_user_id})`
                : ''}
            </span>
            <Button variant="ghost" size="sm" onClick={onRefreshAuthStatus}>
              Обновить статус
            </Button>
          </div>
          <div className="flex flex-wrap gap-2 items-center">
            <Button onClick={onConnectVkCommunity}>Подключить сообщество (OAuth)</Button>
            <Button variant="secondary" onClick={onConnectVkUser}>
              Подключить пользователя (OAuth)
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={onLoadAdminGroups}
              isLoading={loadingAdminGroups}
            >
              Мои сообщества (admin)
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={onTestOwnWall}
              isLoading={testingOwnWall}
            >
              Тест на личную стену
            </Button>
          </div>
          {ownWallTestPostUrl && (
            <p className="text-sm">
              <a
                href={ownWallTestPostUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-400 hover:underline break-all"
              >
                Открыть пост на стене → {ownWallTestPostUrl}
              </a>
            </p>
          )}

          {adminGroups.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs text-[var(--text-muted)]">
                Кликните сообщество — подставится Group to post (сохраните блок «Сообщество»).
              </p>
              <ul className="max-h-56 overflow-y-auto rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] p-3 space-y-1">
                {adminGroups.map((s, i) => (
                  <li key={`admin-${s.id ?? i}`}>
                    <button
                      type="button"
                      className="w-full text-left text-sm px-2 py-1.5 rounded-lg hover:bg-[var(--bg-tertiary)] flex flex-wrap gap-x-3 gap-y-1"
                      onClick={() => s.id != null && onSelectAdminGroup(Number(s.id))}
                    >
                      {s.screen_name && <span className="font-mono text-primary-400">{s.screen_name}</span>}
                      {s.name && <span className="text-[var(--text-secondary)]">{s.name}</span>}
                      {s.id != null && <span className="text-[var(--text-muted)] text-xs">id: {s.id}</span>}
                      {groupToPost === String(s.id) && (
                        <span className="text-xs text-green-400">выбрано</span>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="space-y-3 pt-3 border-t border-[var(--border-color)]">
            <h3 className="text-sm font-semibold">Проверка подписок / групп</h3>
            <p className="text-xs text-[var(--text-muted)]">
              Нужен <strong className="text-[var(--text-primary)]">user OAuth</strong> (кнопка
              «Подключить пользователя» выше). Community-токен для списка подписок не подходит.
            </p>
            {!authStatus?.connected && (
              <p className="text-xs text-amber-400/90">
                User OAuth не подключён — сначала блок 3 (App) → «Подключить пользователя», затем
                обновите статус.
              </p>
            )}
            <Button
              type="button"
              onClick={onLoadSubscriptions}
              isLoading={loadingSubscriptions}
              disabled={!authStatus?.connected}
              title={
                authStatus?.connected
                  ? 'Загрузить подписки через user OAuth'
                  : 'Сначала подключите пользователя (user OAuth)'
              }
            >
              Запросить список
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
                    className="flex flex-wrap gap-x-3 gap-y-1 text-sm border-b border-[var(--border-color)] border-opacity-50 pb-2 last:border-0"
                  >
                    {s.screen_name && <span className="font-mono text-primary-400">{s.screen_name}</span>}
                    {s.name && <span className="text-[var(--text-secondary)]">{s.name}</span>}
                    {s.id != null && <span className="text-[var(--text-muted)] text-xs">id: {s.id}</span>}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="pt-3 border-t border-[var(--border-color)] border-dashed">
            <button
              type="button"
              className="text-sm text-amber-400/90 hover:text-amber-300 underline-offset-2 hover:underline"
              onClick={onToggleSelenium}
            >
              {vkSeleniumOpen ? 'Скрыть' : 'Резервный вход'} (Selenium)
            </button>
            {vkSeleniumOpen && (
              <div className="mt-3 space-y-3 rounded-lg border border-amber-500/25 bg-[var(--bg-tertiary)]/50 p-4">
                <p className="text-xs text-[var(--text-muted)]">
                  Только диагностика веб-страницы VK. Не заменяет OAuth/API-токены для постинга и
                  чтения групп.
                </p>
                <div className="grid gap-3 sm:grid-cols-2">
                  <Input
                    label="Телефон или email VK"
                    value={vkSeleniumLogin}
                    onChange={(e) => onVkSeleniumLoginChange(e.target.value)}
                  />
                  <Input
                    label="Пароль"
                    type="password"
                    value={vkSeleniumPassword}
                    onChange={(e) => onVkSeleniumPasswordChange(e.target.value)}
                  />
                </div>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={onVerifySelenium}
                  isLoading={loadingSeleniumVerify}
                  disabled={!vkSeleniumLogin.trim() || !vkSeleniumPassword}
                >
                  Проверить через Selenium
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
