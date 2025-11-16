'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/Button'
import { FormField } from '@/components/forms/FormField'

export default function RegisterPage() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    name: '',
    acceptTerms: false,
    acceptPrivacy: false,
  })
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [passwordErrors, setPasswordErrors] = useState<string[]>([])

  const validatePassword = (password: string): string[] => {
    const errors: string[] = []
    if (password.length < 8) {
      errors.push('Password must be at least 8 characters')
    }
    if (!/[A-Z]/.test(password)) {
      errors.push('Password must contain at least one uppercase letter')
    }
    if (!/[a-z]/.test(password)) {
      errors.push('Password must contain at least one lowercase letter')
    }
    if (!/[0-9]/.test(password)) {
      errors.push('Password must contain at least one number')
    }
    return errors
  }

  const handlePasswordChange = (password: string) => {
    setFormData({ ...formData, password })
    setPasswordErrors(validatePassword(password))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match')
      return
    }

    // Validate password strength
    const errors = validatePassword(formData.password)
    if (errors.length > 0) {
      setPasswordErrors(errors)
      setError('Please fix password requirements')
      return
    }

    // Validate terms acceptance
    if (!formData.acceptTerms || !formData.acceptPrivacy) {
      setError('You must accept the terms and privacy policy')
      return
    }

    setIsLoading(true)

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
          name: formData.name,
          accept_terms: formData.acceptTerms,
          accept_privacy: formData.acceptPrivacy,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Registration failed')
      }

      // Redirect to email verification page
      router.push(`/auth/verify-email?token=${data.verification_token}&email=${formData.email}`)
    } catch (err: any) {
      setError(err.message || 'An error occurred during registration')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Already have an account?{' '}
            <Link href="/auth/login" className="font-medium text-blue-600 hover:text-blue-500">
              Sign in
            </Link>
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="text-sm text-red-800">{error}</div>
            </div>
          )}
          <div className="space-y-4">
            <FormField
              label="Full Name"
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              autoComplete="name"
            />
            <FormField
              label="Email address"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
              autoComplete="email"
            />
            <div>
              <FormField
                label="Password"
                type="password"
                value={formData.password}
                onChange={(e) => handlePasswordChange(e.target.value)}
                required
                autoComplete="new-password"
              />
              {passwordErrors.length > 0 && (
                <ul className="mt-1 text-sm text-red-600 list-disc list-inside">
                  {passwordErrors.map((err, idx) => (
                    <li key={idx}>{err}</li>
                  ))}
                </ul>
              )}
            </div>
            <FormField
              label="Confirm Password"
              type="password"
              value={formData.confirmPassword}
              onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
              required
              autoComplete="new-password"
            />
            {formData.password && formData.confirmPassword && formData.password !== formData.confirmPassword && (
              <p className="text-sm text-red-600">Passwords do not match</p>
            )}
          </div>

          <div className="space-y-3">
            <div className="flex items-start">
              <input
                id="accept-terms"
                name="accept-terms"
                type="checkbox"
                checked={formData.acceptTerms}
                onChange={(e) => setFormData({ ...formData, acceptTerms: e.target.checked })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mt-0.5"
                required
              />
              <label htmlFor="accept-terms" className="ml-2 block text-sm text-gray-900">
                I accept the{' '}
                <Link href="/terms" className="text-blue-600 hover:text-blue-500" target="_blank">
                  Terms of Service
                </Link>
              </label>
            </div>
            <div className="flex items-start">
              <input
                id="accept-privacy"
                name="accept-privacy"
                type="checkbox"
                checked={formData.acceptPrivacy}
                onChange={(e) => setFormData({ ...formData, acceptPrivacy: e.target.checked })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mt-0.5"
                required
              />
              <label htmlFor="accept-privacy" className="ml-2 block text-sm text-gray-900">
                I accept the{' '}
                <Link href="/privacy" className="text-blue-600 hover:text-blue-500" target="_blank">
                  Privacy Policy
                </Link>
              </label>
            </div>
          </div>

          <div>
            <Button
              type="submit"
              variant="primary"
              className="w-full"
              isLoading={isLoading}
              disabled={isLoading || !formData.acceptTerms || !formData.acceptPrivacy}
            >
              Create account
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
