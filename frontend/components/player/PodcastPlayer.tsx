'use client'

import { useState, useRef, useEffect } from 'react'
import {
  PlayIcon,
  PauseIcon,
  ForwardIcon,
  BackwardIcon,
  SpeakerWaveIcon,
  SpeakerXMarkIcon,
} from '@heroicons/react/24/solid'

interface PodcastPlayerProps {
  episode: {
    id: string
    title: string
    audioUrl: string
    duration?: number
    imageUrl?: string
  }
  showEmbedCode?: boolean
  onSponsorLinkClick?: (sponsorId: string) => void
  sponsorLinks?: Array<{ id: string; name: string; url: string; timestamp: number }>
  className?: string
}

export function PodcastPlayer({
  episode,
  showEmbedCode = false,
  onSponsorLinkClick,
  sponsorLinks = [],
  className = '',
}: PodcastPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolume] = useState(1)
  const [isMuted, setIsMuted] = useState(false)
  const [showEmbedModal, setShowEmbedModal] = useState(false)

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const updateTime = () => setCurrentTime(audio.currentTime)
    const updateDuration = () => setDuration(audio.duration)
    const handleEnded = () => setIsPlaying(false)

    audio.addEventListener('timeupdate', updateTime)
    audio.addEventListener('loadedmetadata', updateDuration)
    audio.addEventListener('ended', handleEnded)

    return () => {
      audio.removeEventListener('timeupdate', updateTime)
      audio.removeEventListener('loadedmetadata', updateDuration)
      audio.removeEventListener('ended', handleEnded)
    }
  }, [])

  const togglePlay = () => {
    const audio = audioRef.current
    if (!audio) return

    if (isPlaying) {
      audio.pause()
    } else {
      audio.play()
    }
    setIsPlaying(!isPlaying)
  }

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current
    if (!audio) return

    const newTime = parseFloat(e.target.value)
    audio.currentTime = newTime
    setCurrentTime(newTime)
  }

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current
    if (!audio) return

    const newVolume = parseFloat(e.target.value)
    audio.volume = newVolume
    setVolume(newVolume)
    setIsMuted(newVolume === 0)
  }

  const toggleMute = () => {
    const audio = audioRef.current
    if (!audio) return

    if (isMuted) {
      audio.volume = volume || 0.5
      setIsMuted(false)
    } else {
      audio.volume = 0
      setIsMuted(true)
    }
  }

  const skip = (seconds: number) => {
    const audio = audioRef.current
    if (!audio) return

    audio.currentTime = Math.max(0, Math.min(audio.currentTime + seconds, duration))
  }

  const formatTime = (seconds: number): string => {
    if (isNaN(seconds)) return '0:00'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getEmbedCode = (): string => {
    const embedUrl = `${window.location.origin}/embed/player/${episode.id}`
    return `<script src="${window.location.origin}/embed.js" data-episode-id="${episode.id}"></script>`
  }

  const copyEmbedCode = () => {
    navigator.clipboard.writeText(getEmbedCode())
    // Show toast notification (implement toast component)
    alert('Embed code copied to clipboard!')
  }

  const currentSponsorLink = sponsorLinks.find(
    (link) => currentTime >= link.timestamp && currentTime < link.timestamp + 30
  )

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-4 ${className}`}>
      <audio ref={audioRef} src={episode.audioUrl} preload="metadata" />

      {/* Episode Info */}
      <div className="flex items-start space-x-4 mb-4">
        {episode.imageUrl && (
          <img
            src={episode.imageUrl}
            alt={episode.title}
            className="w-16 h-16 rounded-lg object-cover"
          />
        )}
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-900 truncate">{episode.title}</h3>
          {currentSponsorLink && (
            <div className="mt-2">
              <a
                href={currentSponsorLink.url}
                onClick={(e) => {
                  e.preventDefault()
                  onSponsorLinkClick?.(currentSponsorLink.id)
                  window.open(currentSponsorLink.url, '_blank')
                }}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                Sponsored by: {currentSponsorLink.name} →
              </a>
            </div>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <input
          type="range"
          min="0"
          max={duration || 0}
          value={currentTime}
          onChange={handleSeek}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
          style={{
            background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${(currentTime / duration) * 100}%, #e5e7eb ${(currentTime / duration) * 100}%, #e5e7eb 100%)`,
          }}
          aria-label="Seek audio"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => skip(-10)}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Rewind 10 seconds"
          >
            <BackwardIcon className="w-5 h-5" />
          </button>
          <button
            onClick={togglePlay}
            className="p-3 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors shadow-lg"
            aria-label={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? (
              <PauseIcon className="w-6 h-6" />
            ) : (
              <PlayIcon className="w-6 h-6 ml-0.5" />
            )}
          </button>
          <button
            onClick={() => skip(10)}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Forward 10 seconds"
          >
            <ForwardIcon className="w-5 h-5" />
          </button>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={toggleMute}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label={isMuted ? 'Unmute' : 'Mute'}
          >
            {isMuted ? (
              <SpeakerXMarkIcon className="w-5 h-5" />
            ) : (
              <SpeakerWaveIcon className="w-5 h-5" />
            )}
          </button>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={isMuted ? 0 : volume}
            onChange={handleVolumeChange}
            className="w-20 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            aria-label="Volume"
          />
        </div>

        {showEmbedCode && (
          <button
            onClick={() => setShowEmbedModal(true)}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Get Embed Code
          </button>
        )}
      </div>

      {/* Embed Code Modal */}
      {showEmbedModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-gray-900">Embed Code</h3>
              <button
                onClick={() => setShowEmbedModal(false)}
                className="text-gray-400 hover:text-gray-600"
                aria-label="Close modal"
              >
                ×
              </button>
            </div>
            <textarea
              readOnly
              value={getEmbedCode()}
              className="w-full h-32 p-3 border border-gray-300 rounded-lg font-mono text-sm bg-gray-50"
            />
            <div className="flex justify-end mt-4">
              <button
                onClick={copyEmbedCode}
                className="px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
              >
                Copy Code
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
