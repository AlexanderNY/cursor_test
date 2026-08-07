import { FormEvent, useEffect, useState } from 'react'
import { useAuth } from '@/contexts/auth-context'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import { SkeletonCard } from '@/components/ui/skeleton'
import { authService } from '@/services/auth-service'
import { coreService } from '@/services/core-service'
import type { GroupResponse, GroupMemberResponse } from '@/types/auth'
import type { UserStatisticsItem } from '@/types/core'
import { isGroupAdmin, roleLabel, type GroupRole } from '@/types/smm'

export function TeamPage() {
  const { user, refreshUserData } = useAuth()
  const [group, setGroup] = useState<GroupResponse | null>(null)
  const [groupError, setGroupError] = useState('')
  const [isLoadingGroup, setIsLoadingGroup] = useState(true)
  const [createName, setCreateName] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  const [editName, setEditName] = useState('')
  const [isSavingName, setIsSavingName] = useState(false)
  const [addEmail, setAddEmail] = useState('')
  const [addRole, setAddRole] = useState<GroupRole>('editor')
  const [isAddingMember, setIsAddingMember] = useState(false)
  const [addError, setAddError] = useState('')
  const [removingUserId, setRemovingUserId] = useState<number | null>(null)
  const [statistics, setStatistics] = useState<UserStatisticsItem[]>([])
  const [isLoadingStats, setIsLoadingStats] = useState(false)
  const [statsError, setStatsError] = useState('')

  const roleInGroup = group?.role_in_group ?? user?.role_in_group
  const isAdmin = isGroupAdmin(roleInGroup) || user?.role === 'admin'
  const canAccess =
    user?.role === 'manager' ||
    user?.role === 'author' ||
    user?.role === 'admin' ||
    !!user?.role_in_group ||
    !!user?.group_id

  async function loadGroup() {
    if (!canAccess) return
    setGroupError('')
    setIsLoadingGroup(true)
    try {
      const data = await authService.getMyGroup()
      setGroup(data)
      setEditName(data.name)
    } catch (e) {
      if ((e as { response?: { status?: number } })?.response?.status === 404) {
        setGroup(null)
      } else {
        setGroupError(e instanceof Error ? e.message : 'Failed to load group')
      }
    } finally {
      setIsLoadingGroup(false)
    }
  }

  useEffect(() => {
    void loadGroup()
  }, [user?.role, user?.id])

  async function handleCreateGroup(e: FormEvent) {
    e.preventDefault()
    if (!createName.trim()) return
    setAddError('')
    setIsCreating(true)
    try {
      const created = await authService.createGroup(createName.trim())
      setGroup(created)
      setEditName(created.name)
      setCreateName('')
      await refreshUserData()
    } catch (e) {
      setAddError(e instanceof Error ? e.message : 'Failed to create group')
    } finally {
      setIsCreating(false)
    }
  }

  async function handleSaveName(e: FormEvent) {
    e.preventDefault()
    if (!group || editName.trim() === group.name) return
    setIsSavingName(true)
    try {
      const updated = await authService.updateGroup(group.id, { name: editName.trim() })
      setGroup(updated)
      await refreshUserData()
    } finally {
      setIsSavingName(false)
    }
  }

  async function handleAddMember(e: FormEvent) {
    e.preventDefault()
    if (!group || !addEmail.trim()) return
    setAddError('')
    setIsAddingMember(true)
    try {
      await authService.addGroupMember(group.id, addEmail.trim(), addRole)
      const updated = await authService.getMyGroup()
      setGroup(updated)
      setAddEmail('')
      if (isAdmin) await loadStats()
    } catch (e) {
      setAddError(e instanceof Error ? e.message : 'Failed to add member')
    } finally {
      setIsAddingMember(false)
    }
  }

  async function handleRemoveMember(member: GroupMemberResponse) {
    if (!group || isGroupAdmin(member.role_in_group)) return
    setRemovingUserId(member.user_id)
    try {
      await authService.removeGroupMember(group.id, member.user_id)
      const updated = await authService.getMyGroup()
      setGroup(updated)
      await loadStats()
    } finally {
      setRemovingUserId(null)
    }
  }

  async function loadStats() {
    setStatsError('')
    setIsLoadingStats(true)
    try {
      const res = await coreService.getGroupStatistics()
      setStatistics(res.users || [])
    } catch (e) {
      setStatsError(e instanceof Error ? e.message : 'Failed to load statistics')
      setStatistics([])
    } finally {
      setIsLoadingStats(false)
    }
  }

  useEffect(() => {
    if (group && isAdmin) void loadStats()
  }, [group?.id, isAdmin])

  if (!canAccess) {
    return (
      <div className="max-w-2xl mx-auto py-8">
        <Alert variant="error">Access denied.</Alert>
      </div>
    )
  }

  if (isLoadingGroup) {
    return (
      <PageContainer>
        <PageHeader title="Team" description="Loading…" />
        <SkeletonCard />
      </PageContainer>
    )
  }

  if (groupError) {
    return (
      <div className="max-w-2xl mx-auto py-8">
        <Alert variant="error">{groupError}</Alert>
      </div>
    )
  }

  if (!group && (user?.role === 'manager' || user?.role === 'admin')) {
    return (
      <PageContainer>
        <PageHeader title="Team" description="Создайте команду с ролями Admin / Editor / Analyst" />
        <Card>
          <CardHeader>
            <CardTitle>Create team</CardTitle>
            <CardDescription>Вы станете Admin без передачи паролей участникам</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateGroup} className="space-y-4">
              <Input value={createName} onChange={(e) => setCreateName(e.target.value)} placeholder="Team name" />
              {addError && <Alert variant="error">{addError}</Alert>}
              <Button type="submit" disabled={!createName.trim() || isCreating}>
                {isCreating ? 'Creating…' : 'Create'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </PageContainer>
    )
  }

  if (!group) {
    return (
      <PageContainer>
        <PageHeader title="Team" description="Вас ещё не добавили в команду" />
        <p className="text-[var(--text-muted)]">Ожидайте приглашения по email.</p>
      </PageContainer>
    )
  }

  return (
    <PageContainer>
      <PageHeader
        title="Team"
        description={`Роль: ${roleLabel(roleInGroup)} · доступы без передачи паролей`}
      />

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>{group.name}</CardTitle>
          <CardDescription>
            Admin — полный доступ · Editor — публикация · Analyst — только аналитика/инбокс (read)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isAdmin && (
            <form onSubmit={handleSaveName} className="flex flex-wrap items-end gap-2">
              <Input label="Name" value={editName} onChange={(e) => setEditName(e.target.value)} />
              <Button type="submit" disabled={isSavingName || editName.trim() === group.name}>
                Save
              </Button>
            </form>
          )}

          {isAdmin && (
            <form onSubmit={handleAddMember} className="flex flex-wrap items-end gap-2">
              <Input
                label="Invite by email"
                value={addEmail}
                onChange={(e) => setAddEmail(e.target.value)}
                placeholder="user@example.com"
              />
              <div>
                <label className="text-sm text-[var(--text-secondary)]">Role</label>
                <select
                  className="block mt-1 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2"
                  value={addRole}
                  onChange={(e) => setAddRole(e.target.value as GroupRole)}
                >
                  <option value="editor">Editor</option>
                  <option value="analyst">Analyst</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <Button type="submit" disabled={isAddingMember || !addEmail.trim()}>
                Invite
              </Button>
              {addError && <Alert variant="error">{addError}</Alert>}
            </form>
          )}

          <ul className="divide-y divide-[var(--border-color)]">
            {group.members?.map((m) => (
              <li key={m.user_id} className="flex justify-between items-center py-3 text-sm">
                <div>
                  <p className="font-medium">{m.username}</p>
                  <p className="text-[var(--text-muted)]">
                    {m.email} · {roleLabel(m.role_in_group)}
                  </p>
                </div>
                {isAdmin && !isGroupAdmin(m.role_in_group) && (
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={removingUserId === m.user_id}
                    onClick={() => void handleRemoveMember(m)}
                  >
                    Remove
                  </Button>
                )}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {isAdmin && (
        <Card>
          <CardHeader>
            <CardTitle>Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoadingStats && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}
            {statsError && <Alert variant="error">{statsError}</Alert>}
            <ul className="text-sm space-y-1">
              {statistics.map((s) => (
                <li key={s.user_id}>
                  user {s.user_id}: collected {s.collected_posts ?? 0} · processed {s.processed_posts ?? 0} ·
                  published {s.published_posts ?? 0}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </PageContainer>
  )
}
