import { useState, FormEvent, useEffect, useCallback } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import {
  TargetSocialNetworksWidget,
  createDefaultTargets,
  type TargetSocialNetworks,
} from '@/components/target-social-networks'
import { instagramService } from '@/services/instagram-service'
import type {
  InstagramFollowingUser,
  InstagramProfile,
  InstagramPostListItem,
  ScheduleType,
} from '@/types/instagram'

function generateId(): string {
  return Math.random().toString(36).substring(2, 9)
}

interface DynamicField {
  id: string
  value: string
}

const INSTAGRAM_CAPTION_MAX = 2200

export function InstagramPage() {
  const [activeTab, setActiveTab] = useState<'auth' | 'create' | 'posts' | 'profile'>('create')

  const [publishEnabled, setPublishEnabled] = useState(false)
  const [collectEnabled, setCollectEnabled] = useState(false)
  const [scheduleType, setScheduleType] = useState<ScheduleType>('immediate')
  const [timeIntervals, setTimeIntervals] = useState<Array<{ id: string; start: string; end: string }>>([
    { id: generateId(), start: '', end: '' },
  ])
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [verificationCode, setVerificationCode] = useState('')
  const [usernamesToRead, setUsernamesToRead] = useState<DynamicField[]>([{ id: generateId(), value: '' }])

  const [hasInstagramSession, setHasInstagramSession] = useState(false)
  const [instagramLastAuthError, setInstagramLastAuthError] = useState<string | null>(null)
  const [instagramVerificationPending, setInstagramVerificationPending] = useState(false)

  const [postCaption, setPostCaption] = useState('')
  const [postTargets, setPostTargets] = useState<TargetSocialNetworks>(() =>
    createDefaultTargets('instagram')
  )
  const [imageFiles, setImageFiles] = useState<FileList | null>(null)
  const [editingPostId, setEditingPostId] = useState<number | null>(null)

  const [posts, setPosts] = useState<InstagramPostListItem[]>([])
  const [isLoadingPosts, setIsLoadingPosts] = useState(false)
  const [hasLoadedPosts, setHasLoadedPosts] = useState(false)
  const [deletingPostId, setDeletingPostId] = useState<number | null>(null)

  const [isLoadingProfile, setIsLoadingProfile] = useState(true)
  const [isSavingProfile, setIsSavingProfile] = useState(false)
  const [isSavingAuth, setIsSavingAuth] = useState(false)
  const [isLoginTesting, setIsLoginTesting] = useState(false)
  const [lastDiagnosticImage, setLastDiagnosticImage] = useState<string | null>(null)
  const [followingPreview, setFollowingPreview] = useState<InstagramFollowingUser[]>([])
  const [isCreatingPost, setIsCreatingPost] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadProfile = useCallback(async () => {
    setIsLoadingProfile(true)
    setError('')
    try {
      const profile = await instagramService.getProfile()
      if (profile) {
        setPublishEnabled(profile.publish_enabled ?? false)
        setCollectEnabled(profile.collect_enabled ?? false)
        setScheduleType((profile.schedule_type as ScheduleType) ?? 'immediate')
        const ti = profile.time_intervals
        if (Array.isArray(ti) && ti.length > 0 && ti[0]?.start) {
          setTimeIntervals(
            ti.map((interval) => ({
              id: generateId(),
              start: interval.start ?? '',
              end: interval.end ?? '',
            }))
          )
        }
        setUsername(profile.username ?? '')
        setPassword('')
        setVerificationCode('')
        setHasInstagramSession(profile.has_instagram_session ?? false)
        setInstagramLastAuthError(profile.instagram_last_auth_error ?? null)
        setInstagramVerificationPending(profile.instagram_verification_pending ?? false)
        const ur = profile.usernames_to_read
        if (Array.isArray(ur) && ur.length > 0) {
          setUsernamesToRead(ur.map((u) => ({ id: generateId(), value: String(u) })))
        }
      }
    } catch (err) {
      console.error('Failed to load profile:', err)
    } finally {
      setIsLoadingProfile(false)
    }
  }, [])

  useEffect(() => {
    loadProfile()
  }, [loadProfile])

  useEffect(() => {
    if (activeTab === 'posts' && !hasLoadedPosts) {
      loadPosts()
    }
  }, [activeTab, hasLoadedPosts])

  async function loadPosts() {
    setIsLoadingPosts(true)
    setError('')
    try {
      const data = await instagramService.getPosts()
      setPosts(data)
      setHasLoadedPosts(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load posts')
    } finally {
      setIsLoadingPosts(false)
    }
  }

  async function handleCreatePost(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsCreatingPost(true)
    if (postCaption.length > INSTAGRAM_CAPTION_MAX) {
      setError(`Caption cannot exceed ${INSTAGRAM_CAPTION_MAX} characters`)
      setIsCreatingPost(false)
      return
    }
    try {
      if (editingPostId !== null) {
        await instagramService.updatePost(editingPostId, { caption: postCaption })
        setSuccess('Post updated successfully')
        setEditingPostId(null)
        setPostCaption('')
        if (hasLoadedPosts) loadPosts()
      } else {
        const hasFiles = imageFiles?.length
        if (hasFiles) {
          const formData = new FormData()
          formData.append('caption', postCaption)
          if (imageFiles) {
            for (let i = 0; i < imageFiles.length; i++) {
              formData.append('images', imageFiles[i])
            }
          }
          await instagramService.createPostWithFiles(formData)
        } else {
          await instagramService.createPost({
            caption: postCaption,
            to_tg: postTargets.tg,
            to_tw: postTargets.tw,
            to_wp: postTargets.wp,
            to_vk: postTargets.vk,
            to_dzen: postTargets.dzen,
            to_threads: postTargets.threads,
            to_instagram: postTargets.instagram,
          })
        }
        setSuccess('Post created successfully')
        setPostCaption('')
        setImageFiles(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save post')
    } finally {
      setIsCreatingPost(false)
    }
  }

  async function handleEditPost(id: number) {
    setError('')
    try {
      const post = await instagramService.getPost(id)
      setPostCaption(post.post_text ?? '')
      setEditingPostId(id)
      setActiveTab('create')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load post')
    }
  }

  async function handleDeletePost(id: number) {
    setError('')
    setDeletingPostId(id)
    try {
      await instagramService.deletePost(id)
      setSuccess('Post deleted')
      if (hasLoadedPosts) loadPosts()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete post')
    } finally {
      setDeletingPostId(null)
    }
  }

  function buildProfilePayload(options?: { includeVerificationCode?: boolean }): Partial<InstagramProfile> {
    const timeIntervalsPayload =
      scheduleType === 'intervals'
        ? timeIntervals.filter((i) => i.start && i.end).map(({ start, end }) => ({ start, end }))
        : []
    const usernamesPayload = usernamesToRead.map((f) => f.value.trim()).filter(Boolean)
    const payload: Partial<InstagramProfile> = {
      publish_enabled: publishEnabled,
      collect_enabled: collectEnabled,
      schedule_type: scheduleType,
      time_intervals: timeIntervalsPayload,
      username: username || undefined,
      password: password || undefined,
      usernames_to_read: usernamesPayload,
    }
    if (options?.includeVerificationCode && verificationCode.trim()) {
      payload.instagram_verification_code = verificationCode.trim()
    }
    return payload
  }

  async function handleSaveProfile(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsSavingProfile(true)
    try {
      await instagramService.saveProfile(buildProfilePayload())
      setSuccess('Profile settings saved successfully')
      await loadProfile()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save profile settings')
    } finally {
      setIsSavingProfile(false)
    }
  }

  async function handleSaveAuth(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsSavingAuth(true)
    try {
      await instagramService.saveProfile(buildProfilePayload({ includeVerificationCode: true }))
      setSuccess('Учётные данные сохранены')
      setVerificationCode('')
      await loadProfile()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить учётные данные')
    } finally {
      setIsSavingAuth(false)
    }
  }

  async function handleLoginTest() {
    setError('')
    setSuccess('')
    setLastDiagnosticImage(null)
    setFollowingPreview([])
    setIsLoginTesting(true)
    try {
      const result = await instagramService.loginTest(50)
      if (result.ok) {
        setLastDiagnosticImage(null)
        const n = result.following?.length ?? result.following_count ?? 0
        setFollowingPreview(result.following ?? [])
        const via =
          result.auth_method === 'selenium' ? ' · способ: браузер (Selenium)' : ''
        setSuccess(
          result.instagram_user_id != null
            ? `Вход выполнен (Instagram user id: ${result.instagram_user_id})${n > 0 ? ` · загружено подписок: ${n}` : ''}${via}`
            : `Вход выполнен успешно${n > 0 ? ` · загружено подписок: ${n}` : ''}${via}`
        )
      } else {
        const b64 = result.selenium_diagnostic_image_base64?.trim()
        if (b64) {
          setLastDiagnosticImage(
            b64.startsWith('data:') ? b64 : `data:image/png;base64,${b64}`
          )
        } else {
          setLastDiagnosticImage(null)
        }
        const extra =
          result.selenium_status && result.selenium_status !== 'success'
            ? ` [Selenium: ${result.selenium_status}]`
            : ''
        const diag =
          result.selenium_diagnostic_s3_key != null && result.selenium_diagnostic_s3_key !== ''
            ? ` Диагностика (S3): ${result.selenium_diagnostic_s3_key}`
            : ''
        setError((result.message || 'Вход не выполнен') + extra + diag)
      }
      await loadProfile()
    } catch (err) {
      setLastDiagnosticImage(null)
      setError(err instanceof Error ? err.message : 'Проверка входа не удалась')
    } finally {
      setIsLoginTesting(false)
    }
  }

  function addUsernameToRead() {
    setUsernamesToRead((prev) => [...prev, { id: generateId(), value: '' }])
  }
  function removeUsernameToRead(id: string) {
    if (usernamesToRead.length > 1) setUsernamesToRead((prev) => prev.filter((f) => f.id !== id))
  }
  function updateUsernameToRead(id: string, value: string) {
    setUsernamesToRead((prev) => prev.map((f) => (f.id === id ? { ...f, value } : f)))
  }

  function addTimeInterval() {
    if (timeIntervals.length < 5) {
      setTimeIntervals((prev) => [...prev, { id: generateId(), start: '', end: '' }])
    }
  }
  function removeTimeInterval(id: string) {
    if (timeIntervals.length > 1) {
      setTimeIntervals((prev) => prev.filter((i) => i.id !== id))
    }
  }
  function updateTimeInterval(id: string, field: 'start' | 'end', value: string) {
    setTimeIntervals((prev) =>
      prev.map((i) => (i.id === id ? { ...i, [field]: value } : i))
    )
  }

  return (
    <PageContainer maxWidth="wide">
      <PageHeader
        title="Instagram"
        description="Профиль, сбор постов и публикация (caption до 2200 символов)"
      />

      {error && (
        <Alert variant="error" className="animate-slide-down">
          {error}
        </Alert>
      )}
      {success && (
        <Alert variant="success" className="animate-slide-down">
          {success}
        </Alert>
      )}

      <div className="flex border-b border-[var(--border-color)] flex-wrap gap-1">
        {[
          { id: 'auth' as const, label: 'Авторизация' },
          { id: 'create' as const, label: 'Create post' },
          { id: 'posts' as const, label: 'Posts' },
          { id: 'profile' as const, label: 'Profile' },
        ].map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 font-medium border-b-2 -mb-px ${
              activeTab === tab.id
                ? 'border-[var(--accent)] text-[var(--accent)]'
                : 'border-transparent hover:border-[var(--border-color)]'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'auth' && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Авторизация Instagram</CardTitle>
            <CardDescription>
              Логин и пароль для instagrapi. Сессия хранится на сервере; пароль после сохранения не
              отображается.
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleSaveAuth}>
            <CardContent className="space-y-4">
              {isLoadingProfile ? (
                <p className="text-sm text-[var(--muted)]">Загрузка…</p>
              ) : (
                <>
                  <div className="flex flex-wrap items-center gap-2 text-sm">
                    <span className="font-medium">Сессия в базе:</span>
                    <span
                      className={
                        hasInstagramSession
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-[var(--muted)]'
                      }
                    >
                      {hasInstagramSession ? 'да' : 'нет'}
                    </span>
                    {instagramVerificationPending && (
                      <span className="text-amber-600 dark:text-amber-400">
                        Ожидается код 2FA — введите его ниже и сохраните, затем снова «Проверить сейчас».
                      </span>
                    )}
                  </div>
                  {instagramLastAuthError && (
                    <p className="text-sm text-red-600 dark:text-red-400 break-words">
                      Последняя ошибка входа: {instagramLastAuthError}
                    </p>
                  )}
                  <div>
                    <label className="block text-sm font-medium mb-1">Имя пользователя (логин)</label>
                    <Input
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder="instagram_username"
                      autoComplete="username"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Пароль</label>
                    <Input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Оставьте пустым, чтобы не менять сохранённый пароль"
                      autoComplete="current-password"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Код 2FA (если требует Instagram)</label>
                    <Input
                      type="text"
                      value={verificationCode}
                      onChange={(e) => setVerificationCode(e.target.value)}
                      placeholder="Одноразовый код из приложения-аутентификатора"
                      autoComplete="one-time-code"
                    />
                  </div>
                </>
              )}
            </CardContent>
            <CardFooter className="flex flex-wrap gap-2">
              <Button type="submit" disabled={isSavingAuth || isLoadingProfile}>
                {isSavingAuth ? 'Сохранение…' : 'Сохранить учётные данные'}
              </Button>
              <Button
                type="button"
                variant="outline"
                disabled={isLoginTesting || isLoadingProfile}
                onClick={() => void handleLoginTest()}
              >
                {isLoginTesting ? 'Проверка…' : 'Проверить сейчас'}
              </Button>
            </CardFooter>
          </form>
          {lastDiagnosticImage && (
            <CardContent className="border-t border-[var(--border-color)] pt-4">
              <p className="text-sm text-[var(--muted)] mb-2">Снимок экрана при ошибке (diag)</p>
              <img
                src={lastDiagnosticImage}
                alt="Диагностика Selenium"
                className="max-w-full h-auto rounded-md border border-[var(--border-color)]"
              />
            </CardContent>
          )}
          {followingPreview.length > 0 && (
            <CardContent className="border-t border-[var(--border-color)] pt-4">
              <p className="text-sm font-medium mb-2">Подписки (аккаунты, на которые вы подписаны)</p>
              <p className="text-xs text-[var(--muted)] mb-2">
                Показано до 50 записей после успешной проверки входа.
              </p>
              <ul
                className="max-h-64 overflow-y-auto text-sm border border-[var(--border-color)] rounded-md divide-y divide-[var(--border-color)]"
                aria-label="Список подписок Instagram"
              >
                {followingPreview.map((u) => (
                  <li key={u.pk || u.username} className="px-3 py-2 flex flex-col gap-0.5">
                    <span className="font-medium">@{u.username || '—'}</span>
                    {u.full_name ? (
                      <span className="text-[var(--muted)]">{u.full_name}</span>
                    ) : null}
                  </li>
                ))}
              </ul>
            </CardContent>
          )}
        </Card>
      )}

      {activeTab === 'profile' && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Instagram profile</CardTitle>
            <CardDescription>Расписание, публикация, сбор и список аккаунтов для чтения</CardDescription>
          </CardHeader>
          <form onSubmit={handleSaveProfile}>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="publish_enabled"
                  checked={publishEnabled}
                  onChange={(e) => setPublishEnabled(e.target.checked)}
                />
                <label htmlFor="publish_enabled">Publish enabled</label>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="collect_enabled"
                  checked={collectEnabled}
                  onChange={(e) => setCollectEnabled(e.target.checked)}
                />
                <label htmlFor="collect_enabled">Collect enabled</label>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Usernames to read (one per line or add fields)</label>
                {usernamesToRead.map((f) => (
                  <div key={f.id} className="flex gap-2 mb-2">
                    <Input
                      value={f.value}
                      onChange={(e) => updateUsernameToRead(f.id, e.target.value)}
                      placeholder="@username"
                    />
                    <Button type="button" variant="outline" onClick={() => removeUsernameToRead(f.id)}>
                      Remove
                    </Button>
                  </div>
                ))}
                <Button type="button" variant="outline" onClick={addUsernameToRead}>
                  Add username
                </Button>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Schedule type</label>
                <select
                  value={scheduleType}
                  onChange={(e) => setScheduleType(e.target.value as ScheduleType)}
                  className="border rounded px-2 py-1"
                >
                  <option value="immediate">Immediate</option>
                  <option value="intervals">Intervals</option>
                </select>
              </div>
              {scheduleType === 'intervals' && (
                <div>
                  <label className="block text-sm font-medium mb-1">Time intervals</label>
                  {timeIntervals.map((i) => (
                    <div key={i.id} className="flex gap-2 mb-2">
                      <Input
                        type="time"
                        value={i.start}
                        onChange={(e) => updateTimeInterval(i.id, 'start', e.target.value)}
                      />
                      <Input
                        type="time"
                        value={i.end}
                        onChange={(e) => updateTimeInterval(i.id, 'end', e.target.value)}
                      />
                      <Button type="button" variant="outline" onClick={() => removeTimeInterval(i.id)}>
                        Remove
                      </Button>
                    </div>
                  ))}
                  <Button type="button" variant="outline" onClick={addTimeInterval}>
                    Add interval
                  </Button>
                </div>
              )}
            </CardContent>
            <CardFooter>
              <Button type="submit" disabled={isSavingProfile}>
                {isSavingProfile ? 'Saving...' : 'Save profile'}
              </Button>
            </CardFooter>
          </form>
        </Card>
      )}

      {activeTab === 'create' && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>{editingPostId ? 'Edit post' : 'Create Instagram post'}</CardTitle>
            <CardDescription>Caption max {INSTAGRAM_CAPTION_MAX} characters. Add images for photo/carousel.</CardDescription>
          </CardHeader>
          <form onSubmit={handleCreatePost}>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Caption</label>
                <textarea
                  className="w-full border rounded px-2 py-1 min-h-[120px]"
                  value={postCaption}
                  onChange={(e) => setPostCaption(e.target.value)}
                  maxLength={INSTAGRAM_CAPTION_MAX}
                  placeholder="Post caption..."
                />
                <span className="text-sm text-[var(--muted)]">
                  {postCaption.length} / {INSTAGRAM_CAPTION_MAX}
                </span>
              </div>
              {!editingPostId && (
                <div>
                  <label className="block text-sm font-medium mb-1">Images</label>
                  <Input
                    type="file"
                    accept="image/*"
                    multiple
                    onChange={(e) => setImageFiles(e.target.files || null)}
                  />
                </div>
              )}
              {!editingPostId && (
                <TargetSocialNetworksWidget value={postTargets} onChange={setPostTargets} />
              )}
            </CardContent>
            <CardFooter>
              <Button type="submit" disabled={isCreatingPost}>
                {isCreatingPost ? 'Saving...' : editingPostId ? 'Update post' : 'Create post'}
              </Button>
              {editingPostId && (
                <Button type="button" variant="outline" onClick={() => setEditingPostId(null)}>
                  Cancel
                </Button>
              )}
            </CardFooter>
          </form>
        </Card>
      )}

      {activeTab === 'posts' && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Posts</CardTitle>
            <CardDescription>List of Instagram posts</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingPosts ? (
              <p>Loading...</p>
            ) : posts.length === 0 ? (
              <p>No posts yet.</p>
            ) : (
              <ul className="space-y-2">
                {posts.map((post) => (
                  <li
                    key={post.id}
                    className="flex items-center justify-between border rounded p-2"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="truncate">{post.post_text || '(no caption)'}</p>
                      <p className="text-sm text-[var(--muted)]">
                        #{post.id} · {post.status} · {post.created_at}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={() => handleEditPost(post.id)}>
                        Edit
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeletePost(post.id)}
                        disabled={deletingPostId === post.id}
                      >
                        {deletingPostId === post.id ? 'Deleting...' : 'Delete'}
                      </Button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      )}
    </PageContainer>
  )
}
