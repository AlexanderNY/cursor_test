import type { Components } from 'react-markdown'
import ReactMarkdown from 'react-markdown'
import { Link } from 'react-router-dom'
import remarkGfm from 'remark-gfm'
import { safeHref } from '@/data/safe-url'

interface MarkdownBodyProps {
  content: string
}

function isInternalPath(href: string | undefined): boolean {
  if (!href) {
    return false
  }
  return href.startsWith('/') && !href.startsWith('//')
}

const components: Components = {
  a: ({ href, children }) => {
    const safe = safeHref(href)
    if (safe && isInternalPath(safe)) {
      return <Link to={safe}>{children}</Link>
    }
    if (safe && (safe.startsWith('http://') || safe.startsWith('https://'))) {
      return (
        <a href={safe} target="_blank" rel="noreferrer">
          {children}
        </a>
      )
    }
    return <span>{children}</span>
  },
}

export function MarkdownBody({ content }: MarkdownBodyProps) {
  return (
    <div className="learn-markdown">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  )
}
