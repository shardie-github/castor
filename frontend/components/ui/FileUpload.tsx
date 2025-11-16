'use client'

import { useRef, useState } from 'react'
import { CloudArrowUpIcon } from '@heroicons/react/24/outline'
import { clsx } from 'clsx'

interface FileUploadProps {
  accept?: string
  multiple?: boolean
  onFileSelect: (files: File[]) => void
  maxSizeMB?: number
  className?: string
}

export function FileUpload({
  accept,
  multiple = false,
  onFileSelect,
  maxSizeMB = 10,
  className,
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (files: FileList | null) => {
    if (!files || files.length === 0) return

    const fileArray = Array.from(files)
    const invalidFiles = fileArray.filter(
      (file) => file.size > maxSizeMB * 1024 * 1024
    )

    if (invalidFiles.length > 0) {
      setError(`Some files exceed the maximum size of ${maxSizeMB}MB`)
      return
    }

    setError(null)
    onFileSelect(fileArray)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    handleFileSelect(e.dataTransfer.files)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  return (
    <div className={clsx('w-full', className)}>
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        className={clsx(
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
        )}
      >
        <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <p className="text-sm text-gray-600 mb-2">
          Drag and drop files here, or click to select
        </p>
        <p className="text-xs text-gray-500">
          Maximum file size: {maxSizeMB}MB
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={(e) => handleFileSelect(e.target.files)}
          className="hidden"
        />
      </div>
      {error && (
        <p className="mt-2 text-sm text-red-600">{error}</p>
      )}
    </div>
  )
}
