import type { Components } from 'react-markdown'
import ReactMarkdown from 'react-markdown'
import { Link } from 'react-router-dom'
import remarkGfm from 'remark-gfm'

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
    if (href && isInternalPath(href)) {
      return <Link to={href}>{children}</Link>
    }
    const isExternal = Boolean(href?.startsWith('http'))
    return (
      <a
        href={href}
        target={isExternal ? '_blank' : undefined}
        rel={isExternal ? 'noreferrer' : undefined}
      >
        {children}
      </a>
    )
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
