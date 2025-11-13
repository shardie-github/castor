'use client'

/**
 * DELTA:20251113_064143 CSV Uploader Component
 * 
 * Drag-and-drop CSV uploader for ETL fallback
 */

import { useState, useCallback } from 'react'

interface CSVUploaderProps {
  onUploadComplete?: (importId: string) => void
  onUploadError?: (error: string) => void
}

export function CSVUploader({ onUploadComplete, onUploadError }: CSVUploaderProps) {
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<string | null>(null)

  const handleFile = useCallback(async (file: File) => {
    if (!file.name.endsWith('.csv')) {
      onUploadError?.('File must be a CSV file')
      return
    }

    setUploading(true)
    setUploadStatus('Uploading...')

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('/api/v1/etl/upload', {
        method: 'POST',
        body: formData,
        headers: {
          // Don't set Content-Type - let browser set it with boundary
        },
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Upload failed')
      }

      const result = await response.json()
      setUploadStatus(`Uploaded! Import ID: ${result.import_id}`)
      onUploadComplete?.(result.import_id)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Upload failed'
      setUploadStatus(`Error: ${message}`)
      onUploadError?.(message)
    } finally {
      setUploading(false)
    }
  }, [onUploadComplete, onUploadError])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragging(false)

    const file = e.dataTransfer.files[0]
    if (file) {
      handleFile(file)
    }
  }, [handleFile])

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleFile(file)
    }
  }, [handleFile])

  return (
    <div className="w-full">
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        } ${uploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          accept=".csv"
          onChange={handleFileInput}
          disabled={uploading}
          className="hidden"
          id="csv-upload"
        />
        <label htmlFor="csv-upload" className="cursor-pointer">
          <div className="space-y-2">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <div className="text-sm text-gray-600">
              {uploading ? (
                <span>Uploading...</span>
              ) : (
                <>
                  <span className="font-semibold text-blue-600">Click to upload</span> or drag and drop
                </>
              )}
            </div>
            <div className="text-xs text-gray-500">CSV file only</div>
            <div className="text-xs text-gray-400 mt-2">
              Format: day,episode_id,source,downloads,listeners,completion_rate,ctr,conversions,revenue_cents
            </div>
          </div>
        </label>
      </div>
      {uploadStatus && (
        <div className={`mt-4 p-3 rounded ${
          uploadStatus.startsWith('Error')
            ? 'bg-red-50 text-red-800'
            : 'bg-green-50 text-green-800'
        }`}>
          {uploadStatus}
        </div>
      )}
    </div>
  )
}
