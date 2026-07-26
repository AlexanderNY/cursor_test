import { FormEvent } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import type {
  PublishScheduleType,
  ConditionsMode,
  SentimentFilter,
  TgAnalyticsAlertItem,
} from '@/types/telegram'
import {
  SCHEDULE_MINUTES,
  MAX_ALERT_RULES,
  MAX_ALERT_LIST_ITEMS,
  type ScheduleMinute,
  type DynamicField,
  type AlertRuleBlock,
  type AvailableChannel,
  channelIdToString,
} from './telegram-helpers'

export interface ProfileSettingsTabProps {
  isLoadingProfile: boolean
  isSavingProfile: boolean
  publishEnabled: boolean
  onPublishEnabledChange: (v: boolean) => void
  publishScheduleType: PublishScheduleType
  onPublishScheduleTypeChange: (v: PublishScheduleType) => void
  publishScheduleHour: number
  onPublishScheduleHourChange: (v: number) => void
  publishScheduleMinute: ScheduleMinute
  onPublishScheduleMinuteChange: (v: ScheduleMinute) => void
  channelToPost: string
  onChannelToPostChange: (v: string) => void
  channelsToPost: string[]
  onChannelsToPostChange: (v: string[]) => void
  availableChannels: AvailableChannel[]
  collectEnabled: boolean
  onCollectEnabledChange: (v: boolean) => void
  chatsToRead: DynamicField[]
  saveConditions: DynamicField[]
  onAddField: (setter: React.Dispatch<React.SetStateAction<DynamicField[]>>) => void
  onRemoveField: (setter: React.Dispatch<React.SetStateAction<DynamicField[]>>, id: string) => void
  onUpdateField: (setter: React.Dispatch<React.SetStateAction<DynamicField[]>>, id: string, value: string) => void
  setChatsToRead: React.Dispatch<React.SetStateAction<DynamicField[]>>
  setSaveConditions: React.Dispatch<React.SetStateAction<DynamicField[]>>
  alertEnabled: boolean
  onAlertEnabledChange: (v: boolean) => void
  alertRules: AlertRuleBlock[]
  recentAlerts: TgAnalyticsAlertItem[]
  onAddAlertRule: () => void
  onRemoveAlertRule: (ruleId: string) => void
  onUpdateAlertRule: (ruleId: string, patch: Partial<Omit<AlertRuleBlock, 'id' | 'chatsToRead' | 'saveConditions'>>) => void
  onAddAlertRuleField: (ruleId: string, field: 'chatsToRead' | 'saveConditions') => void
  onRemoveAlertRuleField: (ruleId: string, field: 'chatsToRead' | 'saveConditions', fieldId: string) => void
  onUpdateAlertRuleField: (ruleId: string, field: 'chatsToRead' | 'saveConditions', fieldId: string, value: string) => void
  onSubmit: (e: FormEvent) => void
}

