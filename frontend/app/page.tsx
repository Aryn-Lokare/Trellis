import Link from 'next/link';
import { ArrowRight, Database, GitFork, SearchCheck, ShieldCheck } from 'lucide-react';

const capabilities = [
  {
    label: '01 / Ingest',
    title: 'Build a traceable evidence graph.',
    description: 'Bring PDFs, call recordings, tables, and schematics into one evidence layer without losing source context.',
    icon: Database,
  },
  {
    label: '02 / Investigate',
    title: 'Ask questions with citations.',
    description: 'Run cross-document investigations and trace each response back to the original source spans.',
    icon: SearchCheck,
  },
  {
    label: '03 / Explore',
    title: 'See the relationships behind the answer.',
    description: 'Move from cited findings into a visual knowledge subgraph of entities and their connections.',
    icon: GitFork,
  },
];

export default function HomePage() {
  return (
    <div className="overflow-hidden">
      <section className="mx-auto max-w-7xl px-4 pb-16 pt-14 sm:px-6 sm:pb-24 sm:pt-20 lg:px-8">
        <span className="mono-label text-[#ff7759]">COMPLIANCE INTELLIGENCE / EVIDENCE-FIRST AI</span>
        <div className="mt-6 grid items-end gap-10 lg:grid-cols-12">
          <div className="lg:col-span-8">
            <h1 className="max-w-4xl text-5xl font-medium leading-[0.96] tracking-[-0.055em] text-[#17171c] sm:text-7xl lg:text-8xl">
              Know what your evidence says.
            </h1>
            <p className="mt-7 max-w-2xl text-lg leading-relaxed text-[#616161]">
              Compliance GraphRAG connects scattered operational evidence into cited investigations and navigable knowledge graphs.
            </p>
          </div>
          <div className="lg:col-span-4 lg:pb-1">
            <Link href="/upload" className="button-primary w-full sm:w-auto">
              Open the workspace <ArrowRight className="h-4 w-4" />
            </Link>
            <Link href="/auth" className="button-secondary ml-0 mt-3 sm:ml-5 sm:mt-0">
              Sign in
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 sm:pb-24 lg:px-8">
        <div className="dark-feature-band overflow-hidden p-7 sm:p-10 lg:p-16">
          <div className="grid gap-10 lg:grid-cols-12 lg:gap-16">
            <div className="lg:col-span-5">
              <span className="mono-label text-[#ffad9b]">ONE EVIDENCE SYSTEM</span>
              <h2 className="mt-3 text-3xl font-medium tracking-tight text-white sm:text-5xl">
                Built for an audit trail, not a black box.
              </h2>
              <p className="mt-5 max-w-md text-base leading-relaxed text-white/70">
                The workspace keeps ingestion, cited reasoning, and graph exploration connected so a compliance team can inspect the path to every finding.
              </p>
            </div>
            <div className="lg:col-span-7">
              <div className="rounded-[16px] border border-white/15 bg-[#071829] p-5 sm:p-6">
                <div className="flex items-center gap-2 border-b border-white/10 pb-4">
                  <ShieldCheck className="h-4 w-4 text-[#ff7759]" />
                  <span className="mono-label text-xs text-white">TRACEABLE INVESTIGATION FLOW</span>
                </div>
                <div className="mt-5 grid gap-3 sm:grid-cols-3">
                  {['Ingest evidence', 'Verify claims', 'Inspect topology'].map((step, index) => (
                    <div key={step} className="rounded-[8px] border border-white/10 bg-white/5 p-4">
                      <span className="mono-label text-[10px] text-[#ffad9b]">0{index + 1}</span>
                      <p className="mt-5 text-sm text-white">{step}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-20 sm:px-6 sm:pb-28 lg:px-8">
        <div className="border-b border-[#d9d9dd] pb-4">
          <span className="mono-label text-[#1863dc]">THE WORKSPACE</span>
        </div>
        <div className="divide-y divide-[#d9d9dd]">
          {capabilities.map(({ label, title, description, icon: Icon }) => (
            <div key={label} className="grid gap-4 py-7 sm:grid-cols-12 sm:items-center">
              <div className="sm:col-span-2"><span className="mono-label text-[#ff7759]">{label}</span></div>
              <div className="sm:col-span-5"><h3 className="text-2xl tracking-tight text-[#17171c]">{title}</h3></div>
              <div className="flex items-start gap-3 sm:col-span-5">
                <Icon className="mt-1 h-4 w-4 shrink-0 text-[#1863dc]" />
                <p className="text-sm leading-relaxed text-[#616161]">{description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
