import Script from 'next/script'

interface EpisodeSchemaProps {
  episode: {
    name: string
    description: string
    datePublished: string
    duration?: string
    audioUrl: string
    image?: string
    podcastName: string
    podcastImage?: string
  }
}

export function EpisodeSchema({ episode }: EpisodeSchemaProps) {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'PodcastEpisode',
    name: episode.name,
    description: episode.description,
    datePublished: episode.datePublished,
    duration: episode.duration,
    image: episode.image,
    partOfSeries: {
      '@type': 'PodcastSeries',
      name: episode.podcastName,
      image: episode.podcastImage,
    },
    associatedMedia: {
      '@type': 'MediaObject',
      contentUrl: episode.audioUrl,
      encodingFormat: 'audio/mpeg',
    },
  }

  return (
    <Script
      id="episode-schema"
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  )
}
