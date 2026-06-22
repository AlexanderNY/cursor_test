import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import Underline from '@tiptap/extension-underline'
import { useEffect } from 'react'
import { Button } from './button'

interface TipTapEditorProps {
  content: string
  onChange: (content: string) => void
  placeholder?: string
  editable?: boolean
  className?: string
  toolbarButtons?: Array<'bold' | 'italic' | 'underline' | 'strike' | 'heading' | 'bulletList' | 'orderedList' | 'blockquote' | 'code' | 'codeBlock' | 'horizontalRule' | 'undo' | 'redo'>
}

export function TipTapEditor({
  content,
  onChange,
  placeholder = 'Enter your content...',
  editable = true,
  className = '',
  toolbarButtons = ['bold', 'italic', 'underline', 'strike', 'heading', 'bulletList', 'orderedList', 'blockquote', 'code', 'undo', 'redo']
}: TipTapEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: {
          levels: [1, 2, 3],
        },
      }),
      Underline,
      Placeholder.configure({
        placeholder,
      }),
    ],
    content,
    editable,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML())
    },
    editorProps: {
      attributes: {
        class: 'prose prose-sm sm:prose lg:prose-lg xl:prose-2xl mx-auto focus:outline-none min-h-[200px] max-w-none',
      },
    },
  })

  // Sync content when it changes externally
  useEffect(() => {
    if (editor && content !== editor.getHTML()) {
      editor.commands.setContent(content, false)
    }
  }, [content, editor])

  if (!editor) {
    return null
  }

  const isActive = (name: string, options?: any) => {
    return editor.isActive(name, options)
  }

  const toggleHeading = (level: 1 | 2 | 3) => {
    editor.chain().focus().toggleHeading({ level }).run()
  }

  return (
    <div className={`tiptap-editor ${className}`}>
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2 p-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-t-xl border-b-0">
        {toolbarButtons.includes('bold') && (
          <Button
            type="button"
            variant={isActive('bold') ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => editor.chain().focus().toggleBold().run()}
            disabled={!editor.can().chain().focus().toggleBold().run()}
            className="font-bold"
          >
            B
          </Button>
        )}

        {toolbarButtons.includes('italic') && (
          <Button
            type="button"
            variant={isActive('italic') ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => editor.chain().focus().toggleItalic().run()}
            disabled={!editor.can().chain().focus().toggleItalic().run()}
            className="italic"
          >
            I
          </Button>
        )}

        {toolbarButtons.includes('underline') && (
          <Button
            type="button"
            variant={isActive('underline') ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => editor.chain().focus().toggleUnderline().run()}
            className="underline"
          >
            U
          </Button>
        )}

        {toolbarButtons.includes('strike') && (
          <Button
            type="button"
            variant={isActive('strike') ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => editor.chain().focus().toggleStrike().run()}
            disabled={!editor.can().chain().focus().toggleStrike().run()}
            className="line-through"
          >
            S
          </Button>
        )}

        {toolbarButtons.includes('heading') && (
          <>
            <div className="w-px h-6 bg-[var(--border-color)] mx-1" />
            <Button
              type="button"
              variant={isActive('heading', { level: 1 }) ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => toggleHeading(1)}
            >
              H1
            </Button>
            <Button
              type="button"
              variant={isActive('heading', { level: 2 }) ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => toggleHeading(2)}
            >
              H2
            </Button>
            <Button
              type="button"
              variant={isActive('heading', { level: 3 }) ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => toggleHeading(3)}
            >
              H3
            </Button>
          </>
        )}

        {toolbarButtons.includes('bulletList') && (
          <>
            <div className="w-px h-6 bg-[var(--border-color)] mx-1" />
            <Button
              type="button"
              variant={isActive('bulletList') ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => editor.chain().focus().toggleBulletList().run()}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </Button>
          </>
        )}

        {toolbarButtons.includes('orderedList') && (
          <Button
            type="button"
            variant={isActive('orderedList') ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => editor.chain().focus().toggleOrderedList().run()}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
            </svg>
          </Button>
        )}

        {toolbarButtons.includes('blockquote') && (
          <>
            <div className="w-px h-6 bg-[var(--border-color)] mx-1" />
            <Button
              type="button"
              variant={isActive('blockquote') ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => editor.chain().focus().toggleBlockquote().run()}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </Button>
          </>
        )}

        {toolbarButtons.includes('code') && (
          <Button
            type="button"
            variant={isActive('code') ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => editor.chain().focus().toggleCode().run()}
            disabled={!editor.can().chain().focus().toggleCode().run()}
            className="font-mono text-xs"
          >
            {'</>'}
          </Button>
        )}

        {toolbarButtons.includes('codeBlock') && (
          <Button
            type="button"
            variant={isActive('codeBlock') ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => editor.chain().focus().toggleCodeBlock().run()}
            className="font-mono text-xs"
          >
            {'{ }'}
          </Button>
        )}

        {toolbarButtons.includes('horizontalRule') && (
          <>
            <div className="w-px h-6 bg-[var(--border-color)] mx-1" />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => editor.chain().focus().setHorizontalRule().run()}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
              </svg>
            </Button>
          </>
        )}

        {toolbarButtons.includes('undo') && (
          <>
            <div className="w-px h-6 bg-[var(--border-color)] mx-1" />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => editor.chain().focus().undo().run()}
              disabled={!editor.can().chain().focus().undo().run()}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
              </svg>
            </Button>
          </>
        )}

        {toolbarButtons.includes('redo') && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => editor.chain().focus().redo().run()}
            disabled={!editor.can().chain().focus().redo().run()}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 10h-10a8 8 0 00-8 8v2M21 10l-6 6m6-6l-6-6" />
            </svg>
          </Button>
        )}
      </div>

      {/* Editor Content */}
      <div className="border border-[var(--border-color)] rounded-b-xl bg-[var(--bg-tertiary)] focus-within:ring-2 focus-within:ring-primary-500/50 focus-within:border-primary-500 transition-all">
        <EditorContent
          editor={editor}
          className="px-4 py-3 min-h-[200px] max-h-[600px] overflow-y-auto text-[var(--text-primary)]"
        />
      </div>
    </div>
  )
}
