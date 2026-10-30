import { avatarPublicSrc } from '@/utils/avatar'

export function UserFace({
  name,
  avatar,
  className = 'h-7 w-7 text-[10px]',
}: {
  name: string
  avatar?: string | null
  className?: string
}) {
  const src = avatarPublicSrc(avatar)
  const initial = (name || '?').slice(0, 1).toUpperCase()
  if (src) {
    return (
      <img
        src={src}
        alt=""
        className={`${className} rounded-full object-cover shrink-0 bg-[var(--bg-tertiary)]`}
      />
    )
  }
  return (
    <span
      className={`${className} rounded-full shrink-0 inline-flex items-center justify-center bg-gradient-to-br from-primary-500 to-accent-500 font-semibold text-white`}
      aria-hidden
    >
      {initial}
    </span>
  )
}
