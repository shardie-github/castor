'use client'

import { InputHTMLAttributes, forwardRef } from 'react'
import { clsx } from 'clsx'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  variant?: 'default' | 'error'
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ variant = 'default', className, ...props }, ref) => {
    const baseStyles = 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2'
    
    const variants = {
      default: 'border-gray-300 focus:ring-blue-500 focus:border-blue-500',
      error: 'border-red-300 focus:ring-red-500 focus:border-red-500',
    }

    return (
      <input
        ref={ref}
        className={clsx(baseStyles, variants[variant], className)}
        {...props}
      />
    )
  }
)

Input.displayName = 'Input'
