'use client'

import React from 'react'
import { clsx } from 'clsx'
import { ExclamationCircleIcon } from '@heroicons/react/24/outline'

export interface FormFieldProps {
  label: string
  name: string
  type?: 'text' | 'email' | 'password' | 'number' | 'textarea' | 'select' | 'date'
  value?: string | number
  onChange?: (value: string | number) => void
  onBlur?: () => void
  placeholder?: string
  required?: boolean
  error?: string
  helpText?: string
  disabled?: boolean
  options?: { value: string; label: string }[]
  rows?: number
  className?: string
}

/**
 * Form Field Component
 * 
 * Reusable form field with label, validation, and error handling.
 */
export function FormField({
  label,
  name,
  type = 'text',
  value,
  onChange,
  onBlur,
  placeholder,
  required = false,
  error,
  helpText,
  disabled = false,
  options,
  rows = 4,
  className,
}: FormFieldProps) {
  const inputId = `field-${name}`

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const newValue = type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value
    onChange?.(newValue)
  }

  return (
    <div className={clsx('mb-4', className)}>
      <label
        htmlFor={inputId}
        className="block text-sm font-medium text-gray-700 mb-1"
      >
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>

      {type === 'textarea' ? (
        <textarea
          id={inputId}
          name={name}
          value={value || ''}
          onChange={handleChange}
          onBlur={onBlur}
          placeholder={placeholder}
          required={required}
          disabled={disabled}
          rows={rows}
          className={clsx(
            'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
            error && 'border-red-300 focus:border-red-500 focus:ring-red-500',
            disabled && 'bg-gray-100 cursor-not-allowed'
          )}
        />
      ) : type === 'select' ? (
        <select
          id={inputId}
          name={name}
          value={value || ''}
          onChange={handleChange}
          onBlur={onBlur}
          required={required}
          disabled={disabled}
          className={clsx(
            'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
            error && 'border-red-300 focus:border-red-500 focus:ring-red-500',
            disabled && 'bg-gray-100 cursor-not-allowed'
          )}
        >
          <option value="">Select {label.toLowerCase()}...</option>
          {options?.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      ) : (
        <input
          id={inputId}
          name={name}
          type={type}
          value={value || ''}
          onChange={handleChange}
          onBlur={onBlur}
          placeholder={placeholder}
          required={required}
          disabled={disabled}
          className={clsx(
            'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
            error && 'border-red-300 focus:border-red-500 focus:ring-red-500',
            disabled && 'bg-gray-100 cursor-not-allowed'
          )}
        />
      )}

      {error && (
        <div className="mt-1 flex items-center text-sm text-red-600">
          <ExclamationCircleIcon className="h-4 w-4 mr-1" />
          {error}
        </div>
      )}

      {helpText && !error && (
        <p className="mt-1 text-sm text-gray-500">{helpText}</p>
      )}
    </div>
  )
}
