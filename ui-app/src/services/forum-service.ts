import { apiClient } from './api-client'
import type {
  ForumKind,
  ForumListResponse,
  ForumPost,
  ForumScope,
  ForumStatus,
  ForumThreadCreate,
  ForumThreadDetail,
  ForumVoteResponse,
} from '@/types/core'

export const forumService = {
  async listThreads(params: {
    scope: ForumScope
    kind?: ForumKind
    q?: string
  }): Promise<ForumListResponse> {
    const response = await apiClient.get<ForumListResponse>('/core/forum/threads', { params })
    return response.data
  },

  async unreadCount(): Promise<number> {
    const response = await apiClient.get<{ count: number }>('/core/forum/unread')
    return response.data.count ?? 0
  },

  async getThread(threadId: number): Promise<ForumThreadDetail> {
    const response = await apiClient.get<ForumThreadDetail>(`/core/forum/threads/${threadId}`)
    return response.data
  },

  async createThread(data: ForumThreadCreate): Promise<ForumThreadDetail> {
    const response = await apiClient.post<ForumThreadDetail>('/core/forum/threads', data)
    return response.data
  },

  async addPost(threadId: number, body: string, quotePostId?: number): Promise<ForumPost> {
    const response = await apiClient.post<ForumPost>(`/core/forum/threads/${threadId}/posts`, {
      body,
      ...(quotePostId ? { quote_post_id: quotePostId } : {}),
    })
    return response.data
  },

  async editPost(postId: number, body: string): Promise<ForumPost> {
    const response = await apiClient.patch<ForumPost>(`/core/forum/posts/${postId}`, { body })
    return response.data
  },

  async updateThread(
    threadId: number,
    patch: { is_closed?: boolean; status?: ForumStatus; is_pinned?: boolean },
  ): Promise<ForumThreadDetail> {
    const response = await apiClient.patch<ForumThreadDetail>(`/core/forum/threads/${threadId}`, patch)
    return response.data
  },

  async uploadAttachment(threadId: number, file: File): Promise<ForumThreadDetail> {
    const body = new FormData()
    body.append('file', file)
    const response = await apiClient.post<ForumThreadDetail>(
      `/core/forum/threads/${threadId}/attachment`,
      body,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
    return response.data
  },

  async setClosed(threadId: number, isClosed: boolean): Promise<ForumThreadDetail> {
    return this.updateThread(threadId, { is_closed: isClosed })
  },

  async deleteThread(threadId: number): Promise<void> {
    await apiClient.delete(`/core/forum/threads/${threadId}`)
  },

  async deletePost(postId: number): Promise<void> {
    await apiClient.delete(`/core/forum/posts/${postId}`)
  },

  async uploadAvatar(file: File): Promise<{ avatar_url: string }> {
    const body = new FormData()
    body.append('file', file)
    const response = await apiClient.post<{ avatar_url: string }>('/core/forum/avatar', body, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  async deleteAvatar(): Promise<void> {
    await apiClient.delete('/core/forum/avatar')
  },

  async toggleVote(threadId: number): Promise<ForumVoteResponse> {
    const response = await apiClient.post<ForumVoteResponse>(`/core/forum/threads/${threadId}/vote`)
    return response.data
  },
}
