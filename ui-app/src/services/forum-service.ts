import { apiClient } from './api-client'
import type {
  ForumKind,
  ForumListResponse,
  ForumPost,
  ForumScope,
  ForumThreadCreate,
  ForumThreadDetail,
  ForumVoteResponse,
} from '@/types/core'

export const forumService = {
  async listThreads(params: { scope: ForumScope; kind?: ForumKind }): Promise<ForumListResponse> {
    const response = await apiClient.get<ForumListResponse>('/core/forum/threads', { params })
    return response.data
  },

  async getThread(threadId: number): Promise<ForumThreadDetail> {
    const response = await apiClient.get<ForumThreadDetail>(`/core/forum/threads/${threadId}`)
    return response.data
  },

  async createThread(data: ForumThreadCreate): Promise<ForumThreadDetail> {
    const response = await apiClient.post<ForumThreadDetail>('/core/forum/threads', data)
    return response.data
  },

  async addPost(threadId: number, body: string): Promise<ForumPost> {
    const response = await apiClient.post<ForumPost>(`/core/forum/threads/${threadId}/posts`, { body })
    return response.data
  },

  async setClosed(threadId: number, isClosed: boolean): Promise<ForumThreadDetail> {
    const response = await apiClient.patch<ForumThreadDetail>(`/core/forum/threads/${threadId}`, {
      is_closed: isClosed,
    })
    return response.data
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

  async toggleVote(threadId: number): Promise<ForumVoteResponse> {
    const response = await apiClient.post<ForumVoteResponse>(`/core/forum/threads/${threadId}/vote`)
    return response.data
  },
}
