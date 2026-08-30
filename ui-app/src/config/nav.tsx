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
  CreditCardIcon,
} from '@/components/icons'

export interface NavItem {
  path: string
  label: string
  Icon: ComponentType<{ className?: string }>
}

/** Top header links (not in sidebar) */
export const topNavItems: NavItem[] = [
  { path: '/profile', label: 'Profile', Icon: UserIcon },
  { path: '/pricing', label: 'Pricing', Icon: CreditCardIcon },
  { path: '/about', label: 'Справка', Icon: DocumentTextIcon },
]

export const navItems: NavItem[] = [
  { path: '/brands', label: 'Brands', Icon: UsersIcon },
  { path: '/channels', label: 'Channels', Icon: LinkIcon },
  { path: '/inbox', label: 'Inbox', Icon: DocumentTextIcon },
  { path: '/posts', label: 'Posts', Icon: PlusIcon },
  { path: '/library', label: 'Library', Icon: DocumentTextIcon },
  { path: '/calendar', label: 'Calendar', Icon: CheckCircleIcon },
  { path: '/analytics', label: 'Analytics', Icon: ChartBarIcon },
  { path: '/competitors', label: 'Competitors', Icon: UsersIcon },
  { path: '/automations', label: 'Automations', Icon: SettingsIcon },
]

/** Advanced / legacy platform silos — secondary in sidebar */
export const platformNavItems: NavItem[] = [
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
