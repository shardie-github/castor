import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'
import Script from 'next/script'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Castor - Podcast Analytics & Sponsorship Marketplace',
  description: 'Comprehensive analytics, sponsorship marketplace, and creator operations for podcasters, sponsors, and agencies. Track listener growth, manage sponsorships, and discover podcast advertising opportunities.',
  keywords: ['podcast analytics', 'podcast sponsorship', 'podcast marketplace', 'podcast advertising', 'creator tools', 'podcast metrics'],
  authors: [{ name: 'Castor' }],
  creator: 'Castor',
  publisher: 'Castor',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'https://castor.app'),
  alternates: {
    canonical: '/',
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: '/',
    siteName: 'Castor',
    title: 'Castor - Podcast Analytics & Sponsorship Marketplace',
    description: 'Comprehensive analytics, sponsorship marketplace, and creator operations for podcasters, sponsors, and agencies.',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Castor - Podcast Analytics & Sponsorship Platform',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Castor - Podcast Analytics & Sponsorship Marketplace',
    description: 'Comprehensive analytics, sponsorship marketplace, and creator operations for podcasters, sponsors, and agencies.',
    images: ['/og-image.png'],
    creator: '@castor',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  manifest: '/manifest.json',
  themeColor: '#3b82f6',
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 5,
    userScalable: true,
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'Castor',
  },
  icons: {
    icon: [
      { url: '/icon-192.png', sizes: '192x192', type: 'image/png' },
      { url: '/icon-512.png', sizes: '512x512', type: 'image/png' },
    ],
    apple: [
      { url: '/icon-192.png', sizes: '192x192', type: 'image/png' },
    ],
  },
}

// Organization Schema for SEO
const organizationSchema = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  name: 'Castor',
  url: 'https://castor.app',
  logo: 'https://castor.app/icon-512.png',
  description: 'Podcast Analytics & Sponsorship Marketplace',
  sameAs: [
    'https://twitter.com/castor',
    'https://linkedin.com/company/castor',
  ],
  contactPoint: {
    '@type': 'ContactPoint',
    contactType: 'Customer Support',
    email: 'support@castor.app',
  },
}

// WebApplication Schema for PWA
const webApplicationSchema = {
  '@context': 'https://schema.org',
  '@type': 'WebApplication',
  name: 'Castor',
  applicationCategory: 'BusinessApplication',
  operatingSystem: 'Web',
  offers: {
    '@type': 'Offer',
    price: '0',
    priceCurrency: 'USD',
  },
  aggregateRating: {
    '@type': 'AggregateRating',
    ratingValue: '4.8',
    ratingCount: '150',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        {/* PWA Service Worker Registration */}
        <Script id="register-sw" strategy="afterInteractive">
          {`
            if ('serviceWorker' in navigator) {
              window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js')
                  .then((registration) => {
                    console.log('SW registered:', registration);
                  })
                  .catch((error) => {
                    console.log('SW registration failed:', error);
                  });
              });
            }
          `}
        </Script>
        
        {/* Structured Data - Organization */}
        <Script
          id="organization-schema"
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationSchema) }}
        />
        
        {/* Structured Data - WebApplication */}
        <Script
          id="webapp-schema"
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(webApplicationSchema) }}
        />
        
        {/* Skip to main content link for accessibility */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded-lg"
        >
          Skip to main content
        </a>
      </head>
      <body className={inter.className}>
        <div id="main-content">
          <Providers>{children}</Providers>
        </div>
      </body>
    </html>
  )
}
