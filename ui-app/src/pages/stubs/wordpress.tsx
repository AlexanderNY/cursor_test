import { useState, useEffect, FormEvent } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import { TipTapEditor } from '@/components/ui/tiptap-editor'
import { wordpressService } from '@/services/wordpress-service'
import {
  TargetSocialNetworksWidget,
  createDefaultTargets,
  type TargetSocialNetworks,
} from '@/components/target-social-networks'
import type { WordPressPost, WordPressPostListItem, PostStatus, PublishScheduleType } from '@/types/wordpress'

function generateId(): string {
  return Math.random().toString(36).substring(2, 9)
}

const SCHEDULE_MINUTES = [0, 15, 30, 45] as const
type ScheduleMinute = (typeof SCHEDULE_MINUTES)[number]

type CollectSiteItem = {
  id: string
  siteUrl: string
  scheduleType: PublishScheduleType
  scheduleHour: number
  scheduleMinute: ScheduleMinute
}

const PUBLISH_INTERVAL_MINUTES_OPTIONS = Array.from({ length: 97 }, (_, i) => 15 + i * 15) // 15 .. 1440, step 15

export function WordPressPage() {
  // Tab state
  const [activeTab, setActiveTab] = useState<'create' | 'posts' | 'profile' | 'processing'>('create')

  // Profile state
  const [siteUrl, setSiteUrl] = useState('')
  const [username, setUsername] = useState('')
  const [appPassword, setAppPassword] = useState('')
  const [publishEnabled, setPublishEnabled] = useState(false)
  const [publishAllReady, setPublishAllReady] = useState(true)
  const [publishLimit, setPublishLimit] = useState('')
  const [publishIntervalMinutes, setPublishIntervalMinutes] = useState(15)
  const [processBeforePublish, setProcessBeforePublish] = useState(false)
  const [processDescription, setProcessDescription] = useState('')
  const [removeEmojis, setRemoveEmojis] = useState(false)
  const [removeImages, setRemoveImages] = useState(false)
  const [cleanHtml, setCleanHtml] = useState(false)
  const [processServiceWordpress, setProcessServiceWordpress] = useState(false)
  const [processServiceTelegram, setProcessServiceTelegram] = useState(false)
  const [processServiceTwitter, setProcessServiceTwitter] = useState(false)
  const [processServiceVkontakte, setProcessServiceVkontakte] = useState(false)
  const [statusReviewAfterProcess, setStatusReviewAfterProcess] = useState(false)
  const [addStaticHtml, setAddStaticHtml] = useState(false)
  const [staticHtmlContent, setStaticHtmlContent] = useState('')
  const [collectEnabled, setCollectEnabled] = useState(false)
  const [collectAllAvailable, setCollectAllAvailable] = useState(true)
  const [collectLimit, setCollectLimit] = useState('1')
  const [publishScheduleType, setPublishScheduleType] = useState<'on_new_messages' | 'by_intervals'>('on_new_messages')
  const [publishScheduleHour, setPublishScheduleHour] = useState(9)
  const [publishScheduleMinute, setPublishScheduleMinute] = useState<ScheduleMinute>(0)
  const [collectSites, setCollectSites] = useState<CollectSiteItem[]>([
    { id: generateId(), siteUrl: '', scheduleType: 'on_new_messages', scheduleHour: 9, scheduleMinute: 0 }
  ])
  
  // Post state
  const [postTitle, setPostTitle] = useState('')
  const [postContent, setPostContent] = useState('')
  const [postStatus, setPostStatus] = useState<PostStatus>('draft')
  const [postCategories, setPostCategories] = useState<string[]>([''])
  const [postTags, setPostTags] = useState<string[]>([''])
  const [postExcerpt, setPostExcerpt] = useState('')
  const [postSlug, setPostSlug] = useState('')
  const [featuredMedia, setFeaturedMedia] = useState('')
  const [postMeta, setPostMeta] = useState('')
  const [postTargets, setPostTargets] = useState<TargetSocialNetworks>(() =>
    createDefaultTargets('wp')
  )

  // Posts list state
  const [posts, setPosts] = useState<WordPressPostListItem[]>([])
  const [isLoadingPosts, setIsLoadingPosts] = useState(false)
  const [hasLoadedPosts, setHasLoadedPosts] = useState(false)
  
  // Editing post (id поста при редактировании; при создании — null)
  const [editingPostId, setEditingPostId] = useState<number | null>(null)
  const [deletingPostId, setDeletingPostId] = useState<number | null>(null)
  
  // Loading and error states
  const [isLoadingProfile, setIsLoadingProfile] = useState(true)
  const [isSavingProfile, setIsSavingProfile] = useState(false)
  const [isCreatingPost, setIsCreatingPost] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')


  // Load profile on mount
  useEffect(() => {
    loadProfile()
  }, [])

  // Load posts when Posts tab is opened first time
  useEffect(() => {
    if (activeTab === 'posts' && !hasLoadedPosts) {
      loadPosts()
    }
  }, [activeTab, hasLoadedPosts])

  async function loadProfile() {
    setIsLoadingProfile(true)
    setError('')
    try {
      const [publishProfile, collectProfile] = await Promise.all([
        wordpressService.getPublishProfile(),
        wordpressService.getCollectProfile(),
      ])
      setSiteUrl(publishProfile.site_url || '')
      setUsername(publishProfile.username || '')
      setAppPassword(publishProfile.app_password || '')
      setPublishEnabled(publishProfile.publish_enabled ?? false)
      setPublishAllReady(publishProfile.publish_all_ready ?? true)
      setPublishLimit(publishProfile.publish_limit != null ? String(publishProfile.publish_limit) : '')
      setPublishIntervalMinutes(
        publishProfile.publish_interval_minutes != null && publishProfile.publish_interval_minutes >= 15 && publishProfile.publish_interval_minutes <= 1440
          ? publishProfile.publish_interval_minutes
          : 15
      )
      setProcessBeforePublish(publishProfile.process_before_publish ?? false)
      setProcessDescription(publishProfile.process_description ?? '')
      setRemoveEmojis(publishProfile.remove_emojis ?? false)
      setRemoveImages(publishProfile.remove_images ?? false)
      setCleanHtml(publishProfile.clean_html ?? false)
      const ps = publishProfile.process_services
      if (Array.isArray(ps)) {
        setProcessServiceWordpress(ps.includes('wordpress'))
        setProcessServiceTelegram(ps.includes('telegram'))
        setProcessServiceTwitter(ps.includes('twitter'))
        setProcessServiceVkontakte(ps.includes('vkontakte'))
      }
      setStatusReviewAfterProcess(publishProfile.status_review_after_process ?? false)
      setAddStaticHtml(publishProfile.add_static_html ?? false)
      setStaticHtmlContent((publishProfile.static_html_content ?? '').slice(0, 1000))
      setCollectEnabled(collectProfile.collect_enabled ?? false)
      setCollectAllAvailable(collectProfile.collect_all_available ?? true)
      const cl = collectProfile.collect_limit
      setCollectLimit(cl != null && cl >= 1 && cl <= 25 ? String(cl) : '1')
      setPublishScheduleType((publishProfile.schedule_type as PublishScheduleType) || 'on_new_messages')
      const ti = publishProfile.time_intervals
      if (typeof ti === 'string' && ti && ti.includes(':')) {
        const [h, m] = ti.split(':').map(Number)
        const hour = Number.isFinite(h) ? Math.max(0, Math.min(23, h)) : 9
        const rawMin = Number.isFinite(m) ? m : 0
        const minute = SCHEDULE_MINUTES.reduce((prev, curr) =>
          Math.abs(curr - rawMin) < Math.abs(prev - rawMin) ? curr : prev
        ) as ScheduleMinute
        setPublishScheduleHour(hour)
        setPublishScheduleMinute(minute)
      } else if (Array.isArray(ti) && ti.length > 0 && ti[0]?.start) {
        const [h, m] = ti[0].start.split(':').map(Number)
        const hour = Number.isFinite(h) ? Math.max(0, Math.min(23, h)) : 9
        const rawMin = Number.isFinite(m) ? m : 0
        const minute = SCHEDULE_MINUTES.reduce((prev, curr) =>
          Math.abs(curr - rawMin) < Math.abs(prev - rawMin) ? curr : prev
        ) as ScheduleMinute
        setPublishScheduleHour(hour)
        setPublishScheduleMinute(minute)
      }
      if (collectProfile.collect_sites && collectProfile.collect_sites.length > 0) {
        setCollectSites(collectProfile.collect_sites.map((s) => {
          let scheduleHour = 9
          let scheduleMinute: ScheduleMinute = 0
          const ti = s.time_intervals
          if (typeof ti === 'string' && ti && ti.includes(':')) {
            const [h, m] = ti.split(':').map(Number)
            scheduleHour = Number.isFinite(h) ? Math.max(0, Math.min(23, h)) : 9
            const rawMin = Number.isFinite(m) ? m : 0
            scheduleMinute = SCHEDULE_MINUTES.reduce((prev, curr) =>
              Math.abs(curr - rawMin) < Math.abs(prev - rawMin) ? curr : prev
            ) as ScheduleMinute
          }
          return {
            id: generateId(),
            siteUrl: s.site_url || '',
            scheduleType: (s.schedule_type as PublishScheduleType) || 'on_new_messages',
            scheduleHour,
            scheduleMinute,
          }
        }))
      }
    } catch (err) {
      console.log('Profile not found, using defaults', err)
    } finally {
      setIsLoadingProfile(false)
    }
  }

  async function loadPosts() {
    setIsLoadingPosts(true)
    setError('')
    try {
      const data = await wordpressService.getPosts()
      setPosts(data)
      setHasLoadedPosts(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load posts')
    } finally {
      setIsLoadingPosts(false)
    }
  }

  async function handleDeletePost(postId: number) {
    if (deletingPostId !== null) return
    setDeletingPostId(postId)
    setError('')
    try {
      await wordpressService.deletePost(postId)
      setPosts((prev) => prev.filter((p) => p.id !== postId))
      setSuccess('Post marked as deleted')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete post')
    } finally {
      setDeletingPostId(null)
    }
  }

  async function handleEditPost(postId: number) {
    setError('')
    try {
      const post = await wordpressService.getPost(postId)
      setPostTitle(post.title ?? '')
      setPostContent(post.post_text ?? '')
      setPostStatus((post.status as PostStatus) ?? 'draft')
      setPostCategories(post.categories && post.categories.length > 0 ? post.categories : [''])
      setPostTags(post.tags && post.tags.length > 0 ? post.tags : [''])
      setPostExcerpt(post.excerpt ?? '')
      setPostSlug(post.slug ?? '')
      setFeaturedMedia(post.featured_media != null ? String(post.featured_media) : '')
      setPostMeta(post.meta ? JSON.stringify(post.meta, null, 2) : '')
      setEditingPostId(postId)
      setActiveTab('create')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load post for editing')
    }
  }

  async function handleSavePostProfile(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsSavingProfile(true)
    const timeIntervals = publishScheduleType === 'by_intervals'
      ? `${String(publishScheduleHour).padStart(2, '0')}:${String(publishScheduleMinute).padStart(2, '0')}`
      : undefined
    const limitNum = publishLimit.trim() ? parseInt(publishLimit, 10) : undefined
    if (publishLimit.trim() && (Number.isNaN(limitNum) || limitNum < 0)) {
      setError('Publish limit must be a non-negative number')
      setIsSavingProfile(false)
      return
    }
    try {
      await wordpressService.savePublishProfile({
        publish_enabled: publishEnabled,
        schedule_type: publishScheduleType,
        time_intervals: timeIntervals,
        site_url: siteUrl || undefined,
        username: username || undefined,
        app_password: appPassword || undefined,
        publish_all_ready: publishAllReady,
        publish_limit: publishAllReady ? undefined : limitNum,
        publish_interval_minutes: publishAllReady ? undefined : publishIntervalMinutes,
        process_before_publish: processBeforePublish,
        process_description: processBeforePublish ? processDescription || undefined : undefined,
        remove_emojis: removeEmojis,
        remove_images: removeImages,
        clean_html: cleanHtml,
        process_services: [
          ...(processServiceWordpress ? ['wordpress'] : []),
          ...(processServiceTelegram ? ['telegram'] : []),
          ...(processServiceTwitter ? ['twitter'] : []),
          ...(processServiceVkontakte ? ['vkontakte'] : []),
        ],
        status_review_after_process: statusReviewAfterProcess,
        add_static_html: addStaticHtml,
        static_html_content: addStaticHtml ? (staticHtmlContent || undefined)?.slice(0, 1000) : undefined,
      })
      setSuccess(activeTab === 'processing' ? 'Processing settings saved successfully' : 'Post profile settings saved successfully')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save post profile settings')
    } finally {
      setIsSavingProfile(false)
    }
  }

  async function handleSaveProfile(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsSavingProfile(true)
    const timeIntervals = publishScheduleType === 'by_intervals'
      ? `${String(publishScheduleHour).padStart(2, '0')}:${String(publishScheduleMinute).padStart(2, '0')}`
      : undefined
    const limitNum = publishLimit.trim() ? parseInt(publishLimit, 10) : undefined
    if (publishLimit.trim() && (Number.isNaN(limitNum) || limitNum < 0)) {
      setError('Publish limit must be a non-negative number')
      setIsSavingProfile(false)
      return
    }
    const collect_sites = collectSites.map((s) => ({
      site_url: s.siteUrl || undefined,
      schedule_type: s.scheduleType,
      time_intervals: `${String(s.scheduleHour).padStart(2, '0')}:${String(s.scheduleMinute).padStart(2, '0')}`,
    }))
    const limitVal = parseInt(collectLimit, 10) || 1
    const collectLimitNum = collectAllAvailable ? undefined : Math.max(1, Math.min(25, limitVal))
    if (!collectAllAvailable && (limitVal < 1 || limitVal > 25)) {
      setError('Ограничение количества постов: от 1 до 25')
      setIsSavingProfile(false)
      return
    }
    try {
      await Promise.all([
        wordpressService.savePublishProfile({
          publish_enabled: publishEnabled,
          schedule_type: publishScheduleType,
          time_intervals: timeIntervals,
          site_url: siteUrl || undefined,
          username: username || undefined,
          app_password: appPassword || undefined,
          publish_all_ready: publishAllReady,
          publish_limit: publishAllReady ? undefined : limitNum,
          publish_interval_minutes: publishAllReady ? undefined : publishIntervalMinutes,
          process_before_publish: processBeforePublish,
          process_description: processBeforePublish ? processDescription || undefined : undefined,
          remove_emojis: removeEmojis,
          remove_images: removeImages,
          clean_html: cleanHtml,
          process_services: [
            ...(processServiceWordpress ? ['wordpress'] : []),
            ...(processServiceTelegram ? ['telegram'] : []),
            ...(processServiceTwitter ? ['twitter'] : []),
            ...(processServiceVkontakte ? ['vkontakte'] : []),
          ],
          status_review_after_process: statusReviewAfterProcess,
          add_static_html: addStaticHtml,
          static_html_content: addStaticHtml ? (staticHtmlContent || undefined)?.slice(0, 1000) : undefined,
        }),
        wordpressService.saveCollectProfile({
          collect_enabled: collectEnabled,
          collect_sites,
          collect_all_available: collectAllAvailable,
          collect_limit: collectLimitNum,
        }),
      ])
      setSuccess('Profile settings saved successfully')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save profile settings')
    } finally {
      setIsSavingProfile(false)
    }
  }

  async function handleCreatePost(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsCreatingPost(true)

    let metaObj: Record<string, any> = {}
    if (postMeta.trim()) {
      try {
        metaObj = JSON.parse(postMeta)
      } catch {
        setError('Invalid JSON format for post.meta')
        setIsCreatingPost(false)
        return
      }
    }

    const post: WordPressPost = {
      to_tg: postTargets.tg,
      to_tw: postTargets.tw,
      to_wp: postTargets.wp,
      to_vk: postTargets.vk,
      to_threads: postTargets.threads,
      to_dzen: postTargets.dzen,
      to_instagram: postTargets.instagram,
      post: {
        title: postTitle,
        content: postContent,
        status: postStatus,
        categories: postCategories.filter(c => c.trim()).length > 0 ? postCategories.filter(c => c.trim()) : undefined,
        tags: postTags.filter(t => t.trim()).length > 0 ? postTags.filter(t => t.trim()) : undefined,
        excerpt: postExcerpt || undefined,
        slug: postSlug || undefined,
        featured_media: featuredMedia ? Number(featuredMedia) : undefined,
        meta: Object.keys(metaObj).length > 0 ? metaObj : undefined,
      },
    }

    try {
      if (editingPostId !== null) {
        await wordpressService.updatePost(editingPostId, post)
        setSuccess('Post updated successfully')
        setEditingPostId(null)
        setPostTitle('')
        setPostContent('')
        setPostStatus('draft')
        setPostCategories([''])
        setPostTags([''])
        setPostExcerpt('')
        setPostSlug('')
        setFeaturedMedia('')
        setPostMeta('')
        loadPosts()
      } else {
        await wordpressService.createPost(post)
        setSuccess('Post created successfully')
        setPostTitle('')
        setPostContent('')
        setPostStatus('draft')
        setPostCategories([''])
        setPostTags([''])
        setPostExcerpt('')
        setPostSlug('')
        setFeaturedMedia('')
        setPostMeta('')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : (editingPostId !== null ? 'Failed to update post' : 'Failed to create post'))
    } finally {
      setIsCreatingPost(false)
    }
  }


  function addCollectSite() {
    if (collectSites.length >= 5) return
    setCollectSites(prev => [...prev, {
      id: generateId(),
      siteUrl: '',
      scheduleType: 'on_new_messages',
      scheduleHour: 9,
      scheduleMinute: 0
    }])
  }

  function removeCollectSite(siteId: string) {
    if (collectSites.length <= 1) return
    setCollectSites(prev => prev.filter(s => s.id !== siteId))
  }

  function updateCollectSiteUrl(siteId: string, value: string) {
    setCollectSites(prev => prev.map(s => s.id === siteId ? { ...s, siteUrl: value } : s))
  }

  function updateCollectSiteScheduleType(siteId: string, value: PublishScheduleType) {
    setCollectSites(prev => prev.map(s => s.id === siteId ? { ...s, scheduleType: value } : s))
  }

  function updateCollectSiteScheduleTime(siteId: string, hour?: number, minute?: ScheduleMinute) {
    setCollectSites(prev => prev.map(s => {
      if (s.id !== siteId) return s
      return {
        ...s,
        ...(hour !== undefined && { scheduleHour: hour }),
        ...(minute !== undefined && { scheduleMinute: minute })
      }
    }))
  }

  function updateStringArray(setter: (arr: string[]) => void, index: number, value: string) {
    setter((prev) => {
      const newArr = [...prev]
      newArr[index] = value
      return newArr
    })
  }

  function addStringArrayField(setter: (arr: string[]) => void) {
    setter(prev => [...prev, ''])
  }

  function removeStringArrayField(setter: (arr: string[]) => void, index: number) {
    setter(prev => prev.filter((_, i) => i !== index))
  }

  return (
    <PageContainer maxWidth="wide">
      <PageHeader title="WordPress Integration" description="Manage your WordPress sites and content" />

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
          className={`px-6 py-3 text-sm font-medium transition-all relative ${
            activeTab === 'create'
              ? 'text-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
          onClick={() => {
            setEditingPostId(null)
            setPostTitle('')
            setPostContent('')
            setPostStatus('draft')
            setPostCategories([''])
            setPostTags([''])
            setPostExcerpt('')
            setPostSlug('')
            setFeaturedMedia('')
            setPostMeta('')
            setActiveTab('create')
          }}
        >
          Create Post
          {activeTab === 'create' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500" />
          )}
        </button>
        <button
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
        <button
          className={`px-6 py-3 text-sm font-medium transition-all relative ${
            activeTab === 'processing'
              ? 'text-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
          onClick={() => setActiveTab('processing')}
        >
          Обработка
          {activeTab === 'processing' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500" />
          )}
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'create' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              Create WordPress Post
            </CardTitle>
            <CardDescription>Create a new post for your WordPress site</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreatePost} className="space-y-6">
              {/* Title */}
              <Input
                label="Title"
                type="text"
                value={postTitle}
                onChange={(e) => setPostTitle(e.target.value)}
                required
                placeholder="Enter post title"
              />

              {/* Content */}
              <div>
                <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">
                  Content (HTML)
                </label>
                <TipTapEditor
                  content={postContent}
                  onChange={setPostContent}
                  placeholder="Enter post content (HTML supported)"
                  toolbarButtons={['bold', 'italic', 'underline', 'strike', 'heading', 'bulletList', 'orderedList', 'blockquote', 'code', 'codeBlock', 'horizontalRule', 'undo', 'redo']}
                />
              </div>

              {/* Status */}
              <div>
                <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">
                  Status
                </label>
                <select
                  value={postStatus}
                  onChange={(e) => setPostStatus(e.target.value as PostStatus)}
                  className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
                >
                  <option value="draft">Draft</option>
                  <option value="publish">Publish</option>
                  <option value="pending">Pending Review</option>
                  <option value="private">Private</option>
                </select>
              </div>

              {/* Categories */}
              <div>
                <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">
                  Categories (IDs)
                </label>
                {postCategories.map((category, index) => (
                  <div key={index} className="flex gap-3 mb-2">
                    <Input
                      value={category}
                      onChange={(e) => updateStringArray(setPostCategories, index, e.target.value)}
                      placeholder="Enter category ID"
                      className="flex-1"
                    />
                    {postCategories.length > 1 && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeStringArrayField(setPostCategories, index)}
                        className="px-3 text-red-400 hover:text-red-300"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </Button>
                    )}
                  </div>
                ))}
                <Button type="button" variant="secondary" size="sm" onClick={() => addStringArrayField(setPostCategories)}>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  Add Category
                </Button>
              </div>

              {/* Tags */}
              <div>
                <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">
                  Tags (IDs)
                </label>
                {postTags.map((tag, index) => (
                  <div key={index} className="flex gap-3 mb-2">
                    <Input
                      value={tag}
                      onChange={(e) => updateStringArray(setPostTags, index, e.target.value)}
                      placeholder="Enter tag ID"
                      className="flex-1"
                    />
                    {postTags.length > 1 && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeStringArrayField(setPostTags, index)}
                        className="px-3 text-red-400 hover:text-red-300"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </Button>
                    )}
                  </div>
                ))}
                <Button type="button" variant="secondary" size="sm" onClick={() => addStringArrayField(setPostTags)}>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  Add Tag
                </Button>
              </div>

              {/* Excerpt */}
              <Input
                label="Excerpt"
                type="text"
                value={postExcerpt}
                onChange={(e) => setPostExcerpt(e.target.value)}
                placeholder="Brief description of the post"
              />

              {/* Slug */}
              <Input
                label="Slug"
                type="text"
                value={postSlug}
                onChange={(e) => setPostSlug(e.target.value)}
                placeholder="URL slug (e.g., my-post-title)"
              />

              {/* Featured Media */}
              <Input
                label="Featured Media ID"
                type="number"
                value={featuredMedia}
                onChange={(e) => setFeaturedMedia(e.target.value)}
                placeholder="ID of the featured image"
              />

              {/* Meta */}
              <div>
                <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">
                  Meta (JSON)
                </label>
                <textarea
                  value={postMeta}
                  onChange={(e) => setPostMeta(e.target.value)}
                  rows={4}
                  className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl font-mono text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
                  placeholder='{"key": "value"}'
                />
                <p className="text-xs text-[var(--text-muted)] mt-1">
                  Enter JSON object for additional post metadata
                </p>
              </div>

              {editingPostId === null && (
                <TargetSocialNetworksWidget value={postTargets} onChange={setPostTargets} />
              )}

              <CardFooter className="px-0">
                {editingPostId !== null ? (
                  <Button type="submit" isLoading={isCreatingPost} className="w-full sm:w-auto">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Update Post
                  </Button>
                ) : (
                  <Button type="submit" isLoading={isCreatingPost} className="w-full sm:w-auto">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                    Create Post
                  </Button>
                )}
              </CardFooter>
            </form>
          </CardContent>
        </Card>
      )}

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
              <CardDescription>All posts from your connected WordPress account</CardDescription>
            </div>
            <Button type="button" variant="secondary" size="sm" onClick={loadPosts} isLoading={isLoadingPosts}>
              Refresh
            </Button>
          </CardHeader>
          <CardContent>
            {isLoadingPosts && posts.length === 0 && (
              <div className="text-center py-8 text-[var(--text-muted)]">Loading posts...</div>
            )}

            {!isLoadingPosts && posts.length === 0 && hasLoadedPosts && (
              <div className="text-center py-8 text-[var(--text-muted)]">
                No posts found for this account.
              </div>
            )}

            {!isLoadingPosts && posts.length > 0 && (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--border-color)] text-left text-[var(--text-secondary)]">
                      <th className="py-2 pr-4 font-medium">Title</th>
                      <th className="py-2 pr-4 font-medium">Status</th>
                      <th className="py-2 pr-4 font-medium">Excerpt</th>
                      <th className="py-2 pr-4 font-medium w-24 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {posts.map((post, index) => (
                      <tr
                        key={post.id ?? index}
                        className="border-b border-[var(--border-color)] last:border-0"
                      >
                        <td className="py-2 pr-4 text-[var(--text-primary)]">{post.title}</td>
                        <td className="py-2 pr-4">
                          <span className="inline-flex items-center rounded-full bg-[var(--bg-secondary)] px-2 py-0.5 text-xs font-medium text-[var(--text-secondary)]">
                            {post.status}
                          </span>
                        </td>
                        <td className="py-2 pr-4 text-[var(--text-secondary)]">
                          {post.excerpt || '—'}
                        </td>
                        <td className="py-2 pr-4 text-right">
                          <div className="flex items-center justify-end gap-1">
                            <button
                              type="button"
                              onClick={() => post.id != null && handleEditPost(post.id)}
                              disabled={post.id == null}
                              className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-primary-400 hover:bg-[var(--bg-secondary)] transition-colors disabled:opacity-50"
                              title="Edit post"
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                              </svg>
                            </button>
                            <button
                              type="button"
                              onClick={() => post.id != null && handleDeletePost(post.id)}
                              disabled={post.id == null || deletingPostId === post.id}
                              className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-red-400 hover:bg-[var(--bg-secondary)] transition-colors disabled:opacity-50"
                              title="Delete post"
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
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

      {/* Profile Settings (Publishing + Collection) */}
      {activeTab === 'profile' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Profile Settings
            </CardTitle>
            <CardDescription>Configure WordPress connection, publishing and collection settings</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingProfile ? (
              <div className="text-center py-8 text-[var(--text-muted)]">Loading profile...</div>
            ) : (
              <form onSubmit={handleSaveProfile} className="space-y-8">
                {/* Publishing */}
                <div className="space-y-4">
                  <h3 className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                    Publishing
                  </h3>
                <label className="flex items-center gap-3 cursor-pointer group">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={publishEnabled}
                      onChange={(e) => setPublishEnabled(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                    <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                  </div>
                  <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                    Enable publishing
                  </span>
                </label>

                {publishEnabled && (
                  <>
                    <label className="flex items-center gap-3 cursor-pointer group">
                      <div className="relative">
                        <input
                          type="checkbox"
                          checked={publishAllReady}
                          onChange={(e) => setPublishAllReady(e.target.checked)}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                        <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                      </div>
                      <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                        Публиковать все посты, готовые к публикации
                      </span>
                    </label>

                    {!publishAllReady && (
                      <div className="p-4 bg-[var(--bg-secondary)] rounded-xl space-y-4 animate-slide-down flex flex-wrap gap-4 items-end">
                        <div className="space-y-2 min-w-[8rem]">
                          <label className="text-sm font-medium text-[var(--text-secondary)] block">Ограничение (кол-во постов)</label>
                          <Input
                            type="number"
                            min={0}
                            value={publishLimit}
                            onChange={(e) => setPublishLimit(e.target.value.replace(/\D/g, '').slice(0, 10))}
                            placeholder="Число"
                            className="w-full"
                          />
                        </div>
                        <div className="space-y-2 min-w-[10rem]">
                          <label className="text-sm font-medium text-[var(--text-secondary)] block">Интервал (минуты)</label>
                          <select
                            value={publishIntervalMinutes}
                            onChange={(e) => setPublishIntervalMinutes(Number(e.target.value))}
                            className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
                          >
                            {PUBLISH_INTERVAL_MINUTES_OPTIONS.map((m) => (
                              <option key={m} value={m}>{m} мин</option>
                            ))}
                          </select>
                        </div>
                      </div>
                    )}
                  </>
                )}

                {publishEnabled && (
                  <div className="p-4 bg-[var(--bg-secondary)] rounded-xl space-y-4 animate-slide-down">
                    <h3 className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                      </svg>
                      WordPress Connection
                    </h3>
                    
                    <Input
                      label="Site URL"
                      type="url"
                      value={siteUrl}
                      onChange={(e) => setSiteUrl(e.target.value)}
                      placeholder="https://example.com"
                    />
                    
                    <Input
                      label="Username"
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder="WordPress username"
                    />
                    
                    <Input
                      label="Application Password"
                      type="password"
                      value={appPassword}
                      onChange={(e) => setAppPassword(e.target.value)}
                      placeholder="Application password (not regular password)"
                    />
                    <p className="text-xs text-[var(--text-muted)]">
                      Generate an Application Password in WordPress: Users → Profile → Application Passwords
                    </p>

                    <div className="space-y-4 pt-4 border-t border-[var(--border-color)]">
                      <label className="text-sm font-medium text-[var(--text-secondary)] block">Publish Schedule</label>
                      <div className="space-y-3">
                        <label className="flex items-center gap-3 cursor-pointer">
                          <input
                            type="radio"
                            name="publishSchedule"
                            value="on_new_messages"
                            checked={publishScheduleType === 'on_new_messages'}
                            onChange={() => setPublishScheduleType('on_new_messages')}
                            className="w-4 h-4 text-primary-500"
                          />
                          <span className="text-[var(--text-primary)]">When new messages are checked</span>
                        </label>
                        <label className="flex items-center gap-3 cursor-pointer">
                          <input
                            type="radio"
                            name="publishSchedule"
                            value="by_intervals"
                            checked={publishScheduleType === 'by_intervals'}
                            onChange={() => setPublishScheduleType('by_intervals')}
                            className="w-4 h-4 text-primary-500"
                          />
                          <span className="text-[var(--text-primary)]">By time intervals</span>
                        </label>
                      </div>

                      {publishScheduleType === 'by_intervals' && (
                        <div className="space-y-3 mt-4 animate-slide-down flex flex-wrap gap-4 items-end">
                          <div className="space-y-2 min-w-[6rem]">
                            <label className="text-sm font-medium text-[var(--text-secondary)] block">Hour</label>
                            <select
                              value={publishScheduleHour}
                              onChange={(e) => setPublishScheduleHour(Number(e.target.value))}
                              className="w-full px-4 py-2.5 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                            >
                              {Array.from({ length: 24 }, (_, i) => (
                                <option key={i} value={i}>{String(i).padStart(2, '0')}</option>
                              ))}
                            </select>
                          </div>
                          <div className="space-y-2 min-w-[6rem]">
                            <label className="text-sm font-medium text-[var(--text-secondary)] block">Minutes</label>
                            <select
                              value={publishScheduleMinute}
                              onChange={(e) => setPublishScheduleMinute(Number(e.target.value) as ScheduleMinute)}
                              className="w-full px-4 py-2.5 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                            >
                              {SCHEDULE_MINUTES.map((m) => (
                                <option key={m} value={m}>{String(m).padStart(2, '0')}</option>
                              ))}
                            </select>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                </div>

                {/* Collection (Parser) */}
                <div className="space-y-4 pt-4 border-t border-[var(--border-color)]">
                  <h3 className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                    </svg>
                    Collection (Parser)
                  </h3>
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={collectEnabled}
                        onChange={(e) => setCollectEnabled(e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                    </div>
                    <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                      Enable collection
                    </span>
                  </label>

                  {collectEnabled && (
                    <>
                      <label className="flex items-center gap-3 cursor-pointer group">
                        <div className="relative">
                          <input
                            type="checkbox"
                            checked={collectAllAvailable}
                            onChange={(e) => setCollectAllAvailable(e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                          <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                        </div>
                        <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                          Собрать все доступное
                        </span>
                      </label>

                      {!collectAllAvailable && (
                        <div className="p-4 bg-[var(--bg-secondary)] rounded-xl space-y-2 animate-slide-down max-w-xs">
                          <label className="text-sm font-medium text-[var(--text-secondary)] block">Ограничение количества постов</label>
                          <Input
                            type="number"
                            min={1}
                            max={25}
                            value={collectLimit || '1'}
                            onChange={(e) => {
                              const v = e.target.value.replace(/\D/g, '').slice(0, 3)
                              if (v === '' || (parseInt(v, 10) >= 1 && parseInt(v, 10) <= 25)) setCollectLimit(v)
                            }}
                            placeholder="1"
                            className="w-full"
                          />
                          <p className="text-xs text-[var(--text-muted)]">От 1 до 25, по умолчанию 1</p>
                        </div>
                      )}
                    </>
                  )}

                  {collectEnabled && (
                    <div className="space-y-6 animate-slide-down">
                      <h4 className="text-sm font-semibold text-[var(--text-primary)]">Collection sites</h4>
                      {collectSites.map((site, index) => (
                        <div key={site.id} className="p-4 bg-[var(--bg-secondary)] rounded-xl space-y-4 border border-[var(--border-color)]">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-[var(--text-secondary)]">Site {index + 1}</span>
                            {collectSites.length > 1 && (
                              <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                onClick={() => removeCollectSite(site.id)}
                                className="text-red-400 hover:text-red-300"
                              >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                                Remove
                              </Button>
                            )}
                          </div>
                          <Input
                            label="Site URL"
                            type="url"
                            value={site.siteUrl}
                            onChange={(e) => updateCollectSiteUrl(site.id, e.target.value)}
                            placeholder="https://example.com"
                          />
                          <div className="space-y-4">
                            <label className="text-sm font-medium text-[var(--text-secondary)] block">Publish Schedule</label>
                            <div className="space-y-3">
                              <label className="flex items-center gap-3 cursor-pointer">
                                <input
                                  type="radio"
                                  name={`collectSchedule-${site.id}`}
                                  value="on_new_messages"
                                  checked={site.scheduleType === 'on_new_messages'}
                                  onChange={() => updateCollectSiteScheduleType(site.id, 'on_new_messages')}
                                  className="w-4 h-4 text-primary-500"
                                />
                                <span className="text-[var(--text-primary)]">When new messages are checked</span>
                              </label>
                              <label className="flex items-center gap-3 cursor-pointer">
                                <input
                                  type="radio"
                                  name={`collectSchedule-${site.id}`}
                                  value="by_intervals"
                                  checked={site.scheduleType === 'by_intervals'}
                                  onChange={() => updateCollectSiteScheduleType(site.id, 'by_intervals')}
                                  className="w-4 h-4 text-primary-500"
                                />
                                <span className="text-[var(--text-primary)]">By time intervals</span>
                              </label>
                            </div>
                            {site.scheduleType === 'by_intervals' && (
                              <div className="space-y-3 mt-4 flex flex-wrap gap-4 items-end">
                                <div className="space-y-2 min-w-[6rem]">
                                  <label className="text-sm font-medium text-[var(--text-secondary)] block">Hour</label>
                                  <select
                                    value={site.scheduleHour}
                                    onChange={(e) => updateCollectSiteScheduleTime(site.id, Number(e.target.value))}
                                    className="w-full px-4 py-2.5 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                                  >
                                    {Array.from({ length: 24 }, (_, i) => (
                                      <option key={i} value={i}>{String(i).padStart(2, '0')}</option>
                                    ))}
                                  </select>
                                </div>
                                <div className="space-y-2 min-w-[6rem]">
                                  <label className="text-sm font-medium text-[var(--text-secondary)] block">Minutes</label>
                                  <select
                                    value={site.scheduleMinute}
                                    onChange={(e) => updateCollectSiteScheduleTime(site.id, undefined, Number(e.target.value) as ScheduleMinute)}
                                    className="w-full px-4 py-2.5 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                                  >
                                    {SCHEDULE_MINUTES.map((m) => (
                                      <option key={m} value={m}>{String(m).padStart(2, '0')}</option>
                                    ))}
                                  </select>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                      {collectSites.length < 5 && (
                        <Button type="button" variant="secondary" size="sm" onClick={addCollectSite}>
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                          </svg>
                          Add collection site
                        </Button>
                      )}
                    </div>
                  )}
                </div>

                <CardFooter className="px-0">
                  <Button type="submit" isLoading={isSavingProfile} className="w-full sm:w-auto">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Save Profile Settings
                  </Button>
                </CardFooter>
              </form>
            )}
          </CardContent>
        </Card>
      )}

      {/* Обработка — настройки обработки перед публикацией */}
      {activeTab === 'processing' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Обработка
            </CardTitle>
            <CardDescription>Настройки обработки постов перед публикацией</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingProfile ? (
              <div className="text-center py-8 text-[var(--text-muted)]">Loading profile...</div>
            ) : (
              <form onSubmit={handleSavePostProfile} className="space-y-6">
                <label className="flex items-center gap-3 cursor-pointer group">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={processBeforePublish}
                      onChange={(e) => setProcessBeforePublish(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                    <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                  </div>
                  <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                    Обрабатывать перед публикацией
                  </span>
                </label>

                {processBeforePublish && (
                  <div className="space-y-2 animate-slide-down">
                    <label className="text-sm font-medium text-[var(--text-secondary)] block">
                      Описание обработки
                    </label>
                    <textarea
                      value={processDescription}
                      onChange={(e) => setProcessDescription(e.target.value)}
                      rows={4}
                      className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
                      placeholder="Опишите, как должны обрабатываться посты перед публикацией..."
                    />
                  </div>
                )}

                <label className="flex items-center gap-3 cursor-pointer group">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={removeEmojis}
                      onChange={(e) => setRemoveEmojis(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                    <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                  </div>
                  <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                    Удалить смайлики/эмодзи
                  </span>
                </label>

                <label className="flex items-center gap-3 cursor-pointer group">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={removeImages}
                      onChange={(e) => setRemoveImages(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                    <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                  </div>
                  <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                    Удалить картинки
                  </span>
                </label>

                <label className="flex items-center gap-3 cursor-pointer group">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={cleanHtml}
                      onChange={(e) => setCleanHtml(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                    <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                  </div>
                  <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                    Очистить HTML
                  </span>
                </label>

                <div className="space-y-3">
                  <span className="text-sm font-medium text-[var(--text-secondary)] block">Для каких сервисов подготовить обработку</span>
                  <div className="flex flex-wrap gap-4">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={processServiceWordpress}
                        onChange={(e) => setProcessServiceWordpress(e.target.checked)}
                        className="w-4 h-4 text-primary-500 rounded"
                      />
                      <span className="text-[var(--text-primary)]">WordPress</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={processServiceTelegram}
                        onChange={(e) => setProcessServiceTelegram(e.target.checked)}
                        className="w-4 h-4 text-primary-500 rounded"
                      />
                      <span className="text-[var(--text-primary)]">Telegram</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={processServiceTwitter}
                        onChange={(e) => setProcessServiceTwitter(e.target.checked)}
                        className="w-4 h-4 text-primary-500 rounded"
                      />
                      <span className="text-[var(--text-primary)]">Twitter</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={processServiceVkontakte}
                        onChange={(e) => setProcessServiceVkontakte(e.target.checked)}
                        className="w-4 h-4 text-primary-500 rounded"
                      />
                      <span className="text-[var(--text-primary)]">VKontakte</span>
                    </label>
                  </div>
                </div>

                <label className="flex items-center gap-3 cursor-pointer group">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={statusReviewAfterProcess}
                      onChange={(e) => setStatusReviewAfterProcess(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                    <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                  </div>
                  <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                    Перевести пост в статус review после обработки
                  </span>
                </label>

                <label className="flex items-center gap-3 cursor-pointer group">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={addStaticHtml}
                      onChange={(e) => setAddStaticHtml(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                    <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                  </div>
                  <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                    Добавлять в посты статичный HTML
                  </span>
                </label>

                {addStaticHtml && (
                  <div className="space-y-2 animate-slide-down">
                    <label className="text-sm font-medium text-[var(--text-secondary)] block">
                      Статичный HTML (до 1000 символов)
                    </label>
                    <textarea
                      value={staticHtmlContent}
                      onChange={(e) => setStaticHtmlContent(e.target.value.slice(0, 1000))}
                      rows={4}
                      maxLength={1000}
                      className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
                      placeholder="Введите статичный HTML для добавления в посты..."
                    />
                    <p className="text-xs text-[var(--text-muted)]">{staticHtmlContent.length} / 1000</p>
                  </div>
                )}

                <CardFooter className="px-0">
                  <Button type="submit" isLoading={isSavingProfile} className="w-full sm:w-auto">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Сохранить настройки обработки
                  </Button>
                </CardFooter>
              </form>
            )}
          </CardContent>
        </Card>
      )}

    </PageContainer>
  )
}
