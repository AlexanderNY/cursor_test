import type { Components } from 'react-markdown'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface MarkdownBodyProps {
  content: string
}

const components: Components = {
  a: ({ href, children }) => {
    const isExternal = Boolean(href?.startsWith('http'))
    return (
      <a href={href} target={isExternal ? '_blank' : undefined} rel={isExternal ? 'noreferrer' : undefined}>
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
