import { useState, FormEvent, useEffect, useMemo, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useAuth } from '@/contexts/auth-context'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import { SkeletonCard } from '@/components/ui/skeleton'
import { useToast } from '@/contexts/toast-context'
import { authService } from '@/services/auth-service'
import { decodeJwt, formatTokenDate, getTimeUntilExpiry } from '@/utils/jwt-utils'
import { StatisticsTabContent } from '@/pages/stubs/statistics'
import { BillingTabContent } from '@/pages/billing/billing'

type ProfileTab = 'main' | 'billing' | 'statistics' | 'group'

function profileTabFromSearch(searchParams: URLSearchParams): ProfileTab {
  const t = searchParams.get('tab')
  if (t === 'billing' || t === 'statistics' || t === 'group') return t
  return 'main'
}

// Компонент для отображения токена с возможностью копирования
function TokenDisplay({ 
  label, 
  token 
}: { 
  label: string
  token: string | null 
}) {
  const [copied, setCopied] = useState(false)
  const payload = token ? decodeJwt(token) : null
  
  const handleCopy = async () => {
    if (!token) return
    try {
      await navigator.clipboard.writeText(token)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }
  
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-[var(--text-secondary)]">{label}</label>
        {token && (
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors"
            title="Copy to clipboard"
          >
            {copied ? (
              <>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-emerald-400">Copied!</span>
              </>
            ) : (
              <>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                <span>Copy</span>
              </>
            )}
          </button>
        )}
      </div>
      
      {payload && (
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-1 text-[var(--text-muted)]">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Issued: {formatTokenDate(payload.iat)}</span>
          </div>
          <div className="flex items-center gap-1 text-[var(--text-muted)]">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Expires: {formatTokenDate(payload.exp)}</span>
          </div>
          <div className="col-span-2 flex items-center gap-1 text-[var(--text-muted)]">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span>Time left: {getTimeUntilExpiry(token!)}</span>
          </div>
        </div>
      )}
      
      <div className="p-3 bg-[var(--bg-tertiary)] rounded-xl font-mono text-xs break-all text-[var(--text-muted)] max-h-24 overflow-y-auto">
        {token || 'No token'}
      </div>
    </div>
  )
}

