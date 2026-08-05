'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname, useRouter } from 'next/navigation';
import { UploadCloud, MessageSquareText, GitFork, LogOut, ShieldCheck } from 'lucide-react';
import { cn } from '../../lib/utils';
import { supabase } from '../../lib/supabase';

export function MainSidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const navItems = [
    { label: 'INGEST', href: '/upload', icon: UploadCloud, description: '1. Ingestion Pipeline' },
    { label: 'INVESTIGATE', href: '/chat', icon: MessageSquareText, description: '2. Cited RAG Query' },
    { label: 'SUBGRAPH', href: '/graph', icon: GitFork, description: '3. Visual Topology' },
  ];

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    router.push('/auth');
  };

  return (
    <aside className="w-64 shrink-0 bg-white border-r border-[#d9d9dd] h-screen fixed left-0 top-0 flex flex-col justify-between p-6 z-40">
      {/* Top Section */}
      <div className="space-y-8">
        {/* Brand Logo */}
        <Link href="/upload" className="flex items-center group px-2 block">
          <Image 
            src="/logo-black.png" 
            alt="Trellis Logo" 
            width={110}
            height={32}
            className="object-contain transition-transform group-hover:scale-105"
            style={{ height: 'auto' }}
          />
        </Link>

        {/* Navigation Link Stack */}
        <nav className="space-y-2">
          <span className="mono-label text-[10px] text-[#93939f] px-2 block font-semibold mb-3">
            WORKSPACE CONSOLE
          </span>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 group text-left',
                  isActive
                    ? 'bg-[#17171c] text-white shadow-md'
                    : 'text-[#616161] hover:text-[#17171c] hover:bg-[#eeece7]/50'
                )}
              >
                <div className={cn(
                  'p-1.5 rounded-lg transition-colors',
                  isActive ? 'bg-[#ff7759]/10 text-[#ff7759]' : 'bg-transparent text-[#93939f] group-hover:text-[#17171c]'
                )}>
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex flex-col min-w-0">
                  <span className="text-xs font-mono font-bold tracking-wider leading-none">
                    {item.label}
                  </span>
                  <span className={cn(
                    'text-[9px] mt-0.5 font-sans leading-none',
                    isActive ? 'text-white/60' : 'text-[#93939f]'
                  )}>
                    {item.description}
                  </span>
                </div>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Bottom Section */}
      <div className="border-t border-[#d9d9dd] pt-4 space-y-4">
        {/* Security / Compliance Badge */}
        <div className="flex items-center gap-2.5 px-2.5 py-2 bg-[#eeece7]/30 border border-[#d9d9dd]/65 rounded-xl">
          <ShieldCheck className="w-4 h-4 text-[#ff7759]" />
          <div className="flex flex-col">
            <span className="text-[10px] font-semibold text-[#17171c] leading-tight">Secure session</span>
            <span className="text-[8px] font-mono text-[#93939f] leading-none">FIPS-COMPLIANT</span>
          </div>
        </div>

        {/* Sign Out Trigger */}
        <button
          onClick={handleSignOut}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-[#b30000] hover:bg-rose-50 transition-colors text-xs font-mono font-bold cursor-pointer"
        >
          <LogOut className="w-4 h-4" />
          <span>SIGN OUT</span>
        </button>
      </div>
    </aside>
  );
}
