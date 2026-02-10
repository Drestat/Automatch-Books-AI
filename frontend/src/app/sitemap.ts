import { MetadataRoute } from 'next'
import { siteConfig } from '@/config/site'

export const revalidate = 3600;

export default function sitemap(): MetadataRoute.Sitemap {
  const routes = [
    '',
    '/pricing',
    '/features',
    '/contact',
    '/privacy',
    '/terms',
  ].map((route) => ({
    url: `${siteConfig.url}${route}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: route === '' ? 1 : 0.8,
  }))

  return routes
}
