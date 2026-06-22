import { useState, FormEvent, useEffect, type ReactNode } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import { TipTapEditor } from '@/components/ui/tiptap-editor'
import { createPostService } from '@/services/create-post-service'
import { coreService } from '@/services/core-service'
import {
  TargetSocialNetworksWidget,
  EMPTY_TARGET_SOCIAL_NETWORKS,
  type TargetSocialNetworks,
} from '@/components/target-social-networks'
import type { CpostPostListItem } from '@/types/create-post'
import type { PostRow } from '@/types/core'

const TEXT_MAX_LENGTH = 150000
const POST_PREVIEW_LENGTH = 80

function htmlToPlainText(html: string): string {
  const div = document.createElement('div')
  div.innerHTML = html
  return (div.textContent ?? div.innerText ?? '').trim()
}

function formatDate(iso?: string | null): string {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    return d.toLocaleString()
  } catch {
    return iso
  }
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
  const [activeTab, setActiveTab] = useState<TabId>('create')

  const [socialNetworks, setSocialNetworks] = useState<TargetSocialNetworks>({
    ...EMPTY_TARGET_SOCIAL_NETWORKS,
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

  const [editingPostId, setEditingPostId] = useState<number | null>(null)
  const [posts, setPosts] = useState<CpostPostListItem[]>([])
  const [isLoadingPosts, setIsLoadingPosts] = useState(false)
  const [hasLoadedPosts, setHasLoadedPosts] = useState(false)
  const [deletingPostId, setDeletingPostId] = useState<number | null>(null)

  const [postsReviewList, setPostsReviewList] = useState<PostRow[]>([])
  const [isLoadingPostsReview, setIsLoadingPostsReview] = useState(false)
  const [postsReviewError, setPostsReviewError] = useState('')

  const [isCreating, setIsCreating] = useState(false)
  const [isLoadingProfile, setIsLoadingProfile] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

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
    if (activeTab === 'posts' && !hasLoadedPosts) {
      loadPosts()
    }
  }, [activeTab, hasLoadedPosts])

  async function loadPosts() {
    setIsLoadingPosts(true)
    setError('')
    try {
      const data = await createPostService.getPosts()
      setPosts(data)
      setHasLoadedPosts(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load posts')
    } finally {
      setIsLoadingPosts(false)
    }
  }

  async function handleEditPost(postId: number) {
    setError('')
    try {
      const post = await createPostService.getPost(postId)
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
        Array.isArray(imgs) ? imgs.filter(Boolean).join('\n') : typeof imgs === 'string' ? imgs : ''
      )
      setImageOverText(post.image_over_text ?? '')
      setComments(post.comments ?? '')
      setReposts(post.reposts ?? '')
      setLikes(post.likes ?? '')
      setViews(post.views ?? '')
      setIsAd(post.is_ad ?? false)
      setStatus(post.status ?? 'collected')
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
      setEditingPostId(postId)
      setActiveTab('create')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load post')
    }
  }

  async function handleDeletePost(postId: number) {
    if (deletingPostId !== null) return
    setDeletingPostId(postId)
    setError('')
    try {
      await createPostService.deletePost(postId)
      setPosts((prev) => prev.filter((p) => p.id !== postId))
      setSuccess('Post deleted')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete post')
    } finally {
      setDeletingPostId(null)
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

    if (!Object.values(socialNetworks).some(Boolean)) {
      setError('Please select at least one social network')
      setIsCreating(false)
      return
    }

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
    }

    try {
      if (editingPostId !== null) {
        const id = editingPostId
        await createPostService.updatePost(id, basePayload)
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
        setPosts((prev) =>
          prev.map((p) =>
            p.id === id
              ? {
                  ...p,
                  title: basePayload.title ?? null,
                  post_text: plainText,
                  domain: basePayload.domain ?? null,
                  url: basePayload.url ?? null,
                  author: basePayload.author ?? null,
                  avatar: basePayload.avatar ?? null,
                  post_date: basePayload.post_date ?? null,
                  screenshot: basePayload.screenshot ?? null,
                  images: basePayload.images ?? [],
                  image_over_text: basePayload.image_over_text ?? null,
                  comments: basePayload.comments ?? 0,
                  reposts: basePayload.reposts ?? 0,
                  likes: basePayload.likes ?? 0,
                  views: basePayload.views ?? 0,
                  is_ad: basePayload.is_ad,
                  status: basePayload.status ?? null,
                  to_tg: socialNetworks.tg,
                  to_tw: socialNetworks.tw,
                  to_wp: socialNetworks.wp,
                  to_vk: socialNetworks.vk,
                  to_threads: socialNetworks.threads,
                  to_dzen: socialNetworks.dzen,
                  to_instagram: socialNetworks.instagram,
                }
              : p
          )
        )
      } else {
        const {
          to_tg: _tg,
          to_tw: _tw,
          to_wp: _wp,
          to_vk: _vk,
          to_threads: _threads,
          to_dzen: _dz,
          to_instagram: _ig,
          ...createFields
        } = basePayload
        await createPostService.createPost({
          social_networks: socialNetworks,
          ...createFields,
        })
        setSuccess('Post created successfully')
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
        const list = await createPostService.getPosts()
        setPosts(list)
        setHasLoadedPosts(true)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save post')
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <PageContainer maxWidth="wide">
      <PageHeader title="Posts" description="Create and manage universal posts for social networks" />

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
                : 'Create a universal post and send it to any selected social network'}
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
              </div>

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

              <TargetSocialNetworksWidget value={socialNetworks} onChange={setSocialNetworks} />

              <CardFooter className="px-0">
                <Button type="submit" isLoading={isCreating} className="w-full sm:w-auto">
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
                  ) : (
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
                          d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                        />
                      </svg>
                      Create Post
                    </>
                  )}
                </Button>
              </CardFooter>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Tab: Posts list */}
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
              <CardDescription>All your manual posts from the posts table</CardDescription>
            </div>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={loadPosts}
              disabled={isLoadingPosts}
            >
              Refresh
            </Button>
          </CardHeader>
          <CardContent>
            {isLoadingPosts && posts.length === 0 && (
              <div className="text-center py-8 text-[var(--text-muted)]">Loading posts...</div>
            )}
            {!isLoadingPosts && posts.length === 0 && hasLoadedPosts && (
              <div className="text-center py-8 text-[var(--text-muted)]">No posts yet.</div>
            )}
            {!isLoadingPosts && posts.length > 0 && (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm whitespace-nowrap">
                  <thead>
                    <tr className="border-b border-[var(--border-color)] text-left text-[var(--text-secondary)]">
                      <th className="py-2 pr-2 font-medium">id</th>
                      <th className="py-2 pr-2 font-medium">user_id</th>
                      <th className="py-2 pr-2 font-medium">domain</th>
                      <th className="py-2 pr-2 font-medium">url</th>
                      <th className="py-2 pr-2 font-medium">title</th>
                      <th className="py-2 pr-2 font-medium">author</th>
                      <th className="py-2 pr-2 font-medium">avatar</th>
                      <th className="py-2 pr-2 font-medium">post_date</th>
                      <th className="py-2 pr-2 font-medium">post_text</th>
                      <th className="py-2 pr-2 font-medium">screenshot</th>
                      <th className="py-2 pr-2 font-medium">images</th>
                      <th className="py-2 pr-2 font-medium">image_over_text</th>
                      <th className="py-2 pr-2 font-medium">comments</th>
                      <th className="py-2 pr-2 font-medium">reposts</th>
                      <th className="py-2 pr-2 font-medium">likes</th>
                      <th className="py-2 pr-2 font-medium">views</th>
                      <th className="py-2 pr-2 font-medium">is_ad</th>
                      <th className="py-2 pr-2 font-medium">status</th>
                      <th className="py-2 pr-2 font-medium">post_type</th>
                      <th className="py-2 pr-2 font-medium">to_tg</th>
                      <th className="py-2 pr-2 font-medium">to_tw</th>
                      <th className="py-2 pr-2 font-medium">to_wp</th>
                      <th className="py-2 pr-2 font-medium">to_vk</th>
                      <th className="py-2 pr-2 font-medium">to_threads</th>
                      <th className="py-2 pr-2 font-medium">to_dzen</th>
                      <th className="py-2 pr-2 font-medium">to_instagram</th>
                      <th className="py-2 pr-2 font-medium">created_at</th>
                      <th className="py-2 pr-2 font-medium">updated_at</th>
                      <th className="py-2 pr-2 font-medium w-32 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {posts.map((post) => (
                      <tr
                        key={post.id}
                        className="border-b border-[var(--border-color)] text-[var(--text-primary)]"
                      >
                        <td className="py-2 pr-2">{cellValue(post.id)}</td>
                        <td className="py-2 pr-2">{cellValue(post.user_id)}</td>
                        <td className="py-2 pr-2 max-w-[120px] truncate" title={post.domain ?? undefined}>
                          {cellValue(post.domain, 40)}
                        </td>
                        <td className="py-2 pr-2 max-w-[120px] truncate" title={post.url ?? undefined}>
                          {cellValue(post.url, 40)}
                        </td>
                        <td className="py-2 pr-2 max-w-[140px] truncate" title={post.title ?? undefined}>
                          {cellValue(post.title, 50)}
                        </td>
                        <td className="py-2 pr-2 max-w-[100px] truncate" title={post.author ?? undefined}>
                          {cellValue(post.author, 30)}
                        </td>
                        <td className="py-2 pr-2 max-w-[100px] truncate" title={post.avatar ?? undefined}>
                          {cellValue(post.avatar, 30)}
                        </td>
                        <td className="py-2 pr-2 text-[var(--text-muted)]">
                          {formatDate(post.post_date)}
                        </td>
                        <td className="py-2 pr-2 max-w-[180px] truncate" title={post.post_text ?? undefined}>
                          {cellValue(post.post_text, POST_PREVIEW_LENGTH)}
                        </td>
                        <td className="py-2 pr-2 max-w-[80px] truncate" title={post.screenshot ?? undefined}>
                          {cellValue(post.screenshot, 30)}
                        </td>
                        <td className="py-2 pr-2">{cellValue(post.images)}</td>
                        <td className="py-2 pr-2 max-w-[80px] truncate" title={post.image_over_text ?? undefined}>
                          {cellValue(post.image_over_text, 30)}
                        </td>
                        <td className="py-2 pr-2">{cellValue(post.comments)}</td>
                        <td className="py-2 pr-2">{cellValue(post.reposts)}</td>
                        <td className="py-2 pr-2">{cellValue(post.likes)}</td>
                        <td className="py-2 pr-2">{cellValue(post.views)}</td>
                        <td className="py-2 pr-2">{cellValue(post.is_ad)}</td>
                        <td className="py-2 pr-2">{cellValue(post.status)}</td>
                        <td className="py-2 pr-2">{cellValue(post.post_type)}</td>
                        <td className="py-2 pr-2">{cellValue(post.to_tg)}</td>
                        <td className="py-2 pr-2">{cellValue(post.to_tw)}</td>
                        <td className="py-2 pr-2">{cellValue(post.to_wp)}</td>
                        <td className="py-2 pr-2">{cellValue(post.to_vk)}</td>
                        <td className="py-2 pr-2">{cellValue(post.to_threads)}</td>
                        <td className="py-2 pr-2">{cellValue(post.to_dzen)}</td>
                        <td className="py-2 pr-2">{cellValue(post.to_instagram)}</td>
                        <td className="py-2 pr-2 text-[var(--text-muted)]">
                          {formatDate(post.created_at)}
                        </td>
                        <td className="py-2 pr-2 text-[var(--text-muted)]">
                          {formatDate(post.updated_at)}
                        </td>
                        <td className="py-2 pr-2 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEditPost(post.id)}
                            >
                              Edit
                            </Button>
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              className="text-red-400 hover:text-red-300"
                              onClick={() => handleDeletePost(post.id)}
                              disabled={deletingPostId === post.id}
                            >
                              {deletingPostId === post.id ? 'Deleting…' : 'Delete'}
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
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
                            onClick={() => handleEditPost(post.id)}
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
