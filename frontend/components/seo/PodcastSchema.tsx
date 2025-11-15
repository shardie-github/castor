import Script from 'next/script'

interface PodcastSchemaProps {
  podcast: {
    name: string
    description: string
    image?: string
    author: {
      name: string
      email?: string
    }
    episodes?: Array<{
      name: string
      description?: string
      datePublished: string
      duration?: string
      audioUrl: string
    }>
  }
}

export function PodcastSchema({ podcast }: PodcastSchemaProps) {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'PodcastSeries',
    name: podcast.name,
    description: podcast.description,
    image: podcast.image,
    author: {
      '@type': 'Person',
      name: podcast.author.name,
      email: podcast.author.email,
    },
    ...(podcast.episodes && {
      episode: podcast.episodes.map((ep) => ({
        '@type': 'PodcastEpisode',
        name: ep.name,
        description: ep.description,
        datePublished: ep.datePublished,
        duration: ep.duration,
        associatedMedia: {
          '@type': 'MediaObject',
          contentUrl: ep.audioUrl,
        },
      })),
    }),
  }

  return (
    <Script
      id="podcast-schema"
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  )
}
