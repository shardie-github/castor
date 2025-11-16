'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/Button'
import { FormField } from '@/components/forms/FormField'
import { CheckCircleIcon } from '@heroicons/react/24/outline'

export default function ResetPasswordPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [step, setStep] = useState<'request' | 'reset' | 'success'>('request')
  const [email, setEmail] = useState('')
  const [token, setToken] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    const tokenParam = searchParams.get('token')
    if (tokenParam) {
      setToken(tokenParam)
      setStep('reset')
    }
  }, [searchParams])

  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/reset-password-request`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Request failed')
      }

      // Show success message (security: don't reveal if email exists)
      setStep('success')
    } catch (err: any) {
      setError(err.message || 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }

    setIsLoading(true)

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token, new_password: password }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Password reset failed')
      }

      setStep('success')
    } catch (err: any) {
      setError(err.message || 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  if (step === 'success') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
              <CheckCircleIcon className="h-8 w-8 text-green-600" />
            </div>
            <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
              {token ? 'Password Reset Successful' : 'Reset Link Sent'}
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              {token
                ? 'Your password has been reset. You can now sign in with your new password.'
                : 'If the email exists, a password reset link has been sent. Please check your email.'}
            </p>
            <div className="mt-6">
              <Button variant="primary" onClick={() => router.push('/auth/login')}>
                Go to Sign In
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            {step === 'request' ? 'Reset your password' : 'Set new password'}
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            {step === 'request' ? (
              <>
                Enter your email address and we'll send you a link to reset your password.
              </>
            ) : (
              <>
                Enter your new password below.
              </>
            )}
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={step === 'request' ? handleRequestReset : handleResetPassword}>
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="text-sm text-red-800">{error}</div>
            </div>
          )}
          {step === 'request' ? (
            <div>
              <FormField
                label="Email address"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>
          ) : (
            <div className="space-y-4">
              <FormField
                label="New Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="new-password"
              />
              <FormField
                label="Confirm New Password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                autoComplete="new-password"
              />
              {password && confirmPassword && password !== confirmPassword && (
                <p className="text-sm text-red-600">Passwords do not match</p>
              )}
            </div>
          )}

          <div>
            <Button
              type="submit"
              variant="primary"
              className="w-full"
              isLoading={isLoading}
              disabled={isLoading}
            >
              {step === 'request' ? 'Send Reset Link' : 'Reset Password'}
            </Button>
          </div>

          <div className="text-center">
            <Link href="/auth/login" className="text-sm font-medium text-blue-600 hover:text-blue-500">
              Back to Sign In
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
}
