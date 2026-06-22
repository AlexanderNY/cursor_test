import { useState, FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/contexts/auth-context'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'

export function ResetPasswordPage() {
  const { resetPassword } = useAuth()
  const [email, setEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [isSuccess, setIsSuccess] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setIsLoading(true)
    
    try {
      await resetPassword(email)
      setIsSuccess(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send reset email')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-[var(--bg-primary)] via-[var(--bg-secondary)] to-[var(--bg-primary)]">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/2 left-1/3 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl animate-pulse-subtle"></div>
        <div className="absolute bottom-1/3 right-1/3 w-96 h-96 bg-accent-500/10 rounded-full blur-3xl animate-pulse-subtle" style={{ animationDelay: '1s' }}></div>
      </div>
      
      <Card variant="glass" className="w-full max-w-md relative animate-fade-in">
        <CardHeader className="text-center">
          <CardTitle className="text-3xl font-bold text-gradient">Reset Password</CardTitle>
          <CardDescription>
            Enter your email and we'll send you a link to reset your password
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          {error && (
            <Alert variant="error" className="mb-6 animate-slide-down">
              {error}
            </Alert>
          )}
          
          {isSuccess ? (
            <div className="space-y-6 animate-fade-in">
              <Alert variant="success">
                Password reset link has been sent to your email. Please check your inbox.
              </Alert>
              <Link to="/sign-in">
                <Button variant="secondary" className="w-full">
                  Back to Sign In
                </Button>
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              <Input
                label="Email"
                type="email"
                placeholder="Enter your email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                icon={
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                }
              />
              
              <Button type="submit" className="w-full" isLoading={isLoading}>
                Send Reset Link
              </Button>
            </form>
          )}
        </CardContent>
        
        <CardFooter className="justify-center">
          <p className="text-[var(--text-secondary)]">
            Remember your password?{' '}
            <Link to="/sign-in" className="text-primary-400 hover:text-primary-300 font-medium transition-colors">
              Sign In
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  )
}


