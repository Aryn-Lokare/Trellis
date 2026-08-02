'use client';

import { FormEvent, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowRight, LockKeyhole, ShieldCheck } from 'lucide-react';
import { isSupabaseConfigured, supabase } from '../../lib/supabase';

type Mode = 'sign-in' | 'sign-up';

export default function AuthPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>('sign-in');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setMessage(null);
    setError(null);
    if (!isSupabaseConfigured) {
      setError('Supabase is not configured. Add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY before signing in.');
      return;
    }

    const formData = new FormData(event.currentTarget);
    const email = String(formData.get('email') || '').trim();
    const password = String(formData.get('password') || '');
    const fullName = String(formData.get('fullName') || '').trim();
    setIsSubmitting(true);

    try {
      if (mode === 'sign-up') {
        const { data, error: signUpError } = await supabase.auth.signUp({
          email,
          password,
          options: { data: { full_name: fullName || null } },
        });
        if (signUpError) throw signUpError;
        if (data.session) {
          router.replace('/upload');
          return;
        }
        setMessage('Account created. Check your email to confirm your address, then return here to sign in.');
      } else {
        const { error: signInError } = await supabase.auth.signInWithPassword({ email, password });
        if (signInError) throw signInError;
        router.replace('/upload');
      }
    } catch (authError) {
      setError(authError instanceof Error ? authError.message : 'Authentication could not be completed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const switchMode = () => {
    setMode(mode === 'sign-in' ? 'sign-up' : 'sign-in');
    setError(null);
    setMessage(null);
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-[#eeece7] px-4 py-10 sm:px-6 sm:py-16">
      <div className="mx-auto grid max-w-6xl overflow-hidden rounded-[22px] border border-[#d9d9dd] bg-white lg:grid-cols-2">
        <section className="bg-[#003c33] p-8 text-white sm:p-12">
          <span className="mono-label text-[#ffad9b]">SECURE WORKSPACE ACCESS</span>
          <h1 className="mt-5 max-w-md text-4xl font-medium leading-tight tracking-tight sm:text-5xl">Enter the evidence workspace.</h1>
          <p className="mt-5 max-w-md text-base leading-relaxed text-white/70">Investigate compliance evidence with source-aware answers and visual graph context.</p>
          <div className="mt-12 rounded-[8px] border border-white/15 bg-white/5 p-5">
            <div className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-[#ff7759]" /><span className="mono-label text-xs">SUPABASE AUTH + PROFILES</span></div>
            <p className="mt-3 text-sm leading-relaxed text-white/65">Passwords are handled by Supabase Auth. Your email and display name are stored in the protected profile record.</p>
          </div>
        </section>

        <section className="p-8 sm:p-12">
          <span className="mono-label text-[#1863dc]">{mode === 'sign-in' ? 'SIGN IN' : 'CREATE ACCOUNT'}</span>
          <h2 className="mt-2 text-3xl tracking-tight text-[#17171c]">{mode === 'sign-in' ? 'Welcome back.' : 'Create your workspace account.'}</h2>
          <p className="mt-2 text-sm text-[#616161]">{mode === 'sign-in' ? 'Use the credentials registered with your organization.' : 'Your profile is created with Supabase when you register.'}</p>
          <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
            {mode === 'sign-up' && <label className="block"><span className="mono-label text-[11px] text-[#616161]">DISPLAY NAME</span><input type="text" name="fullName" autoComplete="name" className="mt-2 w-full rounded-[4px] border border-[#d9d9dd] px-3 py-3 text-sm outline-none focus:border-[#9b60aa] focus:ring-2 focus:ring-[#9b60aa]/15" placeholder="Your name" /></label>}
            <label className="block"><span className="mono-label text-[11px] text-[#616161]">WORK EMAIL</span><input required type="email" name="email" autoComplete="email" className="mt-2 w-full rounded-[4px] border border-[#d9d9dd] px-3 py-3 text-sm outline-none focus:border-[#9b60aa] focus:ring-2 focus:ring-[#9b60aa]/15" placeholder="name@organization.com" /></label>
            <label className="block"><span className="mono-label text-[11px] text-[#616161]">PASSWORD</span><input required minLength={6} type="password" name="password" autoComplete={mode === 'sign-in' ? 'current-password' : 'new-password'} className="mt-2 w-full rounded-[4px] border border-[#d9d9dd] px-3 py-3 text-sm outline-none focus:border-[#9b60aa] focus:ring-2 focus:ring-[#9b60aa]/15" placeholder="At least 6 characters" /></label>
            <button className="button-primary w-full disabled:cursor-not-allowed disabled:opacity-60" disabled={isSubmitting} type="submit"><LockKeyhole className="h-4 w-4" /> {isSubmitting ? 'Please wait…' : mode === 'sign-in' ? 'Sign in' : 'Create account'}</button>
          </form>
          {error && <p className="mt-4 rounded-[8px] border border-[#d9d9dd] bg-white p-3 text-xs leading-relaxed text-[#b30000]" role="alert">{error}</p>}
          {message && <p className="mt-4 rounded-[8px] border border-[#d9d9dd] bg-[#eeece7] p-3 text-xs leading-relaxed text-[#616161]" role="status">{message}</p>}
          <div className="mt-7 flex items-center justify-between gap-3 border-t border-[#d9d9dd] pt-5 text-xs">
            <button type="button" className="button-secondary text-xs" onClick={switchMode}>{mode === 'sign-in' ? 'Need an account? Create one' : 'Already registered? Sign in'}</button>
            <Link href="/" className="inline-flex items-center gap-1.5 text-[#616161] underline underline-offset-4 hover:text-[#1863dc]">Home <ArrowRight className="h-3.5 w-3.5" /></Link>
          </div>
        </section>
      </div>
    </div>
  );
}
