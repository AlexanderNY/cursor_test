import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { SkeletonCard } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/ui'
import type { TelegramPostListItem } from '@/types/telegram'
import { formatDateTime } from '@/utils/date'

export interface PostsTabProps {
  posts: TelegramPostListItem[]
  isLoadingPosts: boolean
  hasLoadedPosts: boolean
  deletingPostId: number | null
  approvingPostId: number | null
  deletingPublishedId: number | null
  onRefresh: () => void
  onEdit: (postId: number) => void
  onDelete: (postId: number) => void
  onApprove: (postId: number) => void
  onDeletePublished: (postId: number) => void
}

function formatScheduled(publishAt?: string | null): string | null {
  if (!publishAt) return null
  return `Scheduled ${formatDateTime(publishAt)}`
}

export function PostsTab({
  posts,
  isLoadingPosts,
  hasLoadedPosts,
  deletingPostId,
  approvingPostId,
  deletingPublishedId,
  onRefresh,
  onEdit,
  onDelete,
  onApprove,
  onDeletePublished,
}: PostsTabProps) {
  return (
    <Card className="animate-slide-up">
      <CardHeader className="flex flex-row items-center justify-between gap-2">
        <div>
          <CardTitle className="flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h10" />
            </svg>
            Posts
          </CardTitle>
          <CardDescription>All posts from your Telegram account</CardDescription>
        </div>
        <Button type="button" variant="secondary" size="sm" onClick={onRefresh} isLoading={isLoadingPosts}>
          Refresh
        </Button>
      </CardHeader>
      <CardContent>
        {isLoadingPosts && posts.length === 0 && (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        )}

        {!isLoadingPosts && posts.length === 0 && hasLoadedPosts && (
          <EmptyState title="No posts found" description="No posts found for this account." />
        )}

        {!isLoadingPosts && posts.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border-color)] text-left text-[var(--text-secondary)]">
                  <th className="py-2 pr-4 font-medium">Text</th>
                  <th className="py-2 pr-4 font-medium">Status</th>
                  <th className="py-2 pr-4 font-medium">Created</th>
                  <th className="py-2 pr-4 font-medium w-32 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {posts.map((post, index) => {
                  const scheduled = formatScheduled(post.publish_at)
                  return (
                    <tr key={post.id ?? index} className="border-b border-[var(--border-color)] last:border-0">
                      <td className="py-2 pr-4 text-[var(--text-primary)]">
                        <div className="max-w-md truncate">{post.post_text}</div>
                        {scheduled && (
                          <div className="text-xs text-primary-400 mt-0.5">{scheduled}</div>
                        )}
                      </td>
                      <td className="py-2 pr-4">
                        <span className="inline-flex items-center rounded-full bg-[var(--bg-secondary)] px-2 py-0.5 text-xs font-medium text-[var(--text-secondary)]">
                          {post.status}
                        </span>
                      </td>
                      <td className="py-2 pr-4 text-[var(--text-secondary)]">
                        {formatDateTime(post.created_at)}
                      </td>
                      <td className="py-2 pr-4 text-right">
                        <div className="flex items-center justify-end gap-1 flex-wrap">
                          {post.status === 'review' && post.id != null && (
                            <Button
                              type="button"
                              variant="secondary"
                              size="sm"
                              onClick={() => onApprove(post.id)}
                              isLoading={approvingPostId === post.id}
                              disabled={approvingPostId === post.id}
                            >
                              Approve
                            </Button>
                          )}
                          {post.status === 'published' && post.telegram_message_id != null && post.id != null && (
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              onClick={() => onDeletePublished(post.id)}
                              isLoading={deletingPublishedId === post.id}
                              disabled={deletingPublishedId === post.id}
                              className="text-red-400 hover:text-red-300"
                            >
                              Delete from TG
                            </Button>
                          )}
                          <button
                            type="button"
                            onClick={() => post.id != null && onEdit(post.id)}
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
                            onClick={() => post.id != null && onDelete(post.id)}
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
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
