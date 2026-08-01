'use client';

import React, { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { usePathname, useRouter } from 'next/navigation';
import { MainNavbar } from '../components/layout/MainNavbar';
import { CitationSourcePanel } from '../components/citations/CitationSourcePanel';
import { isSupabaseConfigured, supabase } from '../lib/supabase';
import './globals.css';

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
    <html lang="en">
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
              <div className="mono-label text-[#93939f]">
                COMPLIANCE GRAPHRAG • DOMAIN 3 GEN AI DEMO
              </div>
              <div className="text-[#93939f]">
                Cohere Editorial Control Framework • Multi-Modal RAG Pipeline
              </div>
            </div>
          </footer>
        </QueryClientProvider>
      </body>
    </html>
  );
}
