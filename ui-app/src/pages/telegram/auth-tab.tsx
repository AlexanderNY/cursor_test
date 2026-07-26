import { FormEvent } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import type { TgAuthStatus } from '@/services/telegram-service'
import type { AvailableChannel } from './telegram-helpers'

export interface AuthTabProps {
  authStatus: TgAuthStatus | null
  isLoadingProfile: boolean
  isSavingProfile: boolean
  isSubmittingAuth: boolean
  isCheckingChannels: boolean
  apiId: string
  onApiIdChange: (v: string) => void
  apiHash: string
  onApiHashChange: (v: string) => void
  telegramUsername: string
  onTelegramUsernameChange: (v: string) => void
  authPhoneNumber: string
  onAuthPhoneNumberChange: (v: string) => void
  authCode: string
  onAuthCodeChange: (v: string) => void
  authPassword: string
  onAuthPasswordChange: (v: string) => void
  availableChannels: AvailableChannel[]
  channelsError: string
  onSaveProfile: (e: FormEvent) => void
  onLoadAuthStatus: () => void
  onSubmitAuthCode: (e: FormEvent) => void
  onSubmitAuthPassword: (e: FormEvent) => void
  onCheckChannels: () => void
}

export function AuthTab({
  authStatus,
  isLoadingProfile,
  isSavingProfile,
  isSubmittingAuth,
  isCheckingChannels,
  apiId,
  onApiIdChange,
  apiHash,
  onApiHashChange,
  telegramUsername,
  onTelegramUsernameChange,
  authPhoneNumber,
  onAuthPhoneNumberChange,
  authCode,
  onAuthCodeChange,
  authPassword,
  onAuthPasswordChange,
  availableChannels,
  channelsError,
  onSaveProfile,
  onLoadAuthStatus,
  onSubmitAuthCode,
  onSubmitAuthPassword,
  onCheckChannels,
}: AuthTabProps) {
  return (
    <Card className="animate-slide-up border-amber-500/30">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-amber-400">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          Telegram авторизация
        </CardTitle>
        <CardDescription>{authStatus?.message || 'Проверка статуса авторизации...'}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {isLoadingProfile ? (
          <div className="p-4 rounded-lg border border-[var(--border-color)] bg-[var(--bg-tertiary)] text-center text-sm text-[var(--text-muted)]">
            Загрузка настроек профиля...
          </div>
        ) : (
          <form onSubmit={onSaveProfile} className="p-4 bg-[var(--bg-secondary)] rounded-xl space-y-4 border border-amber-500/25">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
              Настройки профиля Telegram
            </h3>
            <Input label="API ID" type="text" value={apiId} onChange={(e) => onApiIdChange(e.target.value)} placeholder="e.g., 0157230167" />
            <Input label="API Hash" type="text" value={apiHash} onChange={(e) => onApiHashChange(e.target.value)} placeholder="e.g., afd10c198eaa94bc4fe3f82415eb46ee67" />
            <Input label="Логин в Telegram" type="text" value={telegramUsername} onChange={(e) => onTelegramUsernameChange(e.target.value)} placeholder="e.g., @username" />
            <Input label="Номер телефона для авторизации" type="text" value={authPhoneNumber} onChange={(e) => onAuthPhoneNumberChange(e.target.value)} placeholder="e.g., +79001234567" />
            <p className="text-xs text-[var(--text-muted)]">
              Получите API credentials на my.telegram.org. Номер телефона нужен для первой авторизации в Telegram.
            </p>
            <div className="pt-2">
              <Button type="submit" isLoading={isSavingProfile} className="w-full sm:w-auto">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Сохранить настройки профиля
              </Button>
            </div>
          </form>
        )}

        <div className="flex items-center gap-3 p-3 rounded-lg bg-[var(--bg-tertiary)]">
          <div className={`w-3 h-3 rounded-full ${
            authStatus?.auth_state === 'authorized' ? 'bg-green-400' :
            authStatus?.auth_state === 'pending_code' ? 'bg-amber-400 animate-pulse' :
            authStatus?.auth_state === 'pending_password' ? 'bg-amber-400 animate-pulse' :
            authStatus?.auth_state === 'failed' ? 'bg-red-400' :
            'bg-gray-400'
          }`} />
          <span className="text-sm text-[var(--text-secondary)]">
            Статус: {
              authStatus?.auth_state === 'authorized' ? 'Авторизован' :
              authStatus?.auth_state === 'pending_code' ? 'Ожидает ввода кода' :
              authStatus?.auth_state === 'pending_password' ? 'Ожидает ввода пароля 2FA' :
              authStatus?.auth_state === 'failed' ? 'Ошибка авторизации' :
              authStatus?.auth_state || 'Загрузка...'
            }
          </span>
          <Button variant="ghost" size="sm" onClick={onLoadAuthStatus} className="ml-auto">Обновить</Button>
        </div>

        {authStatus?.auth_state === 'pending_code' && (
          <div className="p-4 rounded-lg border border-amber-500/30 bg-amber-500/5">
            <h3 className="text-sm font-medium text-amber-400 mb-3">Введите код подтверждения</h3>
            <p className="text-xs text-[var(--text-muted)] mb-4">Код отправлен в Telegram на ваш телефон. Проверьте приложение Telegram.</p>
            <form onSubmit={onSubmitAuthCode} className="flex flex-wrap items-end gap-3">
              <div className="flex-1 min-w-[180px]">
                <label className="text-sm font-medium text-[var(--text-secondary)] block mb-1">Код подтверждения</label>
                <input type="text" value={authCode} onChange={(e) => onAuthCodeChange(e.target.value)} placeholder="12345" maxLength={6} autoFocus className="w-full px-4 py-2 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-amber-500/50 text-lg tracking-widest" required />
              </div>
              <Button type="submit" isLoading={isSubmittingAuth} disabled={!authCode.trim()}>Отправить код</Button>
            </form>
          </div>
        )}

        {authStatus?.auth_state === 'pending_password' && (
          <div className="p-4 rounded-lg border border-amber-500/30 bg-amber-500/5">
            <h3 className="text-sm font-medium text-amber-400 mb-3">Введите пароль двухфакторной аутентификации</h3>
            <p className="text-xs text-[var(--text-muted)] mb-4">У вашего аккаунта Telegram включена двухфакторная аутентификация. Введите пароль.</p>
            <form onSubmit={onSubmitAuthPassword} className="flex flex-wrap items-end gap-3">
              <div className="flex-1 min-w-[180px]">
                <label className="text-sm font-medium text-[var(--text-secondary)] block mb-1">Пароль 2FA</label>
                <input type="password" value={authPassword} onChange={(e) => onAuthPasswordChange(e.target.value)} placeholder="••••••••" autoFocus className="w-full px-4 py-2 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-amber-500/50" required />
              </div>
              <Button type="submit" isLoading={isSubmittingAuth} disabled={!authPassword.trim()}>Отправить пароль</Button>
            </form>
          </div>
        )}

        {authStatus?.auth_state === 'failed' && (
          <div className="p-4 rounded-lg border border-red-500/30 bg-red-500/5">
            <p className="text-sm text-red-400">
              Авторизация не удалась. Укажите API ID, API Hash и номер телефона в блоке «Настройки профиля Telegram»
              выше и сохраните — код будет запрошен автоматически.
            </p>
          </div>
        )}

        {authStatus?.auth_state === 'authorized' && (
          <div className="p-4 rounded-lg border border-green-500/30 bg-green-500/5">
            <p className="text-sm text-green-400">Аккаунт Telegram успешно авторизован. Бот готов к работе.</p>
          </div>
        )}

        {!authStatus && (
          <div className="p-4 rounded-lg border border-[var(--border-color)] bg-[var(--bg-tertiary)]">
            <p className="text-sm text-[var(--text-muted)]">
              Статус авторизации загружается... Если статус не появляется,
              проверьте, что в блоке выше указаны API ID, API Hash и номер телефона.
            </p>
          </div>
        )}

        <div className="p-4 rounded-lg border border-amber-500/20 bg-[var(--bg-tertiary)] space-y-3">
          <h3 className="text-sm font-medium text-[var(--text-secondary)]">Доступные каналы</h3>
          <p className="text-xs text-[var(--text-muted)]">
            После успешной авторизации можно проверить список каналов, к которым у аккаунта есть доступ.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <Button type="button" variant="secondary" onClick={onCheckChannels} disabled={isCheckingChannels}>
              {isCheckingChannels ? 'Проверка...' : 'Проверить доступные каналы'}
            </Button>
            {channelsError && <span className="text-sm text-red-400">{channelsError}</span>}
          </div>
          {availableChannels.length > 0 && (
            <div className="pt-2 border-t border-[var(--border-color)]">
              <p className="text-sm font-medium text-[var(--text-secondary)] mb-2">Доступные каналы (id : название):</p>
              <ul className="text-sm text-[var(--text-primary)] space-y-1 max-h-48 overflow-y-auto bg-[var(--bg-secondary)] rounded-lg p-3">
                {availableChannels.map((ch) => (
                  <li key={ch.id} className="font-mono">{ch.id} : {ch.title}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
