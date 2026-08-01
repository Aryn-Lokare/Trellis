'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useHealth } from '../../hooks/useHealth';
import { ArrowRight, Network, UploadCloud, MessageSquareText, GitFork } from 'lucide-react';
import { cn } from '../../lib/utils';

export function MainNavbar() {
  const pathname = usePathname();
  const { data: health, isError, isLoading } = useHealth();

  const isConnected = !isError && health?.status === 'healthy';
  const isDegraded = !isError && health?.status === 'degraded';

  const getHealthBadge = () => {
    if (isLoading) {
      return (
        <span className="flex items-center gap-1.5 text-xs text-[#93939f]">
          <span className="w-2 h-2 rounded-full bg-[#93939f] animate-pulse" />
          <span className="mono-label text-[10px]">CHECKING API</span>
        </span>
      );
    }
    if (isConnected) {
      return (
        <span className="flex items-center gap-1.5 text-xs text-[#212121]">
          <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]" />
          <span className="mono-label text-[10px] text-emerald-700">API CONNECTED</span>
        </span>
      );
    }
    if (isDegraded) {
      return (
        <span className="flex items-center gap-1.5 text-xs text-[#212121]">
          <span className="w-2 h-2 rounded-full bg-amber-500 animate-ping" />
          <span className="mono-label text-[10px] text-amber-700">API DEGRADED</span>
        </span>
      );
    }
    return (
      <span className="flex items-center gap-1.5 text-xs text-[#b30000]">
        <span className="w-2 h-2 rounded-full bg-[#b30000]" />
        <span className="mono-label text-[10px] text-[#b30000]">API DISCONNECTED</span>
      </span>
    );
  };

  const navItems = [
    { label: 'INGEST', href: '/upload', icon: UploadCloud, description: '1. Document Upload' },
    { label: 'INVESTIGATE', href: '/chat', icon: MessageSquareText, description: '2. Cited RAG Query' },
    { label: 'SUBGRAPH', href: '/graph', icon: GitFork, description: '3. Visual Graph' },
  ];

  const isMarketingRoute = pathname === '/' || pathname === '/auth';

  return (
    <header className="sticky top-0 z-40 w-full border-b border-[#d9d9dd] bg-white/95 backdrop-blur">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand / Logo */}
        <Link href={isMarketingRoute ? '/' : '/upload'} className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded-lg bg-[#17171c] text-white flex items-center justify-center font-bold text-base transition-transform group-hover:scale-105">
            <Network className="w-4 h-4 text-[#ff7759]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-base tracking-tight text-[#17171c]">
                Compliance GraphRAG
              </span>
              <span className="mono-label text-[9px] px-1.5 py-0.5 rounded bg-[#eeece7] text-[#616161]">
                ENTERPRISE AI
              </span>
            </div>
          </div>
        </Link>

        {/* Marketing routes use a deliberately quieter navigation shell. */}
        {isMarketingRoute ? (
          <nav className="flex items-center gap-4">
            {pathname !== '/auth' && <Link href="/auth" className="button-secondary text-xs">Sign in</Link>}
            <Link href="/upload" className="button-primary px-4 py-2 text-xs">Open workspace <ArrowRight className="h-3.5 w-3.5" /></Link>
          </nav>
        ) : (
        <nav className="flex items-center space-x-1 sm:space-x-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || (pathname === '/' && item.href === '/upload');

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-2 px-3.5 py-2 rounded-full text-xs font-mono tracking-wider transition-all',
                  isActive
                    ? 'bg-[#17171c] text-white font-medium shadow-none'
                    : 'text-[#616161] hover:text-[#17171c] hover:bg-[#eeece7]'
                )}
              >
                <Icon className={cn('w-3.5 h-3.5', isActive ? 'text-[#ff7759]' : 'text-[#93939f]')} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
        )}

        {/* Backend Health Status Indicator */}
        <div className="hidden lg:flex items-center gap-2 bg-[#eeece7]/60 px-3 py-1.5 rounded-full border border-[#d9d9dd]">
          {getHealthBadge()}
        </div>
      </div>
    </header>
  );
}
