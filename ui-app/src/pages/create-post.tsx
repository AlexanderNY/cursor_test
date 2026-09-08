import { useState, FormEvent, useEffect, type ReactNode } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import { TipTapEditor } from '@/components/ui/tiptap-editor'
import { AiAssistPanel } from '@/components/ai/AiAssistPanel'
import { LibraryPicker } from '@/components/library/LibraryPicker'
import { createPostService } from '@/services/create-post-service'
import { coreService } from '@/services/core-service'
import { smmService } from '@/services/smm-service'
import { useBrand } from '@/contexts/brand-context'
import {
  TargetSocialNetworksWidget,
  EMPTY_TARGET_SOCIAL_NETWORKS,
  EMPTY_SELECTED_BRAND_CHANNELS,
  type TargetSocialNetworks,
  type SelectedBrandChannels,
} from '@/components/target-social-networks'
import type { PostRow } from '@/types/core'
import type { PublishJob } from '@/types/smm'
import { formatDateTime } from '@/utils/date'
import { getErrorMessage } from '@/services/api-client'
import { JobCollabPanel } from '@/components/smm/job-collab-panel'
import {
  CSV_POSTS_COLUMNS,
  downloadPostsCsvTemplate,
} from '@/utils/csv-posts-template'

const TEXT_MAX_LENGTH = 150000
const POST_PREVIEW_LENGTH = 80

function htmlToPlainText(html: string): string {
  const div = document.createElement('div')
  div.innerHTML = html
  return (div.textContent ?? div.innerText ?? '').trim()
}

function plainTextToHtml(text: string): string {
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  const paragraphs = escaped
    .split(/\n{2,}/)
    .map((p) => `<p>${p.replace(/\n/g, '<br>')}</p>`)
  return paragraphs.join('') || '<p></p>'
}

function formatDate(iso?: string | null): string {
  return formatDateTime(iso)
}

function cellValue(
  value: string | number | boolean | null | undefined | unknown,
  truncate = 0
): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'boolean') return value ? 'yes' : 'no'
  if (Array.isArray(value)) return value.length ? `[${value.length}]` : '[]'
  if (typeof value === 'object') return JSON.stringify(value).slice(0, truncate || 50)
  const s = String(value)
  if (truncate && s.length > truncate) return s.slice(0, truncate) + '…'
  return s
}

/** ISO string to datetime-local input value (YYYY-MM-DDTHH:mm) */
function toDatetimeLocal(iso?: string | null): string {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    if (Number.isNaN(d.getTime())) return ''
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const h = String(d.getHours()).padStart(2, '0')
    const min = String(d.getMinutes()).padStart(2, '0')
    return `${y}-${m}-${day}T${h}:${min}`
  } catch {
    return ''
  }
}

function fromDatetimeLocal(value: string): string {
  if (!value.trim()) return ''
  try {
    return new Date(value).toISOString()
  } catch {
    return ''
  }
}

type TabId = 'create' | 'posts' | 'posts-review' | 'profile'

