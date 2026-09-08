import { useState, FormEvent, Fragment, useEffect, useRef, type ReactNode } from 'react'
import { useSearchParams, Navigate } from 'react-router-dom'
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
import { GuideBlocksAdmin } from '@/pages/administration/guide-blocks-admin'
import { AdministrationBillingPanel } from '@/pages/administration/administration-billing'
import { Input } from '@/components/ui/input'
import type { User, RoleTariffHistoryEntry, GroupResponse, AdminAuditLogEntry, AdminProductMetrics } from '@/types/auth'
import type {
  UserStatisticsItem,
  Notification,
  Feedback,
  PostsTablesResponse,
  PostRow,
  PipelineEventsResponse,
  PipelineEventItem,
  StorageFileItem,
  StorageFilesResponse,
  RuntimeLocationResponse,
} from '@/types/core'
import { FEEDBACK_TYPE_LABELS } from '@/types/core'
import { platformStatusCell, platformTableStatusColumns } from '@/pages/checks/checks-utils'
import { formatDateTime } from '@/utils/date'

type AdminTab = 'users' | 'notifications' | 'feedback' | 'guide' | 'posts-tables' | 'runtime-location' | 'storage'
type UsersSubTab = 'management' | 'billing' | 'groups' | 'audit' | 'statistics' | 'growth'

const ADMIN_TABS: AdminTab[] = [
  'users',
  'notifications',
  'feedback',
  'guide',
  'posts-tables',
  'runtime-location',
  'storage',
]

const USERS_SUB_TABS: { id: UsersSubTab; label: string }[] = [
  { id: 'management', label: 'Users Management' },
  { id: 'billing', label: 'Billing' },
  { id: 'groups', label: 'Groups' },
  { id: 'audit', label: 'Audit Log' },
  { id: 'statistics', label: 'Statistics' },
  { id: 'growth', label: 'Growth / UTM' },
]

function formatEngagement(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds <= 0) {
    return '0 мин'
  }
  if (seconds < 60) {
    return `${Math.round(seconds)} сек`
  }
  const totalMinutes = Math.round(seconds / 60)
  if (totalMinutes < 120) {
    return `${totalMinutes} мин`
  }
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.round((seconds % 3600) / 60)
  return minutes > 0 ? `${hours} ч ${minutes} мин` : `${hours} ч`
}

function formatRatio(value: number | null): string {
  if (value == null || !Number.isFinite(value)) {
    return '—'
  }
  return `${(value * 100).toFixed(1)}%`
}