export function ProfileSettingsTab(props: ProfileSettingsTabProps) {
  const {
    isLoadingProfile,
    isSavingProfile,
    publishEnabled,
    onPublishEnabledChange,
    publishScheduleType,
    onPublishScheduleTypeChange,
    publishScheduleHour,
    onPublishScheduleHourChange,
    publishScheduleMinute,
    onPublishScheduleMinuteChange,
    channelToPost,
    onChannelToPostChange,
    channelsToPost,
    onChannelsToPostChange,
    availableChannels,
    collectEnabled,
    onCollectEnabledChange,
    chatsToRead,
    saveConditions,
    onAddField,
    onRemoveField,
    onUpdateField,
    setChatsToRead,
    setSaveConditions,
    alertEnabled,
    onAlertEnabledChange,
    alertRules,
    recentAlerts,
    onAddAlertRule,
    onRemoveAlertRule,
    onUpdateAlertRule,
    onAddAlertRuleField,
    onRemoveAlertRuleField,
    onUpdateAlertRuleField,
    onSubmit,
  } = props

  function toggleChannelToPost(channelId: string) {
    if (channelsToPost.includes(channelId)) {
      const next = channelsToPost.filter((c) => c !== channelId)
      onChannelsToPostChange(next)
      if (channelToPost === channelId) {
        onChannelToPostChange(next[0] || '')
      }
    } else {
      const next = [...channelsToPost, channelId]
      onChannelsToPostChange(next)
      if (!channelToPost) {
        onChannelToPostChange(channelId)
      }
    }
  }

  return (
    <Card className="animate-slide-up">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          Profile Settings
        </CardTitle>
        <CardDescription>Configure Telegram connection, publishing and collection settings</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoadingProfile ? (
          <div className="text-center py-8 text-[var(--text-muted)]">Loading profile...</div>
        ) : (
          <form onSubmit={onSubmit} className="space-y-8">
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
                Publishing
              </h3>
              <label className="flex items-center gap-3 cursor-pointer group">
                <div className="relative">
                  <input type="checkbox" checked={publishEnabled} onChange={(e) => onPublishEnabledChange(e.target.checked)} className="sr-only peer" />
                  <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                  <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                </div>
                <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">Enable publishing</span>
              </label>

              {publishEnabled && (
                <div className="p-4 bg-[var(--bg-secondary)] rounded-xl space-y-4 animate-slide-down">
                  <div className="space-y-4 pt-4 border-t border-[var(--border-color)]">
                    <label className="text-sm font-medium text-[var(--text-secondary)] block">Publish Schedule</label>
                    <div className="space-y-3">
                      <label className="flex items-center gap-3 cursor-pointer">
                        <input type="radio" name="publishSchedule" value="on_new_messages" checked={publishScheduleType === 'on_new_messages'} onChange={() => onPublishScheduleTypeChange('on_new_messages')} className="w-4 h-4 text-primary-500" />
                        <span className="text-[var(--text-primary)]">When new messages are checked</span>
                      </label>
                      <label className="flex items-center gap-3 cursor-pointer">
                        <input type="radio" name="publishSchedule" value="by_intervals" checked={publishScheduleType === 'by_intervals'} onChange={() => onPublishScheduleTypeChange('by_intervals')} className="w-4 h-4 text-primary-500" />
                        <span className="text-[var(--text-primary)]">By time intervals</span>
                      </label>
                    </div>

                    {publishScheduleType === 'by_intervals' && (
                      <div className="space-y-3 mt-4 animate-slide-down flex flex-wrap gap-4 items-end">
                        <div className="space-y-2 min-w-[6rem]">
                          <label className="text-sm font-medium text-[var(--text-secondary)] block">Hour</label>
                          <select value={publishScheduleHour} onChange={(e) => onPublishScheduleHourChange(Number(e.target.value))} className="w-full px-4 py-2.5 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary-500/50">
                            {Array.from({ length: 24 }, (_, i) => (
                              <option key={i} value={i}>{String(i).padStart(2, '0')}</option>
                            ))}
                          </select>
                        </div>
                        <div className="space-y-2 min-w-[6rem]">
                          <label className="text-sm font-medium text-[var(--text-secondary)] block">Minutes</label>
                          <select value={publishScheduleMinute} onChange={(e) => onPublishScheduleMinuteChange(Number(e.target.value) as ScheduleMinute)} className="w-full px-4 py-2.5 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary-500/50">
                            {SCHEDULE_MINUTES.map((m) => (
                              <option key={m} value={m}>{String(m).padStart(2, '0')}</option>
                            ))}
                          </select>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="space-y-4 pt-4 border-t border-[var(--border-color)]">
                    {availableChannels.length > 0 ? (
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-[var(--text-secondary)] block">Channels to Post</label>
                        <div className="space-y-2 max-h-48 overflow-y-auto">
                          {availableChannels.map((ch) => {
                            const idStr = channelIdToString(ch.id)
                            return (
                              <label key={ch.id} className="flex items-center gap-2 cursor-pointer text-sm">
                                <input type="checkbox" checked={channelsToPost.includes(idStr)} onChange={() => toggleChannelToPost(idStr)} className="w-4 h-4 text-primary-500 rounded" />
                                <span className="font-mono text-xs">{idStr}</span>
                                <span className="text-[var(--text-muted)]">: {ch.title}</span>
                              </label>
                            )
                          })}
                        </div>
                      </div>
                    ) : (
                      <Input label="Channel to Post" type="text" value={channelToPost} onChange={(e) => onChannelToPostChange(e.target.value)} placeholder="e.g., -1002009872429" />
                    )}
                    {availableChannels.length > 0 && channelsToPost.length === 0 && (
                      <Input label="Channel to Post (fallback)" type="text" value={channelToPost} onChange={(e) => onChannelToPostChange(e.target.value)} placeholder="e.g., -1002009872429" />
                    )}
                  </div>
                </div>
              )}
            </div>

            <div className="space-y-4 pt-4 border-t border-[var(--border-color)]">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
                Collection (Parser)
              </h3>
              <label className="flex items-center gap-3 cursor-pointer group">
                <div className="relative">
                  <input type="checkbox" checked={collectEnabled} onChange={(e) => onCollectEnabledChange(e.target.checked)} className="sr-only peer" />
                  <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                  <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                </div>
                <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">Enable collection</span>
              </label>

              {collectEnabled && (
                <div className="space-y-6 animate-slide-down">
                  <p className="text-sm text-[var(--text-muted)]">Учётные данные API задаются на вкладке «Авторизация». Здесь настраиваются чаты для чтения.</p>
                  <div className="p-4 bg-[var(--bg-secondary)] rounded-xl space-y-4 border border-[var(--border-color)]">
                    <h4 className="text-sm font-semibold text-[var(--text-primary)]">Chats to Read</h4>
                    {chatsToRead.map((field) => (
                      <div key={field.id} className="flex gap-3">
                        <Input placeholder="e.g., -01001677806302" value={field.value} onChange={(e) => onUpdateField(setChatsToRead, field.id, e.target.value)} className="flex-1" />
                        {chatsToRead.length > 1 && (
                          <Button type="button" variant="ghost" size="sm" onClick={() => onRemoveField(setChatsToRead, field.id)} className="px-3 text-red-400 hover:text-red-300">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                          </Button>
                        )}
                      </div>
                    ))}
                    <Button type="button" variant="secondary" size="sm" onClick={() => onAddField(setChatsToRead)}>
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
                      Add Chat
                    </Button>
                  </div>

                  <div className="p-4 bg-[var(--bg-secondary)] rounded-xl space-y-4 border border-[var(--border-color)]">
                    <h4 className="text-sm font-semibold text-[var(--text-primary)]">Save Conditions</h4>
                    {saveConditions.map((field) => (
                      <div key={field.id} className="flex gap-3">
                        <Input placeholder="Enter condition (e.g., contains keyword)" value={field.value} onChange={(e) => onUpdateField(setSaveConditions, field.id, e.target.value)} className="flex-1" />
                        {saveConditions.length > 1 && (
                          <Button type="button" variant="ghost" size="sm" onClick={() => onRemoveField(setSaveConditions, field.id)} className="px-3 text-red-400 hover:text-red-300">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                          </Button>
                        )}
                      </div>
                    ))}
                    <Button type="button" variant="secondary" size="sm" onClick={() => onAddField(setSaveConditions)}>
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
                      Add Condition
                    </Button>
                  </div>
                </div>
              )}
            </div>

            <div className="space-y-4 pt-4 border-t border-[var(--border-color)]">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                Alerting
              </h3>
              <label className="flex items-center gap-3 cursor-pointer group">
                <div className="relative">
                  <input type="checkbox" checked={alertEnabled} onChange={(e) => onAlertEnabledChange(e.target.checked)} className="sr-only peer" />
                  <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                  <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                </div>
                <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">Enable alerting</span>
              </label>

              {alertEnabled && (
                <div className="space-y-4 animate-slide-down">
                  <p className="text-sm text-[var(--text-muted)]">
                    При совпадении Save Conditions в мониторинговых чатах отправляется оповещение в Channel to Post
                    с ID канала-источника, текстом сообщения и заданным текстом алерта.
                  </p>
                  {recentAlerts.length > 0 && (
                    <div className="p-4 bg-[var(--bg-secondary)] rounded-xl border border-[var(--border-color)]">
                      <h5 className="text-sm font-semibold mb-2">Recent alert events</h5>
                      <ul className="text-xs space-y-1 text-[var(--text-muted)]">
                        {recentAlerts.slice(0, 10).map((item, idx) => (
                          <li key={`${item.created_at}-${idx}`}>
                            {item.event_type} · rule {item.rule_id || '—'} · {item.created_at}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {alertRules.map((rule, ruleIndex) => (
                    <div key={rule.id} className="p-4 bg-[var(--bg-secondary)] rounded-xl space-y-4 border border-[var(--border-color)]">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <h4 className="text-sm font-semibold text-[var(--text-primary)]">Rule {ruleIndex + 1}</h4>
                        <div className="flex items-center gap-3">
                          <label className="flex items-center gap-2 cursor-pointer text-sm text-[var(--text-secondary)]">
                            <input type="checkbox" checked={rule.enabled} onChange={(e) => onUpdateAlertRule(rule.id, { enabled: e.target.checked })} className="w-4 h-4 text-primary-500" />
                            Enabled
                          </label>
                          {alertRules.length > 1 && (
                            <Button type="button" variant="ghost" size="sm" onClick={() => onRemoveAlertRule(rule.id)} className="text-red-400 hover:text-red-300">Remove rule</Button>
                          )}
                        </div>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div>
                          <label className="text-xs text-[var(--text-muted)]">Priority</label>
                          <Input type="number" value={rule.priority} onChange={(e) => onUpdateAlertRule(rule.id, { priority: Number(e.target.value) || 0 })} />
                        </div>
                        <div>
                          <label className="text-xs text-[var(--text-muted)]">Conditions mode</label>
                          <select value={rule.conditionsMode} onChange={(e) => onUpdateAlertRule(rule.id, { conditionsMode: e.target.value as ConditionsMode })} className="w-full px-3 py-2 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-lg">
                            <option value="any_of">Any (OR)</option>
                            <option value="all_of">All (AND)</option>
                            <option value="regex">Regex</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-xs text-[var(--text-muted)]">Dedup window (sec)</label>
                          <Input type="number" value={rule.dedupWindowSec} onChange={(e) => onUpdateAlertRule(rule.id, { dedupWindowSec: Number(e.target.value) || 0 })} />
                        </div>
                        <div>
                          <label className="text-xs text-[var(--text-muted)]">Rate limit / hour</label>
                          <Input placeholder="optional" value={rule.rateLimitPerHour} onChange={(e) => onUpdateAlertRule(rule.id, { rateLimitPerHour: e.target.value })} />
                        </div>
                        <div>
                          <label className="text-xs text-[var(--text-muted)]">Category filter</label>
                          <Input placeholder="optional" value={rule.categoryFilter} onChange={(e) => onUpdateAlertRule(rule.id, { categoryFilter: e.target.value })} />
                        </div>
                        <div>
                          <label className="text-xs text-[var(--text-muted)]">Sentiment filter</label>
                          <select value={rule.sentimentFilter} onChange={(e) => onUpdateAlertRule(rule.id, { sentimentFilter: e.target.value as SentimentFilter | '' })} className="w-full px-3 py-2 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-lg">
                            <option value="">None</option>
                            <option value="positive">Positive</option>
                            <option value="negative">Negative</option>
                            <option value="neutral">Neutral</option>
                          </select>
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-4">
                        <label className="flex items-center gap-2 text-sm">
                          <input type="checkbox" checked={rule.includeAiSummary} onChange={(e) => onUpdateAlertRule(rule.id, { includeAiSummary: e.target.checked })} />
                          AI summary in alert
                        </label>
                        <label className="flex items-center gap-2 text-sm">
                          <input type="checkbox" checked={rule.stopOnMatch} onChange={(e) => onUpdateAlertRule(rule.id, { stopOnMatch: e.target.checked })} />
                          Stop on match
                        </label>
                      </div>

                      <div className="space-y-3">
                        <h5 className="text-sm font-medium text-[var(--text-secondary)]">Chats to Read</h5>
                        {rule.chatsToRead.map((field) => (
                          <div key={field.id} className="flex gap-3">
                            <Input placeholder="e.g., -1002009872429" value={field.value} onChange={(e) => onUpdateAlertRuleField(rule.id, 'chatsToRead', field.id, e.target.value)} className="flex-1" />
                            {rule.chatsToRead.length > 1 && (
                              <Button type="button" variant="ghost" size="sm" onClick={() => onRemoveAlertRuleField(rule.id, 'chatsToRead', field.id)} className="px-3 text-red-400 hover:text-red-300">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                              </Button>
                            )}
                          </div>
                        ))}
                        <Button type="button" variant="secondary" size="sm" disabled={rule.chatsToRead.length >= MAX_ALERT_LIST_ITEMS} onClick={() => onAddAlertRuleField(rule.id, 'chatsToRead')}>Add Chat</Button>
                      </div>

                      <div className="space-y-3">
                        <h5 className="text-sm font-medium text-[var(--text-secondary)]">Save Conditions</h5>
                        {rule.saveConditions.map((field) => (
                          <div key={field.id} className="flex gap-3">
                            <Input placeholder="Enter condition (e.g., contains keyword)" value={field.value} onChange={(e) => onUpdateAlertRuleField(rule.id, 'saveConditions', field.id, e.target.value)} className="flex-1" />
                            {rule.saveConditions.length > 1 && (
                              <Button type="button" variant="ghost" size="sm" onClick={() => onRemoveAlertRuleField(rule.id, 'saveConditions', field.id)} className="px-3 text-red-400 hover:text-red-300">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                              </Button>
                            )}
                          </div>
                        ))}
                        <Button type="button" variant="secondary" size="sm" disabled={rule.saveConditions.length >= MAX_ALERT_LIST_ITEMS} onClick={() => onAddAlertRuleField(rule.id, 'saveConditions')}>Add Condition</Button>
                      </div>

                      <Input label="Channel to Post" type="text" value={rule.channelToPost} onChange={(e) => onUpdateAlertRule(rule.id, { channelToPost: e.target.value })} placeholder="e.g., -1002009872429" />

                      <div>
                        <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">Alert text</label>
                        <textarea value={rule.alertText} onChange={(e) => onUpdateAlertRule(rule.id, { alertText: e.target.value.slice(0, 1000) })} rows={3} maxLength={1000} className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all" placeholder="Текст оповещения..." />
                        <p className="text-xs text-[var(--text-muted)] mt-2">{rule.alertText.length} / 1000 characters</p>
                      </div>
                    </div>
                  ))}
                  <Button type="button" variant="secondary" size="sm" disabled={alertRules.length >= MAX_ALERT_RULES} onClick={onAddAlertRule}>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
                    Add rule
                  </Button>
                </div>
              )}
            </div>

            <CardFooter className="px-0">
              <Button type="submit" isLoading={isSavingProfile} className="w-full sm:w-auto">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                Save Profile Settings
              </Button>
            </CardFooter>
          </form>
        )}
      </CardContent>
    </Card>
  )
}
