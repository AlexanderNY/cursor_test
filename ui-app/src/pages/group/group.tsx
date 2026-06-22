import { useState, useEffect, FormEvent } from 'react'
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

export function GroupPage() {
  const { user, refreshUserData } = useAuth()
  const [group, setGroup] = useState<GroupResponse | null>(null)
  const [groupError, setGroupError] = useState('')
  const [isLoadingGroup, setIsLoadingGroup] = useState(true)
  const [createName, setCreateName] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  const [editName, setEditName] = useState('')
  const [isSavingName, setIsSavingName] = useState(false)
  const [addEmail, setAddEmail] = useState('')
  const [isAddingMember, setIsAddingMember] = useState(false)
  const [addError, setAddError] = useState('')
  const [removingUserId, setRemovingUserId] = useState<number | null>(null)
  const [statistics, setStatistics] = useState<UserStatisticsItem[]>([])
  const [isLoadingStats, setIsLoadingStats] = useState(false)
  const [statsError, setStatsError] = useState('')

  const isManager = user?.role === 'manager' || user?.role_in_group === 'manager'
  const isAuthor = user?.role === 'author' || user?.role_in_group === 'author'

  async function loadGroup() {
    if (user?.role !== 'manager' && user?.role !== 'author') return
    setGroupError('')
    setIsLoadingGroup(true)
    try {
      const data = await authService.getMyGroup()
      setGroup(data)
      setEditName(data.name)
    } catch (e) {
      if ((e as any)?.response?.status === 404) {
        setGroup(null)
      } else {
        setGroupError(e instanceof Error ? e.message : 'Failed to load group')
      }
    } finally {
      setIsLoadingGroup(false)
    }
  }

  useEffect(() => {
    loadGroup()
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
      await authService.addGroupMember(group.id, addEmail.trim(), 'author')
      const updated = await authService.getMyGroup()
      setGroup(updated)
      setAddEmail('')
      if (isManager) await loadStats()
    } catch (e) {
      setAddError(e instanceof Error ? e.message : 'Failed to add member')
    } finally {
      setIsAddingMember(false)
    }
  }

  async function handleRemoveMember(member: GroupMemberResponse) {
    if (!group || member.role_in_group === 'manager') return
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
    if (user?.role !== 'manager' && user?.role !== 'admin') return
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
    if (group && isManager) loadStats()
  }, [group?.id, isManager])

  if (user?.role !== 'manager' && user?.role !== 'author') {
    return (
      <div className="max-w-2xl mx-auto py-8">
        <Alert variant="error">Access denied. Only group managers and authors can view this page.</Alert>
      </div>
    )
  }

  if (isLoadingGroup) {
    return (
      <PageContainer>
        <PageHeader title="My group" description="Loading…" />
        <div className="space-y-4">
          <SkeletonCard />
          <SkeletonCard />
        </div>
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

  if (!group && isManager) {
    return (
      <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold text-[var(--text-primary)]">My group</h1>
          <p className="text-[var(--text-secondary)] mt-1">Create a group to add authors and view their statistics</p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Create group</CardTitle>
            <CardDescription>Enter a name for your group. You will be the manager.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateGroup} className="space-y-4">
              <Input
                value={createName}
                onChange={(e) => setCreateName(e.target.value)}
                placeholder="Group name"
                className="max-w-xs"
              />
              {addError && <Alert variant="error">{addError}</Alert>}
              <Button type="submit" disabled={!createName.trim() || isCreating}>
                {isCreating ? 'Creating…' : 'Create group'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!group && isAuthor) {
    return (
      <div className="max-w-2xl mx-auto py-8">
        <p className="text-[var(--text-muted)]">You are not in any group yet.</p>
      </div>
    )
  }

  if (!group) return null

  const managerMember = group.members?.find((m) => m.role_in_group === 'manager')

  return (
    <PageContainer>
      <PageHeader
        title="My group"
        description={isManager ? 'Manage your group and view statistics' : 'You are an author in this group'}
      />

      <Card>
        <CardHeader>
          <CardTitle>{group.name}</CardTitle>
          <CardDescription>
            {isManager ? 'You are the manager' : `Manager: ${managerMember?.username ?? managerMember?.email ?? '—'}`}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isManager && (
            <form onSubmit={handleSaveName} className="flex flex-wrap items-end gap-2">
              <div>
                <label className="text-sm text-[var(--text-secondary)] block mb-1">Group name</label>
                <Input
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="max-w-xs"
                />
              </div>
              <Button type="submit" size="sm" variant="secondary" disabled={editName.trim() === group.name || isSavingName}>
                {isSavingName ? 'Saving…' : 'Save name'}
              </Button>
            </form>
          )}
          {!isManager && <p className="text-[var(--text-secondary)]">Group: {group.name}</p>}
        </CardContent>
      </Card>

      {isManager && group.members && group.members.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Members</CardTitle>
            <CardDescription>Authors and manager in this group</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={handleAddMember} className="flex flex-wrap items-end gap-2">
              <Input
                type="email"
                value={addEmail}
                onChange={(e) => setAddEmail(e.target.value)}
                placeholder="Author email"
                className="max-w-xs"
              />
              <Button type="submit" size="sm" disabled={!addEmail.trim() || isAddingMember}>
                {isAddingMember ? 'Adding…' : 'Add author'}
              </Button>
            </form>
            {addError && <Alert variant="error">{addError}</Alert>}
            <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
              <table className="w-full">
                <thead className="bg-[var(--bg-tertiary)]">
                  <tr>
                    <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Username</th>
                    <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Email</th>
                    <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Tariff</th>
                    <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Role</th>
                    <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Joined</th>
                    {isManager && <th className="py-3 px-4 text-right text-sm font-medium text-[var(--text-secondary)]">Action</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-color)]">
                  {group.members.map((m) => (
                    <tr key={m.user_id} className="hover:bg-[var(--bg-tertiary)]">
                      <td className="py-3 px-4 text-[var(--text-primary)] font-medium">{m.username}</td>
                      <td className="py-3 px-4 text-[var(--text-secondary)]">{m.email}</td>
                      <td className="py-3 px-4 text-[var(--text-secondary)]">{m.tariff}</td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${m.role_in_group === 'manager' ? 'bg-purple-500/20 text-purple-400' : 'bg-blue-500/20 text-blue-400'}`}>
                          {m.role_in_group}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-[var(--text-secondary)] text-sm">{new Date(m.joined_at).toLocaleDateString()}</td>
                      {isManager && (
                        <td className="py-3 px-4 text-right">
                          {m.role_in_group === 'author' && (
                            <Button
                              size="sm"
                              variant="secondary"
                              disabled={removingUserId === m.user_id}
                              onClick={() => handleRemoveMember(m)}
                            >
                              {removingUserId === m.user_id ? 'Removing…' : 'Remove'}
                            </Button>
                          )}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {isManager && (
        <Card>
          <CardHeader>
            <CardTitle>Group statistics</CardTitle>
            <CardDescription>Publication statistics for group members</CardDescription>
          </CardHeader>
          <CardContent>
            <Button size="sm" variant="secondary" onClick={loadStats} disabled={isLoadingStats} className="mb-4">
              {isLoadingStats ? 'Loading…' : 'Refresh statistics'}
            </Button>
            {statsError && <Alert variant="error" className="mb-4">{statsError}</Alert>}
            {statistics.length > 0 ? (
              <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
                <table className="w-full">
                  <thead className="bg-[var(--bg-tertiary)]">
                    <tr>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Username</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Email</th>
                      <th className="py-3 px-4 text-right text-sm font-medium text-[var(--text-secondary)]">Total</th>
                      <th className="py-3 px-4 text-right text-sm font-medium text-[var(--text-secondary)]">Collected</th>
                      <th className="py-3 px-4 text-right text-sm font-medium text-[var(--text-secondary)]">Processed</th>
                      <th className="py-3 px-4 text-right text-sm font-medium text-[var(--text-secondary)]">Published</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-color)]">
                    {statistics.map((s) => (
                      <tr key={s.user_id} className="hover:bg-[var(--bg-tertiary)]">
                        <td className="py-3 px-4 text-[var(--text-primary)] font-medium">{s.username}</td>
                        <td className="py-3 px-4 text-[var(--text-secondary)]">{s.email}</td>
                        <td className="py-3 px-4 text-right text-[var(--text-secondary)]">{s.total_posts.toLocaleString()}</td>
                        <td className="py-3 px-4 text-right text-[var(--text-secondary)]">{s.collected_posts.toLocaleString()}</td>
                        <td className="py-3 px-4 text-right text-[var(--text-secondary)]">{s.processed_posts.toLocaleString()}</td>
                        <td className="py-3 px-4 text-right text-[var(--text-secondary)]">{s.published_posts.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : !isLoadingStats && !statsError && (
              <p className="text-[var(--text-muted)]">No statistics yet. Click Refresh to load.</p>
            )}
          </CardContent>
        </Card>
      )}
    </PageContainer>
  )
}
