export type UserRole = 'guest' | 'user' | 'admin' | 'manager' | 'author'

export interface User {
  id?: number
  username: string
  email: string
  role: UserRole
  tariff?: string
  is_email_verified: boolean
  /** Аккаунт заблокирован администратором (нет входа и API). */
  is_blocked?: boolean
  created_at: string
  access_token?: string
  refresh_token?: string
  group_id?: number | null
  group_name?: string | null
  role_in_group?: 'owner' | 'editor' | 'approver' | 'viewer' | 'admin' | 'manager' | 'author' | 'analyst' | null
  active_group_id?: number | null
  /** Все группы пользователя (если API отдал список). */
  groups?: Array<{ group_id: number; group_name: string; role_in_group: 'owner' | 'editor' | 'approver' | 'viewer' | 'admin' | 'manager' | 'author' | 'analyst' }> | null
  billing_provider?: string | null
  billing_customer_id?: string | null
  billing_subscription_id?: string | null
  subscription_status?: string | null
  subscription_current_period_end?: string | null
}

export interface BillingPlanDefinition {
  code: string
  display_name: string
  description: string
  monthly_posts_limit: number
  storage_gb_limit: number
  max_connected_platforms: number
  max_own_channels?: number
  max_competitor_channels?: number
  max_brands?: number
  max_targets_per_job?: number
  max_automations?: number
  max_team_seats?: number
  ai_calls_month?: number
  features: Record<string, boolean>
  sort_order: number
  price_monthly?: number
  currency?: string
}

export interface BillingMeResponse {
  tariff: string
  plan: BillingPlanDefinition | null
  billing_provider?: string | null
  billing_customer_id?: string | null
  billing_subscription_id?: string | null
  subscription_status?: string | null
  subscription_current_period_end?: string | null
  stripe_portal_available: boolean
  stripe_checkout_available?: boolean
  pending_request?: BillingPlanRequest | null
}

export type BillingPlanRequestStatus = 'pending' | 'invoiced' | 'applied' | 'rejected' | 'cancelled'

export interface BillingPlanRequest {
  id: number
  user_id: number
  username?: string
  email?: string
  current_tariff: string
  requested_tariff: string
  promo_code?: string | null
  list_price: number
  discount_amount: number
  final_price: number
  currency: string
  status: BillingPlanRequestStatus
  invoice_sent_at?: string | null
  invoice_smtp_sent?: boolean
  invoice_body?: string | null
  admin_comment?: string | null
  smtp_configured?: boolean
  created_at: string
  updated_at?: string
}

export interface PromoCode {
  id: number
  code: string
  description?: string | null
  discount_percent?: number | null
  discount_amount?: number | null
  applies_to_tariff?: string | null
  max_redemptions?: number | null
  redeemed_count: number
  valid_from?: string | null
  valid_until?: string | null
  is_active: boolean
  created_at?: string
}

export interface BillingEventRow {
  id: number
  provider: string
  event_type: string
  created_at: string
}

export interface AdminAuditLogEntry {
  id: number
  admin_user_id: number
  action: string
  target_type?: string | null
  target_id?: string | null
  details_json?: Record<string, unknown> | null
  created_at: string
}

export interface AdminProductMetrics {
  active_users_30d: number
  active_users_60d: number
  total_active_seconds_30d: number
  engagement_seconds: number
  retention: number | null
  paid_active_users_30d: number
  paid_active_users_60d: number
  conversion: number | null
}

export interface GroupMemberResponse {
  user_id: number
  username: string
  email: string
  tariff: string
  role_in_group: 'owner' | 'editor' | 'approver' | 'viewer' | 'admin' | 'manager' | 'author' | 'analyst'
  joined_at: string
}

export interface GroupResponse {
  id: number
  name: string
  description?: string | null
  created_at: string
  created_by_user_id?: number | null
  role_in_group?: 'owner' | 'editor' | 'approver' | 'viewer' | 'admin' | 'manager' | 'author' | 'analyst' | null
  members?: GroupMemberResponse[] | null
}

export interface GroupInviteResponse {
  id: number
  group_id: number
  email?: string | null
  role_in_group: string
  token: string
  invited_by_user_id: number
  status: string
  expires_at: string
  created_at: string
  group_name?: string | null
  invite_path?: string | null
}

export interface InviteActionResponse {
  status: 'added' | 'invited'
  group_name?: string | null
  member?: GroupMemberResponse | null
  invite?: GroupInviteResponse | null
}

export interface InvitePeekResponse {
  group_name: string
  email?: string | null
  role_in_group: string
  status: string
  expires_at: string
}

export interface AcceptInviteResponse {
  group_id: number
  group_name?: string | null
  role_in_group: string
  already_member: boolean
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface RegisterCredentials {
  username: string
  email: string
  password: string
  utm_source?: string
  utm_medium?: string
  utm_campaign?: string
  invite_token?: string
}

export interface ProfileUpdate {
  username?: string
  email?: string
  password?: string
}

export interface EmailVerificationRequest {
  code: string
}

export interface PasswordResetRequest {
  email: string
}

export interface PasswordResetConfirm {
  token: string
  new_password: string
}

export interface RoleTariffHistoryEntry {
  id: number
  user_id: number
  changed_at: string
  changed_by_user_id?: number | null
  role_old?: string | null
  role_new?: string | null
  tariff_old?: string | null
  tariff_new?: string | null
}

export interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

export type AuthAction =
  | { type: 'AUTH_START' }
  | { type: 'AUTH_SUCCESS'; payload: { user: User; tokens: TokenResponse } }
  | { type: 'AUTH_FAILURE'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'UPDATE_USER'; payload: User }
  | { type: 'UPDATE_TOKENS'; payload: TokenResponse }
  | { type: 'CLEAR_ERROR' }


