'use client';

import React, { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { useAppStore } from '@/lib/store';
import { Header } from '@/components/Header';
import { GalleryRail } from '@/components/GalleryRail';
import { InspectSection } from '@/components/InspectSection';
import { ProcessingSection } from '@/components/ProcessingSection';
import { ResultsSection } from '@/components/ResultsSection';
import { ShortcutsModal } from '@/components/ShortcutsModal';
import { StageKey } from '@/lib/types';
import { Menu, Terminal, Satellite } from 'lucide-react';

function SatelliteMissionControlApp() {
  const searchParams = useSearchParams();
  const deepLinkId = searchParams.get('id');

  const {
    samples,
    selectedId,
    statusMap,
    isLoadingSamples,
    loadInitialSamples,
    navigateSample,
    runRemovalForCurrent,
    setActiveStage,
    toggleCompareMode,
    setMobileGalleryOpen,
  } = useAppStore();

  const [isShortcutsOpen, setIsShortcutsOpen] = useState(false);

  // Initialize samples on mount
  useEffect(() => {
    loadInitialSamples(deepLinkId);
  }, [loadInitialSamples, deepLinkId]);

  // Global Keyboard event handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is inside an input or select
      if (
        ['INPUT', 'SELECT', 'TEXTAREA'].includes(
          (e.target as HTMLElement)?.tagName
        )
      ) {
        return;
      }

      switch (e.key) {
        case 'ArrowLeft':
          e.preventDefault();
          navigateSample('prev');
          break;
        case 'ArrowRight':
          e.preventDefault();
          navigateSample('next');
          break;
        case 'Enter':
          e.preventDefault();
          runRemovalForCurrent();
          break;
        case ' ':
          e.preventDefault(); // prevent page scroll
          toggleCompareMode();
          break;
        case '1':
          e.preventDefault();
          setActiveStage('cloudy');
          break;
        case '2':
          e.preventDefault();
          setActiveStage('baseline');
          break;
        case '3':
          e.preventDefault();
          setActiveStage('sharpened');
          break;
        case '4':
          e.preventDefault();
          setActiveStage('final');
          break;
        case '5':
          e.preventDefault();
          setActiveStage('target');
          break;
        case 'Escape':
          setIsShortcutsOpen(false);
          setMobileGalleryOpen(false);
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    navigateSample,
    runRemovalForCurrent,
    setActiveStage,
    toggleCompareMode,
    setMobileGalleryOpen,
  ]);

  if (isLoadingSamples && samples.length === 0) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[#0b0f15] text-[#00f0ff]">
        <div className="relative flex h-16 w-16 items-center justify-center rounded-lg border border-[#00f0ff]/30 bg-[#00f0ff]/10">
          <Satellite className="h-8 w-8 animate-pulse text-[#00f0ff]" />
          <span className="absolute -right-1 -top-1 flex h-3 w-3">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#00f0ff] opacity-75" />
            <span className="relative inline-flex h-3 w-3 rounded-full bg-[#00f0ff]" />
          </span>
        </div>
        <p className="mt-4 font-mono text-xs uppercase tracking-widest text-slate-300">
          Initializing Satellite Telemetry Stream...
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-screen max-h-screen flex-col overflow-hidden bg-[#0b0f15] text-slate-200">
      {/* Header */}
      <div className="shrink-0">
        <Header onOpenShortcuts={() => setIsShortcutsOpen(true)} />
      </div>

      {/* Mobile Bar to open Drawer */}
      <div className="flex shrink-0 items-center justify-between border-b border-[#243042] bg-[#0e131b] px-4 py-2 md:hidden">
        <button
          onClick={() => setMobileGalleryOpen(true)}
          className="flex items-center gap-2 rounded border border-[#243042] bg-[#141b24] px-2.5 py-1 font-mono text-xs text-slate-200"
        >
          <Menu className="h-3.5 w-3.5 text-[#00f0ff]" />
          <span>Browse samples ({samples.length})</span>
        </button>

        <button
          onClick={() => setIsShortcutsOpen(true)}
          className="flex items-center gap-1.5 rounded border border-[#243042] bg-[#141b24] px-2 py-1 text-xs text-slate-300"
        >
          <Terminal className="h-3.5 w-3.5 text-[#00f0ff]" />
          <span className="font-mono text-[11px]">Keys</span>
        </button>
      </div>

      {/* Main Layout: Fixed Left Gallery Rail + Independently Scrollable Right Workspace */}
      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Desktop Left Rail */}
        <GalleryRail />

        {/* Mobile Left Rail Drawer */}
        <GalleryRail isMobile={true} />

        {/* Workspace: Right Column */}
        <main className="h-full flex-1 min-h-0 overflow-y-auto p-3.5 sm:p-5 lg:p-6">
          <div className="mx-auto max-w-6xl space-y-5">
            {/* 1. INSPECT SECTION */}
            <InspectSection />

            {/* 2. PROCESSING SECTION */}
            <ProcessingSection />

            {/* 3. RESULTS SECTION */}
            <ResultsSection />
          </div>
        </main>
      </div>

      {/* Shortcuts Dialog */}
      <ShortcutsModal
        isOpen={isShortcutsOpen}
        onClose={() => setIsShortcutsOpen(false)}
      />
    </div>
  );
}

export default function Page() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-[#0b0f15] font-mono text-xs text-slate-400">
          Loading Mission Control...
        </div>
      }
    >
      <SatelliteMissionControlApp />
    </Suspense>
  );
}
