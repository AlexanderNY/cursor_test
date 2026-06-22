import { useState, FormEvent, Fragment, useEffect, useRef, type ReactNode } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import { TableSkeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/ui'
import { TipTapEditor } from '@/components/ui/tiptap-editor'
import { authService } from '@/services/auth-service'
import { useAuth } from '@/contexts/auth-context'
import { coreService } from '@/services/core-service'
import { notificationsService } from '@/services/notifications-service'
import { feedbackService } from '@/services/feedback-service'
import { Input } from '@/components/ui/input'
import type { User, RoleTariffHistoryEntry, GroupResponse, AdminAuditLogEntry } from '@/types/auth'
import type {
  UserStatisticsItem,
  ScheduleSnapshot,
  Notification,
  Feedback,
  ServicesStatusResponse,
  PostsTablesResponse,
  PlatformMetric,
  PostRow,
  PostingDiagnosticsResponse,
  StorageFileItem,
  StorageFilesResponse,
  RuntimeLocationResponse,
} from '@/types/core'
import { FEEDBACK_TYPE_LABELS } from '@/types/core'

type AdminTab = 'users' | 'audit' | 'groups' | 'statistics' | 'schedule' | 'notifications' | 'feedback' | 'services-status' | 'processor' | 'collector' | 'scheduler' | 'posts-tables' | 'posting-diagnostics' | 'runtime-location' | 'storage'

/** Платформы для «Принудительный запуск ботов» (совпадает с scheduler BOT_PLATFORMS). */
const SCHEDULE_BOT_PLATFORMS = [
  'wp',
  'tg',
  'tw',
  'vk',
  'url',
  'threads',
  'dzen',
  'instagram',
] as const

/** Типичные статусы строк в таблицах *_posts; редкие из БД добавляются колонками справа. */
const PLATFORM_TABLE_STATUS_ORDER: readonly string[] = [
  'collected',
  'created',
  'processing',
  'ready',
  'review',
  'published',
  'failed',
  'skipped',
]

function platformTableStatusColumns(platforms: PlatformMetric[]): string[] {
  const extra = new Set<string>()
  for (const p of platforms) {
    const sc = p.status_counts
    if (!sc) continue
    for (const k of Object.keys(sc)) {
      if (!PLATFORM_TABLE_STATUS_ORDER.includes(k)) {
        extra.add(k)
      }
    }
  }
  return [...PLATFORM_TABLE_STATUS_ORDER, ...Array.from(extra).sort()]
}

function platformStatusCell(p: PlatformMetric, col: string): number {
  const sc = p.status_counts
  if (sc && Object.prototype.hasOwnProperty.call(sc, col)) {
    return Number(sc[col] ?? 0)
  }
  if (col === 'collected') return p.collected_count ?? 0
  if (col === 'created') return p.created_count ?? 0
  if (col === 'ready') return p.ready_count ?? 0
  if (col === 'processing') return p.processing_count ?? 0
  return 0
}

/** Не перезапрашивать те же данные при переключении вкладок чаще этого интервала (мс). */
const STALE_SERVICES_STATUS_MS = 30_000
const STALE_POSTS_TABLES_MS = 60_000

export function AdministrationPage() {
  const { user: currentUser } = useAuth()
  const [activeTab, setActiveTab] = useState<AdminTab>('users')
  const lastServicesStatusLoadedAt = useRef<number | null>(null)
  const lastPostsTablesLoadedAt = useRef<number | null>(null)
  const [users, setUsers] = useState<User[]>([])
  const [statistics, setStatistics] = useState<UserStatisticsItem[]>([])
  const [schedules, setSchedules] = useState<ScheduleSnapshot[]>([])
  const [isLoadingUsers, setIsLoadingUsers] = useState(false)
  const [isLoadingStatistics, setIsLoadingStatistics] = useState(false)
  const [isLoadingSchedule, setIsLoadingSchedule] = useState(false)
  const [isStartingDiscovery, setIsStartingDiscovery] = useState(false)
  const [isStartingBot, setIsStartingBot] = useState(false)
  const [usersError, setUsersError] = useState('')
  const [savingUserId, setSavingUserId] = useState<number | null>(null)
  const [blockingUserId, setBlockingUserId] = useState<number | null>(null)
  const [userUpdateError, setUserUpdateError] = useState('')
  const [expandedHistoryUserId, setExpandedHistoryUserId] = useState<number | null>(null)
  const [historyList, setHistoryList] = useState<RoleTariffHistoryEntry[]>([])
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [historyError, setHistoryError] = useState('')
  const ROLES = ['guest', 'user', 'admin', 'manager', 'author'] as const
  const TARIFFS = ['free', 'basic', 'premium']
  const SUBSCRIPTION_STATUS_FILTERS: { value: string; label: string }[] = [
    { value: '', label: 'All statuses' },
    { value: '__null__', label: 'No status' },
    { value: 'active', label: 'active' },
    { value: 'past_due', label: 'past_due' },
    { value: 'canceled', label: 'canceled' },
    { value: 'unpaid', label: 'unpaid' },
    { value: 'trialing', label: 'trialing' },
  ]
  const [userFilterTariff, setUserFilterTariff] = useState('')
  const [userFilterSubscriptionStatus, setUserFilterSubscriptionStatus] = useState('')
  const [auditLog, setAuditLog] = useState<AdminAuditLogEntry[]>([])
  const [isLoadingAudit, setIsLoadingAudit] = useState(false)
  const [auditError, setAuditError] = useState('')
  const [statisticsError, setStatisticsError] = useState('')
  const [scheduleError, setScheduleError] = useState('')
  const [discoveryMessage, setDiscoveryMessage] = useState('')
  const [botMessage, setBotMessage] = useState('')
  const [selectedBots, setSelectedBots] = useState<{ [key: string]: boolean }>(() =>
    Object.fromEntries(SCHEDULE_BOT_PLATFORMS.map((p) => [p, false]))
  )

  // Notifications state
  const [notificationMessage, setNotificationMessage] = useState('')
  const [isCreatingNotification, setIsCreatingNotification] = useState(false)
  const [notificationError, setNotificationError] = useState('')
  const [notificationSuccess, setNotificationSuccess] = useState('')
  const [notificationsList, setNotificationsList] = useState<Notification[]>([])
  const [isLoadingNotifications, setIsLoadingNotifications] = useState(false)
  const [isDeletingNotification, setIsDeletingNotification] = useState<number | null>(null)

  // Feedback state
  const [feedbackList, setFeedbackList] = useState<Feedback[]>([])
  const [isLoadingFeedback, setIsLoadingFeedback] = useState(false)
  const [feedbackError, setFeedbackError] = useState('')
  const [isDeletingFeedback, setIsDeletingFeedback] = useState<number | null>(null)

  // Services status & Posts tables (admin)
  const [servicesStatus, setServicesStatus] = useState<ServicesStatusResponse | null>(null)
  const [postsTables, setPostsTables] = useState<PostsTablesResponse | null>(null)
  const [isLoadingServicesStatus, setIsLoadingServicesStatus] = useState(false)
  const [isLoadingPostsTables, setIsLoadingPostsTables] = useState(false)
  const [servicesStatusError, setServicesStatusError] = useState('')
  const [postsTablesError, setPostsTablesError] = useState('')
  const [isRunningProcessor, setIsRunningProcessor] = useState(false)
  const [processorRunMessage, setProcessorRunMessage] = useState('')
  const [processorRunError, setProcessorRunError] = useState('')

  // Full posts table (admin)
  const [postsList, setPostsList] = useState<PostRow[]>([])
  const [isLoadingPostsList, setIsLoadingPostsList] = useState(false)
  const [postsListError, setPostsListError] = useState('')

  // Posting diagnostics (admin)
  const [postingDiagnostics, setPostingDiagnostics] = useState<PostingDiagnosticsResponse | null>(null)
  const [isLoadingPostingDiagnostics, setIsLoadingPostingDiagnostics] = useState(false)
  const [postingDiagnosticsError, setPostingDiagnosticsError] = useState('')
  const [isRunningCollect, setIsRunningCollect] = useState(false)
  const [collectMessage, setCollectMessage] = useState('')
  const [collectError, setCollectError] = useState('')
  const [isRunningDistribute, setIsRunningDistribute] = useState(false)
  const [distributeMessage, setDistributeMessage] = useState('')
  const [distributeError, setDistributeError] = useState('')

  // S3 storage files (admin)
  const [storageFiles, setStorageFiles] = useState<StorageFilesResponse | null>(null)
  const [storagePrefix, setStoragePrefix] = useState('')
  const [storageDiagOnly, setStorageDiagOnly] = useState(false)
  const [isLoadingStorageFiles, setIsLoadingStorageFiles] = useState(false)
  const [storageFilesError, setStorageFilesError] = useState('')
  const [storageDeletingKey, setStorageDeletingKey] = useState<string | null>(null)
  const [storageOpeningKey, setStorageOpeningKey] = useState<string | null>(null)

  const [runtimeLocation, setRuntimeLocation] = useState<RuntimeLocationResponse | null>(null)
  const [isLoadingRuntimeLocation, setIsLoadingRuntimeLocation] = useState(false)
  const [runtimeLocationError, setRuntimeLocationError] = useState('')

  const [groupsList, setGroupsList] = useState<GroupResponse[]>([])
  const [isLoadingGroups, setIsLoadingGroups] = useState(false)
  const [groupsError, setGroupsError] = useState('')
  const [newGroupName, setNewGroupName] = useState('')
  const [newGroupDescription, setNewGroupDescription] = useState('')
  const [isCreatingGroup, setIsCreatingGroup] = useState(false)
  const [addMemberForms, setAddMemberForms] = useState<
    Record<number, { email: string; role: 'manager' | 'author' }>
  >({})
  const [addingToGroupId, setAddingToGroupId] = useState<number | null>(null)
  const [removingMemberKey, setRemovingMemberKey] = useState<string | null>(null)

  async function handleLoadUsers() {
    setUsersError('')
    setUserUpdateError('')
    setIsLoadingUsers(true)
    try {
      const data = await authService.getUsers({
        tariff: userFilterTariff || undefined,
        subscription_status: userFilterSubscriptionStatus || undefined,
      })
      setUsers(data)
    } catch (error) {
      setUsersError(error instanceof Error ? error.message : 'Failed to fetch users')
      setUsers([])
    } finally {
      setIsLoadingUsers(false)
    }
  }

  async function handleExportUsersCsv() {
    setUsersError('')
    try {
      await authService.exportUsersCsv({
        tariff: userFilterTariff || undefined,
        subscription_status: userFilterSubscriptionStatus || undefined,
      })
    } catch (error) {
      setUsersError(error instanceof Error ? error.message : 'Export failed')
    }
  }

  async function handleLoadAuditLog() {
    setAuditError('')
    setIsLoadingAudit(true)
    try {
      const data = await authService.getAdminAuditLog(200)
      setAuditLog(data)
    } catch (error) {
      setAuditError(error instanceof Error ? error.message : 'Failed to load audit log')
      setAuditLog([])
    } finally {
      setIsLoadingAudit(false)
    }
  }

  async function handleLoadGroups() {
    setGroupsError('')
    setIsLoadingGroups(true)
    try {
      const data = await authService.getAllGroups()
      setGroupsList(data)
    } catch (error) {
      setGroupsError(error instanceof Error ? error.message : 'Failed to fetch groups')
      setGroupsList([])
    } finally {
      setIsLoadingGroups(false)
    }
  }

  async function handleCreateGroupAdmin(e: FormEvent) {
    e.preventDefault()
    if (!newGroupName.trim()) return
    setGroupsError('')
    setIsCreatingGroup(true)
    try {
      const created = await authService.createGroupAsAdmin(newGroupName.trim(), newGroupDescription.trim())
      setGroupsList((prev) => [...prev, created].sort((a, b) => a.name.localeCompare(b.name)))
      setNewGroupName('')
      setNewGroupDescription('')
    } catch (error) {
      setGroupsError(error instanceof Error ? error.message : 'Failed to create group')
    } finally {
      setIsCreatingGroup(false)
    }
  }

  function getMemberForm(groupId: number) {
    return addMemberForms[groupId] ?? { email: '', role: 'author' as const }
  }

  function setMemberForm(
    groupId: number,
    patch: Partial<{ email: string; role: 'manager' | 'author' }>
  ) {
    setAddMemberForms((prev) => ({
      ...prev,
      [groupId]: { ...getMemberForm(groupId), ...patch },
    }))
  }

  async function handleAddMemberToGroup(group: GroupResponse) {
    const form = getMemberForm(group.id)
    const email = form.email.trim()
    if (!email) return
    const isEmpty = !group.members || group.members.length === 0
    const role = isEmpty ? 'manager' : form.role
    setGroupsError('')
    setAddingToGroupId(group.id)
    try {
      await authService.addGroupMember(group.id, email, role)
      await handleLoadGroups()
      setMemberForm(group.id, { email: '' })
    } catch (error) {
      setGroupsError(error instanceof Error ? error.message : 'Failed to add member')
    } finally {
      setAddingToGroupId(null)
    }
  }

  async function handleRemoveGroupMember(groupId: number, userId: number) {
    setGroupsError('')
    setRemovingMemberKey(`${groupId}-${userId}`)
    try {
      await authService.removeGroupMember(groupId, userId)
      await handleLoadGroups()
    } catch (error) {
      setGroupsError(error instanceof Error ? error.message : 'Failed to remove member')
    } finally {
      setRemovingMemberKey(null)
    }
  }

  function updateUserInList(userId: number, patch: Partial<Pick<User, 'role' | 'tariff'>>) {
    setUsers((prev) =>
      prev.map((u) => (u.id === userId ? { ...u, ...patch } : u))
    )
  }

  async function handleSaveUser(user: User) {
    if (user.id == null) return
    setUserUpdateError('')
    setSavingUserId(user.id)
    try {
      const updated = await authService.updateUser(user.id, {
        role: user.role,
        tariff: user.tariff ?? 'free',
      })
      setUsers((prev) =>
        prev.map((u) => (u.id === user.id ? { ...u, ...updated } : u))
      )
    } catch (error) {
      setUserUpdateError(error instanceof Error ? error.message : 'Failed to update user')
    } finally {
      setSavingUserId(null)
    }
  }

  async function handleSetUserBlocked(user: User, blocked: boolean) {
    if (user.id == null) return
    if (blocked && currentUser?.id === user.id) {
      setUserUpdateError('Нельзя заблокировать собственную учётную запись')
      return
    }
    setUserUpdateError('')
    setBlockingUserId(user.id)
    try {
      const updated = await authService.updateUser(user.id, { is_blocked: blocked })
      setUsers((prev) =>
        prev.map((u) => (u.id === user.id ? { ...u, ...updated } : u))
      )
    } catch (error) {
      setUserUpdateError(error instanceof Error ? error.message : 'Failed to update block status')
    } finally {
      setBlockingUserId(null)
    }
  }

  async function handleToggleHistory(userId: number) {
    if (expandedHistoryUserId === userId) {
      setExpandedHistoryUserId(null)
      return
    }
    setExpandedHistoryUserId(userId)
    setHistoryError('')
    setIsLoadingHistory(true)
    try {
      const data = await authService.getRoleTariffHistory(userId)
      setHistoryList(data)
    } catch (error) {
      setHistoryError(error instanceof Error ? error.message : 'Failed to load history')
      setHistoryList([])
    } finally {
      setIsLoadingHistory(false)
    }
  }

  async function handleLoadStatistics() {
    setStatisticsError('')
    setIsLoadingStatistics(true)
    try {
      const response = await coreService.getUsersStatistics()
      setStatistics(response.users || [])
    } catch (error) {
      setStatisticsError(error instanceof Error ? error.message : 'Failed to fetch statistics')
      setStatistics([])
    } finally {
      setIsLoadingStatistics(false)
    }
  }

  async function handleLoadSchedule() {
    setScheduleError('')
    setIsLoadingSchedule(true)
    try {
      const response = await coreService.getSchedule()
      setSchedules(response.schedules || [])
    } catch (error) {
      setScheduleError(error instanceof Error ? error.message : 'Failed to fetch schedule')
      setSchedules([])
    } finally {
      setIsLoadingSchedule(false)
    }
  }

  async function handleStartDiscovery() {
    setDiscoveryMessage('')
    setScheduleError('')
    setIsStartingDiscovery(true)
    try {
      const response = await coreService.startDiscovery()
      setDiscoveryMessage(response.message + (response.changed ? ' (Changes detected)' : ' (No changes)'))
    } catch (error) {
      setScheduleError(error instanceof Error ? error.message : 'Failed to start discovery')
      setDiscoveryMessage('')
    } finally {
      setIsStartingDiscovery(false)
    }
  }

  async function handleStartBot() {
    const selectedPlatforms = Object.entries(selectedBots)
      .filter(([_, selected]) => selected)
      .map(([platform]) => platform)
    
    if (selectedPlatforms.length === 0) {
      setBotMessage('Please select at least one bot')
      return
    }

    setBotMessage('')
    setScheduleError('')
    setIsStartingBot(true)
    try {
      const response = await coreService.startBot(selectedPlatforms)
      const results = Object.entries(response.results || {})
        .map(([platform, result]: [string, any]) => 
          `${platform}: ${result.status === 'success' ? 'Success' : 'Error'}`
        )
        .join(', ')
      setBotMessage(`Bots started: ${results}`)
    } catch (error) {
      setScheduleError(error instanceof Error ? error.message : 'Failed to start bots')
      setBotMessage('')
    } finally {
      setIsStartingBot(false)
    }
  }

  function handleBotToggle(platform: string) {
    setSelectedBots(prev => ({
      ...prev,
      [platform]: !prev[platform]
    }))
  }

  async function handleCreateNotification(e: FormEvent) {
    e.preventDefault()
    setNotificationError('')
    setNotificationSuccess('')
    setIsCreatingNotification(true)

    // TipTap returns <p></p> for empty content
    const strippedMessage = notificationMessage.replace(/<[^>]*>/g, '').trim()
    if (!strippedMessage) {
      setNotificationError('Message cannot be empty')
      setIsCreatingNotification(false)
      return
    }

    try {
      await notificationsService.createNotification({ message: notificationMessage })
      setNotificationSuccess('Notification created successfully')
      setNotificationMessage('')
    } catch (error) {
      setNotificationError(error instanceof Error ? error.message : 'Failed to create notification')
    } finally {
      setIsCreatingNotification(false)
    }
  }

  async function loadNotifications() {
    setIsLoadingNotifications(true)
    try {
      const response = await notificationsService.getNotifications()
      setNotificationsList(response.notifications || [])
    } catch (error) {
      console.error('Failed to load notifications:', error)
      setNotificationsList([])
    } finally {
      setIsLoadingNotifications(false)
    }
  }

  async function handleDeleteNotification(notificationId: number) {
    setIsDeletingNotification(notificationId)
    try {
      await notificationsService.deleteNotification(notificationId)
      setNotificationsList(prev => prev.filter(n => n.id !== notificationId))
      setNotificationSuccess('Notification deleted successfully')
    } catch (error) {
      setNotificationError(error instanceof Error ? error.message : 'Failed to delete notification')
    } finally {
      setIsDeletingNotification(null)
    }
  }

  async function loadFeedback() {
    setIsLoadingFeedback(true)
    setFeedbackError('')
    try {
      const response = await feedbackService.getFeedbackList()
      setFeedbackList(response.feedback || [])
    } catch (error) {
      setFeedbackError(error instanceof Error ? error.message : 'Failed to load feedback')
      setFeedbackList([])
    } finally {
      setIsLoadingFeedback(false)
    }
  }

  async function handleDeleteFeedback(feedbackId: number) {
    if (!window.confirm('Удалить эту запись обратной связи?')) {
      return
    }

    setIsDeletingFeedback(feedbackId)
    setFeedbackError('')
    try {
      await feedbackService.deleteFeedback(feedbackId)
      setFeedbackList(prev => prev.filter(item => item.id !== feedbackId))
    } catch (error) {
      setFeedbackError(error instanceof Error ? error.message : 'Failed to delete feedback')
    } finally {
      setIsDeletingFeedback(null)
    }
  }

  async function handleLoadServicesStatus() {
    setServicesStatusError('')
    setIsLoadingServicesStatus(true)
    try {
      const data = await coreService.getServicesStatus()
      setServicesStatus(data)
      lastServicesStatusLoadedAt.current = Date.now()
    } catch (error) {
      setServicesStatusError(error instanceof Error ? error.message : 'Failed to fetch services status')
      setServicesStatus(null)
    } finally {
      setIsLoadingServicesStatus(false)
    }
  }

  async function handleRunProcessorCycle() {
    setProcessorRunMessage('')
    setProcessorRunError('')
    setIsRunningProcessor(true)
    try {
      const data = await coreService.runProcessorCycle()
      if (data.status === 'success') {
        setProcessorRunMessage(`Обработано постов: ${data.count}. ${data.message}`)
        lastPostsTablesLoadedAt.current = null
        await handleLoadServicesStatus()
      } else {
        setProcessorRunError(data.message || 'Processor cycle failed')
      }
    } catch (error) {
      setProcessorRunError(error instanceof Error ? error.message : 'Failed to run processor cycle')
    } finally {
      setIsRunningProcessor(false)
    }
  }

  async function handleLoadPostsTables() {
    setPostsTablesError('')
    setIsLoadingPostsTables(true)
    try {
      const data = await coreService.getPostsTablesOverview()
      setPostsTables(data)
      lastPostsTablesLoadedAt.current = Date.now()
    } catch (error) {
      setPostsTablesError(error instanceof Error ? error.message : 'Failed to fetch posts tables')
      setPostsTables(null)
    } finally {
      setIsLoadingPostsTables(false)
    }
  }

  async function handleRunPostingDiagnostics() {
    setPostingDiagnosticsError('')
    setPostingDiagnostics(null)
    setIsLoadingPostingDiagnostics(true)
    try {
      const data = await coreService.getPostingDiagnostics()
      setPostingDiagnostics(data)
    } catch (error) {
      setPostingDiagnosticsError(error instanceof Error ? error.message : 'Failed to run posting diagnostics')
      setPostingDiagnostics(null)
    } finally {
      setIsLoadingPostingDiagnostics(false)
    }
  }

  async function handleRunCollectCycle() {
    setCollectError('')
    setCollectMessage('')
    setIsRunningCollect(true)
    try {
      const data = await coreService.runCollectCycle()
      if (data.status === 'success') {
        setCollectMessage(`Собрано постов: ${data.count}. ${data.message}`)
        lastPostsTablesLoadedAt.current = null
        await handleRunPostingDiagnostics()
      } else if (data.status === 'partial') {
        setCollectMessage(`Собрано постов: ${data.count}. ${data.message}`)
        if (data.errors?.length) setCollectError(data.errors.join('; '))
        lastPostsTablesLoadedAt.current = null
        await handleRunPostingDiagnostics()
      } else {
        setCollectError(data.message || 'Ошибка цикла сбора')
        if (data.errors?.length) setCollectError((prev) => prev + '\n' + data.errors!.join('\n'))
      }
    } catch (error) {
      setCollectError(error instanceof Error ? error.message : 'Ошибка запуска сбора')
    } finally {
      setIsRunningCollect(false)
    }
  }

  async function handleRunDistributeCycle() {
    setDistributeError('')
    setDistributeMessage('')
    setIsRunningDistribute(true)
    try {
      const data = await coreService.runDistributeCycle()
      if (data.status === 'success') {
        setDistributeMessage(`Распределено постов: ${data.count}. ${data.message}`)
        lastPostsTablesLoadedAt.current = null
        await handleRunPostingDiagnostics()
      } else {
        setDistributeError(data.message || 'Ошибка цикла распределения')
      }
    } catch (error) {
      setDistributeError(error instanceof Error ? error.message : 'Ошибка запуска распределения')
    } finally {
      setIsRunningDistribute(false)
    }
  }

  async function handleLoadStorageFiles() {
    setStorageFilesError('')
    setIsLoadingStorageFiles(true)
    try {
      const data = await coreService.getStorageFiles({
        prefix: storagePrefix.trim() || undefined,
        limit: 500,
        ...(storageDiagOnly ? { key_contains: 'diag' } : {}),
      })
      setStorageFiles(data)
    } catch (error) {
      setStorageFilesError(error instanceof Error ? error.message : 'Failed to fetch storage files')
      setStorageFiles(null)
    } finally {
      setIsLoadingStorageFiles(false)
    }
  }

  async function handleOpenStorageFile(key: string) {
    setStorageFilesError('')
    setStorageOpeningKey(key)
    try {
      const { url } = await coreService.getStoragePresignedUrl(key)
      window.open(url, '_blank', 'noopener,noreferrer')
    } catch (error) {
      setStorageFilesError(error instanceof Error ? error.message : 'Не удалось открыть файл')
    } finally {
      setStorageOpeningKey(null)
    }
  }

  async function handleDeleteStorageFile(key: string) {
    const ok = window.confirm(
      `Удалить объект из S3? Это действие необратимо.\n\n${key}`
    )
    if (!ok) return
    setStorageFilesError('')
    setStorageDeletingKey(key)
    try {
      await coreService.deleteStorageFile(key)
      setStorageFiles((prev) => {
        if (!prev?.enabled) return prev
        return {
          ...prev,
          objects: prev.objects.filter((o) => o.key !== key),
        }
      })
    } catch (error) {
      setStorageFilesError(error instanceof Error ? error.message : 'Не удалось удалить файл')
    } finally {
      setStorageDeletingKey(null)
    }
  }

  async function handleLoadRuntimeLocation() {
    setRuntimeLocationError('')
    setIsLoadingRuntimeLocation(true)
    try {
      const data = await coreService.getRuntimeLocation()
      setRuntimeLocation(data)
    } catch (error) {
      setRuntimeLocationError(error instanceof Error ? error.message : 'Failed to fetch runtime location')
      setRuntimeLocation(null)
    } finally {
      setIsLoadingRuntimeLocation(false)
    }
  }

  async function handleLoadPostsList() {
    setPostsListError('')
    setIsLoadingPostsList(true)
    try {
      const data = await coreService.getPostsList(500, 0)
      setPostsList(data.posts)
    } catch (error) {
      setPostsListError(error instanceof Error ? error.message : 'Failed to fetch posts list')
      setPostsList([])
    } finally {
      setIsLoadingPostsList(false)
    }
  }

  // Подгрузка при открытии вкладок инфраструктуры: без лишних запросов, пока кэш не устарел
  useEffect(() => {
    if (activeTab !== 'processor' && activeTab !== 'collector' && activeTab !== 'scheduler') {
      return
    }
    const now = Date.now()
    const servicesStale =
      lastServicesStatusLoadedAt.current === null ||
      now - lastServicesStatusLoadedAt.current > STALE_SERVICES_STATUS_MS
    if (servicesStale) {
      void handleLoadServicesStatus()
    }
    if (activeTab === 'processor' || activeTab === 'collector') {
      const postsStale =
        lastPostsTablesLoadedAt.current === null ||
        now - lastPostsTablesLoadedAt.current > STALE_POSTS_TABLES_MS
      if (postsStale) {
        void handleLoadPostsTables()
      }
    }
  }, [activeTab])

  useEffect(() => {
    if (activeTab === 'feedback') {
      void loadFeedback()
    }
  }, [activeTab])

  const POSTS_TABLE_COLUMNS: { key: keyof PostRow; label: string }[] = [
    { key: 'id', label: 'ID' },
    { key: 'user_id', label: 'User ID' },
    { key: 'domain', label: 'Domain' },
    { key: 'url', label: 'URL' },
    { key: 'title', label: 'Title' },
    { key: 'author', label: 'Author' },
    { key: 'avatar', label: 'Avatar' },
    { key: 'post_date', label: 'Post Date' },
    { key: 'post_text', label: 'Post Text' },
    { key: 'screenshot', label: 'Screenshot' },
    { key: 'images', label: 'Images' },
    { key: 'image_over_text', label: 'Image Over Text' },
    { key: 'comments', label: 'Comments' },
    { key: 'reposts', label: 'Reposts' },
    { key: 'likes', label: 'Likes' },
    { key: 'views', label: 'Views' },
    { key: 'is_ad', label: 'Is Ad' },
    { key: 'status', label: 'Status' },
    { key: 'post_type', label: 'Post Type' },
    { key: 'to_tg', label: 'To TG' },
    { key: 'to_tw', label: 'To TW' },
    { key: 'to_wp', label: 'To WP' },
    { key: 'to_vk', label: 'To VK' },
    { key: 'created_at', label: 'Created At' },
    { key: 'updated_at', label: 'Updated At' },
    { key: 'source_platform', label: 'Source Platform' },
    { key: 'source_id', label: 'Source ID' },
  ]

  function formatPostCell(post: PostRow, key: keyof PostRow): ReactNode {
    const v = post[key]
    if (v === null || v === undefined) return <span className="text-[var(--text-muted)]">—</span>
    if (key === 'post_date' || key === 'created_at' || key === 'updated_at') {
      return <span className="text-[var(--text-secondary)] whitespace-nowrap">{new Date(String(v)).toLocaleString()}</span>
    }
    if (key === 'images') {
      const arr = Array.isArray(v) ? v : []
      return <span className="text-[var(--text-secondary)]">{arr.length} items</span>
    }
    if (key === 'post_text' || key === 'screenshot' || key === 'url' || key === 'image_over_text' || key === 'avatar') {
      const s = String(v)
      const truncated = s.length > 80 ? s.slice(0, 80) + '…' : s
      return <span className="text-[var(--text-secondary)] max-w-[200px] truncate block" title={s}>{truncated}</span>
    }
    if (typeof v === 'boolean') {
      return v ? <span className="text-emerald-400">true</span> : <span className="text-[var(--text-muted)]">false</span>
    }
    return <span className="text-[var(--text-secondary)]">{String(v)}</span>
  }

  return (
    <PageContainer maxWidth="wide">
      <PageHeader
        title="Administration"
        description="Пользователи и группы, статистика, уведомления, мониторинг сервисов (core, collector, processor, scheduler), пайплайн постов, диагностика постинга, расписания, S3 и сведения о окружении."
      />

      {/* Tabs */}
      <div className="flex space-x-1 border-b border-[var(--border-color)]">
        <button
          onClick={() => setActiveTab('users')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'users'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          Users
        </button>
        <button
          onClick={() => setActiveTab('audit')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'audit'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          Audit log
        </button>
        <button
          onClick={() => setActiveTab('groups')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'groups'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          Groups
        </button>
        <button
          onClick={() => setActiveTab('statistics')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'statistics'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          Statistics
        </button>
        <button
          onClick={() => setActiveTab('schedule')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'schedule'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          Schedule
        </button>
        <button
          onClick={() => setActiveTab('notifications')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'notifications'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          Notifications
        </button>
        <button
          onClick={() => setActiveTab('feedback')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'feedback'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          Обратная связь
        </button>
        <button
          onClick={() => setActiveTab('services-status')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'services-status'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          Services Status
        </button>
        <button
          onClick={() => setActiveTab('processor')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'processor'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          Processor
        </button>
        <button
          onClick={() => setActiveTab('collector')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'collector'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          Collector
        </button>
        <button
          onClick={() => setActiveTab('scheduler')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'scheduler'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          Scheduler
        </button>
        <button
          onClick={() => setActiveTab('posts-tables')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'posts-tables'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          Posts
        </button>
        <button
          onClick={() => setActiveTab('posting-diagnostics')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'posting-diagnostics'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          Диагностика постинга
        </button>
        <button
          onClick={() => setActiveTab('runtime-location')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'runtime-location'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          IP / регион / TZ
        </button>
        <button
          onClick={() => setActiveTab('storage')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'storage'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          S3 Storage
        </button>
      </div>

      {/* Users Tab */}
      {activeTab === 'users' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
              Users Management
            </CardTitle>
            <CardDescription>View and manage all registered users</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
              <Button 
                onClick={handleLoadUsers} 
                isLoading={isLoadingUsers}
                className="w-full sm:w-auto"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Load Users
              </Button>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-[var(--text-muted)]">Tariff</label>
                <select
                  value={userFilterTariff}
                  onChange={(e) => setUserFilterTariff(e.target.value)}
                  className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] px-3 py-2 text-sm text-[var(--text-primary)]"
                >
                  <option value="">All tariffs</option>
                  {TARIFFS.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-[var(--text-muted)]">Subscription</label>
                <select
                  value={userFilterSubscriptionStatus}
                  onChange={(e) => setUserFilterSubscriptionStatus(e.target.value)}
                  className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] px-3 py-2 text-sm text-[var(--text-primary)] min-w-[140px]"
                >
                  {SUBSCRIPTION_STATUS_FILTERS.map((o) => (
                    <option key={o.value || 'all'} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              <Button type="button" variant="secondary" onClick={handleExportUsersCsv} className="w-full sm:w-auto">
                Export CSV
              </Button>
            </div>

            {isLoadingUsers && <TableSkeleton rows={5} cols={10} className="mt-4" />}

            {usersError && (
              <Alert variant="error" className="animate-slide-down">
                {usersError}
              </Alert>
            )}

            {userUpdateError && (
              <Alert variant="error" className="animate-slide-down">
                {userUpdateError}
              </Alert>
            )}

            {users.length > 0 && (
              <div className="overflow-x-auto animate-slide-down">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="border-b border-[var(--border-color)]">
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Username</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Email</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Role</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Tariff</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Subscription</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Email Verified</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Access</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Created At</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => {
                      const tariffOptions = TARIFFS.includes(user.tariff ?? '')
                        ? TARIFFS
                        : [user.tariff ?? 'free', ...TARIFFS]
                      return (
                        <Fragment key={user.id ?? user.email}>
                        <tr
                          className={`border-b border-[var(--border-color)] hover:bg-[var(--bg-secondary)] transition-colors ${user.is_blocked ? 'opacity-80' : ''}`}
                        >
                          <td className="py-3 px-4 text-[var(--text-secondary)] font-medium">{user.username}</td>
                          <td className="py-3 px-4 text-[var(--text-secondary)]">{user.email}</td>
                          <td className="py-3 px-4">
                            <select
                              value={user.role}
                              onChange={(e) =>
                                updateUserInList(user.id!, {
                                  role: e.target.value as User['role'],
                                })
                              }
                              className="w-full min-w-[90px] rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] px-2 py-1.5 text-sm text-[var(--text-primary)] focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-400"
                            >
                              {ROLES.map((r) => (
                                <option key={r} value={r}>
                                  {r}
                                </option>
                              ))}
                            </select>
                          </td>
                          <td className="py-3 px-4">
                            <select
                              value={user.tariff ?? 'free'}
                              onChange={(e) =>
                                updateUserInList(user.id!, { tariff: e.target.value })
                              }
                              className="w-full min-w-[90px] rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] px-2 py-1.5 text-sm text-[var(--text-primary)] focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-400"
                            >
                              {tariffOptions.map((t) => (
                                <option key={t} value={t}>
                                  {t}
                                </option>
                              ))}
                            </select>
                          </td>
                          <td className="py-3 px-4 text-xs text-[var(--text-secondary)] max-w-[120px]">
                            {user.subscription_status ?? '—'}
                          </td>
                          <td className="py-3 px-4">
                            {user.is_email_verified ? (
                              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium bg-emerald-500/20 text-emerald-400">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                                Verified
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium bg-yellow-500/20 text-yellow-400">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                                Not Verified
                              </span>
                            )}
                          </td>
                          <td className="py-3 px-4 align-top">
                            <div className="flex flex-col gap-2">
                              {user.is_blocked ? (
                                <span className="inline-flex w-fit items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-red-500/20 text-red-400">
                                  Заблокирован
                                </span>
                              ) : (
                                <span className="inline-flex w-fit items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/15 text-emerald-400">
                                  Активен
                                </span>
                              )}
                              {user.id != null && (
                                <Button
                                  size="sm"
                                  variant={user.is_blocked ? 'secondary' : 'danger'}
                                  disabled={
                                    blockingUserId === user.id ||
                                    (user.is_blocked !== true && currentUser?.id === user.id)
                                  }
                                  isLoading={blockingUserId === user.id}
                                  onClick={() => handleSetUserBlocked(user, !user.is_blocked)}
                                  className="w-fit"
                                >
                                  {user.is_blocked ? 'Разблокировать' : 'Заблокировать'}
                                </Button>
                              )}
                            </div>
                          </td>
                          <td className="py-3 px-4 text-[var(--text-secondary)]">
                            {new Date(user.created_at).toLocaleDateString()}
                          </td>
                          <td className="py-3 px-4 flex flex-wrap gap-2">
                            <Button
                              size="sm"
                              variant="secondary"
                              disabled={user.id == null || savingUserId === user.id}
                              onClick={() => handleSaveUser(user)}
                            >
                              {savingUserId === user.id ? 'Saving…' : 'Save'}
                            </Button>
                            {user.id != null && (
                              <Button
                                size="sm"
                                variant="secondary"
                                onClick={() => handleToggleHistory(user.id!)}
                              >
                                {expandedHistoryUserId === user.id ? 'Hide history' : 'History'}
                              </Button>
                            )}
                          </td>
                        </tr>
                        {user.id != null && expandedHistoryUserId === user.id && (
                          <tr className="bg-[var(--bg-tertiary)]">
                            <td colSpan={8} className="py-4 px-4">
                              {isLoadingHistory ? (
                                <p className="text-[var(--text-muted)] text-sm">Loading history…</p>
                              ) : historyError ? (
                                <Alert variant="error" className="animate-slide-down">
                                  {historyError}
                                </Alert>
                              ) : historyList.length === 0 ? (
                                <p className="text-[var(--text-muted)] text-sm">No role/tariff history</p>
                              ) : (
                                <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
                                  <table className="w-full border-collapse text-sm">
                                    <thead>
                                      <tr className="border-b border-[var(--border-color)]">
                                        <th className="text-left py-2 px-3 font-semibold text-[var(--text-primary)]">Date</th>
                                        <th className="text-left py-2 px-3 font-semibold text-[var(--text-primary)]">Changed by (ID)</th>
                                        <th className="text-left py-2 px-3 font-semibold text-[var(--text-primary)]">Role (old → new)</th>
                                        <th className="text-left py-2 px-3 font-semibold text-[var(--text-primary)]">Tariff (old → new)</th>
                                      </tr>
                                    </thead>
                                    <tbody>
                                      {historyList.map((entry) => (
                                        <tr key={entry.id} className="border-b border-[var(--border-color)] last:border-0">
                                          <td className="py-2 px-3 text-[var(--text-secondary)]">
                                            {new Date(entry.changed_at).toLocaleString()}
                                          </td>
                                          <td className="py-2 px-3 text-[var(--text-secondary)]">
                                            {entry.changed_by_user_id ?? '—'}
                                          </td>
                                          <td className="py-2 px-3 text-[var(--text-secondary)]">
                                            {(entry.role_old ?? '—')} → {(entry.role_new ?? '—')}
                                          </td>
                                          <td className="py-2 px-3 text-[var(--text-secondary)]">
                                            {(entry.tariff_old ?? '—')} → {(entry.tariff_new ?? '—')}
                                          </td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              )}
                            </td>
                          </tr>
                        )}
                        </Fragment>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {users.length === 0 && !isLoadingUsers && !usersError && (
              <EmptyState
                title="No users loaded"
                description='Click "Load Users" to fetch the list of users.'
              />
            )}
          </CardContent>
        </Card>
      )}

      {activeTab === 'audit' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle>Admin audit log</CardTitle>
            <CardDescription>
              Изменения ролей и тарифов, блокировки (записи при действиях администраторов)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button onClick={handleLoadAuditLog} isLoading={isLoadingAudit} className="w-full sm:w-auto">
              Load audit log
            </Button>
            {auditError && (
              <Alert variant="error" className="animate-slide-down">
                {auditError}
              </Alert>
            )}
            {auditLog.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-[var(--border-color)]">
                      <th className="text-left py-2 px-3">Time</th>
                      <th className="text-left py-2 px-3">Admin ID</th>
                      <th className="text-left py-2 px-3">Action</th>
                      <th className="text-left py-2 px-3">Target</th>
                      <th className="text-left py-2 px-3">Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditLog.map((row) => (
                      <tr key={row.id} className="border-b border-[var(--border-color)]">
                        <td className="py-2 px-3 whitespace-nowrap text-[var(--text-secondary)]">
                          {new Date(row.created_at).toLocaleString()}
                        </td>
                        <td className="py-2 px-3">{row.admin_user_id}</td>
                        <td className="py-2 px-3">{row.action}</td>
                        <td className="py-2 px-3 text-xs">
                          {row.target_type ?? '—'} {row.target_id ?? ''}
                        </td>
                        <td className="py-2 px-3 text-xs font-mono max-w-[280px] truncate" title={JSON.stringify(row.details_json ?? {})}>
                          {row.details_json ? JSON.stringify(row.details_json) : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {auditLog.length === 0 && !isLoadingAudit && !auditError && (
              <EmptyState title="No entries" description='Click "Load audit log" to fetch records.' />
            )}
          </CardContent>
        </Card>
      )}

      {/* Groups Tab */}
      {activeTab === 'groups' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              Groups
            </CardTitle>
            <CardDescription>
              Создайте группу с описанием и добавляйте пользователей по email. Один пользователь может состоять в нескольких группах.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <form onSubmit={handleCreateGroupAdmin} className="space-y-3 rounded-xl border border-[var(--border-color)] p-4 bg-[var(--bg-secondary)]">
              <h3 className="text-sm font-semibold text-[var(--text-primary)]">Новая группа</h3>
              <div className="flex flex-col sm:flex-row gap-3 flex-wrap">
                <Input
                  placeholder="Название группы"
                  value={newGroupName}
                  onChange={(e) => setNewGroupName(e.target.value)}
                  className="max-w-md"
                />
                <Button type="submit" disabled={!newGroupName.trim() || isCreatingGroup} isLoading={isCreatingGroup}>
                  Создать группу
                </Button>
              </div>
              <textarea
                className="w-full max-w-2xl rounded-lg border border-[var(--border-color)] bg-[var(--bg-tertiary)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] min-h-[88px] focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-400"
                placeholder="Описание (необязательно)"
                value={newGroupDescription}
                onChange={(e) => setNewGroupDescription(e.target.value)}
              />
            </form>

            <Button
              onClick={handleLoadGroups}
              isLoading={isLoadingGroups}
              className="w-full sm:w-auto"
              variant="secondary"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Обновить список
            </Button>
            {groupsError && (
              <Alert variant="error" className="animate-slide-down">
                {groupsError}
              </Alert>
            )}
            {groupsList.length > 0 && (
              <div className="space-y-6 animate-slide-down">
                {groupsList.map((group) => {
                  const isEmpty = !group.members || group.members.length === 0
                  const form = getMemberForm(group.id)
                  return (
                    <div key={group.id} className="rounded-xl border border-[var(--border-color)] p-4 bg-[var(--bg-secondary)]">
                      <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-1">{group.name}</h3>
                      {group.description ? (
                        <p className="text-sm text-[var(--text-secondary)] whitespace-pre-wrap mb-2">{group.description}</p>
                      ) : null}
                      <p className="text-sm text-[var(--text-muted)] mb-4">
                        ID: {group.id} · Создана: {new Date(group.created_at).toLocaleString()}
                      </p>

                      <div className="mb-4 space-y-2">
                        <p className="text-sm font-medium text-[var(--text-primary)]">Добавить участника по email</p>
                        {isEmpty && (
                          <p className="text-xs text-amber-400/90">
                            В пустую группу первым должен быть добавлен менеджер (роль задаётся автоматически).
                          </p>
                        )}
                        <div className="flex flex-col sm:flex-row gap-2 flex-wrap items-end">
                          <Input
                            placeholder="email@example.com"
                            type="email"
                            value={form.email}
                            onChange={(e) => setMemberForm(group.id, { email: e.target.value })}
                            className="max-w-sm"
                          />
                          {!isEmpty && (
                            <select
                              value={form.role}
                              onChange={(e) =>
                                setMemberForm(group.id, { role: e.target.value as 'manager' | 'author' })
                              }
                              className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-tertiary)] px-3 py-2 text-sm text-[var(--text-primary)]"
                            >
                              <option value="author">author</option>
                              <option value="manager">manager</option>
                            </select>
                          )}
                          <Button
                            type="button"
                            size="sm"
                            onClick={() => handleAddMemberToGroup(group)}
                            disabled={!form.email.trim() || addingToGroupId === group.id}
                            isLoading={addingToGroupId === group.id}
                          >
                            Добавить
                          </Button>
                        </div>
                      </div>

                      {group.members && group.members.length > 0 ? (
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b border-[var(--border-color)]">
                                <th className="text-left py-2 px-3 font-medium text-[var(--text-secondary)]">Username</th>
                                <th className="text-left py-2 px-3 font-medium text-[var(--text-secondary)]">Email</th>
                                <th className="text-left py-2 px-3 font-medium text-[var(--text-secondary)]">Tariff</th>
                                <th className="text-left py-2 px-3 font-medium text-[var(--text-secondary)]">Role</th>
                                <th className="text-right py-2 px-3 font-medium text-[var(--text-secondary)]"> </th>
                              </tr>
                            </thead>
                            <tbody>
                              {group.members.map((m) => (
                                <tr key={m.user_id} className="border-b border-[var(--border-color)] last:border-0">
                                  <td className="py-2 px-3 text-[var(--text-primary)]">{m.username}</td>
                                  <td className="py-2 px-3 text-[var(--text-secondary)]">{m.email}</td>
                                  <td className="py-2 px-3 text-[var(--text-secondary)]">{m.tariff}</td>
                                  <td className="py-2 px-3">
                                    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${m.role_in_group === 'manager' ? 'bg-purple-500/20 text-purple-400' : 'bg-blue-500/20 text-blue-400'}`}>
                                      {m.role_in_group}
                                    </span>
                                  </td>
                                  <td className="py-2 px-3 text-right">
                                    <Button
                                      type="button"
                                      size="sm"
                                      variant="ghost"
                                      className="text-red-400 hover:text-red-300"
                                      disabled={removingMemberKey === `${group.id}-${m.user_id}`}
                                      isLoading={removingMemberKey === `${group.id}-${m.user_id}`}
                                      onClick={() => handleRemoveGroupMember(group.id, m.user_id)}
                                    >
                                      Удалить
                                    </Button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <p className="text-[var(--text-muted)] text-sm">Нет участников</p>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
            {groupsList.length === 0 && !isLoadingGroups && !groupsError && (
              <EmptyState
                title="Список пуст"
                description='Создайте группу выше или нажмите «Обновить список», чтобы загрузить данные.'
              />
            )}
          </CardContent>
        </Card>
      )}

      {/* Statistics Tab */}
      {activeTab === 'statistics' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Usage Statistics
            </CardTitle>
            <CardDescription>View usage statistics for all users</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button 
              onClick={handleLoadStatistics} 
              isLoading={isLoadingStatistics}
              className="w-full sm:w-auto"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Collect Statistics
            </Button>

            {statisticsError && (
              <Alert variant="error" className="animate-slide-down">
                {statisticsError}
              </Alert>
            )}

            {statistics.length > 0 && (
              <div className="overflow-x-auto animate-slide-down">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="border-b border-[var(--border-color)]">
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Username</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Email</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Role</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Total Posts</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Collected</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Processed</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Published</th>
                    </tr>
                  </thead>
                  <tbody>
                    {statistics.map((stat) => (
                      <tr 
                        key={stat.user_id} 
                        className="border-b border-[var(--border-color)] hover:bg-[var(--bg-secondary)] transition-colors"
                      >
                        <td className="py-3 px-4 text-[var(--text-secondary)] font-medium">{stat.username}</td>
                        <td className="py-3 px-4 text-[var(--text-secondary)]">{stat.email}</td>
                        <td className="py-3 px-4">
                          <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${
                            stat.role === 'admin'
                              ? 'bg-purple-500/20 text-purple-400'
                              : stat.role === 'manager'
                              ? 'bg-amber-500/20 text-amber-400'
                              : stat.role === 'author'
                              ? 'bg-teal-500/20 text-teal-400'
                              : stat.role === 'user'
                              ? 'bg-blue-500/20 text-blue-400'
                              : 'bg-gray-500/20 text-gray-400'
                          }`}>
                            {stat.role}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-[var(--text-secondary)] font-medium">{stat.total_posts.toLocaleString()}</td>
                        <td className="py-3 px-4 text-[var(--text-secondary)]">{stat.collected_posts.toLocaleString()}</td>
                        <td className="py-3 px-4 text-[var(--text-secondary)]">{stat.processed_posts.toLocaleString()}</td>
                        <td className="py-3 px-4 text-[var(--text-secondary)]">{stat.published_posts.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {statistics.length === 0 && !isLoadingStatistics && !statisticsError && (
              <p className="text-[var(--text-muted)] text-center py-8">
                Click "Collect Statistics" to view usage statistics
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Schedule Tab */}
      {activeTab === 'schedule' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              Schedule Snapshots
            </CardTitle>
            <CardDescription>View schedule snapshots from schedule_snapshots table</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Кнопка запуска сбора расписаний */}
            <div className="space-y-4 border-t border-[var(--border-color)] pt-4">
              <div>
                <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Запуск сбора расписаний</h3>
                <p className="text-sm text-[var(--text-secondary)] mb-4">
                  Принудительно запускает один цикл сбора расписаний из core сервиса
                </p>
                <Button 
                  onClick={handleStartDiscovery} 
                  isLoading={isStartingDiscovery}
                  className="w-full sm:w-auto"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Запуск сбора расписаний
                </Button>
                {discoveryMessage && (
                  <Alert variant="success" className="mt-2 animate-slide-down">
                    {discoveryMessage}
                  </Alert>
                )}
              </div>
            </div>

            {/* Форма принудительного запуска ботов */}
            <div className="space-y-4 border-t border-[var(--border-color)] pt-4">
              <div>
                <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Принудительный запуск ботов</h3>
                <p className="text-sm text-[var(--text-secondary)] mb-4">
                  Выберите ботов для запуска и нажмите кнопку запуска
                </p>
                
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
                  {SCHEDULE_BOT_PLATFORMS.map((platform) => (
                    <label
                      key={platform}
                      className="flex items-center space-x-2 cursor-pointer p-3 rounded-lg border border-[var(--border-color)] hover:bg-[var(--bg-secondary)] transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={selectedBots[platform]}
                        onChange={() => handleBotToggle(platform)}
                        className="w-4 h-4 text-primary-400 rounded focus:ring-primary-400"
                      />
                      <span className="text-[var(--text-secondary)] font-medium uppercase">{platform}</span>
                    </label>
                  ))}
                </div>

                <Button 
                  onClick={handleStartBot} 
                  isLoading={isStartingBot}
                  className="w-full sm:w-auto"
                  disabled={Object.values(selectedBots).every(v => !v)}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Запустить боты
                </Button>
                {botMessage && (
                  <Alert variant={botMessage.includes('Error') ? 'error' : 'success'} className="mt-2 animate-slide-down">
                    {botMessage}
                  </Alert>
                )}
              </div>
            </div>

            {/* Кнопка получения расписания */}
            <div className="space-y-4 border-t border-[var(--border-color)] pt-4">
              <div>
                <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Просмотр расписаний</h3>
                <p className="text-sm text-[var(--text-secondary)] mb-4">
                  Загрузить расписания из таблицы schedule_snapshots
                </p>
                <Button 
                  onClick={handleLoadSchedule} 
                  isLoading={isLoadingSchedule}
                  className="w-full sm:w-auto"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Получить расписание
                </Button>
              </div>
            </div>

            {scheduleError && (
              <Alert variant="error" className="animate-slide-down">
                {scheduleError}
              </Alert>
            )}

            {schedules.length > 0 && (
              <div className="overflow-x-auto animate-slide-down">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="border-b border-[var(--border-color)]">
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">User ID</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Platform</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Publish Enabled</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Collect Enabled</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Schedule Type</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Time Intervals</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Updated At</th>
                    </tr>
                  </thead>
                  <tbody>
                    {schedules.map((schedule, index) => (
                      <tr 
                        key={`${schedule.user_id}-${schedule.platform}-${index}`} 
                        className="border-b border-[var(--border-color)] hover:bg-[var(--bg-secondary)] transition-colors"
                      >
                        <td className="py-3 px-4 text-[var(--text-secondary)] font-medium">{schedule.user_id}</td>
                        <td className="py-3 px-4">
                          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium bg-blue-500/20 text-blue-400">
                            {schedule.platform}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          {schedule.publish_enabled ? (
                            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium bg-emerald-500/20 text-emerald-400">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                              Enabled
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium bg-gray-500/20 text-gray-400">
                              Disabled
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          {schedule.collect_enabled ? (
                            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium bg-emerald-500/20 text-emerald-400">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                              Enabled
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium bg-gray-500/20 text-gray-400">
                              Disabled
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-[var(--text-secondary)]">{schedule.schedule_type}</td>
                        <td className="py-3 px-4 text-[var(--text-secondary)]">
                          {schedule.time_intervals && schedule.time_intervals.length > 0 ? (
                            <div className="flex flex-col gap-1">
                              {schedule.time_intervals.map((interval, idx) => (
                                <span key={idx} className="text-xs">
                                  {interval.start} - {interval.end}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <span className="text-[var(--text-muted)]">No intervals</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-[var(--text-secondary)]">
                          {new Date(schedule.updated_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {schedules.length === 0 && !isLoadingSchedule && !scheduleError && (
              <p className="text-[var(--text-muted)] text-center py-8">
                Click "Получить расписание" to fetch schedule snapshots
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Notifications Tab */}
      {activeTab === 'notifications' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              Notifications Management
            </CardTitle>
            <CardDescription>Create notifications visible to all users</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Create Notification Form */}
            <form onSubmit={handleCreateNotification} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">
                  Notification Message
                </label>
                <TipTapEditor
                  content={notificationMessage}
                  onChange={setNotificationMessage}
                  placeholder="Enter notification message..."
                  toolbarButtons={['bold', 'italic', 'underline', 'strike', 'bulletList', 'orderedList', 'undo', 'redo']}
                />
              </div>

              {notificationError && (
                <Alert variant="error" className="animate-slide-down">
                  {notificationError}
                </Alert>
              )}

              {notificationSuccess && (
                <Alert variant="success" className="animate-slide-down">
                  {notificationSuccess}
                </Alert>
              )}

              <Button type="submit" isLoading={isCreatingNotification} className="w-full sm:w-auto">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
                Send Notification
              </Button>
            </form>

            {/* Notifications List */}
            <div className="border-t border-[var(--border-color)] pt-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-[var(--text-primary)]">Recent Notifications</h3>
                <Button 
                  variant="secondary" 
                  size="sm" 
                  onClick={loadNotifications}
                  isLoading={isLoadingNotifications}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Refresh
                </Button>
              </div>

              {notificationsList.length > 0 ? (
                <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
                  <table className="w-full">
                    <thead className="bg-[var(--bg-tertiary)]">
                      <tr>
                        <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">ID</th>
                        <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Created At</th>
                        <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Message</th>
                        <th className="py-3 px-4 text-center text-sm font-medium text-[var(--text-secondary)]">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[var(--border-color)]">
                      {notificationsList.map((notification) => (
                        <tr key={notification.id} className="hover:bg-[var(--bg-tertiary)] transition-colors">
                          <td className="py-3 px-4 text-[var(--text-primary)] font-mono text-sm">{notification.id}</td>
                          <td className="py-3 px-4 text-[var(--text-secondary)] text-sm">
                            {new Date(notification.created_at).toLocaleString()}
                          </td>
                          <td className="py-3 px-4 text-[var(--text-primary)]">
                            <div 
                              className="notification-content max-w-md truncate"
                              dangerouslySetInnerHTML={{ __html: notification.message }}
                            />
                          </td>
                          <td className="py-3 px-4 text-center">
                            <button
                              onClick={() => handleDeleteNotification(notification.id)}
                              disabled={isDeletingNotification === notification.id}
                              className="p-2 rounded-lg hover:bg-red-500/20 text-red-400 hover:text-red-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                              title="Delete notification"
                            >
                              {isDeletingNotification === notification.id ? (
                                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                              ) : (
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                              )}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-[var(--text-muted)] text-center py-8">
                  {isLoadingNotifications ? 'Loading notifications...' : 'Click "Refresh" to load notifications'}
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === 'feedback' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              Обратная связь
            </CardTitle>
            <CardDescription>Сообщения пользователей: ошибки, предложения, контакты</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {feedbackError && (
              <Alert variant="error" className="animate-slide-down">
                {feedbackError}
              </Alert>
            )}

            <div className="flex justify-end">
              <Button
                variant="secondary"
                onClick={() => void loadFeedback()}
                isLoading={isLoadingFeedback}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Refresh
              </Button>
            </div>

            {feedbackList.length > 0 ? (
              <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
                <table className="w-full">
                  <thead className="bg-[var(--bg-tertiary)]">
                    <tr>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Тип</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Текст</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Email</th>
                      <th className="py-3 px-4 text-center text-sm font-medium text-[var(--text-secondary)]">Действие</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-color)]">
                    {feedbackList.map((item) => (
                      <tr key={item.id} className="hover:bg-[var(--bg-tertiary)] transition-colors">
                        <td className="py-3 px-4 text-[var(--text-primary)] text-sm whitespace-nowrap">
                          {FEEDBACK_TYPE_LABELS[item.type] ?? item.type}
                        </td>
                        <td className="py-3 px-4 text-[var(--text-primary)] text-sm max-w-md">
                          <p className="whitespace-pre-wrap break-words">{item.text}</p>
                        </td>
                        <td className="py-3 px-4 text-[var(--text-secondary)] text-sm whitespace-nowrap">
                          {item.email || '—'}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <button
                            onClick={() => void handleDeleteFeedback(item.id)}
                            disabled={isDeletingFeedback === item.id}
                            className="p-2 rounded-lg hover:bg-red-500/20 text-red-400 hover:text-red-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Удалить"
                          >
                            {isDeletingFeedback === item.id ? (
                              <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                            ) : (
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                              </svg>
                            )}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-[var(--text-muted)] text-center py-8">
                {isLoadingFeedback ? 'Загрузка...' : 'Записей обратной связи пока нет'}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Services Status Tab */}
      {activeTab === 'services-status' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Services Status
            </CardTitle>
            <CardDescription>CORE, PROCESSOR, SCHEDULER, COLLECTOR health and status</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <Button
              onClick={handleLoadServicesStatus}
              isLoading={isLoadingServicesStatus}
              className="w-full sm:w-auto"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Load Services Status
            </Button>

            {servicesStatusError && (
              <Alert variant="error" className="animate-slide-down">{servicesStatusError}</Alert>
            )}

            {servicesStatus && (
              <div className="space-y-6 animate-slide-down">
                <div>
                  <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Healthchecks</h3>
                  <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
                    <table className="w-full">
                      <thead className="bg-[var(--bg-tertiary)]">
                        <tr>
                          <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Service</th>
                          <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Status</th>
                          <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Server time</th>
                          <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Error</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[var(--border-color)]">
                        {(servicesStatus.healthchecks || []).map((h) => (
                          <tr key={h.service_name} className="hover:bg-[var(--bg-tertiary)]">
                            <td className="py-3 px-4 text-[var(--text-primary)] font-medium">{h.service_name}</td>
                            <td className="py-3 px-4">
                              <span className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${h.status === 'ok' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                                {h.status}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-[var(--text-secondary)] text-sm">{h.server_time ? new Date(h.server_time).toLocaleString() : '—'}</td>
                            <td className="py-3 px-4 text-[var(--text-secondary)] text-sm">{h.error ?? '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  {servicesStatus.collector && (
                    <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                      <h4 className="font-semibold text-[var(--text-primary)] mb-2">COLLECTOR</h4>
                      {servicesStatus.collector.error ? (
                        <p className="text-red-400 text-sm">{servicesStatus.collector.error}</p>
                      ) : (
                        <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                          <li>Server time: {servicesStatus.collector.current_time ? new Date(servicesStatus.collector.current_time).toLocaleString() : '—'}</li>
                          <li>Interval: collect {servicesStatus.collector.collect_interval_sec}s / distribute {servicesStatus.collector.distribute_interval_sec}s</li>
                          {servicesStatus.collector.collector && (
                            <li>Collector: last run {servicesStatus.collector.collector.last_run_at ? new Date(servicesStatus.collector.collector.last_run_at).toLocaleString() : '—'}, total {servicesStatus.collector.collector.total_processed}</li>
                          )}
                          {servicesStatus.collector.distributor && (
                            <li>Distributor: last run {servicesStatus.collector.distributor.last_run_at ? new Date(servicesStatus.collector.distributor.last_run_at).toLocaleString() : '—'}, total {servicesStatus.collector.distributor.total_processed}</li>
                          )}
                        </ul>
                      )}
                    </div>
                  )}
                  {servicesStatus.processor && (
                    <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                      <h4 className="font-semibold text-[var(--text-primary)] mb-2">PROCESSOR</h4>
                      {servicesStatus.processor.error ? (
                        <p className="text-red-400 text-sm">{servicesStatus.processor.error}</p>
                      ) : (
                        <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                          <li>Server time: {servicesStatus.processor.current_time ? new Date(servicesStatus.processor.current_time).toLocaleString() : '—'}</li>
                          <li>Interval: {servicesStatus.processor.process_interval_sec}s</li>
                          {servicesStatus.processor.processor && (
                            <li>Last run: {servicesStatus.processor.processor.last_run_at ? new Date(servicesStatus.processor.processor.last_run_at).toLocaleString() : '—'}, total {servicesStatus.processor.processor.total_processed}</li>
                          )}
                        </ul>
                      )}
                      <div className="mt-3 pt-3 border-t border-[var(--border-color)]">
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={handleRunProcessorCycle}
                          isLoading={isRunningProcessor}
                          className="w-full sm:w-auto"
                        >
                          Запустить цикл обработки
                        </Button>
                        {processorRunMessage && (
                          <Alert variant="success" className="mt-2 animate-slide-down">
                            {processorRunMessage}
                          </Alert>
                        )}
                        {processorRunError && (
                          <Alert variant="error" className="mt-2 animate-slide-down">
                            {processorRunError}
                          </Alert>
                        )}
                      </div>
                    </div>
                  )}
                  {servicesStatus.scheduler && (
                    <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                      <h4 className="font-semibold text-[var(--text-primary)] mb-2">SCHEDULER</h4>
                      {servicesStatus.scheduler.error ? (
                        <p className="text-red-400 text-sm">{servicesStatus.scheduler.error}</p>
                      ) : (
                        <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                          <li>Server time: {servicesStatus.scheduler.current_time ? new Date(servicesStatus.scheduler.current_time).toLocaleString() : '—'}</li>
                          <li>Poll interval: {servicesStatus.scheduler.poll_interval_sec}s</li>
                          <li>Last poll: {servicesStatus.scheduler.last_poll_at ? new Date(servicesStatus.scheduler.last_poll_at).toLocaleString() : '—'}</li>
                        </ul>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {!servicesStatus && !isLoadingServicesStatus && !servicesStatusError && (
              <p className="text-[var(--text-muted)] text-center py-8">Click &quot;Load Services Status&quot; to fetch</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Processor Tab */}
      {activeTab === 'processor' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7" />
              </svg>
              Processor
            </CardTitle>
            <CardDescription>Статус processor и сводка по статусам в таблице posts; полные данные — на вкладке Posts.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <Button
              onClick={handleLoadServicesStatus}
              isLoading={isLoadingServicesStatus}
              className="w-full sm:w-auto"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Обновить статус сервисов
            </Button>
            {servicesStatusError && (
              <Alert variant="error" className="animate-slide-down">{servicesStatusError}</Alert>
            )}
            {servicesStatus?.processor && (
              <>
                <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] space-y-2">
                  <h3 className="text-lg font-semibold text-[var(--text-primary)]">Service status</h3>
                  {servicesStatus.processor.error ? (
                    <p className="text-red-400 text-sm">{servicesStatus.processor.error}</p>
                  ) : (
                    <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                      <li>State: <span className={servicesStatus.healthchecks?.find(h => h.service_name === 'processor')?.status === 'ok' ? 'text-emerald-400' : 'text-red-400'}>{servicesStatus.healthchecks?.find(h => h.service_name === 'processor')?.status ?? '—'}</span></li>
                      <li>Started at: {servicesStatus.processor.started_at ? new Date(servicesStatus.processor.started_at).toLocaleString() : '—'}</li>
                      <li>Last run: {servicesStatus.processor.processor?.last_run_at ? new Date(String(servicesStatus.processor.processor.last_run_at)).toLocaleString() : '—'}</li>
                    </ul>
                  )}
                  <div className="pt-3 border-t border-[var(--border-color)]">
                    <Button size="sm" variant="secondary" onClick={handleRunProcessorCycle} isLoading={isRunningProcessor} className="w-full sm:w-auto">
                      Запустить цикл обработки
                    </Button>
                    {processorRunMessage && <Alert variant="success" className="mt-2">{processorRunMessage}</Alert>}
                    {processorRunError && <Alert variant="error" className="mt-2">{processorRunError}</Alert>}
                  </div>
                </div>
                {!servicesStatus.processor.error && (
                  <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                    <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Конфигурация сервиса</h3>
                    <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                      <li>Периодичность запуска: <strong className="text-[var(--text-primary)]">{servicesStatus.processor.process_interval_sec ?? '—'} с</strong></li>
                      <li>Размер батча за цикл: <strong className="text-[var(--text-primary)]">{servicesStatus.processor.process_batch_size ?? '—'}</strong> постов</li>
                    </ul>
                  </div>
                )}
                {!servicesStatus.processor.error && servicesStatus.processor.processing_options && servicesStatus.processor.processing_options.length > 0 && (
                  <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                    <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Функции обработки</h3>
                    <p className="text-sm text-[var(--text-muted)] mb-3">
                      Эти опции включаются для каждого пользователя в настройках профиля платформы (Telegram, WordPress, VK, Custom URL). Глобальное изменение по умолчанию здесь не предусмотрено.
                    </p>
                    <div className="space-y-3">
                      {servicesStatus.processor.processing_options.map((opt) => (
                        <div key={opt.id} className="flex flex-col gap-1 rounded-lg border border-[var(--border-color)] p-3 bg-[var(--bg-tertiary)]">
                          <span className="font-medium text-[var(--text-primary)]">{opt.name_ru}</span>
                          <span className="text-sm text-[var(--text-secondary)]">{opt.description}</span>
                          <span className="text-xs text-[var(--text-muted)] font-mono">{opt.id}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
            <div>
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Таблица posts (сводка processor)</h3>
              <p className="text-sm text-[var(--text-muted)] mb-3">
                Счётчики по статусам в центральной таблице posts (метрики processor). Полная таблица строк и платформенные метрики — на вкладке{' '}
                <strong className="text-[var(--text-secondary)]">Posts</strong>.
              </p>
              <Button onClick={handleLoadPostsTables} isLoading={isLoadingPostsTables} size="sm" variant="secondary" className="mb-2">
                Обновить сводку
              </Button>
              {postsTablesError && <Alert variant="error" className="mb-2">{postsTablesError}</Alert>}
              {postsTables?.posts_table_processor && Object.keys(postsTables.posts_table_processor).length > 0 && (
                <div className="flex flex-wrap gap-4">
                  {Object.entries(postsTables.posts_table_processor).map(([status, count]) => (
                    <span key={status} className="px-3 py-1 rounded-lg bg-[var(--bg-tertiary)] text-[var(--text-secondary)] text-sm">
                      {status}: <strong className="text-[var(--text-primary)]">{Number(count).toLocaleString()}</strong>
                    </span>
                  ))}
                </div>
              )}
              <div className="mt-4">
                <Button type="button" variant="secondary" onClick={() => setActiveTab('posts-tables')}>
                  Открыть вкладку Posts — полная таблица и метрики
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Collector Tab */}
      {activeTab === 'collector' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 14v6a2 2 0 002 2h14a2 2 0 002-2v-6a2 2 0 00-2-2M5 14V9" />
              </svg>
              Collector
            </CardTitle>
            <CardDescription>Collector service status and platform tables</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <Button onClick={handleLoadServicesStatus} isLoading={isLoadingServicesStatus} className="w-full sm:w-auto">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh status
            </Button>
            {servicesStatusError && <Alert variant="error">{servicesStatusError}</Alert>}
            {servicesStatus?.collector && (
              <>
                <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                  <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Service status</h3>
                  {servicesStatus.collector.error ? (
                    <p className="text-red-400 text-sm">{servicesStatus.collector.error}</p>
                  ) : (
                    <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                      <li>State: <span className={servicesStatus.healthchecks?.find(h => h.service_name === 'collector')?.status === 'ok' ? 'text-emerald-400' : 'text-red-400'}>{servicesStatus.healthchecks?.find(h => h.service_name === 'collector')?.status ?? '—'}</span></li>
                      <li>Started at: {servicesStatus.collector.started_at ? new Date(servicesStatus.collector.started_at).toLocaleString() : '—'}</li>
                      <li>Collector last run: {servicesStatus.collector.collector?.last_run_at ? new Date(String(servicesStatus.collector.collector.last_run_at)).toLocaleString() : '—'}</li>
                      <li>Distributor last run: {servicesStatus.collector.distributor?.last_run_at ? new Date(String(servicesStatus.collector.distributor.last_run_at)).toLocaleString() : '—'}</li>
                    </ul>
                  )}
                </div>
                {!servicesStatus.collector.error && (
                  <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                    <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Конфигурация сервиса</h3>
                    <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                      <li>Периодичность сбора постов: <strong className="text-[var(--text-primary)]">{servicesStatus.collector.collect_interval_sec ?? '—'} с</strong></li>
                      <li>Периодичность распределения: <strong className="text-[var(--text-primary)]">{servicesStatus.collector.distribute_interval_sec ?? '—'} с</strong></li>
                      <li>Размер батча сбора: <strong className="text-[var(--text-primary)]">{servicesStatus.collector.collect_batch_size ?? '—'}</strong> постов за цикл</li>
                      <li>Размер батча распределения: <strong className="text-[var(--text-primary)]">{servicesStatus.collector.distribute_batch_size ?? '—'}</strong> постов за цикл</li>
                    </ul>
                  </div>
                )}
                {!servicesStatus.collector.error && servicesStatus.collector.collect_functions && servicesStatus.collector.collect_functions.length > 0 && (
                  <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                    <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Функции сервиса</h3>
                    <p className="text-sm text-[var(--text-muted)] mb-3">
                      Запуск сбора постов для сервисов и распределение готовых постов по платформам.
                    </p>
                    <div className="space-y-3">
                      {servicesStatus.collector.collect_functions.map((fn) => (
                        <div key={fn.id} className="flex flex-col gap-1 rounded-lg border border-[var(--border-color)] p-3 bg-[var(--bg-tertiary)]">
                          <span className="font-medium text-[var(--text-primary)]">{fn.name_ru}</span>
                          <span className="text-sm text-[var(--text-secondary)]">{fn.description}</span>
                          <span className="text-xs text-[var(--text-muted)] font-mono">{fn.id}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
            <div>
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Platform tables</h3>
              <p className="text-sm text-[var(--text-muted)] mb-2">
                Все платформенные таблицы постов из collector (включая threads, cpost и т.д.); по колонкам — статусы строк в каждой *_posts.
              </p>
              <Button onClick={handleLoadPostsTables} isLoading={isLoadingPostsTables} size="sm" variant="secondary" className="mb-2">
                Load posts tables
              </Button>
              {postsTablesError && <Alert variant="error" className="mb-2">{postsTablesError}</Alert>}
              {postsTables?.platforms && postsTables.platforms.length > 0 && (() => {
                const statusCols = platformTableStatusColumns(postsTables.platforms)
                return (
                <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
                  <table className="w-full min-w-max">
                    <thead className="bg-[var(--bg-tertiary)]">
                      <tr>
                        <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)] whitespace-nowrap">Platform</th>
                        <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)] whitespace-nowrap">Table</th>
                        {statusCols.map((col) => (
                          <th
                            key={col}
                            className="py-3 px-2 text-right text-xs font-medium text-[var(--text-secondary)] whitespace-nowrap"
                          >
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[var(--border-color)]">
                      {postsTables.platforms.map((p) => (
                        <tr key={p.table} className="hover:bg-[var(--bg-tertiary)]">
                          <td className="py-3 px-4 text-[var(--text-primary)] font-medium whitespace-nowrap">{p.platform}</td>
                          <td className="py-3 px-4 text-[var(--text-secondary)] font-mono text-sm whitespace-nowrap">{p.table}</td>
                          {statusCols.map((col) => (
                            <td key={col} className="py-3 px-2 text-right text-sm text-[var(--text-secondary)] tabular-nums">
                              {platformStatusCell(p, col).toLocaleString()}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                )
              })()}
              {postsTables?.posts_table_collector && Object.keys(postsTables.posts_table_collector).length > 0 && (
                <div className="mt-4">
                  <h4 className="font-semibold text-[var(--text-primary)] mb-2">Central table posts (collector view)</h4>
                  <div className="flex flex-wrap gap-4">
                    {Object.entries(postsTables.posts_table_collector).map(([status, count]) => (
                      <span key={status} className="px-3 py-1 rounded-lg bg-[var(--bg-tertiary)] text-[var(--text-secondary)] text-sm">
                        {status}: <strong className="text-[var(--text-primary)]">{Number(count).toLocaleString()}</strong>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Scheduler Tab */}
      {activeTab === 'scheduler' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              Scheduler
            </CardTitle>
            <CardDescription>Статус сервиса scheduler. Просмотр и действия с расписаниями — на вкладке Schedule.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <Button onClick={handleLoadServicesStatus} isLoading={isLoadingServicesStatus} className="w-full sm:w-auto">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh status
            </Button>
            {servicesStatusError && <Alert variant="error">{servicesStatusError}</Alert>}
            {servicesStatus?.scheduler && (
              <>
                <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                  <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Service status</h3>
                  {servicesStatus.scheduler.error ? (
                    <p className="text-red-400 text-sm">{servicesStatus.scheduler.error}</p>
                  ) : (
                    <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                      <li>State: <span className={servicesStatus.healthchecks?.find(h => h.service_name === 'scheduler')?.status === 'ok' ? 'text-emerald-400' : 'text-red-400'}>{servicesStatus.healthchecks?.find(h => h.service_name === 'scheduler')?.status ?? '—'}</span></li>
                      <li>Started at: {servicesStatus.scheduler.started_at ? new Date(servicesStatus.scheduler.started_at).toLocaleString() : '—'}</li>
                      <li>Last poll: {servicesStatus.scheduler.last_poll_at ? new Date(servicesStatus.scheduler.last_poll_at).toLocaleString() : '—'}</li>
                    </ul>
                  )}
                </div>
                {!servicesStatus.scheduler.error && (
                  <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                    <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Конфигурация сервиса</h3>
                    <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                      <li>Периодичность опроса (сбор расписаний): <strong className="text-[var(--text-primary)]">{servicesStatus.scheduler.poll_interval_sec ?? '—'} с</strong></li>
                      <li>Оповещать ботов только при изменении: <strong className="text-[var(--text-primary)]">{servicesStatus.scheduler.notify_on_change_only === true ? 'да' : servicesStatus.scheduler.notify_on_change_only === false ? 'нет' : '—'}</strong></li>
                    </ul>
                  </div>
                )}
                {!servicesStatus.scheduler.error && servicesStatus.scheduler.schedule_functions && servicesStatus.scheduler.schedule_functions.length > 0 && (
                  <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                    <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Функции сервиса</h3>
                    <p className="text-sm text-[var(--text-muted)] mb-3">
                      Запуск сбора расписаний для сервисов и связанные операции.
                    </p>
                    <div className="space-y-3">
                      {servicesStatus.scheduler.schedule_functions.map((fn) => (
                        <div key={fn.id} className="flex flex-col gap-1 rounded-lg border border-[var(--border-color)] p-3 bg-[var(--bg-tertiary)]">
                          <span className="font-medium text-[var(--text-primary)]">{fn.name_ru}</span>
                          <span className="text-sm text-[var(--text-secondary)]">{fn.description}</span>
                          <span className="text-xs text-[var(--text-muted)] font-mono">{fn.id}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
            <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Расписания и снимки</h3>
              <p className="text-sm text-[var(--text-secondary)] mb-3">
                Таблица <code className="text-xs font-mono">schedule_snapshots</code>, запуск сбора расписаний и принудительный запуск ботов находятся на вкладке{' '}
                <strong className="text-[var(--text-primary)]">Schedule</strong>, чтобы не дублировать интерфейс.
              </p>
              <Button type="button" variant="secondary" onClick={() => setActiveTab('schedule')}>
                Перейти к Schedule Snapshots
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Posts Tables Tab */}
      {activeTab === 'posts-tables' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
              </svg>
              Posts
            </CardTitle>
            <CardDescription>Обзор таблиц постов и полная таблица posts</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <Button
              onClick={handleLoadPostsTables}
              isLoading={isLoadingPostsTables}
              className="w-full sm:w-auto"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Load Posts Tables
            </Button>

            {postsTablesError && (
              <Alert variant="error" className="animate-slide-down">{postsTablesError}</Alert>
            )}

            {postsTables && (
              <div className="space-y-6 animate-slide-down">
                {(postsTables.collector_error || postsTables.processor_error) && (
                  <Alert variant="error">
                    {postsTables.collector_error && <span>Collector: {postsTables.collector_error}. </span>}
                    {postsTables.processor_error && <span>Processor: {postsTables.processor_error}</span>}
                  </Alert>
                )}

                {postsTables.platforms && postsTables.platforms.length > 0 && (() => {
                  const statusCols = platformTableStatusColumns(postsTables.platforms)
                  return (
                  <div>
                    <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Platform tables</h3>
                    <p className="text-sm text-[var(--text-muted)] mb-2">
                      Все платформенные таблицы постов из collector; по колонкам — статусы строк в *_posts (типичные + любые встреченные в БД).
                    </p>
                    <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
                      <table className="w-full min-w-max">
                        <thead className="bg-[var(--bg-tertiary)]">
                          <tr>
                            <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)] whitespace-nowrap">Platform</th>
                            <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)] whitespace-nowrap">Table</th>
                            {statusCols.map((col) => (
                              <th
                                key={col}
                                className="py-3 px-2 text-right text-xs font-medium text-[var(--text-secondary)] whitespace-nowrap"
                              >
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[var(--border-color)]">
                          {postsTables.platforms.map((p) => (
                            <tr key={p.table} className="hover:bg-[var(--bg-tertiary)]">
                              <td className="py-3 px-4 text-[var(--text-primary)] font-medium whitespace-nowrap">{p.platform}</td>
                              <td className="py-3 px-4 text-[var(--text-secondary)] font-mono text-sm whitespace-nowrap">{p.table}</td>
                              {statusCols.map((col) => (
                                <td key={col} className="py-3 px-2 text-right text-sm text-[var(--text-secondary)] tabular-nums">
                                  {platformStatusCell(p, col).toLocaleString()}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                  )
                })()}

                {postsTables.posts_table_collector && Object.keys(postsTables.posts_table_collector).length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Central table <code className="text-sm">posts</code> (collector view)</h3>
                    <div className="flex flex-wrap gap-4">
                      {Object.entries(postsTables.posts_table_collector).map(([status, count]) => (
                        <span key={status} className="px-3 py-1 rounded-lg bg-[var(--bg-tertiary)] text-[var(--text-secondary)] text-sm">
                          {status}: <strong className="text-[var(--text-primary)]">{Number(count).toLocaleString()}</strong>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {postsTables.posts_table_processor && Object.keys(postsTables.posts_table_processor).length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Central table <code className="text-sm">posts</code> (processor view)</h3>
                    <div className="flex flex-wrap gap-4">
                      {Object.entries(postsTables.posts_table_processor).map(([status, count]) => (
                        <span key={status} className="px-3 py-1 rounded-lg bg-[var(--bg-tertiary)] text-[var(--text-secondary)] text-sm">
                          {status}: <strong className="text-[var(--text-primary)]">{Number(count).toLocaleString()}</strong>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="border-t border-[var(--border-color)] pt-6">
                  <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Таблица posts (все столбцы)</h3>
                  <p className="text-sm text-[var(--text-secondary)] mb-4">
                    Загрузить полный список записей из таблицы posts (до 500 строк).
                  </p>
                  <Button
                    onClick={handleLoadPostsList}
                    isLoading={isLoadingPostsList}
                    className="w-full sm:w-auto"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Загрузить таблицу posts
                  </Button>
                  {postsListError && (
                    <Alert variant="error" className="mt-2 animate-slide-down">{postsListError}</Alert>
                  )}
                  {postsList.length > 0 && (
                    <div className="overflow-x-auto mt-4 rounded-xl border border-[var(--border-color)]">
                      <table className="w-full border-collapse min-w-max">
                        <thead className="bg-[var(--bg-tertiary)]">
                          <tr>
                            {POSTS_TABLE_COLUMNS.map(({ key, label }) => (
                              <th key={key} className="py-2 px-3 text-left text-sm font-medium text-[var(--text-secondary)] whitespace-nowrap">
                                {label}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[var(--border-color)]">
                          {postsList.map((post) => (
                            <tr key={post.id} className="hover:bg-[var(--bg-tertiary)] transition-colors">
                              {POSTS_TABLE_COLUMNS.map(({ key }) => (
                                <td key={key} className="py-2 px-3 text-sm whitespace-nowrap">
                                  {formatPostCell(post, key)}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                  {postsList.length === 0 && !isLoadingPostsList && !postsListError && (
                    <p className="text-[var(--text-muted)] text-sm mt-2">Нажмите «Загрузить таблицу posts», чтобы загрузить данные.</p>
                  )}
                </div>
              </div>
            )}

            {!postsTables && !isLoadingPostsTables && !postsTablesError && (
              <div className="space-y-6">
                <p className="text-[var(--text-muted)] text-center py-4">Нажмите «Load Posts Tables» для сводки метрик.</p>
                <div className="border-t border-[var(--border-color)] pt-6">
                  <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Таблица posts (все столбцы)</h3>
                  <Button onClick={handleLoadPostsList} isLoading={isLoadingPostsList} className="w-full sm:w-auto">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Загрузить таблицу posts
                  </Button>
                  {postsListError && <Alert variant="error" className="mt-2">{postsListError}</Alert>}
                  {postsList.length > 0 && (
                    <div className="overflow-x-auto mt-4 rounded-xl border border-[var(--border-color)]">
                      <table className="w-full border-collapse min-w-max">
                        <thead className="bg-[var(--bg-tertiary)]">
                          <tr>
                            {POSTS_TABLE_COLUMNS.map(({ key, label }) => (
                              <th key={key} className="py-2 px-3 text-left text-sm font-medium text-[var(--text-secondary)] whitespace-nowrap">{label}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[var(--border-color)]">
                          {postsList.map((post) => (
                            <tr key={post.id} className="hover:bg-[var(--bg-tertiary)] transition-colors">
                              {POSTS_TABLE_COLUMNS.map(({ key }) => (
                                <td key={key} className="py-2 px-3 text-sm whitespace-nowrap">{formatPostCell(post, key)}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Posting diagnostics Tab */}
      {activeTab === 'posting-diagnostics' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
              Диагностика постинга (Telegram)
            </CardTitle>
            <CardDescription>
              Сводки по tg_posts и posts по статусам и подсказки при застревании постов в collected
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <Button
              onClick={handleRunPostingDiagnostics}
              isLoading={isLoadingPostingDiagnostics}
              className="w-full sm:w-auto"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Запустить диагностику
            </Button>

            <div className="flex flex-wrap gap-3 items-center">
              <span className="text-sm font-medium text-[var(--text-secondary)]">Быстрые действия:</span>
              <Button
                variant="secondary"
                size="sm"
                onClick={handleRunCollectCycle}
                isLoading={isRunningCollect}
              >
                Запустить сбор (collect)
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={handleRunDistributeCycle}
                isLoading={isRunningDistribute}
              >
                Запустить распределение (distribute)
              </Button>
              <span className="text-xs text-[var(--text-muted)]">
                Цикл обработки — на вкладке Processor
              </span>
            </div>
            {(collectMessage || collectError) && (
              <Alert variant={collectError ? 'error' : 'success'} className="animate-slide-down">
                {collectError || collectMessage}
              </Alert>
            )}
            {(distributeMessage || distributeError) && (
              <Alert variant={distributeError ? 'error' : 'success'} className="animate-slide-down">
                {distributeError || distributeMessage}
              </Alert>
            )}

            {postingDiagnosticsError && (
              <Alert variant="error" className="animate-slide-down">
                {postingDiagnosticsError}
              </Alert>
            )}

            {postingDiagnostics && (
              <div className="space-y-6 animate-slide-down">
                {postingDiagnostics.collected_at && (
                  <p className="text-sm text-[var(--text-muted)]">
                    Собрано: {new Date(postingDiagnostics.collected_at).toLocaleString()}
                  </p>
                )}

                <div>
                  <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">tg_posts по статусам</h3>
                  <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
                    <table className="w-full">
                      <thead className="bg-[var(--bg-tertiary)]">
                        <tr>
                          <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Статус</th>
                          <th className="py-3 px-4 text-right text-sm font-medium text-[var(--text-secondary)]">Количество</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[var(--border-color)]">
                        {postingDiagnostics.tg_posts_by_status.length === 0 ? (
                          <tr>
                            <td colSpan={2} className="py-3 px-4 text-[var(--text-muted)] text-sm">Нет данных</td>
                          </tr>
                        ) : (
                          postingDiagnostics.tg_posts_by_status.map((row) => (
                            <tr key={row.status} className="hover:bg-[var(--bg-tertiary)]">
                              <td className="py-3 px-4 text-[var(--text-primary)] font-medium">{row.status}</td>
                              <td className="py-3 px-4 text-right text-[var(--text-secondary)]">{row.count.toLocaleString()}</td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">posts по статусам и платформе</h3>
                  <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
                    <table className="w-full">
                      <thead className="bg-[var(--bg-tertiary)]">
                        <tr>
                          <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Статус</th>
                          <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Платформа</th>
                          <th className="py-3 px-4 text-right text-sm font-medium text-[var(--text-secondary)]">Количество</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[var(--border-color)]">
                        {postingDiagnostics.posts_by_status.length === 0 ? (
                          <tr>
                            <td colSpan={3} className="py-3 px-4 text-[var(--text-muted)] text-sm">Нет данных</td>
                          </tr>
                        ) : (
                          postingDiagnostics.posts_by_status.map((row, idx) => (
                            <tr key={`${row.status}-${row.source_platform ?? ''}-${idx}`} className="hover:bg-[var(--bg-tertiary)]">
                              <td className="py-3 px-4 text-[var(--text-primary)] font-medium">{row.status}</td>
                              <td className="py-3 px-4 text-[var(--text-secondary)]">{row.source_platform ?? '—'}</td>
                              <td className="py-3 px-4 text-right text-[var(--text-secondary)]">{row.count.toLocaleString()}</td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="flex flex-wrap gap-4">
                  <span className="px-3 py-1.5 rounded-lg bg-[var(--bg-tertiary)] text-[var(--text-secondary)] text-sm">
                    Готовы к публикации в TG: <strong className="text-[var(--text-primary)]">{postingDiagnostics.ready_for_telegram.toLocaleString()}</strong>
                  </span>
                  <span className="px-3 py-1.5 rounded-lg bg-[var(--bg-tertiary)] text-[var(--text-secondary)] text-sm">
                    Профилей с каналом: <strong className="text-[var(--text-primary)]">{postingDiagnostics.profiles_with_channel.toLocaleString()}</strong>
                  </span>
                </div>

                {postingDiagnostics.hints.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Рекомендации</h3>
                    <ul className="space-y-2">
                      {postingDiagnostics.hints.map((hint, idx) => (
                        <li key={idx} className="flex gap-2 text-sm text-[var(--text-secondary)]">
                          <span className="text-amber-400 shrink-0">•</span>
                          <span>{hint}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {!postingDiagnostics && !isLoadingPostingDiagnostics && !postingDiagnosticsError && (
              <p className="text-[var(--text-muted)] text-center py-8">
                Нажмите «Запустить диагностику», чтобы получить сводки и подсказки по пайплайну постинга.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Runtime: public IP, geo by IP, container TZ */}
      {activeTab === 'runtime-location' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              IP, регион и часовой пояс (core)
            </CardTitle>
            <CardDescription>
              Публичный исходящий IP и геоданные по нему — ориентир «откуда виден трафик». Часовой пояс процесса core и переменная TZ — фактическая настройка контейнера.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <Button
              onClick={handleLoadRuntimeLocation}
              isLoading={isLoadingRuntimeLocation}
              className="w-full sm:w-auto"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Обновить
            </Button>

            {runtimeLocationError && (
              <Alert variant="error" className="animate-slide-down">{runtimeLocationError}</Alert>
            )}

            {isLoadingRuntimeLocation && <TableSkeleton rows={4} cols={2} className="mt-2" />}

            {runtimeLocation && !isLoadingRuntimeLocation && (
              <div className="space-y-6 animate-slide-down">
                <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                  <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-3">Публичный IP и гео</h3>
                  <ul className="text-sm text-[var(--text-secondary)] space-y-2">
                    <li>
                      <span className="text-[var(--text-muted)]">Публичный IP: </span>
                      <span className="font-mono text-[var(--text-primary)]">{runtimeLocation.public_ip ?? '—'}</span>
                    </li>
                    {runtimeLocation.public_lookup_error && (
                      <li className="text-amber-400 text-sm">Ошибка определения IP: {runtimeLocation.public_lookup_error}</li>
                    )}
                    {runtimeLocation.geo_by_ip && (
                      <>
                        <li><span className="text-[var(--text-muted)]">Страна: </span>{runtimeLocation.geo_by_ip.country ?? '—'}</li>
                        <li><span className="text-[var(--text-muted)]">Регион: </span>{runtimeLocation.geo_by_ip.region ?? '—'}</li>
                        <li><span className="text-[var(--text-muted)]">Город: </span>{runtimeLocation.geo_by_ip.city ?? '—'}</li>
                        <li>
                          <span className="text-[var(--text-muted)]">Часовой пояс (по IP, ориентир): </span>
                          <span className="font-mono">{runtimeLocation.geo_by_ip.timezone ?? '—'}</span>
                        </li>
                        <li><span className="text-[var(--text-muted)]">Провайдер / org: </span>{runtimeLocation.geo_by_ip.isp ?? '—'}</li>
                      </>
                    )}
                    {runtimeLocation.geo_lookup_error && !runtimeLocation.geo_by_ip && (
                      <li className="text-amber-400 text-sm">Ошибка геолокации: {runtimeLocation.geo_lookup_error}</li>
                    )}
                  </ul>
                </div>

                <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                  <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-3">Контейнер / процесс core</h3>
                  <ul className="text-sm text-[var(--text-secondary)] space-y-2">
                    <li><span className="text-[var(--text-muted)]">Hostname: </span><span className="font-mono text-[var(--text-primary)]">{runtimeLocation.hostname}</span></li>
                    <li>
                      <span className="text-[var(--text-muted)]">TZ (переменная окружения): </span>
                      <span className="font-mono">{runtimeLocation.tz_environment_variable ?? '—'}</span>
                    </li>
                    <li>
                      <span className="text-[var(--text-muted)]">Локальный часовой пояс: </span>
                      <span className="font-mono text-[var(--text-primary)]">{runtimeLocation.local_timezone}</span>
                      {' '}(UTC{runtimeLocation.local_utc_offset})
                    </li>
                    <li>
                      <span className="text-[var(--text-muted)]">Текущее время (core): </span>
                      {runtimeLocation.local_now_iso}
                    </li>
                    {runtimeLocation.cloud_aws_region && (
                      <li>
                        <span className="text-[var(--text-muted)]">AWS_REGION / AWS_DEFAULT_REGION: </span>
                        <span className="font-mono text-[var(--text-primary)]">{runtimeLocation.cloud_aws_region}</span>
                      </li>
                    )}
                  </ul>
                </div>
              </div>
            )}

            {!runtimeLocation && !isLoadingRuntimeLocation && !runtimeLocationError && (
              <p className="text-[var(--text-muted)] text-center py-8">
                Нажмите «Обновить», чтобы запросить данные с сервиса core.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* S3 Storage Tab */}
      {activeTab === 'storage' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
              </svg>
              S3 Storage (файлы хранилища)
            </CardTitle>
            <CardDescription>
              Список файлов в едином S3-хранилище (MinIO / AWS S3). Префикс — фильтр по началу ключа. Режим «diag» показывает только объекты, в имени ключа которых есть подстрока «diag» (диагностические скриншоты при ошибках Selenium, см. vk/tw/instagram боты).
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-3 items-center">
              <Input
                placeholder="Префикс (например vk/ или uploads/)"
                value={storagePrefix}
                onChange={(e) => setStoragePrefix(e.target.value)}
                className="max-w-xs"
              />
              <label className="flex items-center gap-2 text-sm text-[var(--text-secondary)] cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={storageDiagOnly}
                  onChange={(e) => setStorageDiagOnly(e.target.checked)}
                  className="rounded border-[var(--border-color)]"
                />
                Только диагностика Selenium (ключ содержит «diag»)
              </label>
              <Button onClick={handleLoadStorageFiles} isLoading={isLoadingStorageFiles}>
                Загрузить список файлов
              </Button>
            </div>
            {storageFiles?.filter_applied && (
              <p className="text-xs text-[var(--text-muted)]">
                Фильтр по ключу: «{storageFiles.filter_applied}»
                {storageFiles.pages_scanned != null ? ` · просмотрено страниц S3: ${storageFiles.pages_scanned}` : ''}
                {storageFiles.filter_truncated ? ' · список может быть неполным (лимит сканирования).' : ''}
              </p>
            )}

            {storageFilesError && (
              <Alert variant="error">{storageFilesError}</Alert>
            )}

            {storageFiles && !storageFiles.enabled && (
              <Alert variant="default">
                S3-хранилище не настроено (переменные S3_* не заданы или пусты).
              </Alert>
            )}

            {storageFiles?.enabled && (
              <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
                <table className="w-full">
                  <thead className="bg-[var(--bg-tertiary)]">
                    <tr>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Ключ</th>
                      <th className="py-3 px-4 text-right text-sm font-medium text-[var(--text-secondary)]">Размер</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Изменён</th>
                      <th className="py-3 px-4 text-right text-sm font-medium text-[var(--text-secondary)] min-w-[200px]">Действия</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-color)]">
                    {storageFiles.objects.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="py-3 px-4 text-[var(--text-muted)] text-sm">
                          Файлов нет{storagePrefix ? ` по префиксу «${storagePrefix}»` : ''}.
                        </td>
                      </tr>
                    ) : (
                      storageFiles.objects.map((obj: StorageFileItem) => (
                        <tr key={obj.key} className="hover:bg-[var(--bg-tertiary)]">
                          <td className="py-3 px-4 text-[var(--text-primary)] font-mono text-sm break-all">{obj.key}</td>
                          <td className="py-3 px-4 text-right text-[var(--text-secondary)] text-sm">
                            {obj.size >= 1024 ? `${(obj.size / 1024).toFixed(1)} KB` : `${obj.size} B`}
                          </td>
                          <td className="py-3 px-4 text-[var(--text-secondary)] text-sm">
                            {obj.last_modified ? new Date(obj.last_modified).toLocaleString() : '—'}
                          </td>
                          <td className="py-3 px-4 text-right">
                            <div className="flex flex-wrap justify-end gap-2">
                              <Button
                                type="button"
                                variant="secondary"
                                size="sm"
                                isLoading={storageOpeningKey === obj.key}
                                disabled={storageOpeningKey !== null && storageOpeningKey !== obj.key}
                                onClick={() => handleOpenStorageFile(obj.key)}
                              >
                                Открыть
                              </Button>
                              <Button
                                type="button"
                                variant="danger"
                                size="sm"
                                isLoading={storageDeletingKey === obj.key}
                                disabled={storageDeletingKey !== null && storageDeletingKey !== obj.key}
                                onClick={() => handleDeleteStorageFile(obj.key)}
                              >
                                Удалить
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {!storageFiles && !isLoadingStorageFiles && !storageFilesError && (
              <p className="text-[var(--text-muted)] text-center py-8">
                Нажмите «Загрузить список файлов», чтобы проверить содержимое S3.
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </PageContainer>
  )
}
