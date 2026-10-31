'use client';

import React from 'react';
import { BookOpen, Satellite, Layers, Terminal } from 'lucide-react';
import { DOCS_URL, GITHUB_URL } from '@/lib/config';

const GithubIcon: React.FC<{ className?: string }> = ({ className = 'h-3.5 w-3.5' }) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
    <path d="M9 18c-4.51 2-5-2-7-2" />
  </svg>
);

interface HeaderProps {
  onOpenShortcuts?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenShortcuts }) => {
  return (
    <header className="sticky top-0 z-30 flex items-center justify-between border-b border-[#243042] bg-[#0d1219]/95 px-4 py-3 backdrop-blur-md sm:px-6">
      {/* Left: Telemetry identity and model badges */}
      <div className="flex items-center gap-3 md:gap-5">
        <div className="flex items-center gap-2.5">
          <div className="relative flex h-8 w-8 items-center justify-center rounded-sm border border-[#00f0ff]/40 bg-[#00f0ff]/10 text-[#00f0ff]">
            <Satellite className="h-4 w-4" />
            <span className="absolute -right-0.5 -top-0.5 flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#00f0ff] opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-[#00f0ff]" />
            </span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-display text-sm font-bold tracking-tight text-slate-100 sm:text-base">
                SAR-Guided Optical Satellite Cloud Removal
              </h1>
              <span className="hidden rounded bg-[#1e2736] px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-slate-400 lg:inline-block">
                S1-SAR / S2-MSI
              </span>
            </div>
            <p className="hidden text-[11px] text-slate-400 sm:block">
              Multi-scale edge-conditioned restoration and adversarial texture refinement
            </p>
          </div>
        </div>

        {/* Model badges */}
        <div className="hidden items-center gap-1.5 sm:flex">
          <span className="inline-flex items-center gap-1 rounded border border-[#00f0ff]/30 bg-[#00f0ff]/10 px-2 py-0.5 font-mono text-[11px] font-semibold text-[#00f0ff]">
            <Layers className="h-3 w-3" />
            ECRformer
          </span>
          <span className="inline-flex items-center gap-1 rounded border border-slate-700 bg-slate-800/80 px-2 py-0.5 font-mono text-[11px] font-semibold text-slate-300">
            PatchGAN
          </span>
        </div>
      </div>

      {/* Right: External links and shortcut trigger */}
      <div className="flex items-center gap-2 sm:gap-3">
        {onOpenShortcuts && (
          <button
            onClick={onOpenShortcuts}
            title="Keyboard Shortcuts"
            className="hidden items-center gap-1.5 rounded border border-[#243042] bg-[#141b24] px-2.5 py-1 text-xs text-slate-300 transition-colors hover:border-[#00f0ff]/50 hover:text-[#00f0ff] md:flex"
          >
            <Terminal className="h-3.5 w-3.5 text-slate-400" />
            <span className="font-mono text-[11px]">Shortcuts</span>
          </button>
        )}

        <a
          href={DOCS_URL}
          target="_blank"
          rel="noopener noreferrer"
          title="Documentation"
          className="flex items-center gap-1.5 rounded border border-[#243042] bg-[#141b24] px-2.5 py-1 text-xs text-slate-200 transition-colors hover:border-[#00f0ff]/50 hover:bg-[#182230] hover:text-[#00f0ff]"
        >
          <BookOpen className="h-3.5 w-3.5 text-[#00f0ff]" />
          <span className="hidden font-mono text-[11px] font-medium sm:inline">Docs</span>
        </a>

        <a
          href={GITHUB_URL}
          target="_blank"
          rel="noopener noreferrer"
          title="GitHub Repository"
          className="flex items-center gap-1.5 rounded border border-[#243042] bg-[#141b24] px-2.5 py-1 text-xs text-slate-200 transition-colors hover:border-[#00f0ff]/50 hover:bg-[#182230] hover:text-[#00f0ff]"
        >
          <GithubIcon className="h-3.5 w-3.5 text-slate-300" />
          <span className="hidden font-mono text-[11px] font-medium sm:inline">GitHub</span>
        </a>
      </div>
    </header>
  );
};