export function CreatePostPage() {
  const { selectedBrandId, selectedBrand, connectedPublishChannels, ownChannels } = useBrand()
  const [searchParams] = useSearchParams()
  const [activeTab, setActiveTab] = useState<TabId>('create')

  const [socialNetworks, setSocialNetworks] = useState<TargetSocialNetworks>({
    ...EMPTY_TARGET_SOCIAL_NETWORKS,
  })
  const [selectedChannels, setSelectedChannels] = useState<SelectedBrandChannels>({
    ...EMPTY_SELECTED_BRAND_CHANNELS,
  })
  const [postTitle, setPostTitle] = useState('')
  const [postContent, setPostContent] = useState('')
  const [domain, setDomain] = useState('')
  const [url, setUrl] = useState('')
  const [author, setAuthor] = useState('')
  const [avatar, setAvatar] = useState('')
  const [postDate, setPostDate] = useState('')
  const [screenshot, setScreenshot] = useState('')
  const [imagesText, setImagesText] = useState('')
  const [imageOverText, setImageOverText] = useState('')
  const [comments, setComments] = useState<number | ''>('')
  const [reposts, setReposts] = useState<number | ''>('')
  const [likes, setLikes] = useState<number | ''>('')
  const [views, setViews] = useState<number | ''>('')
  const [isAd, setIsAd] = useState(false)
  const [status, setStatus] = useState('collected')
  const [selectedChannelId, setSelectedChannelId] = useState<number | null>(null)
  const [smmPublishAt, setSmmPublishAt] = useState('')
  const [aiBusy, setAiBusy] = useState(false)
  const [csvResult, setCsvResult] = useState('')
  const [csvErrors, setCsvErrors] = useState<{ line: number; error: string }[]>([])
  const [adaptPreview, setAdaptPreview] = useState<Record<string, string> | null>(null)
  const [adaptLimits, setAdaptLimits] = useState<Record<string, number> | null>(null)
  const [requireApproval, setRequireApproval] = useState(false)
  const [planFeatures, setPlanFeatures] = useState<Record<string, boolean>>({})
  const [horizonDays, setHorizonDays] = useState(7)
  const [bestSlots, setBestSlots] = useState<{ weekday: number; hour: number; score: number }[]>([])

  const [editingPostId, setEditingPostId] = useState<number | null>(null)
  const [editingSource, setEditingSource] = useState<'cpost' | 'pipeline'>('cpost')
  const [publishJobs, setPublishJobs] = useState<PublishJob[]>([])
  const [collabJobId, setCollabJobId] = useState<number | null>(null)
  const [isLoadingPosts, setIsLoadingPosts] = useState(false)
  const [hasLoadedPosts, setHasLoadedPosts] = useState(false)

  const [postsReviewList, setPostsReviewList] = useState<PostRow[]>([])
  const [isLoadingPostsReview, setIsLoadingPostsReview] = useState(false)
  const [postsReviewError, setPostsReviewError] = useState('')

  const [isCreating, setIsCreating] = useState(false)
  const [isLoadingProfile, setIsLoadingProfile] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    void smmService.getPlan().then((p) => {
      setPlanFeatures((p.limits?.features || {}) as Record<string, boolean>)
      if (p.limits?.schedule_horizon_days != null) {
        setHorizonDays(Number(p.limits.schedule_horizon_days))
      }
    }).catch(() => undefined)
  }, [])

  useEffect(() => {
    const fromQuery = Number(searchParams.get('channelId') || '')
    if (fromQuery && connectedPublishChannels.some((c) => c.id === fromQuery)) {
      setSelectedChannelId(fromQuery)
      return
    }
    setSelectedChannelId((prev) => {
      if (prev != null && connectedPublishChannels.some((c) => c.id === prev)) return prev
      return connectedPublishChannels[0]?.id ?? null
    })
  }, [connectedPublishChannels, searchParams])

  useEffect(() => {
    const draft = searchParams.get('draft')
    if (!draft) return
    try {
      const text = draft.trim()
      if (!text) return
      setPostContent(plainTextToHtml(text))
      const firstLine = text.split('\n').map((l) => l.trim()).find(Boolean)
      if (firstLine && !postTitle) setPostTitle(firstLine.slice(0, 120))
      setActiveTab('create')
    } catch {
      /* ignore */
    }
    // intentionally only on mount / draft param change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams])

  useEffect(() => {
    async function loadProfile() {
      setIsLoadingProfile(true)
      try {
        const profile = await createPostService.getProfile()
        if (profile) {
          setSocialNetworks({
            ...EMPTY_TARGET_SOCIAL_NETWORKS,
            tg: profile.social_networks.tg ?? false,
            tw: profile.social_networks.tw ?? false,
            vk: profile.social_networks.vk ?? false,
            wp: profile.social_networks.wp ?? false,
            threads: profile.social_networks.threads ?? false,
            instagram: profile.social_networks.instagram ?? false,
            dzen: profile.social_networks.dzen ?? false,
          })
        }
      } catch (err) {
        console.error('Failed to load profile:', err)
      } finally {
        setIsLoadingProfile(false)
      }
    }
    loadProfile()
  }, [])

  useEffect(() => {
    if (activeTab === 'posts') {
      void loadPosts()
    }
  }, [activeTab, selectedBrandId])

  async function loadPosts() {
    setIsLoadingPosts(true)
    setError('')
    try {
      const data = await smmService.listJobs({
        brand_id: selectedBrandId ?? undefined,
      })
      setPublishJobs(data)
      setHasLoadedPosts(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load posts')
    } finally {
      setIsLoadingPosts(false)
    }
  }

  function fillFormFromPipelinePost(post: PostRow) {
    setPostTitle(post.title ?? '')
    setPostContent(post.post_text ?? '')
    setDomain(post.domain ?? '')
    setUrl(post.url ?? '')
    setAuthor(post.author ?? '')
    setAvatar(post.avatar ?? '')
    setPostDate(toDatetimeLocal(post.post_date))
    setScreenshot(post.screenshot ?? '')
    const imgs = post.images
    setImagesText(
      Array.isArray(imgs)
        ? imgs.filter((x): x is string => typeof x === 'string' && Boolean(x)).join('\n')
        : typeof imgs === 'string'
          ? imgs
          : ''
    )
    setImageOverText(post.image_over_text ?? '')
    setComments(post.comments ?? '')
    setReposts(post.reposts ?? '')
    setLikes(post.likes ?? '')
    setViews(post.views ?? '')
    setIsAd(post.is_ad ?? false)
    setStatus(post.status ?? 'review')
    setSocialNetworks({
      ...EMPTY_TARGET_SOCIAL_NETWORKS,
      tg: post.to_tg ?? false,
      tw: post.to_tw ?? false,
      vk: post.to_vk ?? false,
      wp: post.to_wp ?? false,
      threads: post.to_threads ?? false,
      instagram: post.to_instagram ?? false,
      dzen: post.to_dzen ?? false,
    })
    setEditingPostId(post.id)
    setEditingSource('pipeline')
    setActiveTab('create')
  }

  async function handleEditPipelinePost(post: PostRow) {
    setError('')
    try {
      // Prefer fresh fetch; fall back to list row if endpoint unavailable.
      try {
        const fresh = await coreService.getPipelinePost(post.id)
        fillFormFromPipelinePost(fresh)
      } catch {
        fillFormFromPipelinePost(post)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load post')
    }
  }

  async function handleLoadPostsReview() {
    setPostsReviewError('')
    setIsLoadingPostsReview(true)
    try {
      const data = await coreService.getPostsList(500, 0, 'review')
      setPostsReviewList(data.posts)
    } catch (err) {
      setPostsReviewError(err instanceof Error ? err.message : 'Failed to fetch posts in review')
      setPostsReviewList([])
    } finally {
      setIsLoadingPostsReview(false)
    }
  }

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
    { key: 'to_threads', label: 'To Threads' },
    { key: 'to_dzen', label: 'To Dzen' },
    { key: 'to_instagram', label: 'To Instagram' },
    { key: 'created_at', label: 'Created At' },
    { key: 'updated_at', label: 'Updated At' },
    { key: 'source_platform', label: 'Source Platform' },
    { key: 'source_id', label: 'Source ID' },
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

  async function handleSaveProfile(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    try {
      await createPostService.saveProfile({
        social_networks: socialNetworks,
      })
      setSuccess('Profile settings saved successfully')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save profile settings')
    }
  }

  async function handleCreatePost(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsCreating(true)

    const plainText = htmlToPlainText(postContent)

    if (plainText.length > TEXT_MAX_LENGTH) {
      setError(`Post text cannot exceed ${TEXT_MAX_LENGTH} characters`)
      setIsCreating(false)
      return
    }

    if (!plainText.trim()) {
      setError('Post text cannot be empty')
      setIsCreating(false)
      return
    }

    const imagesList = imagesText
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean)
    const num = (v: number | '') => (v === '' ? undefined : Number(v))
    const effectiveStatus =
      editingPostId !== null && status.trim() === 'review' ? 'ready' : status.trim() || undefined
    const basePayload = {
      title: postTitle.trim() || undefined,
      text: plainText,
      domain: domain.trim() || undefined,
      url: url.trim() || undefined,
      author: author.trim() || undefined,
      avatar: avatar.trim() || undefined,
      post_date: postDate.trim() ? fromDatetimeLocal(postDate) : undefined,
      screenshot: screenshot.trim() || undefined,
      images: imagesList.length ? imagesList : undefined,
      image_over_text: imageOverText.trim() || undefined,
      comments: num(comments),
      reposts: num(reposts),
      likes: num(likes),
      views: num(views),
      is_ad: isAd,
      status: effectiveStatus,
      to_tg: socialNetworks.tg,
      to_tw: socialNetworks.tw,
      to_wp: socialNetworks.wp,
      to_vk: socialNetworks.vk,
      to_threads: socialNetworks.threads,
      to_dzen: socialNetworks.dzen,
      to_instagram: socialNetworks.instagram,
      target_channels: selectedChannels.tg,
      target_groups: selectedChannels.vk,
    }

    try {
      if (editingPostId !== null) {
        const id = editingPostId
        if (editingSource === 'pipeline') {
          await coreService.updatePipelinePost(id, basePayload)
        } else {
          await createPostService.updatePost(id, basePayload)
        }
        setSuccess(
          effectiveStatus === 'ready'
            ? 'Post updated and set to ready for distribution'
            : 'Post updated successfully'
        )
        if (effectiveStatus === 'ready') {
          setPostsReviewList((prev) => prev.filter((p) => p.id !== id))
        }
        setPostTitle('')
        setPostContent('')
        setDomain('')
        setUrl('')
        setAuthor('')
        setAvatar('')
        setPostDate('')
        setScreenshot('')
        setImagesText('')
        setImageOverText('')
        setComments('')
        setReposts('')
        setLikes('')
        setViews('')
        setIsAd(false)
        setStatus('collected')
        setEditingPostId(null)
        setEditingSource('cpost')
      } else {
        if (!selectedBrandId) {
          setError('Выберите бренд в шапке')
          setIsCreating(false)
          return
        }
        const channel = connectedPublishChannels.find((c) => c.id === selectedChannelId)
        if (!channel) {
          setError(
            'Выберите один канал с подтверждёнными правами (Channels → Recheck / Connect)',
          )
          setIsCreating(false)
          return
        }
        if (smmPublishAt) {
          const picked = new Date(smmPublishAt)
          const max = new Date()
          max.setDate(max.getDate() + horizonDays)
          if (picked > max) {
            setError(
              `Schedule outside plan horizon (${horizonDays} days). Pick an earlier slot or upgrade.`,
            )
            setIsCreating(false)
            return
          }
        }
        const overrides = adaptPreview
          ? Object.fromEntries(
              Object.entries(adaptPreview).map(([net, t]) => [net, { text: t }]),
            )
          : undefined
        let jobStatus: string = smmPublishAt ? 'scheduled' : 'ready'
        if (requireApproval && planFeatures.approval_workflow) {
          jobStatus = 'pending_approval'
        }
        await smmService.createJob({
          brand_id: selectedBrandId,
          text: postContent,
          media_urls: imagesList,
          targets: [{ network: channel.network, external_id: channel.external_id }],
          publish_at: smmPublishAt ? fromDatetimeLocal(smmPublishAt) : null,
          adapt: true,
          status: jobStatus,
          adapter_overrides: overrides,
        })
        setSuccess(
          jobStatus === 'pending_approval'
            ? 'Пост отправлен на согласование'
            : smmPublishAt
              ? `Запланировано в ${channel.network}: ${channel.title || channel.external_id}`
              : `Отправлено в ${channel.network}: ${channel.title || channel.external_id}`,
        )
        setPostTitle('')
        setPostContent('')
        setImagesText('')
        setSmmPublishAt('')
        setAdaptPreview(null)
        setAdaptLimits(null)
        setHasLoadedPosts(false)
        if (activeTab === 'posts') {
          await loadPosts()
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save post')
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <PageContainer maxWidth="wide">
      <PageHeader
        title="Posts"
        description="Создайте пост и отправьте в один канал с подтверждёнными правами"
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

      {/* Tabs */}
      <div className="flex border-b border-[var(--border-color)]">
        <button
          type="button"
          className={`px-6 py-3 text-sm font-medium transition-all relative ${
            activeTab === 'create'
              ? 'text-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
          onClick={() => {
            setEditingPostId(null)
            setEditingSource('cpost')
            setPostTitle('')
            setPostContent('')
            setDomain('')
            setUrl('')
            setAuthor('')
            setAvatar('')
            setPostDate('')
            setScreenshot('')
            setImagesText('')
            setImageOverText('')
            setComments('')
            setReposts('')
            setLikes('')
            setViews('')
            setIsAd(false)
            setStatus('collected')
            setActiveTab('create')
          }}
        >
          Create Post
          {activeTab === 'create' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500" />
          )}
        </button>
        <button
          type="button"
          className={`px-6 py-3 text-sm font-medium transition-all relative ${
            activeTab === 'posts'
              ? 'text-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
          onClick={() => setActiveTab('posts')}
        >
          Posts
          {activeTab === 'posts' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500" />
          )}
        </button>
        <button
          type="button"
          className={`px-6 py-3 text-sm font-medium transition-all relative ${
            activeTab === 'posts-review'
              ? 'text-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
          onClick={() => setActiveTab('posts-review')}
        >
          Posts Review
          {activeTab === 'posts-review' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500" />
          )}
        </button>
        <button
          type="button"
          className={`px-6 py-3 text-sm font-medium transition-all relative ${
            activeTab === 'profile'
              ? 'text-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
          onClick={() => setActiveTab('profile')}
        >
          Profile Settings
          {activeTab === 'profile' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500" />
          )}
        </button>
      </div>

      {/* Tab: Create Post */}
      {activeTab === 'create' && connectedPublishChannels.length === 0 && editingPostId === null && (
        <Alert variant="info" className="mb-4">
          Нет каналов с подтверждёнными правами публикации. Подключите канал в{' '}
          <Link to="/channels" className="underline">
            Channels
          </Link>{' '}
          и нажмите Recheck / Connect.
        </Alert>
      )}
      {activeTab === 'create' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-6 w-6 text-primary-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
              Create Post
            </CardTitle>
            <CardDescription>
              {editingPostId !== null
                ? 'Edit the post and save changes'
                : 'Текст → один канал с confirmed access → отправка'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreatePost} className="space-y-6">
              <Input
                label="Title (optional)"
                type="text"
                value={postTitle}
                onChange={(e) => setPostTitle(e.target.value)}
                placeholder="Enter post title"
              />

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="domain"
                  type="text"
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  placeholder="Domain"
                />
                <Input
                  label="url"
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="URL"
                />
                <Input
                  label="author"
                  type="text"
                  value={author}
                  onChange={(e) => setAuthor(e.target.value)}
                  placeholder="Author"
                />
                <Input
                  label="avatar"
                  type="text"
                  value={avatar}
                  onChange={(e) => setAvatar(e.target.value)}
                  placeholder="Avatar URL"
                />
                <div className="sm:col-span-2">
                  <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">
                    post_date
                  </label>
                  <input
                    type="datetime-local"
                    value={postDate}
                    onChange={(e) => setPostDate(e.target.value)}
                    className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">
                  Content (post_text)
                </label>
                <TipTapEditor
                  content={postContent}
                  onChange={setPostContent}
                  placeholder="Enter your post content (HTML supported)"
                  toolbarButtons={[
                    'bold',
                    'italic',
                    'underline',
                    'strike',
                    'heading',
                    'bulletList',
                    'orderedList',
                    'blockquote',
                    'code',
                    'codeBlock',
                    'horizontalRule',
                    'undo',
                    'redo',
                  ]}
                />
                <p className="text-xs text-[var(--text-muted)] mt-2">
                  Plain text length: {htmlToPlainText(postContent).length} / {TEXT_MAX_LENGTH} characters
                </p>
                <LibraryPicker
                  className="mt-3"
                  brandId={selectedBrandId}
                  onApplyText={(text, meta) => {
                    if (meta.mode === 'replace') {
                      setPostContent(plainTextToHtml(text))
                    } else {
                      const current = htmlToPlainText(postContent)
                      const next = current ? `${current}\n\n${text}` : text
                      setPostContent(plainTextToHtml(next))
                    }
                    setSuccess(`Из библиотеки: ${meta.title}`)
                  }}
                  onApplyPrompt={(note) => {
                    setSuccess(`Промпт из библиотеки: ${note.slice(0, 80)}`)
                  }}
                  onApplyMedia={(keys, caption) => {
                    if (caption) {
                      const current = htmlToPlainText(postContent)
                      if (!current) setPostContent(plainTextToHtml(caption))
                    }
                    setSuccess(
                      keys.length
                        ? `Медиа из библиотеки: ${keys.length} файл(ов). Добавьте URL вручную при публикации: ${keys.slice(0, 2).join(', ')}`
                        : 'Медиа-пакет пуст',
                    )
                  }}
                />
              </div>

              {editingPostId === null && (
              <div className="rounded-xl border border-[var(--border-color)] p-4 space-y-3 bg-[var(--bg-tertiary)]/40">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h4 className="font-medium text-[var(--text-primary)]">
                    Канал публикации
                    {selectedBrand && (
                      <span className="ml-2 text-sm text-[var(--text-muted)]">
                        · {selectedBrand.name}
                      </span>
                    )}
                  </h4>
                  <Button
                    type="button"
                    size="sm"
                    variant="secondary"
                    disabled={aiBusy || !htmlToPlainText(postContent) || selectedChannelId == null}
                    onClick={async () => {
                      setAiBusy(true)
                      setError('')
                      try {
                        const channel = connectedPublishChannels.find(
                          (c) => c.id === selectedChannelId,
                        )
                        const targets = channel ? [channel.network] : ['tg']
                        const res = await smmService.aiAdapt(
                          htmlToPlainText(postContent),
                          targets,
                          { brand_id: selectedBrandId },
                        )
                        setAdaptPreview(res.variants)
                        setAdaptLimits(res.limits ?? null)
                        setSuccess(
                          `Preview для ${Object.keys(res.variants).length} сетей готов`,
                        )
                      } catch (err) {
                        setError(getErrorMessage(err))
                      } finally {
                        setAiBusy(false)
                      }
                    }}
                  >
                    {aiBusy ? 'Adapt…' : 'Adapt preview'}
                  </Button>
                </div>

                <AiAssistPanel
                  sourceText={htmlToPlainText(postContent)}
                  source="post"
                  sourceId={editingPostId ?? undefined}
                  brandId={selectedBrandId}
                  brandToneHint={
                    [selectedBrand?.tone_of_voice, selectedBrand?.style_notes]
                      .filter(Boolean)
                      .join(' · ') || null
                  }
                  promptSnippets={selectedBrand?.prompt_snippets}
                  allowedActions={['summarize', 'categorize', 'rewrite']}
                  defaultAction="summarize"
                  onApply={(text, meta) => {
                    if (meta.action === 'categorize') {
                      setSuccess(`Категория: ${text}`)
                      return
                    }
                    setPostContent(plainTextToHtml(text))
                    setSuccess('AI результат применён к тексту поста')
                  }}
                />

                {adaptPreview && (
                  <div className="grid gap-2 sm:grid-cols-2 text-xs">
                    {Object.entries(adaptPreview).map(([net, text]) => {
                      const limit = adaptLimits?.[net]
                      return (
                        <div key={net} className="rounded border border-[var(--border-color)] p-2">
                          <p className="uppercase text-[var(--text-muted)] mb-1 flex justify-between gap-2">
                            <span>{net} override</span>
                            <span
                              className={
                                limit && text.length > limit
                                  ? 'text-amber-400'
                                  : 'text-[var(--text-muted)]'
                              }
                            >
                              {text.length}
                              {limit != null ? ` / ${limit}` : ''}
                            </span>
                          </p>
                          <textarea
                            value={text}
                            rows={4}
                            className="w-full bg-transparent whitespace-pre-wrap text-[var(--text-primary)] border border-[var(--border-color)] rounded p-1"
                            onChange={(e) =>
                              setAdaptPreview((prev) =>
                                prev ? { ...prev, [net]: e.target.value } : prev,
                              )
                            }
                          />
                        </div>
                      )
                    })}
                  </div>
                )}

                <div>
                  <p className="text-sm text-[var(--text-secondary)] mb-2">
                    Выберите один канал (только connected)
                  </p>
                  <div className="space-y-1 max-h-48 overflow-y-auto">
                    {connectedPublishChannels.map((c) => (
                      <label key={c.id} className="flex items-center gap-2 text-sm cursor-pointer">
                        <input
                          type="radio"
                          name="publish-channel"
                          checked={selectedChannelId === c.id}
                          onChange={() => setSelectedChannelId(c.id)}
                        />
                        <span
                          className="h-2 w-2 rounded-full"
                          style={{ backgroundColor: selectedBrand?.color ?? '#3B82F6' }}
                        />
                        <span className="uppercase text-[var(--text-muted)]">{c.network}</span>
                        {c.title || c.external_id}
                      </label>
                    ))}
                    {connectedPublishChannels.length === 0 && (
                      <p className="text-xs text-[var(--text-muted)]">
                        Нет подтверждённых каналов —{' '}
                        <Link to="/channels" className="text-primary-400 hover:underline">
                          Channels
                        </Link>
                        {ownChannels.length > 0
                          ? ` (${ownChannels.length} own без confirmed access)`
                          : ''}
                      </p>
                    )}
                  </div>
                </div>

                  <div className="flex flex-wrap items-end gap-3">
                  <div>
                    <label className="text-sm text-[var(--text-secondary)]">Schedule</label>
                    <input
                      type="datetime-local"
                      value={smmPublishAt}
                      max={(() => {
                        const d = new Date()
                        d.setDate(d.getDate() + horizonDays)
                        const pad = (n: number) => String(n).padStart(2, '0')
                        return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T23:59`
                      })()}
                      onChange={(e) => {
                        setSmmPublishAt(e.target.value)
                        if (e.target.value) {
                          const picked = new Date(e.target.value)
                          const max = new Date()
                          max.setDate(max.getDate() + horizonDays)
                          if (picked > max) {
                            setError(
                              `Schedule outside plan horizon (${horizonDays} days). Pick an earlier slot or upgrade.`,
                            )
                          }
                        }
                      }}
                      className="block mt-1 px-3 py-2 rounded-xl border border-[var(--border-color)] bg-[var(--bg-primary)]"
                    />
                    <p className="text-xs text-[var(--text-muted)] mt-1">
                      Plan horizon: {horizonDays} days
                    </p>
                  </div>
                  {planFeatures.best_times && (
                    <div className="self-center space-y-1">
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        onClick={async () => {
                          try {
                            const res = await smmService.bestTimes(selectedBrandId)
                            setBestSlots(res.slots ?? [])
                          } catch (err) {
                            setError(err instanceof Error ? err.message : 'Best times failed')
                          }
                        }}
                      >
                        Suggest best time
                      </Button>
                      {bestSlots.slice(0, 4).map((s, i) => {
                        const daysAhead = (s.weekday - new Date().getDay() + 7) % 7 || 7
                        const d = new Date()
                        d.setDate(d.getDate() + daysAhead)
                        d.setHours(s.hour, 0, 0, 0)
                        if (d <= new Date()) d.setDate(d.getDate() + 7)
                        const max = new Date()
                        max.setDate(max.getDate() + horizonDays)
                        if (d > max) return null
                        const pad = (n: number) => String(n).padStart(2, '0')
                        const local = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:00`
                        return (
                          <button
                            key={i}
                            type="button"
                            className="block text-xs text-primary-400 hover:underline"
                            onClick={() => setSmmPublishAt(local)}
                          >
                            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][s.weekday]}{' '}
                            {pad(s.hour)}:00 (score {s.score})
                          </button>
                        )
                      })}
                    </div>
                  )}
                  {planFeatures.approval_workflow && (
                    <label className="flex items-center gap-2 text-sm self-center">
                      <input
                        type="checkbox"
                        checked={requireApproval}
                        onChange={(e) => setRequireApproval(e.target.checked)}
                      />
                      Require approval
                    </label>
                  )}
                  <div className="flex flex-col gap-2 sm:col-span-2 w-full">
                    <div className="flex flex-wrap items-center gap-3">
                      <button
                        type="button"
                        className="text-sm underline text-primary-400"
                        onClick={() => downloadPostsCsvTemplate()}
                      >
                        Download CSV template
                      </button>
                      <label className="text-sm cursor-pointer underline text-primary-400">
                        Import CSV
                        <input
                          type="file"
                          accept=".csv,text/csv"
                          className="hidden"
                          onChange={async (e) => {
                            const file = e.target.files?.[0]
                            if (!file) return
                            setCsvErrors([])
                            setCsvResult('')
                            try {
                              const res = await smmService.importCsv(file, selectedBrandId)
                              const queue =
                                res.status === 'pending_approval'
                                  ? ' → review queue on Calendar'
                                  : ' as drafts'
                              setCsvResult(
                                `Created ${res.created}${queue}` +
                                  (res.errors.length ? `, errors: ${res.errors.length}` : ''),
                              )
                              setCsvErrors(res.errors.slice(0, 20))
                              setSuccess(
                                res.status === 'pending_approval'
                                  ? 'CSV imported into approval queue'
                                  : 'CSV imported (no media)',
                              )
                              if (res.errors.length) {
                                setError(
                                  `CSV: ${res.errors.length} row(s) failed (see details below)`,
                                )
                              }
                            } catch (err) {
                              setError(err instanceof Error ? err.message : 'CSV import failed')
                            }
                            e.target.value = ''
                          }}
                        />
                      </label>
                    </div>
                    <p className="text-xs text-[var(--text-muted)]">
                      Columns: {CSV_POSTS_COLUMNS.map((c) => c.key).join(', ')}. Dates in UTC
                      (ISO or DD.MM.YYYY HH:MM). Comma or semicolon delimiter. With approval
                      workflow each row needs network+channel; without channel jobs stay drafts
                      only when approval is off. Media is not imported.
                    </p>
                    {csvResult && (
                      <span className="text-xs text-[var(--text-muted)]">{csvResult}</span>
                    )}
                    {csvErrors.length > 0 && (
                      <ul className="text-xs text-red-400 list-disc pl-4 space-y-0.5 max-h-32 overflow-y-auto">
                        {csvErrors.map((err) => (
                          <li key={`${err.line}-${err.error}`}>
                            Line {err.line}: {err.error}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="screenshot"
                  type="text"
                  value={screenshot}
                  onChange={(e) => setScreenshot(e.target.value)}
                  placeholder="Screenshot URL"
                />
                <div className="sm:col-span-2">
                  <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">
                    images (one URL per line)
                  </label>
                  <textarea
                    value={imagesText}
                    onChange={(e) => setImagesText(e.target.value)}
                    rows={3}
                    className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
                    placeholder="https://example.com/1.jpg"
                  />
                </div>
                <Input
                  label="image_over_text"
                  type="text"
                  value={imageOverText}
                  onChange={(e) => setImageOverText(e.target.value)}
                  placeholder="Image over text"
                  className="sm:col-span-2"
                />
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <Input
                  label="comments"
                  type="number"
                  min={0}
                  value={comments === '' ? '' : comments}
                  onChange={(e) => {
                    const v = e.target.value
                    setComments(v === '' ? '' : (parseInt(v, 10) || 0))
                  }}
                  placeholder="0"
                />
                <Input
                  label="reposts"
                  type="number"
                  min={0}
                  value={reposts === '' ? '' : reposts}
                  onChange={(e) => {
                    const v = e.target.value
                    setReposts(v === '' ? '' : (parseInt(v, 10) || 0))
                  }}
                  placeholder="0"
                />
                <Input
                  label="likes"
                  type="number"
                  min={0}
                  value={likes === '' ? '' : likes}
                  onChange={(e) => {
                    const v = e.target.value
                    setLikes(v === '' ? '' : (parseInt(v, 10) || 0))
                  }}
                  placeholder="0"
                />
                <Input
                  label="views"
                  type="number"
                  min={0}
                  value={views === '' ? '' : views}
                  onChange={(e) => {
                    const v = e.target.value
                    setViews(v === '' ? '' : (parseInt(v, 10) || 0))
                  }}
                  placeholder="0"
                />
              </div>

              <div className="flex flex-wrap items-center gap-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isAd}
                    onChange={(e) => setIsAd(e.target.checked)}
                    className="w-4 h-4 rounded border-[var(--border-color)] text-primary-500 focus:ring-primary-500/50"
                  />
                  <span className="text-sm text-[var(--text-primary)]">is_ad</span>
                </label>
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-[var(--text-secondary)]">status</label>
                  <select
                    value={status}
                    onChange={(e) => setStatus(e.target.value)}
                    className="px-4 py-2 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                  >
                    <option value="collected">collected</option>
                    <option value="processed">processed</option>
                    <option value="published">published</option>
                    <option value="draft">draft</option>
                    <option value="pending">pending</option>
                    <option value="private">private</option>
                  </select>
                </div>
              </div>

              {editingPostId !== null && (
                <TargetSocialNetworksWidget
                  value={socialNetworks}
                  onChange={setSocialNetworks}
                  selectedChannels={selectedChannels}
                  onSelectedChannelsChange={setSelectedChannels}
                />
              )}

              <CardFooter className="px-0">
                <Button
                  type="submit"
                  isLoading={isCreating}
                  className="w-full sm:w-auto"
                  disabled={
                    editingPostId === null &&
                    (selectedChannelId == null || connectedPublishChannels.length === 0)
                  }
                >
                  {editingPostId !== null ? (
                    <>
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-5 w-5 mr-2"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                      Update Post
                    </>
                  ) : requireApproval ? (
                    'Отправить на согласование'
                  ) : smmPublishAt ? (
                    'Запланировать в канал'
                  ) : (
                    'Отправить в выбранный канал'
                  )}
                </Button>
              </CardFooter>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Tab: Posts (SMM publish jobs) */}
      {activeTab === 'posts' && (
        <Card className="animate-slide-up">
          <CardHeader className="flex flex-row items-center justify-between gap-2">
            <div>
              <CardTitle className="flex items-center gap-2">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-6 w-6 text-primary-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 10h16M4 14h10"
                  />
                </svg>
                Posts
              </CardTitle>
              <CardDescription>
                Отправки в каналы (SMM jobs)
                {selectedBrand ? ` · ${selectedBrand.name}` : ''}
              </CardDescription>
            </div>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => void loadPosts()}
              disabled={isLoadingPosts}
            >
              Refresh
            </Button>
          </CardHeader>
          <CardContent>
            {isLoadingPosts && publishJobs.length === 0 && (
              <div className="text-center py-8 text-[var(--text-muted)]">Loading posts...</div>
            )}
            {!isLoadingPosts && publishJobs.length === 0 && hasLoadedPosts && (
              <div className="text-center py-8 text-[var(--text-muted)]">
                Пока нет отправок. Создайте пост на вкладке Create Post.
              </div>
            )}
            {!isLoadingPosts && publishJobs.length > 0 && (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--border-color)] text-left text-[var(--text-secondary)]">
                      <th className="py-2 pr-3 font-medium">ID</th>
                      <th className="py-2 pr-3 font-medium">Status</th>
                      <th className="py-2 pr-3 font-medium">Channel</th>
                      <th className="py-2 pr-3 font-medium">Text</th>
                      <th className="py-2 pr-3 font-medium">Schedule</th>
                      <th className="py-2 pr-3 font-medium">Created</th>
                      <th className="py-2 pr-3 font-medium">Error</th>
                    </tr>
                  </thead>
                  <tbody>
                    {publishJobs.map((job) => {
                      const plain = htmlToPlainText(job.source_text || '')
                      const targets = (job.targets || [])
                        .map((t) => `${t.network}:${t.external_id}`)
                        .join(', ')
                      const isSelected = collabJobId === job.id
                      return (
                        <tr
                          key={job.id}
                          className={`border-b border-[var(--border-color)] text-[var(--text-primary)] cursor-pointer hover:bg-[var(--bg-secondary)] ${
                            isSelected ? 'bg-[var(--bg-secondary)]' : ''
                          }`}
                          onClick={() => setCollabJobId(isSelected ? null : job.id)}
                        >
                          <td className="py-2 pr-3 whitespace-nowrap">{job.id}</td>
                          <td className="py-2 pr-3 whitespace-nowrap">
                            <span
                              className={
                                job.status === 'published'
                                  ? 'text-emerald-400'
                                  : job.status === 'failed' || job.status === 'partial'
                                    ? 'text-amber-400'
                                    : 'text-[var(--text-secondary)]'
                              }
                            >
                              {job.status}
                            </span>
                          </td>
                          <td
                            className="py-2 pr-3 max-w-[200px] truncate whitespace-nowrap"
                            title={targets}
                          >
                            {targets || '—'}
                          </td>
                          <td className="py-2 pr-3 max-w-[280px] truncate" title={plain}>
                            {plain.slice(0, POST_PREVIEW_LENGTH) || '—'}
                            {plain.length > POST_PREVIEW_LENGTH ? '…' : ''}
                          </td>
                          <td className="py-2 pr-3 text-[var(--text-muted)] whitespace-nowrap">
                            {job.publish_at ? formatDate(job.publish_at) : '—'}
                          </td>
                          <td className="py-2 pr-3 text-[var(--text-muted)] whitespace-nowrap">
                            {formatDate(job.created_at)}
                          </td>
                          <td
                            className="py-2 pr-3 max-w-[200px] truncate text-amber-400"
                            title={job.last_error || undefined}
                          >
                            {job.last_error || '—'}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
            {collabJobId != null && (() => {
              const job = publishJobs.find((j) => j.id === collabJobId)
              if (!job) return null
              return (
                <div className="mt-4">
                  <JobCollabPanel
                    job={job}
                    onJobRestored={(restored) => {
                      setPublishJobs((prev) =>
                        prev.map((j) => (j.id === restored.id ? restored : j)),
                      )
                    }}
                  />
                </div>
              )
            })()}
          </CardContent>
        </Card>
      )}

      {/* Tab: Posts Review */}
      {activeTab === 'posts-review' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle>Posts Review</CardTitle>
            <CardDescription>Ваши посты в статусе review (до 500)</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              onClick={handleLoadPostsReview}
              isLoading={isLoadingPostsReview}
              className="w-full sm:w-auto"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Загрузить посты в статусе review
            </Button>
            {postsReviewError && (
              <Alert variant="error" className="animate-slide-down">{postsReviewError}</Alert>
            )}
            {postsReviewList.length > 0 && (
              <div className="overflow-x-auto mt-4 rounded-xl border border-[var(--border-color)]">
                <table className="w-full border-collapse min-w-max">
                  <thead className="bg-[var(--bg-tertiary)]">
                    <tr>
                      {POSTS_TABLE_COLUMNS.map(({ key, label }) => (
                        <th key={key} className="py-2 px-3 text-left text-sm font-medium text-[var(--text-secondary)] whitespace-nowrap">
                          {label}
                        </th>
                      ))}
                      <th className="py-2 px-3 text-right text-sm font-medium text-[var(--text-secondary)] whitespace-nowrap">
                        Действия
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-color)]">
                    {postsReviewList.map((post) => (
                      <tr key={post.id} className="hover:bg-[var(--bg-tertiary)] transition-colors">
                        {POSTS_TABLE_COLUMNS.map(({ key }) => (
                          <td key={key} className="py-2 px-3 text-sm whitespace-nowrap">
                            {formatPostCell(post, key)}
                          </td>
                        ))}
                        <td className="py-2 px-3 text-right">
                          <Button
                            type="button"
                            variant="secondary"
                            size="sm"
                            onClick={() => handleEditPipelinePost(post)}
                          >
                            Редактировать
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {postsReviewList.length === 0 && !isLoadingPostsReview && !postsReviewError && (
              <p className="text-[var(--text-muted)] mt-2">Нажмите «Загрузить посты в статусе review».</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab: Profile Settings */}
      {activeTab === 'profile' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle>Profile Settings</CardTitle>
            <CardDescription>Select default target social networks for posts</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSaveProfile} className="space-y-6">
              <TargetSocialNetworksWidget
                value={socialNetworks}
                onChange={setSocialNetworks}
                disabled={
                  isLoadingProfile
                    ? {
                        tg: true,
                        vk: true,
                        instagram: true,
                        threads: true,
                        wp: true,
                        dzen: true,
                        tw: true,
                      }
                    : {}
                }
              />
              <CardFooter className="px-0">
                <Button type="submit" className="w-full">
                  Save Profile Settings
                </Button>
              </CardFooter>
            </form>
          </CardContent>
        </Card>
      )}
    </PageContainer>
  )
}
