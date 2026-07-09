import type { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'AlphaDeals | Premium Investor Portal',
    short_name: 'AlphaDeals',
    description: 'UK distressed and off-market property deal pipeline for investors.',
    start_url: '/',
    display: 'standalone',
    background_color: '#0a1118',
    theme_color: '#ea580c',
    icons: [
      {
        src: '/icons/icon-192.png',
        sizes: '192x192',
        type: 'image/png',
      },
      {
        src: '/icons/icon-512.png',
        sizes: '512x512',
        type: 'image/png',
      },
      {
        src: '/icons/icon-512-maskable.png',
        sizes: '512x512',
        type: 'image/png',
        purpose: 'maskable',
      },
    ],
  };
}
