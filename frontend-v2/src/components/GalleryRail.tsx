'use client';

import React, { useMemo } from 'react';
import { useAppStore } from '@/lib/store';
import { Sample } from '@/lib/types';
import { CheckCircle2, ArrowUpDown, Filter, X } from 'lucide-react';

interface GalleryRailProps {
  isMobile?: boolean;
}

export const GalleryRail: React.FC<GalleryRailProps> = ({ isMobile = false }) => {
  const {
    samples,
    selectedId,
    resultsMap,
    filterCoverage,
    sortBy,
    isMobileGalleryOpen,
    selectSample,
    setFilterCoverage,
    setSortBy,
    setMobileGalleryOpen,
  } = useAppStore();

  const filteredAndSortedSamples = useMemo(() => {
    let list = [...samples];

    // Filter
    if (filterCoverage === 'light') {
      list = list.filter((s) => s.cloudCoverage < 30);
    } else if (filterCoverage === 'medium') {
      list = list.filter((s) => s.cloudCoverage >= 30 && s.cloudCoverage <= 60);
    } else if (filterCoverage === 'heavy') {
      list = list.filter((s) => s.cloudCoverage > 60);
    }

    // Sort
    list.sort((a, b) => {
      if (sortBy === 'coverage_asc') {
        return a.cloudCoverage - b.cloudCoverage;
      }
      if (sortBy === 'coverage_desc') {
        return b.cloudCoverage - a.cloudCoverage;
      }
      return a.filename.localeCompare(b.filename);
    });

    return list;
  }, [samples, filterCoverage, sortBy]);

  const getCoverageBadge = (coverage: number) => {
    if (coverage < 30) {
      return {
        label: `${coverage}%`,
        badgeClass: 'border-emerald-500/40 bg-emerald-950/60 text-emerald-400',
        barClass: 'bg-emerald-500',
      };
    }
    if (coverage <= 60) {
      return {
        label: `${coverage}%`,
        badgeClass: 'border-amber-500/40 bg-amber-950/60 text-amber-400',
        barClass: 'bg-amber-500',
      };
    }
    return {
      label: `${coverage}%`,
      badgeClass: 'border-rose-500/40 bg-rose-950/60 text-rose-400',
      barClass: 'bg-rose-500',
    };
  };

  const content = (
    <div className="flex h-full w-full flex-col overflow-hidden bg-[#0f141c] text-slate-200">
      {/* Top Header & Telemetry metadata */}
      <div className="shrink-0 border-b border-[#243042] p-3 sm:p-4">
        <div className="flex items-center justify-between pb-2.5">
          <div className="flex items-center gap-2">
            <span className="font-display text-xs font-bold uppercase tracking-wider text-slate-300">
              Scene Telemetry Catalog
            </span>
            <span className="rounded bg-[#1a2330] px-1.5 py-0.5 font-mono text-[10px] text-[#00f0ff]">
              {filteredAndSortedSamples.length}/{samples.length}
            </span>
          </div>
          {isMobile && (
            <button
              onClick={() => setMobileGalleryOpen(false)}
              className="rounded p-1 text-slate-400 hover:bg-[#1a2330] hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Filter chips */}
        <div className="mb-2.5 flex items-center gap-1 overflow-x-auto text-[11px]">
          <span className="mr-1 flex items-center text-slate-500">
            <Filter className="mr-0.5 h-3 w-3" />
          </span>
          {(['all', 'light', 'medium', 'heavy'] as const).map((chip) => {
            const active = filterCoverage === chip;
            return (
              <button
                key={chip}
                onClick={() => setFilterCoverage(chip)}
                className={`rounded px-2 py-0.5 font-mono text-[11px] capitalize transition-all ${active
                    ? 'border border-[#00f0ff]/50 bg-[#00f0ff]/15 font-semibold text-[#00f0ff]'
                    : 'border border-transparent bg-[#161d28] text-slate-400 hover:border-slate-700 hover:text-slate-200'
                  }`}
              >
                {chip}
              </button>
            );
          })}
        </div>

        {/* Sort selector */}
        <div className="flex items-center justify-between text-[11px] text-slate-400">
          <span className="flex items-center gap-1 font-mono text-[10px]">
            <ArrowUpDown className="h-3 w-3 text-slate-500" />
            Sort:
          </span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="rounded border border-[#243042] bg-[#141b24] px-2 py-1 font-mono text-[11px] text-slate-200 focus:border-[#00f0ff] focus:outline-none"
          >
            <option value="coverage_asc">Cloud Coverage (Asc)</option>
            <option value="coverage_desc">Cloud Coverage (Desc)</option>
            <option value="name">Scene Filename</option>
          </select>
        </div>
      </div>

      {/* 2-column independently scrollable grid */}
      <div className="flex-1 min-h-0 overflow-y-auto p-2.5 sm:p-3">
        <div className="grid grid-cols-2 gap-2.5">
          {filteredAndSortedSamples.map((sample: Sample) => {
            const isSelected = sample.id === selectedId;
            const hasResult = Boolean(resultsMap[sample.id]);
            const coverage = getCoverageBadge(sample.cloudCoverage);

            return (
              <button
                key={sample.id}
                onClick={() => {
                  selectSample(sample.id);
                  if (isMobile) setMobileGalleryOpen(false);
                }}
                className={`group relative flex flex-col overflow-hidden rounded border text-left transition-all ${isSelected
                    ? 'border-[#00f0ff] bg-[#162232] shadow-[0_0_12px_rgba(0,240,255,0.2)] ring-1 ring-[#00f0ff]'
                    : 'border-[#243042] bg-[#131923] hover:border-slate-600 hover:bg-[#18212e]'
                  }`}
              >
                {/* Thumbnail using plain <img> tag */}
                <div className="relative aspect-square w-full overflow-hidden bg-black/60">
                  <img
                    src={sample.previews.cloudy}
                    alt={sample.filename}
                    loading="lazy"
                    className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                  />

                  {/* Coverage Badge */}
                  <div className="absolute right-1.5 top-1.5 z-10">
                    <span
                      className={`inline-block rounded border px-1.5 py-0.5 font-mono text-[9px] font-semibold tabular-nums shadow-sm ${coverage.badgeClass}`}
                    >
                      {coverage.label}
                    </span>
                  </div>

                  {/* Check dot if processed */}
                  {hasResult && (
                    <div
                      className="absolute left-1.5 top-1.5 z-10 flex h-4 w-4 items-center justify-center rounded-full bg-emerald-950/90 text-emerald-400 ring-1 ring-emerald-500/50"
                      title="Removal processed & cached"
                    >
                      <CheckCircle2 className="h-3 w-3" />
                    </div>
                  )}

                  {/* Dimension tag */}
                  <div className="absolute bottom-1 left-1.5 z-10">
                    <span className="rounded bg-black/70 px-1 py-0.2 font-mono text-[8px] text-slate-400 backdrop-blur-xs">
                      512×512
                    </span>
                  </div>
                </div>

                {/* Info & thin coverage bar */}
                <div className="flex flex-col p-2">
                  <span
                    className="truncate font-mono text-[10px] text-slate-300"
                    title={sample.filename}
                  >
                    {sample.filename}
                  </span>

                  {/* Thin coverage bar */}
                  <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-slate-800">
                    <div
                      className={`h-full ${coverage.barClass}`}
                      style={{ width: `${sample.cloudCoverage}%` }}
                    />
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );

  if (isMobile) {
    if (!isMobileGalleryOpen) return null;
    return (
      <div className="fixed inset-0 z-50 flex bg-black/75 backdrop-blur-sm">
        <div className="h-full w-4/5 max-w-sm border-r border-[#243042] shadow-2xl">
          {content}
        </div>
        <div
          className="flex-1"
          onClick={() => setMobileGalleryOpen(false)}
        />
      </div>
    );
  }

  return (
    <aside className="hidden h-full w-72 shrink-0 flex-col overflow-hidden border-r border-[#243042] md:flex lg:w-80">
      {content}
    </aside>
  );
};
