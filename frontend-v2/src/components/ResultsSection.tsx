'use client';

import React, { useState } from 'react';
import { useAppStore } from '@/lib/store';
import { StageKey, Metrics } from '@/lib/types';
import {
  calculateDelta,
  getBestMetricStages,
  METRIC_TOOLTIPS,
  METRIC_LABELS,
} from '@/lib/metrics-utils';
import {
  ReactCompareSlider,
  ReactCompareSliderHandle,
} from 'react-compare-slider';
import {
  TransformWrapper,
  TransformComponent,
} from 'react-zoom-pan-pinch';
import {
  Columns2,
  ArrowRightLeft,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  CheckCircle2,
  HelpCircle,
  TrendingUp,
  TrendingDown,
  Eye,
  Award,
  Layers,
  ChevronRight,
} from 'lucide-react';

export const ResultsSection: React.FC = () => {
  const {
    samples,
    selectedId,
    statusMap,
    resultsMap,
    activeStage,
    isCompareMode,
    compareLeft,
    compareRight,
    setActiveStage,
    toggleCompareMode,
    setCompareMode,
    setCompareStages,
    swapCompareStages,
    viewCachedResult,
  } = useAppStore();

  const [viewerScale, setViewerScale] = useState(1);
  const isZoomed = viewerScale > 1.05;

  const currentSample = samples.find((s) => s.id === selectedId);
  const currentStatus = selectedId ? statusMap[selectedId] || 'idle' : 'idle';
  const cachedResult = selectedId ? resultsMap[selectedId] : null;

  // 1. WAITING / CACHED STATE (when status is idle or running or error)
  if (currentStatus !== 'done') {
    return (
      <section className="relative rounded border border-dashed border-[#243042] bg-[#0d121a]/70 p-6 text-center">
        {cachedResult ? (
          // CACHED RESULT NOTICE (per state rule: show check mark and "View previous result" button)
          <div className="flex flex-col items-center justify-center py-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-950/80 text-emerald-400 ring-1 ring-emerald-500/50">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <h3 className="mt-3 font-display text-sm font-bold uppercase tracking-wider text-slate-200">
              Cached Removal Results Available
            </h3>
            <p className="mt-1 max-w-md text-xs text-slate-400">
              This scene has previously been processed through the ECRformer + PatchGAN pipeline.
            </p>
            <button
              onClick={() => viewCachedResult()}
              className="mt-4 flex items-center gap-2 rounded border border-[#00f0ff] bg-[#00f0ff]/15 px-4 py-2 font-mono text-xs font-bold uppercase tracking-wider text-[#00f0ff] transition hover:bg-[#00f0ff]/25 active:scale-98"
            >
              <Eye className="h-4 w-4" />
              <span>View Previous Result</span>
            </button>
          </div>
        ) : (
          // DIMMED PLACEHOLDER SKELETON
          <div className="py-8">
            <div className="mb-4 flex items-center justify-between text-xs text-slate-500">
              <span className="font-mono uppercase tracking-wider">
                Stage 3: Reconstruction Telemetry & Results
              </span>
              <span className="font-mono text-[10px]">Awaiting Pipeline Output</span>
            </div>

            {/* Skeleton frames to prevent page jump */}
            <div className="grid grid-cols-1 gap-4 opacity-40 md:grid-cols-3">
              <div className="h-48 rounded border border-slate-800 bg-slate-900/40" />
              <div className="h-48 rounded border border-slate-800 bg-slate-900/40" />
              <div className="h-48 rounded border border-slate-800 bg-slate-900/40" />
            </div>

            <p className="mt-6 font-mono text-xs text-slate-400">
              Run cloud removal to see results, comparative sliders, and spectral telemetry
            </p>
          </div>
        )}
      </section>
    );
  }

  // 2. DONE STATE: RENDER FULL RESULTS
  if (!currentSample || !cachedResult) return null;

  const getStageUrl = (st: StageKey): string => {
    if (st === 'cloudy') return currentSample.previews.cloudy;
    return cachedResult.stages[st];
  };

  const getStageMetrics = (st: StageKey): Metrics | null => {
    if (st === 'target') return null;
    return cachedResult.metrics[st];
  };

  const bestStages = getBestMetricStages(cachedResult.metrics);

  const stageDisplayNames: Record<StageKey, string> = {
    cloudy: 'Cloudy (S2 Input)',
    baseline: 'Baseline (ECRformer)',
    sharpened: 'Sharpened (Wavelet)',
    final: 'Final (PatchGAN)',
    target: 'Ground Truth Target',
  };

  return (
    <section className="space-y-5 rounded border border-[#243042] bg-[#121822] p-4 shadow-2xl sm:p-5">
      {/* (A) PIPELINE STEPPER & STAGE NAVIGATION */}
      <div className="rounded border border-[#243042] bg-[#0e141d] p-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-1 sm:gap-2">
            <span className="mr-2 font-mono text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Pipeline Stage:
            </span>
            {(['cloudy', 'baseline', 'sharpened', 'final'] as const).map(
              (stage, idx) => {
                const isSelected = activeStage === stage && !isCompareMode;
                return (
                  <React.Fragment key={stage}>
                    <button
                      onClick={() => {
                        setActiveStage(stage);
                        setCompareMode(false);
                      }}
                      className={`flex items-center gap-1.5 rounded px-2.5 py-1 font-mono text-xs transition-all ${
                        isSelected
                          ? 'border border-[#00f0ff] bg-[#00f0ff]/15 font-semibold text-[#00f0ff]'
                          : 'border border-transparent bg-[#161f2c] text-slate-300 hover:border-slate-700 hover:text-white'
                      }`}
                    >
                      <span className="font-mono text-[10px] text-slate-500">
                        0{idx + 1}
                      </span>
                      <span className="capitalize">{stage}</span>
                    </button>
                    {idx < 3 && (
                      <ChevronRight className="h-3 w-3 text-slate-600" />
                    )}
                  </React.Fragment>
                );
              }
            )}
          </div>

          {/* Separate "Clear Target" Reference */}
          <div className="flex items-center gap-2 border-t border-slate-800 pt-2 sm:border-t-0 sm:pt-0">
            <button
              onClick={() => {
                setActiveStage('target');
                setCompareMode(false);
              }}
              className={`rounded px-2.5 py-1 font-mono text-xs transition-all ${
                activeStage === 'target' && !isCompareMode
                  ? 'border border-[#00f0ff] bg-[#00f0ff]/15 font-semibold text-[#00f0ff]'
                  : 'border border-slate-700 bg-[#161f2c] text-slate-400 hover:border-slate-600 hover:text-slate-200'
              }`}
            >
              Clear Target (Reference)
            </button>

            <button
              onClick={() => toggleCompareMode()}
              className={`flex items-center gap-1.5 rounded border px-3 py-1 font-mono text-xs font-semibold transition-all ${
                isCompareMode
                  ? 'border-[#00f0ff] bg-[#00f0ff] text-black shadow-[0_0_10px_rgba(0,240,255,0.3)]'
                  : 'border-[#243042] bg-[#161f2c] text-slate-300 hover:border-[#00f0ff]/40 hover:text-[#00f0ff]'
              }`}
            >
              <Columns2 className="h-3.5 w-3.5" />
              <span>Compare Mode</span>
            </button>
          </div>
        </div>
      </div>

      {/* (B) MAIN STAGE VIEWER: 2-COLUMN BLOCK (50/50 SPLIT) */}
      <div className="grid grid-cols-1 items-stretch gap-4 lg:grid-cols-2">
        {/* Left Column (Viewer): 50% */}
        <div className="flex w-full flex-col rounded border border-[#243042] bg-[#0c1017]">
          {/* Top Viewer Controls */}
          <div className="flex h-[42px] flex-wrap items-center justify-between border-b border-[#243042] px-3.5 text-xs">
            {isCompareMode ? (
              /* Compare Controls */
              <div className="flex items-center gap-2">
                <span className="font-mono text-[11px] text-slate-400">Left:</span>
                <select
                  value={compareLeft}
                  onChange={(e) =>
                    setCompareStages(e.target.value as StageKey, compareRight)
                  }
                  className="h-7 rounded border border-[#243042] bg-[#141b24] px-2 py-0.5 font-mono text-[11px] text-[#00f0ff] focus:outline-none focus:border-[#00f0ff]"
                >
                  <option value="cloudy">Cloudy</option>
                  <option value="baseline">Baseline</option>
                  <option value="sharpened">Sharpened</option>
                  <option value="final">Final</option>
                  <option value="target">Target</option>
                </select>

                <button
                  onClick={swapCompareStages}
                  title="Swap Left & Right Stages"
                  className="flex h-7 w-7 items-center justify-center rounded border border-[#243042] bg-[#141b24] text-slate-300 hover:border-[#00f0ff] hover:text-[#00f0ff]"
                >
                  <ArrowRightLeft className="h-3 w-3" />
                </button>

                <span className="font-mono text-[11px] text-slate-400">Right:</span>
                <select
                  value={compareRight}
                  onChange={(e) =>
                    setCompareStages(compareLeft, e.target.value as StageKey)
                  }
                  className="h-7 rounded border border-[#243042] bg-[#141b24] px-2 py-0.5 font-mono text-[11px] text-[#00f0ff] focus:outline-none focus:border-[#00f0ff]"
                >
                  <option value="cloudy">Cloudy</option>
                  <option value="baseline">Baseline</option>
                  <option value="sharpened">Sharpened</option>
                  <option value="final">Final</option>
                  <option value="target">Target</option>
                </select>
              </div>
            ) : (
              /* Segmented Stage Control */
              <div className="flex h-7 items-center gap-1 rounded border border-[#243042] bg-[#101620] p-0.5">
                {(['cloudy', 'baseline', 'sharpened', 'final', 'target'] as const).map(
                  (st) => (
                    <button
                      key={st}
                      onClick={() => setActiveStage(st)}
                      className={`h-full rounded px-2.5 font-mono text-[11px] capitalize transition ${
                        activeStage === st
                          ? 'border border-[#00f0ff]/50 bg-[#00f0ff]/20 font-bold text-[#00f0ff]'
                          : 'border border-transparent text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {st}
                    </button>
                  )
                )}
              </div>
            )}

            {/* Stage Label & Dimensions */}
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] text-slate-400">
                {isCompareMode
                  ? `${compareLeft.toUpperCase()} vs ${compareRight.toUpperCase()}`
                  : `${activeStage.toUpperCase()} — 512 × 512 px`}
              </span>
            </div>
          </div>

          {/* Visual Display Container (Edge-to-edge square, ZERO black bars) */}
          <div className="relative aspect-square w-full overflow-hidden bg-black">
            {isCompareMode ? (
              /* Compare Slider View */
              <ReactCompareSlider
                itemOne={
                  <div className="relative h-full w-full">
                    <img
                      src={getStageUrl(compareLeft)}
                      alt={compareLeft}
                      className="h-full w-full object-cover"
                    />
                    <div className="absolute left-2 top-2 rounded bg-black/75 px-2 py-0.5 font-mono text-[10px] font-semibold text-[#00f0ff] backdrop-blur-xs">
                      {compareLeft.toUpperCase()}
                    </div>
                  </div>
                }
                itemTwo={
                  <div className="relative h-full w-full">
                    <img
                      src={getStageUrl(compareRight)}
                      alt={compareRight}
                      className="h-full w-full object-cover"
                    />
                    <div className="absolute right-2 top-2 rounded bg-black/75 px-2 py-0.5 font-mono text-[10px] font-semibold text-[#00f0ff] backdrop-blur-xs">
                      {compareRight.toUpperCase()}
                    </div>
                  </div>
                }
                handle={
                  <ReactCompareSliderHandle
                    buttonStyle={{
                      backdropFilter: 'blur(4px)',
                      background: 'rgba(11, 15, 21, 0.85)',
                      border: '1px solid #00f0ff',
                      color: '#00f0ff',
                    }}
                    linesStyle={{ opacity: 0.7, color: '#00f0ff' }}
                  />
                }
                className="h-full w-full select-none"
              />
            ) : (
              /* Single Mode with Zoom/Pan */
              <TransformWrapper
                initialScale={1}
                minScale={1}
                maxScale={6}
                onTransform={(_, state) => setViewerScale(Math.max(1, state.scale))}
              >
                {({ zoomIn, zoomOut, resetTransform }) => (
                  <>
                    {/* Floating Zoom Controls */}
                    <div className="absolute bottom-3 right-3 z-20 flex items-center gap-1 rounded border border-[#243042] bg-[#0d1219]/90 p-1 shadow-lg backdrop-blur-xs">
                      <button
                        onClick={() => zoomIn(0.4)}
                        title="Zoom In"
                        className="rounded p-1 text-slate-300 hover:text-[#00f0ff]"
                      >
                        <ZoomIn className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => {
                          if (viewerScale <= 1.05) {
                            resetTransform();
                            setViewerScale(1);
                            return;
                          }
                          zoomOut(0.4);
                        }}
                        title="Zoom Out"
                        className="rounded p-1 text-slate-300 hover:text-[#00f0ff]"
                      >
                        <ZoomOut className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => {
                          resetTransform();
                          setViewerScale(1);
                        }}
                        title="Reset Zoom"
                        className="rounded p-1 text-slate-300 hover:text-[#00f0ff]"
                      >
                        <RotateCcw className="h-3.5 w-3.5" />
                      </button>
                      <span className="px-1 font-mono text-[10px] text-[#00f0ff]">
                        {Math.round(viewerScale * 100)}%
                      </span>
                    </div>

                    <TransformComponent
                      wrapperClass="!w-full !h-full"
                      contentClass="!w-full !h-full"
                    >
                      <img
                        src={getStageUrl(activeStage)}
                        alt={activeStage}
                        className={`h-full w-full object-contain ${
                          isZoomed ? 'pixelated' : ''
                        }`}
                      />
                    </TransformComponent>
                  </>
                )}
              </TransformWrapper>
            )}
          </div>
        </div>

        {/* Right Column (Metrics Panel): 50% (Height-aligned with viewer) */}
        <div className="flex w-full flex-col rounded border border-[#243042] bg-[#0c1017] p-3.5 sm:p-4">
          <div className="mb-2.5 flex items-center justify-between border-b border-[#243042] pb-2">
            <span className="font-display text-xs font-bold uppercase tracking-wider text-slate-200">
              Spectral & Spatial Metrics Telemetry
            </span>
            <span className="rounded bg-[#1a2330] px-2 py-0.5 font-mono text-[10px] text-[#00f0ff]">
              {isCompareMode ? 'Differential Analysis' : 'Direct Readout'}
            </span>
          </div>

          {/* Mode 1: Compare Mode Differential Table */}
          {isCompareMode ? (
            compareLeft === 'target' || compareRight === 'target' ? (
              <div className="flex flex-1 flex-col">
                <div className="mb-2 text-[11px] text-slate-400">
                  Comparing <span className="font-mono text-[#00f0ff]">{compareLeft}</span> vs{' '}
                  <span className="font-mono text-[#00f0ff]">{compareRight}</span>
                </div>
                <div className="flex flex-1 flex-col items-center justify-center p-6 text-center text-slate-400">
                  <h4 className="font-mono text-xs font-bold text-slate-200">
                    Ground Truth Optical Reference
                  </h4>
                  <p className="mt-1 font-mono text-[11px] text-slate-400">
                    Reference image, no metrics.
                  </p>
                  <p className="mt-2 text-[11px] text-slate-500">
                    All model stages (Cloudy, Baseline, Sharpened, Final) are mathematically evaluated against this target.
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="text-[11px] text-slate-400">
                  Comparing <span className="font-mono text-[#00f0ff]">{compareLeft}</span> vs{' '}
                  <span className="font-mono text-[#00f0ff]">{compareRight}</span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-[#243042] font-mono text-[10px] uppercase text-slate-500">
                        <th className="py-2">Metric</th>
                        <th className="py-2 font-mono text-center">{compareLeft}</th>
                        <th className="py-2 font-mono text-center">{compareRight}</th>
                        <th className="py-2 font-mono text-right">Delta</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#1e2736]">
                      {(['psnr', 'sam', 'edgeCorr', 'hfRetention'] as const).map(
                        (key) => {
                          const leftMetrics = getStageMetrics(compareLeft)!;
                          const rightMetrics = getStageMetrics(compareRight)!;
                          const leftVal = leftMetrics[key];
                          const rightVal = rightMetrics[key];
                          const delta = calculateDelta(rightVal, leftVal, key);

                          const isImproved = delta.isImproved;

                          return (
                            <tr key={key} className="font-mono">
                              <td className="py-2.5 text-slate-300">
                                <span title={METRIC_TOOLTIPS[key]}>
                                  {METRIC_LABELS[key]}
                                </span>
                              </td>
                              <td className="py-2.5 text-center text-slate-400 tabular-nums">
                                {leftVal}
                              </td>
                              <td className="py-2.5 text-center font-semibold text-slate-200 tabular-nums">
                                {rightVal}
                              </td>
                              <td
                                className={`py-2.5 text-right font-semibold tabular-nums ${
                                  isImproved ? 'text-emerald-400' : 'text-rose-400'
                                }`}
                              >
                                <span className="inline-flex items-center gap-1 justify-end">
                                  {delta.diffText}
                                  {delta.arrow === 'up' && (
                                    <TrendingUp className="h-3 w-3" />
                                  )}
                                  {delta.arrow === 'down' && (
                                    <TrendingDown className="h-3 w-3" />
                                  )}
                                </span>
                              </td>
                            </tr>
                          );
                        }
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )
          ) : /* Mode 2: Single Stage Mode */
          activeStage === 'target' ? (
            <div className="flex flex-1 flex-col">
              <div className="mb-2 text-[11px] text-slate-400">
                Active Stage: <span className="font-mono text-[#00f0ff]">target</span>
              </div>
              <div className="flex flex-1 flex-col items-center justify-center p-6 text-center text-slate-400">
                <h4 className="font-mono text-xs font-bold text-slate-200">
                  Ground Truth Optical Reference
                </h4>
                <p className="mt-1 font-mono text-[11px] text-slate-400">
                  Reference image, no metrics.
                </p>
                <p className="mt-2 text-[11px] text-slate-500">
                  All model stages (Cloudy, Baseline, Sharpened, Final) are mathematically evaluated against this target.
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-3.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-mono text-slate-400">Active Stage:</span>
                <span className="font-mono font-bold text-[#00f0ff]">
                  {stageDisplayNames[activeStage]}
                </span>
              </div>

              {/* Four Metric Cards (Tightly and fixed spaced) */}
              <div className="space-y-2.5">
                {(['psnr', 'sam', 'edgeCorr', 'hfRetention'] as const).map((key) => {
                  const stageMetrics = getStageMetrics(activeStage)!;
                  const cloudyMetrics = cachedResult.metrics.cloudy;
                  const baselineMetrics = cachedResult.metrics.baseline;

                  const curVal = stageMetrics[key];
                  const deltaVsCloudy = calculateDelta(curVal, cloudyMetrics[key], key);
                  const deltaVsBaseline = calculateDelta(
                    curVal,
                    baselineMetrics[key],
                    key
                  );

                  const isBest = bestStages[key] === activeStage;

                  return (
                    <div
                      key={key}
                      className={`rounded border p-2.5 transition ${
                        isBest
                          ? 'border-[#00f0ff]/40 bg-[#00f0ff]/5'
                          : 'border-[#243042] bg-[#101620]'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono text-xs font-semibold text-slate-200">
                            {METRIC_LABELS[key]}
                          </span>
                          <span
                            title={METRIC_TOOLTIPS[key]}
                            className="cursor-help text-slate-500 hover:text-slate-300"
                          >
                            <HelpCircle className="h-3 w-3" />
                          </span>
                          {isBest && (
                            <span className="rounded bg-[#00f0ff]/20 px-1 py-0.2 font-mono text-[9px] font-bold text-[#00f0ff]">
                              BEST
                            </span>
                          )}
                        </div>

                        {/* Main Metric Value */}
                        <span className="font-mono text-base font-bold text-slate-100 tabular-nums">
                          {curVal}
                        </span>
                      </div>

                      {/* Deltas vs Cloudy and vs Baseline */}
                      <div className="mt-2 flex items-center justify-between border-t border-[#1e2736] pt-1.5 font-mono text-[10px]">
                        <span className="text-slate-400">
                          vs Cloudy:{' '}
                          <span
                            className={`font-semibold tabular-nums ${
                              deltaVsCloudy.isImproved
                                ? 'text-emerald-400'
                                : 'text-rose-400'
                            }`}
                          >
                            {deltaVsCloudy.diffText}
                          </span>
                        </span>

                        {activeStage !== 'cloudy' && (
                          <span className="text-slate-400">
                            vs Baseline:{' '}
                            <span
                              className={`font-semibold tabular-nums ${
                                deltaVsBaseline.isImproved
                                  ? 'text-emerald-400'
                                  : 'text-rose-400'
                              }`}
                            >
                              {deltaVsBaseline.diffText}
                            </span>
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* (C) STAGE CARDS ROW: 4 METRIC CARDS + FINAL HERO + CLEAR TARGET */}
      <div className="border-t border-[#243042] pt-4">
        <div className="mb-3 flex items-center justify-between">
          <span className="font-display text-xs font-bold uppercase tracking-wider text-slate-300">
            Pipeline Progression & Evaluation
          </span>
          <span className="font-mono text-[10px] text-slate-500">
            Click any stage to inspect in viewer
          </span>
        </div>

        <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
          {/* 1. Cloudy Card */}
          <button
            onClick={() => {
              setActiveStage('cloudy');
              setCompareMode(false);
            }}
            className={`flex flex-col overflow-hidden rounded border text-left transition ${
              activeStage === 'cloudy' && !isCompareMode
                ? 'border-[#00f0ff] ring-1 ring-[#00f0ff]'
                : 'border-[#243042] bg-[#111722] hover:border-slate-600'
            }`}
          >
            <div className="relative aspect-video w-full overflow-hidden bg-black">
              <img
                src={currentSample.previews.cloudy}
                alt="Cloudy preview"
                className="h-full w-full object-cover"
              />
              <span className="absolute bottom-1 left-1 rounded bg-black/70 px-1 font-mono text-[8px] text-slate-400">
                Cloudy Input
              </span>
            </div>
            <div className="space-y-1 p-2 font-mono text-[10px]">
              <div className="flex justify-between">
                <span className="text-slate-500">PSNR:</span>
                <span className="font-semibold text-slate-300 tabular-nums">
                  {cachedResult.metrics.cloudy.psnr} dB
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">SAM:</span>
                <span className="font-semibold text-slate-300 tabular-nums">
                  {cachedResult.metrics.cloudy.sam}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Edge:</span>
                <span className="font-semibold text-slate-300 tabular-nums">
                  {cachedResult.metrics.cloudy.edgeCorr}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">HF Ret:</span>
                <span className="font-semibold text-slate-300 tabular-nums">
                  {cachedResult.metrics.cloudy.hfRetention}
                </span>
              </div>
            </div>
          </button>

          {/* 2. Baseline Card */}
          <button
            onClick={() => {
              setActiveStage('baseline');
              setCompareMode(false);
            }}
            className={`flex flex-col overflow-hidden rounded border text-left transition ${
              activeStage === 'baseline' && !isCompareMode
                ? 'border-[#00f0ff] ring-1 ring-[#00f0ff]'
                : 'border-[#243042] bg-[#111722] hover:border-slate-600'
            }`}
          >
            <div className="relative aspect-video w-full overflow-hidden bg-black">
              <img
                src={cachedResult.stages.baseline}
                alt="Baseline preview"
                className="h-full w-full object-cover"
              />
              <span className="absolute bottom-1 left-1 rounded bg-black/70 px-1 font-mono text-[8px] text-slate-400">
                Baseline
              </span>
            </div>
            <div className="space-y-1 p-2 font-mono text-[10px]">
              <div className="flex justify-between">
                <span className="text-slate-500">PSNR:</span>
                <span className="font-semibold text-slate-200 tabular-nums">
                  {cachedResult.metrics.baseline.psnr} dB
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">SAM:</span>
                <span className="font-semibold text-slate-200 tabular-nums">
                  {cachedResult.metrics.baseline.sam}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Edge:</span>
                <span className="font-semibold text-slate-200 tabular-nums">
                  {cachedResult.metrics.baseline.edgeCorr}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">HF Ret:</span>
                <span className="font-semibold text-slate-200 tabular-nums">
                  {cachedResult.metrics.baseline.hfRetention}
                </span>
              </div>
            </div>
          </button>

          {/* 3. Sharpened Card */}
          <button
            onClick={() => {
              setActiveStage('sharpened');
              setCompareMode(false);
            }}
            className={`flex flex-col overflow-hidden rounded border text-left transition ${
              activeStage === 'sharpened' && !isCompareMode
                ? 'border-[#00f0ff] ring-1 ring-[#00f0ff]'
                : 'border-[#243042] bg-[#111722] hover:border-slate-600'
            }`}
          >
            <div className="relative aspect-video w-full overflow-hidden bg-black">
              <img
                src={cachedResult.stages.sharpened}
                alt="Sharpened preview"
                className="h-full w-full object-cover"
              />
              <span className="absolute bottom-1 left-1 rounded bg-black/70 px-1 font-mono text-[8px] text-slate-400">
                Sharpened
              </span>
            </div>
            <div className="space-y-1 p-2 font-mono text-[10px]">
              {(['psnr', 'sam', 'edgeCorr', 'hfRetention'] as const).map((k) => {
                const val = cachedResult.metrics.sharpened[k];
                const deltaVsBase = calculateDelta(
                  val,
                  cachedResult.metrics.baseline[k],
                  k
                );
                return (
                  <div key={k} className="flex justify-between">
                    <span className="text-slate-500 uppercase">{k}:</span>
                    <span className="font-semibold text-slate-200 tabular-nums">
                      {val}{' '}
                      <span
                        className={`text-[9px] ${
                          deltaVsBase.isImproved
                            ? 'text-emerald-400'
                            : 'text-rose-400'
                        }`}
                      >
                        ({deltaVsBase.diffText})
                      </span>
                    </span>
                  </div>
                );
              })}
            </div>
          </button>

          {/* 4. FINAL HERO CARD (Visually larger hero with accent border) */}
          <button
            onClick={() => {
              setActiveStage('final');
              setCompareMode(false);
            }}
            className={`relative flex flex-col overflow-hidden rounded-md border text-left transition shadow-lg ${
              activeStage === 'final' && !isCompareMode
                ? 'border-[#00f0ff] bg-[#162436] shadow-[0_0_15px_rgba(0,240,255,0.35)] ring-2 ring-[#00f0ff]'
                : 'border-[#00f0ff]/60 bg-[#141d2a] hover:border-[#00f0ff]'
            }`}
          >
            {/* Hero Badge */}
            <div className="absolute right-1.5 top-1.5 z-10 flex items-center gap-1 rounded bg-[#00f0ff] px-1.5 py-0.2 font-mono text-[9px] font-bold text-black shadow-sm">
              <Award className="h-2.5 w-2.5" />
              HERO
            </div>

            <div className="relative aspect-video w-full overflow-hidden bg-black">
              <img
                src={cachedResult.stages.final}
                alt="Final synthesis"
                className="h-full w-full object-cover"
              />
              <span className="absolute bottom-1 left-1 rounded bg-black/80 px-1.5 py-0.2 font-mono text-[8px] font-bold text-[#00f0ff]">
                Final Output (PatchGAN)
              </span>
            </div>

            <div className="space-y-1 bg-[#101824] p-2 font-mono text-[10px]">
              {(['psnr', 'sam', 'edgeCorr', 'hfRetention'] as const).map((k) => {
                const val = cachedResult.metrics.final[k];
                const deltaVsBase = calculateDelta(
                  val,
                  cachedResult.metrics.baseline[k],
                  k
                );
                return (
                  <div key={k} className="flex justify-between">
                    <span className="text-slate-400 uppercase font-semibold">
                      {k}:
                    </span>
                    <span className="font-bold text-[#00f0ff] tabular-nums">
                      {val}{' '}
                      <span className="text-[9px] text-emerald-400">
                        ({deltaVsBase.diffText})
                      </span>
                    </span>
                  </div>
                );
              })}
            </div>
          </button>

          {/* 5. CLEAR TARGET REFERENCE (Plain thumbnail card with NO metrics) */}
          <button
            onClick={() => {
              setActiveStage('target');
              setCompareMode(false);
            }}
            className={`flex flex-col overflow-hidden rounded border text-left transition ${
              activeStage === 'target' && !isCompareMode
                ? 'border-[#00f0ff] ring-1 ring-[#00f0ff]'
                : 'border-slate-700 bg-[#0f141c] hover:border-slate-500'
            }`}
          >
            <div className="relative aspect-video w-full overflow-hidden bg-black">
              <img
                src={cachedResult.stages.target}
                alt="Clear target ground truth"
                className="h-full w-full object-cover"
              />
              <span className="absolute bottom-1 left-1 rounded bg-black/70 px-1 font-mono text-[8px] text-slate-400">
                Ground Truth
              </span>
            </div>
            <div className="flex flex-1 flex-col items-center justify-center p-2 text-center">
              <span className="font-mono text-[10px] font-semibold text-slate-300">
                Clear Target
              </span>
              <span className="mt-0.5 text-[9px] text-slate-500">
                Optical Ground Truth
              </span>
              <span className="mt-1 rounded bg-slate-800/80 px-1.5 py-0.2 font-mono text-[8px] text-slate-400">
                No Metrics (Ref)
              </span>
            </div>
          </button>
        </div>
      </div>
    </section>
  );
};
