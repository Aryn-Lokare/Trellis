'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { ArrowRight, Network, UploadCloud, MessageSquareText, GitFork } from 'lucide-react';
import { cn } from '../../lib/utils';

export function MainNavbar() {
  const pathname = usePathname();
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navItems = [
    { label: 'INGEST', href: '/upload', icon: UploadCloud, description: '1. Document Upload' },
    { label: 'INVESTIGATE', href: '/chat', icon: MessageSquareText, description: '2. Cited RAG Query' },
    { label: 'SUBGRAPH', href: '/graph', icon: GitFork, description: '3. Visual Graph' },
  ];

  const isMarketingRoute = pathname === '/' || pathname === '/auth';
  const isHomepage = pathname === '/';

  const headerClass = isHomepage
    ? cn(
        'transition-all duration-300 w-full z-50',
        isScrolled 
          ? 'sticky top-0 border-b border-white/10 bg-transparent backdrop-blur' 
          : 'absolute top-0 left-0 bg-transparent border-b-transparent'
      )
    : 'sticky top-0 z-40 w-full border-b border-[#d9d9dd] bg-white/95 backdrop-blur';

  return (
    <header className={headerClass}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand / Logo */}
        <Link href={isMarketingRoute ? '/' : '/upload'} className="flex items-center group">
          <div className="relative w-28 h-8 transition-transform group-hover:scale-105">
            <Image 
              src="/trellis (1).png" 
              alt="Trellis Logo" 
              fill
              sizes="112px"
              priority
              className="object-contain"
            />
          </div>
        </Link>

        {/* Marketing routes use a deliberately quieter navigation shell. */}
        {isMarketingRoute ? (
          <nav className="flex items-center gap-4">
            {pathname !== '/auth' && (
              <Link 
                href="/auth" 
                className={isHomepage 
                  ? "text-white/85 hover:text-white hover:underline underline-offset-4 text-xs font-mono tracking-wider transition-colors"
                  : "button-secondary text-xs"
                }
              >
                Sign in
              </Link>
            )}
            <Link 
              href="/upload" 
              className={isHomepage
                ? "rounded-full bg-white text-[#17171c] px-4 py-2 text-xs font-mono tracking-wider font-medium hover:bg-white/95 transition-all active:scale-[0.98] flex items-center gap-1.5 border border-white/10"
                : "button-primary px-4 py-2 text-xs"
              }
            >
              Open workspace <ArrowRight className="h-3.5 w-3.5" />
            </Link>
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
      </div>
    </header>
  );
}
