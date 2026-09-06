/** CSV template + column hints for SMM posts import on /posts. */

export const CSV_POSTS_COLUMNS = [
  {
    key: 'text',
    required: true,
    aliases: 'post_text, content, текст',
    description: 'Текст поста',
  },
  {
    key: 'publish_at',
    required: false,
    aliases: 'scheduled_at, planned_date, planned_publication, дата_публикации',
    description: 'Планируемая дата (UTC): ISO или ДД.ММ.ГГГГ [ЧЧ:ММ]',
  },
  {
    key: 'network',
    required: false,
    aliases: 'сеть',
    description: 'Площадка: tg или vk (нужна вместе с channel при approval)',
  },
  {
    key: 'channel',
    required: false,
    aliases: 'external_id, канал',
    description: 'ID канала/группы для публикации',
  },
  {
    key: 'assigned_to',
    required: false,
    aliases: 'assignee',
    description: 'Опционально: user id для review',
  },
] as const

export const CSV_POSTS_EXAMPLE = [
  'text,publish_at,network,channel',
  '"Первый пост сезона",2026-09-10T10:00:00Z,tg,-1001234567890',
  '"Второй пост",10.09.2026 18:00,tg,-1001234567890',
  '"Черновик без канала",2026-09-12T12:00:00Z,,',
].join('\n')

export function downloadPostsCsvTemplate(filename = 'posts-import-template.csv'): void {
  const blob = new Blob([`\uFEFF${CSV_POSTS_EXAMPLE}\n`], {
    type: 'text/csv;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}
