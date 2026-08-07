'use client';

import Link from 'next/link';
import { 
  ArrowRight, 
  ShieldCheck, 
  CheckCircle2, 
  AlertCircle, 
  FileText, 
  Volume2, 
  Table, 
  Network, 
  Database, 
  Search, 
  GitFork,
  ArrowUpRight
} from 'lucide-react';
import { InteractiveDemo } from '../components/landing/InteractiveDemo';

export default function HomePage() {
  return (
    <div className="overflow-hidden bg-[#ffffff] font-sans antialiased text-[#212121]">
      
      {/* 1. HERO SECTION (WITH MERGED NAVBAR DESIGN & GRADIENT) */}
      <div className="w-full hero-gradient">
        <section className="mx-auto max-w-7xl px-4 pb-20 pt-28 sm:px-6 sm:pb-32 sm:pt-36 lg:px-8">
          <div className="text-center flex flex-col items-center">
            {/* Display Headline */}
            <h1 className="max-w-4xl text-5xl font-normal leading-[0.95] tracking-[-0.04em] text-white sm:text-7xl lg:text-8xl font-display mb-8">
              Compliance answers you can trace, not guess.
            </h1>
            
            {/* Subheadline */}
            <p className="max-w-2xl text-lg leading-relaxed text-white/70 mb-10">
              Trellis ingests your PDFs, audio logs, spreadsheets to build a unified compliance knowledge graph. Get precise, accurate answers grounded in real connections—backed by exact document, page, and timestamp citations.
            </p>
            
            {/* CTAs */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 w-full sm:w-auto mb-16">
              <Link href="/upload" className="rounded-full bg-white text-[#17171c] w-full sm:w-auto text-sm px-7 py-3.5 flex items-center justify-center gap-2 group font-mono tracking-wider font-semibold hover:bg-white/95 transition-all active:scale-[0.98]">
                Try the Demo 
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1 text-[#17171c]" />
              </Link>
              <Link 
                href="https://github.com/Aryn-Lokare/Trellis" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="text-white hover:text-[#ff7759] text-sm font-mono tracking-wider flex items-center gap-1 group transition-colors hover:underline underline-offset-4"
              >
                View on GitHub
                <ArrowUpRight className="h-3.5 w-3.5 opacity-65 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </Link>
            </div>
          </div>

          {/* Custom Premium Interactive Demo Widget */}
          <div className="mt-4 p-1 rounded-3xl border border-white/10 bg-white/5 backdrop-blur-sm">
            <div className="bg-white rounded-[22px] p-6 lg:p-10 border border-[#d9d9dd] text-[#212121]">
              <div className="max-w-3xl mb-8">
                <span className="mono-label text-[10px] text-[#ff7759] block mb-2">INTERACTIVE WALKTHROUGH</span>
                <h3 className="text-2xl font-medium tracking-tight text-[#17171c] font-display">
                  Click a prompt below to see how Trellis links multi-format compliance logs.
                </h3>
              </div>
              <InteractiveDemo />
            </div>
          </div>
        </section>
      </div>

      {/* 2. PROBLEM SECTION */}
      <section className="border-t border-[#d9d9dd] bg-[#eeece7]/30 py-20 sm:py-32">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid gap-12 lg:grid-cols-12 lg:gap-16">
            
            <div className="lg:col-span-5 flex flex-col justify-center">
              <span className="mono-label text-xs tracking-wider text-[#ff7759]">THE PROBLEM</span>
              <h2 className="mt-4 text-4xl font-normal leading-[1.05] tracking-tight text-[#17171c] sm:text-5xl font-display">
                Enterprise compliance isn't flat. Naive AI search treats it like it is.
              </h2>
              <p className="mt-6 text-base leading-relaxed text-[#616161]">
                Compliance is defined by relationships. When records are split, isolated, and queried on raw text match alone, critical dependencies fall through the cracks.
              </p>
            </div>

            <div className="lg:col-span-7 flex flex-col justify-center gap-6">
              {/* Problem 1 */}
              <div className="bg-white rounded-2xl border border-[#d9d9dd] p-6 flex items-start gap-4">
                <div className="p-3 rounded-xl bg-[#ff7759]/5 border border-[#ff7759]/15 text-[#ff7759] shrink-0">
                  <Database className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-base font-semibold text-[#17171c] font-display">Scattered & Siloed Files</h4>
                  <p className="mt-2 text-sm leading-relaxed text-[#616161]">
                    A vendor contract in a PDF, an auditor phone call in a WAV audio log, and a flagged transaction in a spreadsheet. Today, these are connected only in someone's head, separated by incompatible storage silos.
                  </p>
                </div>
              </div>

              {/* Problem 2 */}
              <div className="bg-white rounded-2xl border border-[#d9d9dd] p-6 flex items-start gap-4">
                <div className="p-3 rounded-xl bg-[#ff7759]/5 border border-[#ff7759]/15 text-[#ff7759] shrink-0">
                  <AlertCircle className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-base font-semibold text-[#17171c] font-display">The Vector RAG Failure Mode</h4>
                  <p className="mt-2 text-sm leading-relaxed text-[#616161]">
                    Standard enterprise AI search (vector RAG) chops documents into isolated chunks. By stripping away connections, it cannot correlate rules. This lack of relationship logic leads directly to hallucinated or incomplete answers.
                  </p>
                </div>
              </div>

              {/* Problem 3 */}
              <div className="bg-white rounded-2xl border border-[#d9d9dd] p-6 flex items-start gap-4">
                <div className="p-3 rounded-xl bg-[#ff7759]/5 border border-[#ff7759]/15 text-[#ff7759] shrink-0">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-base font-semibold text-[#17171c] font-display">The High-Stakes Risk</h4>
                  <p className="mt-2 text-sm leading-relaxed text-[#616161]">
                    In compliance, audit, and risk control, a "mostly correct" or generic answer is a critical security failure. Regulators and compliance officers cannot rely on black-box guesswork.
                  </p>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* 3. HOW IT WORKS SECTION */}
      <section className="bg-[#003c33] text-white py-20 sm:py-32">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mb-16">
            <span className="mono-label text-xs tracking-wider text-[#ffad9b]">SYSTEM PIPELINE</span>
            <h2 className="mt-4 text-4xl font-normal leading-[1.05] tracking-tight text-white sm:text-5xl font-display">
              From raw documents to verified knowledge.
            </h2>
            <p className="mt-4 text-base text-white/70">
              Our backend extracts structured connections directly from raw multi-format files to model compliance requirements natively.
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            
            {/* Step 1 */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-all duration-300">
              <span className="mono-label text-[10px] text-[#ffad9b] font-bold">01 / INGEST</span>
              <h3 className="mt-6 text-xl font-medium tracking-tight text-white font-display">Ingest Any Format</h3>
              <p className="mt-3 text-xs leading-relaxed text-white/70">
                Upload enterprise PDFs, recorded compliance calls, financial spreadsheets, and system architecture diagrams.
              </p>
            </div>

            {/* Step 2 */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-all duration-300">
              <span className="mono-label text-[10px] text-[#ffad9b] font-bold">02 / EXTRACT</span>
              <h3 className="mt-6 text-xl font-medium tracking-tight text-white font-display">Extract Entities</h3>
              <p className="mt-3 text-xs leading-relaxed text-white/70">
                Our system parses your files to automatically identify compliance regulations, dates, actors, and requirements.
              </p>
            </div>

            {/* Step 3 */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-all duration-300">
              <span className="mono-label text-[10px] text-[#ffad9b] font-bold">03 / CONNECT</span>
              <h3 className="mt-6 text-xl font-medium tracking-tight text-white font-display">Map the Graph</h3>
              <p className="mt-3 text-xs leading-relaxed text-white/70">
                Instead of chunking text in isolation, Trellis links extracted items together to map how every file connects across systems.
              </p>
            </div>

            {/* Step 4 */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-all duration-300">
              <span className="mono-label text-[10px] text-[#ffad9b] font-bold">04 / ANSWER</span>
              <h3 className="mt-6 text-xl font-medium tracking-tight text-white font-display">Deliver Cited Answers</h3>
              <p className="mt-3 text-xs leading-relaxed text-white/70">
                Query the database to get exact answers grounded in the graph, with page numbers and audio timestamps for every claim.
              </p>
            </div>

          </div>
        </div>
      </section>

      {/* 4. WHY IT'S DIFFERENT SECTION */}
      <section className="py-20 sm:py-32">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <span className="mono-label text-xs tracking-wider text-[#ff7759]">ARCHITECTURE COMPARISON</span>
            <h2 className="mt-4 text-4xl font-normal leading-[1.05] tracking-tight text-[#17171c] sm:text-5xl font-display">
              Relational mapping vs. semantic search.
            </h2>
          </div>

          <div className="grid gap-8 md:grid-cols-2 max-w-5xl mx-auto">
            {/* Standard RAG */}
            <div className="bg-white border border-[#d9d9dd] rounded-[22px] p-8 opacity-75">
              <span className="mono-label text-[10px] text-[#93939f] font-bold block mb-4">STANDARD AI SEARCH (VECTOR RAG)</span>
              
              <ul className="space-y-6">
                <li className="flex items-start gap-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#ff7759] mt-2 shrink-0" />
                  <div>
                    <h4 className="text-sm font-semibold text-[#17171c] font-display">Isolated Chunks</h4>
                    <p className="mt-1 text-xs text-[#616161] leading-relaxed">Cuts files into fragments, completely losing connections and context across different documents.</p>
                  </div>
                </li>
                
                <li className="flex items-start gap-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#ff7759] mt-2 shrink-0" />
                  <div>
                    <h4 className="text-sm font-semibold text-[#17171c] font-display">Plausible Hallucinations</h4>
                    <p className="mt-1 text-xs text-[#616161] leading-relaxed">Generates fluent, authoritative-sounding answers that are factually wrong when source files conflict or are separated.</p>
                  </div>
                </li>

                <li className="flex items-start gap-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#ff7759] mt-2 shrink-0" />
                  <div>
                    <h4 className="text-sm font-semibold text-[#17171c] font-display">Unverifiable Claims</h4>
                    <p className="mt-1 text-xs text-[#616161] leading-relaxed">Points you to generic, large file names, leaving you to search hundreds of pages manually to confirm if a claim is real.</p>
                  </div>
                </li>
              </ul>
            </div>

            {/* Trellis */}
            <div className="bg-[#17171c] text-white border border-white/5 rounded-[22px] p-8 shadow-xl relative overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-[#003c33]/60 rounded-full blur-2xl pointer-events-none" />
              
              <span className="mono-label text-[10px] text-[#ff7759] font-bold block mb-4">TRELLIS (KNOWLEDGE GRAPH)</span>
              
              <ul className="space-y-6">
                <li className="flex items-start gap-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#10b981] mt-2 shrink-0" />
                  <div>
                    <h4 className="text-sm font-semibold text-white font-display">Connected Graphs</h4>
                    <p className="mt-1 text-xs text-white/70 leading-relaxed">Maps explicit entities and relationships across your entire document inventory, creating a unified web of connections.</p>
                  </div>
                </li>
                
                <li className="flex items-start gap-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#10b981] mt-2 shrink-0" />
                  <div>
                    <h4 className="text-sm font-semibold text-white font-display">Grounded In Truth</h4>
                    <p className="mt-1 text-xs text-white/70 leading-relaxed">Designed with strict verification filters that refuse to answer if clear support does not exist in the source data.</p>
                  </div>
                </li>

                <li className="flex items-start gap-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#10b981] mt-2 shrink-0" />
                  <div>
                    <h4 className="text-sm font-semibold text-white font-display">Pinpoint Traceability</h4>
                    <p className="mt-1 text-xs text-white/70 leading-relaxed">Generates direct links mapping to exact page numbers, spreadsheet coordinates, or audio timestamp intervals.</p>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* 5. TRUST / CREDIBILITY SECTION */}
      <section className="bg-[#eeece7]/40 border-t border-b border-[#d9d9dd] py-20 sm:py-32">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          <div className="bg-[#edfce9] border border-[#003c33]/20 rounded-3xl p-8 sm:p-12 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-[#003c33]/5 rounded-full blur-2xl pointer-events-none" />
            
            <div className="flex flex-col items-center text-center">
              <div className="p-3 rounded-full bg-[#003c33]/5 border border-[#003c33]/15 text-[#003c33] mb-6">
                <ShieldCheck className="w-8 h-8" />
              </div>
              
              <h3 className="text-2xl sm:text-3xl font-medium tracking-tight text-[#003c33] font-display">
                Designed for environments where "close enough" is a violation.
              </h3>
              
              <p className="mt-6 text-sm sm:text-base leading-relaxed text-[#212121]/80 max-w-2xl">
                Compliance operations require absolute grounding. We designed Trellis around a strict refusal policy: if the ingested data does not explicitly contain the answer, our system will state that it does not know, rather than attempt a guess.
              </p>

              <div className="w-full border-t border-[#003c33]/10 my-6" />

              <p className="text-xs sm:text-sm leading-relaxed text-[#212121]/75 max-w-2xl">
                Every generated response is directly mapped to its source. Every document page, table cell, and audio millisecond is permanently linked to the final answer, turning compliance reviews into a simple 10-second verification step.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 6. CLOSING CTA SECTION */}
      <section className="py-24 sm:py-32 text-center relative overflow-hidden bg-white">
        <div className="absolute -bottom-48 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-[#edfce9]/40 rounded-full blur-3xl pointer-events-none" />
        
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col items-center">
          <span className="mono-label text-xs tracking-wider text-[#ff7759] mb-4">GET STARTED</span>
          <h2 className="max-w-2xl text-4xl font-normal leading-[1.05] tracking-tight text-[#17171c] sm:text-5xl font-display mb-6">
            Build your compliance knowledge graph today.
          </h2>
          <p className="max-w-md text-sm leading-relaxed text-[#616161] mb-8">
            Experience zero-hallucination document search designed for high-stakes enterprise compliance.
          </p>
          <Link href="/upload" className="button-primary px-8 py-4 text-sm flex items-center gap-2 group">
            Try the Demo
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Link>
        </div>
      </section>

    </div>
  );
}
