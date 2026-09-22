import { MarkdownBody } from '@/components/learn-markdown'
import type { LearnContentFormat } from '@/data/learn/learn-store'
import { sanitizeLearnHtml } from '@/data/learn/sanitize-html'

interface LearnContentProps {
  content: string
  format: LearnContentFormat
}

export function LearnContent({ content, format }: LearnContentProps) {
  if (format === 'html') {
    return (
      <div
        className="learn-markdown"
        dangerouslySetInnerHTML={{ __html: sanitizeLearnHtml(content) }}
      />
    )
  }

  return <MarkdownBody content={content} />
}
