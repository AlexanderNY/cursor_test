import { apiClient } from './api-client'

export interface GuideBlockStyle {
  titleColor?: string
  subtitleColor?: string
  textColor?: string
  backgroundColor?: string
  borderColor?: string
  borderRadius?: string
  padding?: string
  titleFontSize?: string
  bodyFontSize?: string
  titleFontWeight?: string
}

export interface GuideBlock {
  id: number
  slug: string
  toc_label: string
  title: string
  subtitle: string
  body: string
  sort_order: number
  is_visible: boolean
  style: GuideBlockStyle
}

export const guideService = {
  async listPublic(): Promise<GuideBlock[]> {
    const { data } = await apiClient.get<{ blocks: GuideBlock[] }>('/core/guide/blocks')
    return data.blocks ?? []
  },

  async listAdmin(): Promise<GuideBlock[]> {
    const { data } = await apiClient.get<{ blocks: GuideBlock[] }>('/core/guide/blocks/admin')
    return data.blocks ?? []
  },

  async create(payload: Partial<GuideBlock> & { slug: string }): Promise<GuideBlock> {
    const { data } = await apiClient.post<GuideBlock>('/core/guide/blocks', payload)
    return data
  },

  async update(id: number, payload: Partial<GuideBlock>): Promise<GuideBlock> {
    const { data } = await apiClient.patch<GuideBlock>(`/core/guide/blocks/${id}`, payload)
    return data
  },

  async remove(id: number): Promise<void> {
    await apiClient.delete(`/core/guide/blocks/${id}`)
  },

  async seed(): Promise<GuideBlock[]> {
    const { data } = await apiClient.post<{ blocks: GuideBlock[] }>('/core/guide/blocks/seed')
    return data.blocks ?? []
  },
}
