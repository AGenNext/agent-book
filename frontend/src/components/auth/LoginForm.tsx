'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/hooks/use-auth'
import { useAuthStore } from '@/lib/stores/auth-store'
import { getConfig } from '@/lib/config'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertCircle } from 'lucide-react'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'

export function LoginForm() {
  const [password, setPassword] = useState('')
  const { login, isLoading, error } = useAuth()
  const { authRequired, checkAuthRequired, hasHydrated } = useAuthStore()
  const [isCheckingAuth, setIsCheckingAuth] = useState(true)
  const [configInfo, setConfigInfo] = useState<{ apiUrl: string; version: string } | null>(null)
  const router = useRouter()
  
  // Signup state
  const [isSignup, setIsSignup] = useState(false)
  const [email, setEmail] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [signupError, setSignupError] = useState('')
  const [signupSuccess, setSignupSuccess] = useState(false)
  const [allowSignup, setAllowSignup] = useState(false)

  useEffect(() => {
    getConfig().then(cfg => setConfigInfo({ apiUrl: cfg.apiUrl, version: cfg.version })).catch(() => {})
  }, [])

  useEffect(() => {
    if (!hasHydrated) return
    checkAuthRequired().then(required => {
      if (!required) router.push('/notebooks')
      else setIsCheckingAuth(false)
    }).catch(() => setIsCheckingAuth(false))
  }, [hasHydrated])

  useEffect(() => {
    fetch('/api/auth/config').then(r => r.json()).then(cfg => setAllowSignup(cfg.allow_signup === true)).catch(() => {})
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSignupError('')
    
    if (isSignup) {
      if (password !== confirmPassword) { setSignupError('Passwords do not match'); return }
      if (password.length < 8) { setSignupError('Password must be at least 8 characters'); return }
      try {
        const res = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        })
        const data = await res.json()
        if (!res.ok) { setSignupError(data.detail || 'Signup failed'); return }
        setSignupSuccess(true)
        setIsSignup(false)
        setEmail(''); setPassword(''); setConfirmPassword('')
      } catch (e: any) { setSignupError(e.message || 'Signup failed') }
    } else {
      await login(password)
    }
  }

  if (isCheckingAuth || !hasHydrated) {
    return <div className="flex items-center justify-center min-h-[400px]"><LoadingSpinner /></div>
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4">
      <Card className="w-full max-w-md border-slate-700 bg-slate-800/50">
        <CardHeader className="text-center">
          <div className="mx-auto w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center text-3xl mb-4">📚</div>
          <CardTitle className="text-2xl font-bold">AgentBook</CardTitle>
          <CardDescription>{isSignup ? 'Create your account' : 'Enter your password'}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {isSignup && (
              <Input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required className="bg-slate-700 border-slate-600" />
            )}
            <Input type="password" placeholder={isSignup ? "Create password" : "Password"} value={password} onChange={e => setPassword(e.target.value)} required className="bg-slate-700 border-slate-600" />
            {isSignup && (
              <Input type="password" placeholder="Confirm password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required className="bg-slate-700 border-slate-600" />
            )}
            {(error || signupError) && (
              <div className="flex items-center gap-2 text-red-400 text-sm"><AlertCircle className="w-4 h-4" />{error || signupError}</div>
            )}
            {signupSuccess && <div className="text-green-400 text-sm">Account created! Please log in.</div>}
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? <LoadingSpinner /> : (isSignup ? 'Sign Up' : 'Sign In')}
            </Button>
            {allowSignup && (
              <button type="button" onClick={() => { setIsSignup(!isSignup); setSignupError(''); setSignupSuccess(false); }} className="w-full text-center text-sm text-slate-400 hover:text-slate-300">
                {isSignup ? 'Already have an account? Sign in' : "Don't have an account? Sign up"}
              </button>
            )}
          </form>
          {configInfo && <div className="mt-4 pt-4 border-t border-slate-700 text-xs text-slate-500 text-center">{configInfo.apiUrl} • v{configInfo.version}</div>}
        </CardContent>
      </Card>
    </div>
  )
}