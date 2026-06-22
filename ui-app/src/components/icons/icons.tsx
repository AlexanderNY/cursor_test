import type { SVGProps } from 'react'

const defaultSize = 20

interface IconProps extends SVGProps<SVGSVGElement> {
  size?: number
}

export function UserIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
    </svg>
  )
}

export function CreditCardIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
    </svg>
  )
}

export function ChartBarIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  )
}

export function TelegramIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
    </svg>
  )
}

export function ThreadsIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M7 8h10M7 12h4m5 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
    </svg>
  )
}

export function WordPressIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M21.469 6.825c.84 1.537 1.318 3.3 1.318 5.175 0 3.979-2.156 7.456-5.363 9.325l3.295-9.527c.615-1.54.82-2.771.82-3.864 0-.405-.026-.78-.07-1.11m-7.981.105c.647-.034 1.232-.1 1.232-.1.582-.075.514-.93-.067-.899 0 0-1.755.138-2.885.138-1.063 0-2.855-.138-2.855-.138-.581-.031-.649.857-.068.899 0 0 .548.066 1.13.1l1.681 4.605-2.36 7.076-3.929-11.68c.65-.034 1.234-.1 1.234-.1.581-.075.514-.93-.068-.899 0 0-1.754.138-2.885.138-.202 0-.44-.006-.692-.014C5.644 3.404 8.577 1.214 12 1.214c2.55 0 4.87.975 6.607 2.57-.042-.003-.084-.007-.127-.007-.961 0-1.644.842-1.644 1.745 0 .811.467 1.497.967 2.308.374.65.811 1.482.811 2.687 0 .834-.32 1.8-.748 3.146l-.98 3.275-3.55-10.567zm-4.39 16.307c-1.354-.46-2.576-1.17-3.615-2.078l3.042-8.828 3.115 8.533c.02.05.046.095.072.138-1.32.56-2.77.87-4.287.87-.442 0-.877-.028-1.305-.082m-1.885-.906C4.001 20.054 1.214 16.303 1.214 12c0-1.628.367-3.17 1.022-4.547l5.627 15.418c.03.082.063.162.099.24-.015-.005-.03-.01-.045-.016l-.003-.001z" />
    </svg>
  )
}

export function TwitterIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  )
}

export function VKontakteIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M15.684 0H8.316C1.592 0 0 1.592 0 8.316v7.368C0 22.408 1.592 24 8.316 24h7.368C22.408 24 24 22.408 24 15.684V8.316C24 1.592 22.408 0 15.684 0zm3.692 17.123h-1.744c-.66 0-.864-.525-2.05-1.727-1.033-1-1.49-1.135-1.744-1.135-.356 0-.458.102-.458.593v1.575c0 .424-.135.678-1.253.678-1.846 0-3.896-1.12-5.335-3.202-2.168-3.03-2.763-5.302-2.763-5.775 0-.254.102-.491.593-.491h1.744c.44 0 .61.203.78.678.864 2.49 2.303 4.675 2.896 4.675.22 0 .322-.102.322-.66V9.721c-.068-1.186-.695-1.287-.695-1.71 0-.203.17-.407.44-.407h2.744c.373 0 .508.203.508.643v3.473c0 .372.17.508.271.508.22 0 .407-.136.813-.542 1.254-1.406 2.151-3.574 2.151-3.574.119-.254.322-.491.763-.491h1.744c.525 0 .644.27.525.643-.22 1.017-2.354 4.031-2.354 4.031-.186.305-.254.44 0 .78.186.254.796.779 1.203 1.253.745.847 1.32 1.558 1.473 2.05.17.49-.085.744-.576.744z" />
    </svg>
  )
}

export function LinkIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
    </svg>
  )
}

export function PlusIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
    </svg>
  )
}

export function SettingsIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  )
}

export function UsersIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>
  )
}

export function RefreshIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  )
}

export function ChevronLeftIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
    </svg>
  )
}

export function ChevronRightIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
    </svg>
  )
}

export function SunIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
    </svg>
  )
}

export function MoonIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
    </svg>
  )
}

export function LogOutIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
    </svg>
  )
}

export function CloseIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  )
}

export function MenuIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  )
}

export function CheckIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  )
}

export function XCircleIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
}

export function DocumentTextIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  )
}

export function UserGroupIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>
  )
}

export function CheckCircleIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
}

export function ExclamationIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  )
}

export function InstagramIcon({ className, size = defaultSize, ...props }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className ?? `h-5 w-5`} width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  )
}
