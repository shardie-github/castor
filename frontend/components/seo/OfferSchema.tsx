import Script from 'next/script'

interface OfferSchemaProps {
  offer: {
    name: string
    description: string
    price: number
    priceCurrency: string
    availability: string
    validFrom?: string
    validThrough?: string
    seller: {
      name: string
      url?: string
    }
  }
}

export function OfferSchema({ offer }: OfferSchemaProps) {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'Offer',
    name: offer.name,
    description: offer.description,
    price: offer.price,
    priceCurrency: offer.priceCurrency,
    availability: offer.availability,
    validFrom: offer.validFrom,
    validThrough: offer.validThrough,
    seller: {
      '@type': 'Organization',
      name: offer.seller.name,
      url: offer.seller.url,
    },
  }

  return (
    <Script
      id="offer-schema"
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  )
}
