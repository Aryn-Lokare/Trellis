'use client';

import React, { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { usePathname, useRouter } from 'next/navigation';
import { Space_Grotesk, Inter } from 'next/font/google';
import Image from 'next/image';
import Lenis from 'lenis';
import { MainNavbar } from '../components/layout/MainNavbar';
import { CitationSourcePanel } from '../components/citations/CitationSourcePanel';
import { isSupabaseConfigured, supabase } from '../lib/supabase';
import './globals.css';

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-display',
  display: 'swap',
});

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isMarketingRoute = pathname === '/' || pathname === '/auth';
  const [authReady, setAuthReady] = useState(isMarketingRoute);
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      })
  );

  useEffect(() => {
    const lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      gestureOrientation: 'vertical',
      smoothWheel: true,
    });

    function raf(time: number) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }

    requestAnimationFrame(raf);

    return () => {
      lenis.destroy();
    };
  }, []);

  useEffect(() => {
    if (isMarketingRoute) {
      setAuthReady(true);
      return;
    }

    setAuthReady(false);
    if (!isSupabaseConfigured) {
      router.replace('/auth');
      return;
    }

    let active = true;
    const verifySession = async () => {
      const { data } = await supabase.auth.getUser();
      if (!active) return;
      if (data.user) setAuthReady(true);
      else router.replace('/auth');
    };
    void verifySession();

    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!active) return;
      if (session) setAuthReady(true);
      else router.replace('/auth');
    });

    return () => {
      active = false;
      listener.subscription.unsubscribe();
    };
  }, [isMarketingRoute, router]);

  return (
    <html lang="en" className={`${spaceGrotesk.variable} ${inter.variable}`}>
      <head>
        <title>Compliance GraphRAG — Enterprise AI Platform</title>
        <meta
          name="description"
          content="Multi-modal compliance evidence ingestion, cited RAG reasoning, and visual knowledge subgraph analysis."
        />
      </head>
      <body className="min-h-screen bg-white text-[#212121] flex flex-col font-sans">
        <QueryClientProvider client={queryClient}>
          <MainNavbar />
          <main className={isMarketingRoute ? 'flex-1' : 'flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8'}>
            {isMarketingRoute || authReady ? children : <div className="py-24 text-center"><span className="mono-label text-[#616161]">VERIFYING SECURE SESSION</span></div>}
          </main>
          {!isMarketingRoute && <CitationSourcePanel />}
          <footer className="border-t border-[#d9d9dd] py-6 bg-[#17171c] text-white">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
              <div className="flex items-center gap-2">
                <div className="relative w-20 h-6">
                  <Image 
                    src="/logo-white.png" 
                    alt="Trellis Logo" 
                    fill
                    sizes="80px"
                    className="object-contain"
                  />
                </div>
              </div>
            </div>
          </footer>
        </QueryClientProvider>
      </body>
    </html>
  );
}
