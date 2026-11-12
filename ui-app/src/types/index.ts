export * from './auth'
export * from './telegram'
export * from './core'

// Platform modules repeat TimeInterval / schedule unions. export * cannot
// re-export those names twice, so each later module lists its own types and
// aliases the collisions. The un-aliased names stay the first module's
// (telegram TimeInterval and PublishScheduleType, vkontakte ScheduleType).
export type {
  PostStatus,
  WordPressCollectProfile,
  WordPressCollectSiteItem,
  WordPressPost,
  WordPressPostFull,
  WordPressPostListItem,
  WordPressProfile,
  WordPressPublishProfile,
} from './wordpress'
export type {
  PublishScheduleType as WordPressPublishScheduleType,
  TimeInterval as WordPressTimeInterval,
} from './wordpress'

export type {
  TwPostRow,
  TwitterFollowingResponse,
  TwitterFollowingUser,
  TwitterOAuthStatus,
  TwitterPost,
  TwitterProfile,
  TwitterScheduleType,
  TwitterSeleniumVerifyResponse,
} from './twitter'
export type { TimeInterval as TwitterTimeInterval } from './twitter'

export type {
  ScheduleType,
  VKAuthStatus,
  VKAuthVerifyResult,
  VKSeleniumVerifyResponse,
  VKSubscriptionItem,
  VKSubscriptionsResult,
  VKontakteAttachmentItem,
  VKontaktePost,
  VKontaktePostFull,
  VKontaktePostListItem,
  VKontakteProfile,
  VKontakteTab,
} from './vkontakte'
export type { TimeInterval as VKontakteTimeInterval } from './vkontakte'

export type {
  DzenCollectSource,
  DzenPendingDiagResponse,
  DzenPost,
  DzenPostFull,
  DzenPostListItem,
  DzenProfile,
  DzenSubscriptionItem,
  DzenVerifyResponse,
} from './dzen'
export type {
  ScheduleType as DzenScheduleType,
  TimeInterval as DzenTimeInterval,
} from './dzen'

export type {
  InstagramFollowingUser,
  InstagramPost,
  InstagramPostFull,
  InstagramPostListItem,
  InstagramProfile,
} from './instagram'
export type {
  ScheduleType as InstagramScheduleType,
  TimeInterval as InstagramTimeInterval,
} from './instagram'

export * from './custom-url'
export * from './create-post'

export type {
  ThreadsAuthStatus,
  ThreadsAuthVerify,
  ThreadsConfig,
  ThreadsGraphPermission,
  ThreadsPostFull,
  ThreadsPostListItem,
  ThreadsSeleniumAttemptResult,
  ThreadsSeleniumSessionRow,
} from './threads'
export type {
  PublishScheduleType as ThreadsPublishScheduleType,
  TimeInterval as ThreadsTimeInterval,
} from './threads'

export * from './game'