export function AdministrationPage() {
  const { user: currentUser } = useAuth()
  const [searchParams] = useSearchParams()
  const [activeTab, setActiveTab] = useState<AdminTab>('users')
  const [usersSubTab, setUsersSubTab] = useState<UsersSubTab>('management')
  const [users, setUsers] = useState<User[]>([])
  const [statistics, setStatistics] = useState<UserStatisticsItem[]>([])
  const [isLoadingUsers, setIsLoadingUsers] = useState(false)
  const [isLoadingStatistics, setIsLoadingStatistics] = useState(false)
  const [usersError, setUsersError] = useState('')
  const [savingUserId, setSavingUserId] = useState<number | null>(null)
  const [blockingUserId, setBlockingUserId] = useState<number | null>(null)
  const [userUpdateError, setUserUpdateError] = useState('')
  const [userUpdateNotice, setUserUpdateNotice] = useState('')
  const savedTariffsRef = useRef<Record<number, string>>({})
  const [expandedHistoryUserId, setExpandedHistoryUserId] = useState<number | null>(null)
  const [historyList, setHistoryList] = useState<RoleTariffHistoryEntry[]>([])
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [historyError, setHistoryError] = useState('')
  const ROLES = ['guest', 'user', 'admin', 'manager', 'author'] as const
  const TARIFFS = ['free', 'standard', 'full']
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
  const [growthSummary, setGrowthSummary] = useState<{
    total_registrations: number
    s01_registrations: number
    by_campaign: Array<{ utm_campaign: string; registrations: number }>
  } | null>(null)
  const [isLoadingGrowth, setIsLoadingGrowth] = useState(false)
  const [growthError, setGrowthError] = useState('')
  const [productMetrics, setProductMetrics] = useState<AdminProductMetrics | null>(null)
  const [isLoadingProductMetrics, setIsLoadingProductMetrics] = useState(false)
  const [productMetricsError, setProductMetricsError] = useState('')

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

  // Posts tables (admin)
  const [postsTables, setPostsTables] = useState<PostsTablesResponse | null>(null)
  const [isLoadingPostsTables, setIsLoadingPostsTables] = useState(false)
  const [postsTablesError, setPostsTablesError] = useState('')

  // Full posts table (admin)
  const [postsList, setPostsList] = useState<PostRow[]>([])
  const [isLoadingPostsList, setIsLoadingPostsList] = useState(false)
  const [postsListError, setPostsListError] = useState('')
  const [pipelineEvents, setPipelineEvents] = useState<PipelineEventsResponse | null>(null)
  const [isLoadingPipelineEvents, setIsLoadingPipelineEvents] = useState(false)
  const [pipelineEventsError, setPipelineEventsError] = useState('')

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
      savedTariffsRef.current = Object.fromEntries(
        data
          .filter((u) => u.id != null)
          .map((u) => [u.id as number, (u.tariff ?? 'free').toLowerCase()]),
      )
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

  async function handleLoadGrowthSummary() {
    setGrowthError('')
    setIsLoadingGrowth(true)
    try {
      const data = await authService.getGrowthSummary(50)
      setGrowthSummary(data)
    } catch (error) {
      setGrowthError(error instanceof Error ? error.message : 'Failed to load growth summary')
      setGrowthSummary(null)
    } finally {
      setIsLoadingGrowth(false)
    }
  }

  async function handleLoadProductMetrics() {
    setProductMetricsError('')
    setIsLoadingProductMetrics(true)
    try {
      const data = await authService.getProductMetrics()
      setProductMetrics(data)
    } catch (error) {
      setProductMetricsError(error instanceof Error ? error.message : 'Failed to load product metrics')
      setProductMetrics(null)
    } finally {
      setIsLoadingProductMetrics(false)
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
    setUserUpdateNotice('')
    setSavingUserId(user.id)
    try {
      const baseline = savedTariffsRef.current[user.id] ?? 'free'
      const nextTariff = (user.tariff ?? 'free').toLowerCase()
      const updated = await authService.updateUser(user.id, {
        role: user.role,
      })
      if (nextTariff !== baseline) {
        if (nextTariff !== 'free' && nextTariff !== 'standard' && nextTariff !== 'full') {
          throw new Error('Неизвестный тариф')
        }
        await authService.adminCreatePlanRequest(user.id, nextTariff)
        setUsers((prev) =>
          prev.map((u) =>
            u.id === user.id ? { ...u, ...updated, tariff: baseline } : u
          )
        )
        setUserUpdateNotice(
          `Заявка на тариф ${nextTariff} создана. Счёт или включение тарифа — во вкладке Billing.`,
        )
        return
      }
      setUsers((prev) =>
        prev.map((u) => (u.id === user.id ? { ...u, ...updated } : u))
      )
      setUserUpdateNotice('Роль сохранена')
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

  async function handleLoadPostsTables() {
    setPostsTablesError('')
    setIsLoadingPostsTables(true)
    try {
      const data = await coreService.getPostsTablesOverview()
      setPostsTables(data)
    } catch (error) {
      setPostsTablesError(error instanceof Error ? error.message : 'Failed to fetch posts tables')
      setPostsTables(null)
    } finally {
      setIsLoadingPostsTables(false)
    }
  }

  async function handleLoadPipelineEvents() {
    setPipelineEventsError('')
    setIsLoadingPipelineEvents(true)
    try {
      const data = await coreService.getPipelineEvents(50)
      setPipelineEvents(data)
    } catch (error) {
      setPipelineEventsError(error instanceof Error ? error.message : 'Failed to fetch pipeline events')
      setPipelineEvents(null)
    } finally {
      setIsLoadingPipelineEvents(false)
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

  // Подгрузка обратной связи при открытии вкладки
  useEffect(() => {
    if (activeTab === 'feedback') {
      void loadFeedback()
    }
  }, [activeTab])

  useEffect(() => {
    if (activeTab !== 'users' || usersSubTab !== 'statistics') {
      return
    }
    let cancelled = false
    setProductMetricsError('')
    setIsLoadingProductMetrics(true)
    void authService
      .getProductMetrics()
      .then((data) => {
        if (!cancelled) setProductMetrics(data)
      })
      .catch((error) => {
        if (!cancelled) {
          setProductMetricsError(error instanceof Error ? error.message : 'Failed to load product metrics')
          setProductMetrics(null)
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoadingProductMetrics(false)
      })
    return () => {
      cancelled = true
    }
  }, [activeTab, usersSubTab])

  useEffect(() => {
    const tabParam = searchParams.get('tab')
    if (tabParam === 'schedule') {
      return
    }
    if (tabParam === 'audit' || tabParam === 'groups' || tabParam === 'statistics' || tabParam === 'billing') {
      setActiveTab('users')
      setUsersSubTab(tabParam)
      return
    }
    if (tabParam && ADMIN_TABS.includes(tabParam as AdminTab)) {
      setActiveTab(tabParam as AdminTab)
    }
    const subParam = searchParams.get('sub')
    if (
      subParam === 'management' ||
      subParam === 'billing' ||
      subParam === 'groups' ||
      subParam === 'audit' ||
      subParam === 'statistics'
    ) {
      setUsersSubTab(subParam)
    }
  }, [searchParams])

  if (searchParams.get('tab') === 'schedule') {
    return <Navigate to="/checks/scheduler" replace />
  }

  const POSTS_TABLE_COLUMNS: { key: keyof PostRow; label: string }[] = [
    { key: 'id', label: 'ID' },
    { key: 'user_id', label: 'User ID' },
    { key: 'status', label: 'Status' },
    { key: 'published_channel', label: 'Published Channel' },
    { key: 'source_platform', label: 'Source Platform' },
    { key: 'source_id', label: 'Source ID' },
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
    { key: 'post_type', label: 'Post Type' },
    { key: 'to_tg', label: 'To TG' },
    { key: 'to_tw', label: 'To TW' },
    { key: 'to_wp', label: 'To WP' },
    { key: 'to_vk', label: 'To VK' },
    { key: 'created_at', label: 'Created At' },
    { key: 'updated_at', label: 'Updated At' },
  ]

  function formatPostCell(post: PostRow, key: keyof PostRow): ReactNode {
    const v = post[key]
    if (v === null || v === undefined) return <span className="text-[var(--text-muted)]">—</span>
    if (key === 'post_date' || key === 'created_at' || key === 'updated_at') {
      return <span className="text-[var(--text-secondary)] whitespace-nowrap">{formatDateTime(String(v))}</span>
    }
    if (key === 'images') {
      const arr = Array.isArray(v) ? v : []
      return <span className="text-[var(--text-secondary)]">{arr.length} items</span>
    }
    if (key === 'published_channel') {
      return <span className="text-primary-400 font-mono text-xs">{String(v)}</span>
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

  function renderPipelineEventsTable(
    title: string,
    description: string,
    rows: PipelineEventItem[],
    mode: 'channel' | 'service' = 'channel',
  ) {
    return (
      <div>
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-1">{title}</h3>
        <p className="text-sm text-[var(--text-muted)] mb-2">{description}</p>
        {rows.length === 0 ? (
          <p className="text-sm text-[var(--text-muted)]">Нет событий</p>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
            <table className="w-full min-w-max">
              <thead className="bg-[var(--bg-tertiary)]">
                <tr>
                  <th className="py-2 px-3 text-left text-xs font-medium text-[var(--text-secondary)]">Time</th>
                  {mode === 'service' ? (
                    <>
                      <th className="py-2 px-3 text-left text-xs font-medium text-[var(--text-secondary)]">Service</th>
                      <th className="py-2 px-3 text-left text-xs font-medium text-[var(--text-secondary)]">Cycle</th>
                      <th className="py-2 px-3 text-left text-xs font-medium text-[var(--text-secondary)]">Status</th>
                      <th className="py-2 px-3 text-right text-xs font-medium text-[var(--text-secondary)]">Items</th>
                    </>
                  ) : (
                    <>
                      <th className="py-2 px-3 text-left text-xs font-medium text-[var(--text-secondary)]">Channel</th>
                      <th className="py-2 px-3 text-left text-xs font-medium text-[var(--text-secondary)]">Type</th>
                      <th className="py-2 px-3 text-left text-xs font-medium text-[var(--text-secondary)]">User</th>
                    </>
                  )}
                  <th className="py-2 px-3 text-left text-xs font-medium text-[var(--text-secondary)]">Summary</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-color)]">
                {rows.map((ev, idx) => (
                  <tr key={`${ev.id ?? idx}-${ev.channel ?? ''}-${ev.created_at ?? idx}`} className="hover:bg-[var(--bg-tertiary)]">
                    <td className="py-2 px-3 text-xs text-[var(--text-secondary)] whitespace-nowrap">
                      {ev.created_at ? formatDateTime(ev.created_at) : '—'}
                    </td>
                    {mode === 'service' ? (
                      <>
                        <td className="py-2 px-3 text-sm text-[var(--text-primary)] font-medium">{ev.service ?? '—'}</td>
                        <td className="py-2 px-3 text-sm text-[var(--text-secondary)]">{ev.cycle_type ?? '—'}</td>
                        <td className="py-2 px-3 text-sm text-[var(--text-secondary)]">{ev.status ?? '—'}</td>
                        <td className="py-2 px-3 text-sm text-right tabular-nums text-[var(--text-secondary)]">{ev.items_processed ?? 0}</td>
                      </>
                    ) : (
                      <>
                        <td className="py-2 px-3 text-sm font-mono text-primary-400 max-w-[220px] truncate" title={ev.channel ?? ''}>
                          {ev.channel ?? '—'}
                        </td>
                        <td className="py-2 px-3 text-sm text-[var(--text-secondary)]">{ev.event_type ?? ev.platform ?? '—'}</td>
                        <td className="py-2 px-3 text-sm text-[var(--text-secondary)]">{ev.user_id ?? '—'}</td>
                      </>
                    )}
                    <td className="py-2 px-3 text-sm text-[var(--text-muted)] max-w-[320px] truncate" title={ev.summary ?? ''}>
                      {ev.summary || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    )
  }

  return (
    <PageContainer maxWidth="wide">
      <PageHeader
        title="Administration"
        description="Пользователи и группы, статистика, уведомления, таблицы постов, S3 и сведения о окружении. Мониторинг сервисов и расписания — в разделе Checks."
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
          onClick={() => setActiveTab('guide')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'guide'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          Справка
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

      {/* Users Tab: Management / Groups / Audit Log */}
      {activeTab === 'users' && (
        <div className="space-y-4 animate-slide-up">
          <div className="flex flex-wrap gap-1 border-b border-[var(--border-color)]">
            {USERS_SUB_TABS.map((sub) => (
              <button
                key={sub.id}
                type="button"
                onClick={() => setUsersSubTab(sub.id)}
                className={`px-3 py-2 text-sm font-medium transition-colors ${
                  usersSubTab === sub.id
                    ? 'text-primary-400 border-b-2 border-primary-400'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                }`}
              >
                {sub.label}
              </button>
            ))}
          </div>

          {usersSubTab === 'billing' && <AdministrationBillingPanel />}

          {usersSubTab === 'management' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
              Users Management
            </CardTitle>
            <CardDescription>
              Роль сохраняется сразу. Смена тарифа создаёт заявку — счёт или включение во вкладке Billing.
            </CardDescription>
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
            {userUpdateNotice && (
              <Alert variant="success" className="animate-slide-down">
                {userUpdateNotice}
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
                            {formatDateTime(user.created_at)}
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
                                            {formatDateTime(entry.changed_at)}
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

          {usersSubTab === 'audit' && (
        <Card>
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
                          {formatDateTime(row.created_at)}
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

          {usersSubTab === 'growth' && (
        <Card>
          <CardHeader>
            <CardTitle>Growth / UTM</CardTitle>
            <CardDescription>
              Регистрации по utm_campaign (воронка S01 → CopyParse)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button onClick={handleLoadGrowthSummary} isLoading={isLoadingGrowth} className="w-full sm:w-auto">
              Load growth summary
            </Button>
            {growthError && (
              <Alert variant="error" className="animate-slide-down">
                {growthError}
              </Alert>
            )}
            {growthSummary && (
              <div className="space-y-3">
                <p className="text-sm text-[var(--text-secondary)]">
                  Всего регистраций: <strong>{growthSummary.total_registrations}</strong>
                  {' · '}
                  из S01 (campaign s01*): <strong>{growthSummary.s01_registrations}</strong>
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse text-sm">
                    <thead>
                      <tr className="border-b border-[var(--border-color)]">
                        <th className="text-left py-2 px-3">utm_campaign</th>
                        <th className="text-left py-2 px-3">Registrations</th>
                      </tr>
                    </thead>
                    <tbody>
                      {growthSummary.by_campaign.map((row) => (
                        <tr key={row.utm_campaign} className="border-b border-[var(--border-color)]">
                          <td className="py-2 px-3 font-mono text-xs">{row.utm_campaign}</td>
                          <td className="py-2 px-3">{row.registrations}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            {!growthSummary && !isLoadingGrowth && !growthError && (
              <EmptyState
                title="No data loaded"
                description='Click "Load growth summary" to fetch UTM registration stats.'
              />
            )}
          </CardContent>
        </Card>
          )}

          {usersSubTab === 'groups' && (
        <Card>
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
                        ID: {group.id} · Создана: {formatDateTime(group.created_at)}
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

          {usersSubTab === 'statistics' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Product metrics
            </CardTitle>
            <CardDescription>
              Active Users, Engagement, Retention и Conversion за последние 30 / 60 дней
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              onClick={handleLoadProductMetrics}
              isLoading={isLoadingProductMetrics}
              className="w-full sm:w-auto"
            >
              Refresh metrics
            </Button>
            {productMetricsError && (
              <Alert variant="error" className="animate-slide-down">
                {productMetricsError}
              </Alert>
            )}
            {productMetrics && (
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
                <div className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-tertiary)] p-4">
                  <p className="text-sm text-[var(--text-muted)]">Active Users</p>
                  <p className="mt-1 text-2xl font-semibold text-[var(--text-primary)]">
                    {productMetrics.active_users_30d.toLocaleString()}
                  </p>
                  <p className="mt-2 text-xs text-[var(--text-secondary)]">
                    Уникальные пользователи, заходившие в сервис за последние 30 дней
                  </p>
                </div>
                <div className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-tertiary)] p-4">
                  <p className="text-sm text-[var(--text-muted)]">Engagement</p>
                  <p className="mt-1 text-2xl font-semibold text-[var(--text-primary)]">
                    {formatEngagement(productMetrics.engagement_seconds)}
                  </p>
                  <p className="mt-2 text-xs text-[var(--text-secondary)]">
                    Среднее время в приложении за 30 дней на одного активного пользователя
                  </p>
                </div>
                <div className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-tertiary)] p-4">
                  <p className="text-sm text-[var(--text-muted)]">Retention</p>
                  <p className="mt-1 text-2xl font-semibold text-[var(--text-primary)]">
                    {formatRatio(productMetrics.retention)}
                  </p>
                  <p className="mt-2 text-xs text-[var(--text-secondary)]">
                    {productMetrics.active_users_30d.toLocaleString()} / {productMetrics.active_users_60d.toLocaleString()} активных за 30 / 60 дней
                  </p>
                </div>
                <div className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-tertiary)] p-4">
                  <p className="text-sm text-[var(--text-muted)]">Conversion</p>
                  <p className="mt-1 text-2xl font-semibold text-[var(--text-primary)]">
                    {formatRatio(productMetrics.conversion)}
                  </p>
                  <p className="mt-2 text-xs text-[var(--text-secondary)]">
                    {productMetrics.paid_active_users_30d.toLocaleString()} / {productMetrics.paid_active_users_60d.toLocaleString()} активных на платных тарифах за 30 / 60 дней
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
        )}
          {usersSubTab === 'statistics' && (
        <Card>
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
        </div>
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
                            {formatDateTime(notification.created_at)}
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

      {activeTab === 'guide' && <GuideBlocksAdmin />}

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
            <CardDescription>Обзор таблиц постов, события пайплайна и полная таблица posts</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex flex-wrap gap-2">
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
              <Button
                onClick={handleLoadPipelineEvents}
                isLoading={isLoadingPipelineEvents}
                variant="secondary"
                className="w-full sm:w-auto"
              >
                Загрузить события пайплайна
              </Button>
            </div>

            {postsTablesError && (
              <Alert variant="error" className="animate-slide-down">{postsTablesError}</Alert>
            )}
            {pipelineEventsError && (
              <Alert variant="error" className="animate-slide-down">{pipelineEventsError}</Alert>
            )}

            {pipelineEvents && (
              <div className="space-y-6 animate-slide-down border border-[var(--border-color)] rounded-xl p-4 bg-[var(--bg-secondary)]">
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <h3 className="text-lg font-semibold text-[var(--text-primary)]">Диагностика срабатываний</h3>
                  {pipelineEvents.collected_at && (
                    <span className="text-xs text-[var(--text-muted)]">
                      Обновлено: {formatDateTime(pipelineEvents.collected_at)}
                    </span>
                  )}
                </div>
                {pipelineEvents.services_error && (
                  <Alert variant="error">Service log: {pipelineEvents.services_error}</Alert>
                )}
                {renderPipelineEventsTable(
                  'Alerting',
                  'Срабатывания алертов с каналом назначения (или source chat).',
                  pipelineEvents.alerting,
                )}
                {renderPipelineEventsTable(
                  'Publishing',
                  'Публикации в Telegram: по одной строке на каждый канал (telegram_chat_id / target_channels).',
                  pipelineEvents.publishing,
                )}
                {renderPipelineEventsTable(
                  'Collection (Parser)',
                  'Сбор сообщений из каналов (parser / chats_to_read).',
                  pipelineEvents.collection,
                )}
                {renderPipelineEventsTable(
                  'Custom URL',
                  'Срабатывания url-bot / url_posts (в колонке Channel — URL).',
                  pipelineEvents.custom_url,
                )}
                {renderPipelineEventsTable(
                  'Scheduler / Collector / Processor',
                  'Циклы фоновых сервисов (service_cycle_log).',
                  pipelineEvents.services,
                  'service',
                )}
              </div>
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
                            {obj.last_modified ? formatDateTime(obj.last_modified) : '—'}
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