export function ProfilePage() {
  const { user, accessToken, refreshToken, updateProfile, logout, logoutAll, refreshUserData } = useAuth()
  const { addToast } = useToast()
  const [searchParams, setSearchParams] = useSearchParams()

  const activeTab = useMemo(() => profileTabFromSearch(searchParams), [searchParams])

  const setTab = useCallback(
    (tab: ProfileTab) => {
      if (tab === 'main') {
        setSearchParams({}, { replace: true })
      } else {
        setSearchParams({ tab }, { replace: true })
      }
    },
    [setSearchParams]
  )

  const [isEditing, setIsEditing] = useState(false)
  const [email, setEmail] = useState(user?.email || '')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  
  const [verificationCode, setVerificationCode] = useState('')
  const [isVerifying, setIsVerifying] = useState(false)

  useEffect(() => {
    if (user?.email) {
      setEmail(user.email)
    }
  }, [user])

  async function handleUpdateProfile(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsLoading(true)
    
    try {
      const updateData: { email?: string; password?: string } = {}
      if (email !== user?.email) {
        updateData.email = email
      }
      if (password) {
        updateData.password = password
      }
      
      if (Object.keys(updateData).length === 0) {
        setError('No changes to save')
        setIsLoading(false)
        return
      }
      
      await updateProfile(updateData)
      setSuccess('Profile updated successfully')
      addToast('Profile updated successfully')
      setIsEditing(false)
      setPassword('')
      await refreshUserData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile')
    } finally {
      setIsLoading(false)
    }
  }

  async function handleVerifyEmail(e: FormEvent) {
    e.preventDefault()
    setIsVerifying(true)
    setError('')
    setSuccess('')
    
    try {
      await authService.verifyEmail(verificationCode)
      setSuccess('Email verified successfully')
      addToast('Email verified successfully')
      setVerificationCode('')
      await refreshUserData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification failed')
    } finally {
      setIsVerifying(false)
    }
  }

  async function handleLogoutAll() {
    if (confirm('Are you sure you want to logout from all devices?')) {
      await logoutAll()
    }
  }

  if (!user) {
    return (
      <PageContainer>
        <PageHeader title="Profile" description="Manage your account settings and preferences" />
        <div className="grid gap-6 md:grid-cols-2">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </PageContainer>
    )
  }

  return (
    <PageContainer maxWidth={activeTab === 'statistics' ? 'wide' : 'default'}>
      <PageHeader title="Profile" description="Manage your account settings and preferences" />

      <div className="flex flex-wrap gap-1 border-b border-[var(--border-color)] mb-4">
        <button
          type="button"
          onClick={() => setTab('main')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'main'
              ? 'text-primary-400 border-b-2 border-primary-400 -mb-px'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          Main
        </button>
        <button
          type="button"
          onClick={() => setTab('billing')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'billing'
              ? 'text-primary-400 border-b-2 border-primary-400 -mb-px'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          Billing
        </button>
        <button
          type="button"
          onClick={() => setTab('statistics')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'statistics'
              ? 'text-primary-400 border-b-2 border-primary-400 -mb-px'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          Statistics
        </button>
        <button
          type="button"
          onClick={() => setTab('group')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'group'
              ? 'text-primary-400 border-b-2 border-primary-400 -mb-px'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          Group
        </button>
      </div>

      {error && (
        <Alert variant="error" className="animate-slide-down">
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert variant="success" className="animate-slide-down">
          {success}
        </Alert>
      )}

      {activeTab === 'main' && (
      <>
      <div className="grid gap-6 md:grid-cols-2">
        {/* User Info Card */}
        <Card className="animate-slide-up animate-stagger-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-white text-xl font-bold">
                {user?.username?.charAt(0).toUpperCase()}
              </div>
              <div>
                <span className="block">{user?.username}</span>
                <span className="text-sm font-normal text-[var(--text-secondary)]">
                  {user?.is_email_verified ? (
                    <span className="text-emerald-400 flex items-center gap-1">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Verified
                    </span>
                  ) : (
                    <span className="text-amber-400 flex items-center gap-1">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                      Unverified
                    </span>
                  )}
                </span>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center py-3 border-b border-[var(--border-color)]">
              <span className="text-[var(--text-secondary)]">Username</span>
              <span className="font-medium">{user?.username}</span>
            </div>
            <div className="flex justify-between items-center py-3 border-b border-[var(--border-color)]">
              <span className="text-[var(--text-secondary)]">Email</span>
              <span className="font-medium">{user?.email}</span>
            </div>
            <div className="flex justify-between items-center py-3 border-b border-[var(--border-color)]">
              <span className="text-[var(--text-secondary)]">Password</span>
              <span className="font-medium text-[var(--text-muted)]">••••••••</span>
            </div>
            <div className="flex justify-between items-center py-3 border-b border-[var(--border-color)]">
              <span className="text-[var(--text-secondary)]">Role</span>
              <span className="font-medium">{user?.role ?? '—'}</span>
            </div>
            <div className="flex justify-between items-center py-3 border-b border-[var(--border-color)]">
              <span className="text-[var(--text-secondary)]">Tariff</span>
              <Link
                to="/profile?tab=billing"
                className="font-medium text-primary-400 hover:text-primary-300 hover:underline focus:outline-none focus:underline"
              >
                {user?.tariff ?? 'free'}
              </Link>
            </div>
            <div className="flex justify-between items-center py-3">
              <span className="text-[var(--text-secondary)]">Member since</span>
              <span className="font-medium">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Working group */}
        {(user?.group_name ?? user?.group_id) && (
          <Card className="animate-slide-up animate-stagger-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                Рабочая группа
              </CardTitle>
              <CardDescription>Ваша группа и роль в ней</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between items-center py-3 border-b border-[var(--border-color)]">
                <span className="text-[var(--text-secondary)]">Группа</span>
                <Link to="/group" className="font-medium text-primary-400 hover:text-primary-300 hover:underline">
                  {user?.group_name ?? `ID ${user?.group_id}`}
                </Link>
              </div>
              <div className="flex justify-between items-center py-3">
                <span className="text-[var(--text-secondary)]">Роль в группе</span>
                <span className="font-medium">{user?.role_in_group === 'manager' ? 'Менеджер' : user?.role_in_group === 'author' ? 'Автор' : '—'}</span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tokens Card */}
        <Card className="animate-slide-up animate-stagger-2">
          <CardHeader>
            <CardTitle>Session Tokens</CardTitle>
            <CardDescription>Your current authentication tokens with expiry info</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <TokenDisplay 
              label="Access Token" 
              token={user?.access_token || accessToken || null} 
            />
            <TokenDisplay 
              label="Refresh Token" 
              token={user?.refresh_token || refreshToken || null} 
            />
          </CardContent>
        </Card>

        {/* Edit Profile Card */}
        <Card className="animate-slide-up animate-stagger-3">
          <CardHeader>
            <CardTitle>Edit Profile</CardTitle>
            <CardDescription>Update your profile information</CardDescription>
          </CardHeader>
          <CardContent>
            {isEditing ? (
              <form onSubmit={handleUpdateProfile} className="space-y-4">
                <Input
                  label="Email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter new email"
                />
                <Input
                  label="Password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter new password (leave empty to keep current)"
                />
                <div className="flex gap-3">
                  <Button type="submit" isLoading={isLoading}>
                    Save Changes
                  </Button>
                  <Button 
                    type="button" 
                    variant="secondary" 
                    onClick={() => {
                      setIsEditing(false)
                      setEmail(user?.email || '')
                      setPassword('')
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            ) : (
              <Button onClick={() => setIsEditing(true)}>
                Edit Profile
              </Button>
            )}
          </CardContent>
        </Card>

        {/* Email Verification Card */}
        {!user?.is_email_verified && (
          <Card className="animate-slide-up animate-stagger-4">
            <CardHeader>
              <CardTitle>Email Verification</CardTitle>
              <CardDescription>Verify your email address to unlock all features</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleVerifyEmail} className="space-y-4">
                <Input
                  label="Verification Code"
                  type="text"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value)}
                  placeholder="Enter the code sent to your email"
                />
                <Button type="submit" isLoading={isVerifying}>
                  Verify Email
                </Button>
              </form>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Session Management Card */}
      <Card className="animate-slide-up animate-stagger-5">
        <CardHeader>
          <CardTitle>Session Management</CardTitle>
          <CardDescription>Manage your active sessions across devices</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <Button variant="secondary" onClick={logout}>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Logout (This Device)
            </Button>
            <Button variant="danger" onClick={handleLogoutAll}>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
              </svg>
              Logout All Devices
            </Button>
          </div>
        </CardContent>
        <CardFooter>
          <p className="text-sm text-[var(--text-muted)]">
            Logging out from all devices will invalidate all active sessions and require re-authentication.
          </p>
        </CardFooter>
      </Card>
      </>
      )}

      {activeTab === 'billing' && <BillingTabContent />}

      {activeTab === 'statistics' && <StatisticsTabContent />}

      {activeTab === 'group' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle>Group</CardTitle>
            <CardDescription>Раздел в разработке</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-[var(--text-muted)]">Скоро здесь появятся настройки группы.</p>
          </CardContent>
        </Card>
      )}
    </PageContainer>
  )
}


