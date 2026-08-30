import { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import type { ScheduleType } from '@/types/vkontakte'
import type { DynamicField } from './vkontakte-helpers'

export interface ProfileSettingsTabProps {
  isLoadingProfile: boolean
  isSavingProfile: boolean
  publishEnabled: boolean
  onPublishEnabledChange: (v: boolean) => void
  fromGroup: boolean
  onFromGroupChange: (v: boolean) => void
  groupToPost: string
  onGroupToPostChange: (v: string) => void
  scheduleType: ScheduleType
  onScheduleTypeChange: (v: ScheduleType) => void
  timeIntervals: Array<{ id: string; start: string; end: string }>
  onAddTimeInterval: () => void
  onRemoveTimeInterval: (id: string) => void
  onUpdateTimeInterval: (id: string, field: 'start' | 'end', value: string) => void
  collectEnabled: boolean
  onCollectEnabledChange: (v: boolean) => void
  /** User OAuth connected — required to enable Collect */
  userOauthConnected: boolean
  groupsToRead: DynamicField[]
  onAddGroupToRead: () => void
  onRemoveGroupToRead: (id: string) => void
  onUpdateGroupToRead: (id: string, value: string) => void
  onSubmit: (e: FormEvent) => void
}

export function ProfileSettingsTab({
  isLoadingProfile,
  isSavingProfile,
  publishEnabled,
  onPublishEnabledChange,
  fromGroup,
  onFromGroupChange,
  groupToPost,
  onGroupToPostChange,
  scheduleType,
  onScheduleTypeChange,
  timeIntervals,
  onAddTimeInterval,
  onRemoveTimeInterval,
  onUpdateTimeInterval,
  collectEnabled,
  onCollectEnabledChange,
  userOauthConnected,
  groupsToRead,
  onAddGroupToRead,
  onRemoveGroupToRead,
  onUpdateGroupToRead,
  onSubmit,
}: ProfileSettingsTabProps) {
  return (
    <Card className="animate-slide-up">
      <CardHeader>
        <CardTitle>Profile Settings</CardTitle>
        <CardDescription>Publishing, connection and collection settings</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoadingProfile ? (
          <div className="text-center py-8 text-[var(--text-muted)]">Loading profile...</div>
        ) : (
          <form onSubmit={onSubmit} className="space-y-8">
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-[var(--text-primary)]">Publishing</h3>
              <label className="flex items-center gap-3 cursor-pointer group">
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={publishEnabled}
                    onChange={(e) => onPublishEnabledChange(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                  <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                </div>
                <span className="text-[var(--text-primary)]">Enable publishing</span>
              </label>
              <label className="flex items-center gap-3 cursor-pointer group">
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={fromGroup}
                    onChange={(e) => onFromGroupChange(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                  <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                </div>
                <span className="text-[var(--text-primary)]">From group</span>
              </label>
              <Input
                label="Group to post (ID or short name)"
                value={groupToPost}
                onChange={(e) => onGroupToPostChange(e.target.value)}
                placeholder="e.g. 123456 or club123456"
              />
              <div className="space-y-2">
                <label className="text-sm font-medium text-[var(--text-secondary)] block">Publish schedule</label>
                <div className="space-y-3">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="radio"
                      name="schedule"
                      checked={scheduleType === 'immediate'}
                      onChange={() => onScheduleTypeChange('immediate')}
                      className="w-4 h-4 text-primary-500"
                    />
                    <span className="text-[var(--text-primary)]">Immediate</span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="radio"
                      name="schedule"
                      checked={scheduleType === 'intervals'}
                      onChange={() => onScheduleTypeChange('intervals')}
                      className="w-4 h-4 text-primary-500"
                    />
                    <span className="text-[var(--text-primary)]">By time intervals</span>
                  </label>
                </div>
                {scheduleType === 'intervals' && (
                  <div className="space-y-3 mt-4">
                    {timeIntervals.map((interval, idx) => (
                      <div key={interval.id} className="flex gap-3 items-end">
                        <Input
                          label={`Interval ${idx + 1} start`}
                          type="time"
                          value={interval.start}
                          onChange={(e) => onUpdateTimeInterval(interval.id, 'start', e.target.value)}
                          className="flex-1"
                        />
                        <Input
                          label="End"
                          type="time"
                          value={interval.end}
                          onChange={(e) => onUpdateTimeInterval(interval.id, 'end', e.target.value)}
                          className="flex-1"
                        />
                        {timeIntervals.length > 1 && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => onRemoveTimeInterval(interval.id)}
                            className="text-red-400 hover:text-red-300"
                          >
                            Remove
                          </Button>
                        )}
                      </div>
                    ))}
                    {timeIntervals.length < 5 && (
                      <Button type="button" variant="secondary" size="sm" onClick={onAddTimeInterval}>
                        Add interval
                      </Button>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-4 pt-4 border-t border-[var(--border-color)]">
              <h3 className="text-sm font-semibold text-[var(--text-primary)]">Collection (Parser)</h3>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                Для чтения стен (<code>wall.get</code>) нужен{' '}
                <strong className="text-[var(--text-primary)]">user OAuth</strong> на вкладке{' '}
                <Link to="/vkontakte?auth=1" className="text-primary-400 underline">
                  Авторизация → блок 4
                </Link>
                . Токена сообщества недостаточно.
              </p>
              {!userOauthConnected && (
                <Alert variant="warning">
                  User OAuth не подключён — включить сбор нельзя. Откройте Авторизация → «Подключить
                  пользователя».
                </Alert>
              )}
              <label
                className={`flex items-center gap-3 group ${
                  userOauthConnected ? 'cursor-pointer' : 'cursor-not-allowed opacity-60'
                }`}
              >
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={collectEnabled && userOauthConnected}
                    disabled={!userOauthConnected}
                    onChange={(e) => {
                      if (!userOauthConnected) return
                      onCollectEnabledChange(e.target.checked)
                    }}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                  <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                </div>
                <span className="text-[var(--text-primary)]">Enable collection</span>
              </label>
              {collectEnabled && userOauthConnected && (
                <div className="space-y-4 animate-slide-down">
                  <p className="text-sm text-[var(--text-muted)]">
                    User OAuth уже есть. Укажите, с каких групп читать стену (fallback, если нет
                    brand-каналов в Channels).
                  </p>
                  <div className="p-4 bg-[var(--bg-secondary)] rounded-xl space-y-4 border border-[var(--border-color)]">
                    <h4 className="text-sm font-semibold text-[var(--text-primary)]">Groups to read (wall.get)</h4>
                    <p className="text-xs text-[var(--text-muted)]">
                      Enter VK group IDs (e.g. 123456 or -123456). One per field.
                    </p>
                    {groupsToRead.map((field) => (
                      <div key={field.id} className="flex gap-3">
                        <Input
                          placeholder="e.g. 123456"
                          value={field.value}
                          onChange={(e) => onUpdateGroupToRead(field.id, e.target.value)}
                          className="flex-1"
                        />
                        {groupsToRead.length > 1 && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => onRemoveGroupToRead(field.id)}
                            className="px-3 text-red-400 hover:text-red-300"
                          >
                            Remove
                          </Button>
                        )}
                      </div>
                    ))}
                    <Button type="button" variant="secondary" size="sm" onClick={onAddGroupToRead}>
                      Add group
                    </Button>
                  </div>
                </div>
              )}
            </div>

            <CardFooter className="px-0">
              <Button type="submit" isLoading={isSavingProfile}>
                Save Profile Settings
              </Button>
            </CardFooter>
          </form>
        )}
      </CardContent>
    </Card>
  )
}
