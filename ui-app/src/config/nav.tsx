import type { ComponentType } from 'react'
import {
  UserIcon,
  TelegramIcon,
  ThreadsIcon,
  WordPressIcon,
  TwitterIcon,
  VKontakteIcon,
  InstagramIcon,
  LinkIcon,
  PlusIcon,
  SettingsIcon,
  UserGroupIcon,
  DocumentTextIcon,
  PollIcon,
  CheckCircleIcon,
  ChartBarIcon,
  UsersIcon,
} from '@/components/icons'

export interface NavItem {
  path: string
  label: string
  Icon: ComponentType<{ className?: string }>
}

export const navItems: NavItem[] = [
  { path: '/profile', label: 'Profile', Icon: UserIcon },
  { path: '/brands', label: 'Brands', Icon: UsersIcon },
  { path: '/inbox', label: 'Inbox', Icon: DocumentTextIcon },
  { path: '/posts', label: 'Posts', Icon: PlusIcon },
  { path: '/calendar', label: 'Calendar', Icon: CheckCircleIcon },
  { path: '/analytics', label: 'Analytics', Icon: ChartBarIcon },
  { path: '/automations', label: 'Automations', Icon: SettingsIcon },
  { path: '/telegram', label: 'Telegram', Icon: TelegramIcon },
  { path: '/vkontakte', label: 'VKontakte', Icon: VKontakteIcon },
  { path: '/instagram', label: 'Instagram', Icon: InstagramIcon },
  { path: '/threads', label: 'Threads', Icon: ThreadsIcon },
  { path: '/wordpress', label: 'WordPress', Icon: WordPressIcon },
  { path: '/dzen', label: 'Дзен', Icon: DocumentTextIcon },
  { path: '/twitter', label: 'Twitter', Icon: TwitterIcon },
  { path: '/custom-url', label: 'Custom URL', Icon: LinkIcon },
]

export const groupNavItem: NavItem = {
  path: '/team',
  label: 'Team',
  Icon: UserGroupIcon,
}

export const adminNavItems: NavItem[] = [
  { path: '/administration', label: 'Administration', Icon: SettingsIcon },
  { path: '/polls', label: 'Polls', Icon: PollIcon },
  { path: '/checks', label: 'Checks', Icon: CheckCircleIcon },
]
