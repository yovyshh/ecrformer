'use client';

import React, { useRef, useState, useCallback } from 'react';
import { useAppStore } from '@/lib/store';
import {
  TransformWrapper,
  TransformComponent,
  ReactZoomPanPinchRef,
} from 'react-zoom-pan-pinch';
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Sparkles,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Info,
} from 'lucide-react';

export const InspectSection: React.FC = () => {
  const {
    samples,
    selectedId,
    statusMap,
    inspectExpanded,
    selectSample,
    navigateSample,
    runRemovalForCurrent,
    setInspectExpanded,
  } = useAppStore();

  const currentSample = samples.find((s) => s.id === selectedId);
  const currentStatus = selectedId ? statusMap[selectedId] || 'idle' : 'idle';
  const isRunning = currentStatus === 'running';
  const isDone = currentStatus === 'done';
  const isError = currentStatus === 'error';

  // Refs for linked zoom/pan across 3 panels
  const cloudyRef = useRef<ReactZoomPanPinchRef>(null);
  const sarRef = useRef<ReactZoomPanPinchRef>(null);
  const maskRef = useRef<ReactZoomPanPinchRef>(null);
  const isSyncingRef = useRef(false);

  const [currentZoomScale, setCurrentZoomScale] = useState(1);
  const isZoomed = currentZoomScale > 1.05;

  const syncTransforms = useCallback(
    (
      sourceRef: ReactZoomPanPinchRef,
      state: { scale: number; positionX: number; positionY: number }
    ) => {
      if (isSyncingRef.current) return;
      isSyncingRef.current = true;

      const clampedScale = Math.max(1, state.scale);
      setCurrentZoomScale(clampedScale);

      const targets = [cloudyRef.current, sarRef.current, maskRef.current].filter(
        (ref) => ref && ref !== sourceRef
      );

      targets.forEach((target) => {
        if (target) {
          target.setTransform(state.positionX, state.positionY, clampedScale, 0);
        }
      });

      // Release sync lock
      requestAnimationFrame(() => {
        isSyncingRef.current = false;
      });
    },
    []
  );

  const handleZoomInAll = () => {
    cloudyRef.current?.zoomIn(0.3);
  };

  const handleZoomOutAll = () => {
    if (currentZoomScale <= 1.05) {
      handleResetZoomAll();
      return;
    }
    cloudyRef.current?.zoomOut(0.3);
  };

  const handleResetZoomAll = () => {
    cloudyRef.current?.resetTransform();
    sarRef.current?.resetTransform();
    maskRef.current?.resetTransform();
    setCurrentZoomScale(1);
  };

  if (!currentSample) {
    return (
      <div className="rounded border border-[#243042] bg-[#131923] p-6 text-center text-slate-400">
        No satellite scene selected.
      </div>
    );
  }

  const coverageBadgeClass =
    currentSample.cloudCoverage < 30
      ? 'border-emerald-500/40 bg-emerald-950/60 text-emerald-400'
      : currentSample.cloudCoverage <= 60
      ? 'border-amber-500/40 bg-amber-950/60 text-amber-400'
      : 'border-rose-500/40 bg-rose-950/60 text-rose-400';

  // COLLAPSED STRIP VIEW
  if (!inspectExpanded) {
    return (
      <div className="rounded border border-[#243042] bg-[#131923] px-4 py-3 shadow-md transition-all">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="font-mono text-xs font-semibold uppercase tracking-wider text-slate-400">
              1. Inspect Telemetry
            </span>
            <div className="h-3 w-px bg-slate-700" />
            <span className="font-mono text-xs font-medium text-[#00f0ff]">
              {currentSample.filename}
            </span>
            <span
              className={`rounded border px-1.5 py-0.5 font-mono text-[10px] font-semibold ${coverageBadgeClass}`}
            >
              Cloud: {currentSample.cloudCoverage}%
            </span>
          </div>

          <div className="flex items-center gap-2">
            {isDone && (
              <button
                onClick={() => runRemovalForCurrent()}
                disabled={isRunning}
                className="flex items-center gap-1.5 rounded border border-[#00f0ff]/40 bg-[#00f0ff]/10 px-2.5 py-1 font-mono text-xs font-semibold text-[#00f0ff] transition hover:bg-[#00f0ff]/20 disabled:opacity-50"
              >
                <RefreshCw className="h-3 w-3" />
                Re-run
              </button>
            )}

            <button
              onClick={() => setInspectExpanded(true)}
              className="flex items-center gap-1 rounded border border-[#243042] bg-[#18212e] px-2.5 py-1 text-xs text-slate-300 transition hover:border-slate-500 hover:text-white"
            >
              <span>Expand Panels</span>
              <ChevronDown className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // OPEN EXPANDED INSPECT CARD
  return (
    <section className="rounded border border-[#243042] bg-[#131923] p-4 shadow-xl sm:p-5">
      {/* Top Header Bar */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-[#243042] pb-3.5">
        <div className="flex items-center gap-3">
          <span className="rounded bg-[#1a2332] px-2 py-0.5 font-mono text-[11px] font-semibold uppercase tracking-wider text-[#00f0ff]">
            Stage 1: Pre-Inference Inspection
          </span>
          <h2 className="font-mono text-xs font-semibold text-slate-200 sm:text-sm">
            {currentSample.filename}
          </h2>
          <span
            className={`rounded border px-2 py-0.5 font-mono text-[10px] font-semibold ${coverageBadgeClass}`}
          >
            Coverage: {currentSample.cloudCoverage}%
          </span>
        </div>

        {/* Navigation & Collapse */}
        <div className="flex items-center gap-2">
          <div className="flex items-center rounded border border-[#243042] bg-[#161e2a] text-xs">
            <button
              onClick={() => navigateSample('prev')}
              title="Previous Scene (Left Arrow)"
              className="px-2 py-1 text-slate-300 transition hover:bg-[#202b3c] hover:text-white"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <div className="h-4 w-px bg-[#243042]" />
            <button
              onClick={() => navigateSample('next')}
              title="Next Scene (Right Arrow)"
              className="px-2 py-1 text-slate-300 transition hover:bg-[#202b3c] hover:text-white"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>

          {(isDone || isRunning) && (
            <button
              onClick={() => setInspectExpanded(false)}
              title="Collapse Inspection"
              className="flex items-center gap-1 rounded border border-[#243042] bg-[#161e2a] px-2 py-1 text-xs text-slate-400 hover:text-slate-200"
            >
              <ChevronUp className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Linked Zoom/Pan Toolbar */}
      <div className="mb-3.5 flex flex-wrap items-center justify-between gap-3 rounded bg-[#0f141c] px-3 py-2 text-xs text-slate-300">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[11px] text-slate-400">Linked Zoom/Pan:</span>
          <div className="flex items-center gap-1">
            <button
              onClick={handleZoomInAll}
              title="Zoom In All"
              className="rounded border border-[#243042] bg-[#161e2a] p-1 text-slate-300 hover:border-[#00f0ff]/50 hover:text-[#00f0ff]"
            >
              <ZoomIn className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={handleZoomOutAll}
              title="Zoom Out All"
              className="rounded border border-[#243042] bg-[#161e2a] p-1 text-slate-300 hover:border-[#00f0ff]/50 hover:text-[#00f0ff]"
            >
              <ZoomOut className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={handleResetZoomAll}
              title="Reset Zoom"
              className="rounded border border-[#243042] bg-[#161e2a] p-1 text-slate-300 hover:border-[#00f0ff]/50 hover:text-[#00f0ff]"
            >
              <RotateCcw className="h-3.5 w-3.5" />
            </button>
            <span className="ml-1 font-mono text-[10px] text-[#00f0ff]">
              {Math.round(currentZoomScale * 100)}%
            </span>
          </div>
        </div>
      </div>

      {/* Three Equal-Size Linked Panels */}
      <div className="grid grid-cols-1 gap-3.5 md:grid-cols-3">
        {/* Panel 1: Cloudy Preview */}
        <div className="flex flex-col rounded border border-[#243042] bg-[#0c1017]">
          <div className="flex items-center justify-between border-b border-[#243042] px-3 py-1.5 text-[11px]">
            <span className="font-mono font-medium text-slate-200">
              Cloudy Optical (S2-RGB)
            </span>
            <span className="font-mono text-[10px] text-slate-400">512 × 512 px</span>
          </div>
          <div className="relative aspect-square w-full overflow-hidden bg-black">
            <TransformWrapper
              ref={cloudyRef}
              onTransform={(ref, state) => syncTransforms(ref, state)}
              initialScale={1}
              minScale={1}
              maxScale={6}
            >
              <TransformComponent
                wrapperClass="!w-full !h-full"
                contentClass="!w-full !h-full"
              >
                <div className="relative h-full w-full">
                  <img
                    src={currentSample.previews.cloudy}
                    alt={`Cloudy scene ${currentSample.filename}`}
                    className={`h-full w-full object-contain ${
                      isZoomed ? 'pixelated' : ''
                    }`}
                  />
                </div>
              </TransformComponent>
            </TransformWrapper>
          </div>
          <div className="border-t border-[#1e2736] px-3 py-1 text-[10px] text-slate-400">
            Sentinel-2 Top-of-Atmosphere Reflectance
          </div>
        </div>

        {/* Panel 2: SAR Preview */}
        <div className="flex flex-col rounded border border-[#243042] bg-[#0c1017]">
          <div className="flex items-center justify-between border-b border-[#243042] px-3 py-1.5 text-[11px]">
            <span className="font-mono font-medium text-slate-200">
              SAR Backscatter (S1-C-Band)
            </span>
            <span className="font-mono text-[10px] text-slate-400">512 × 512 px</span>
          </div>
          <div className="relative aspect-square w-full overflow-hidden bg-black">
            <TransformWrapper
              ref={sarRef}
              onTransform={(ref, state) => syncTransforms(ref, state)}
              initialScale={1}
              minScale={1}
              maxScale={6}
            >
              <TransformComponent
                wrapperClass="!w-full !h-full"
                contentClass="!w-full !h-full"
              >
                <img
                  src={currentSample.previews.sar}
                  alt={`SAR backscatter ${currentSample.filename}`}
                  className={`h-full w-full object-contain filter grayscale ${
                    isZoomed ? 'pixelated' : ''
                  }`}
                />
              </TransformComponent>
            </TransformWrapper>
          </div>
          <div className="flex items-center gap-1 border-t border-[#1e2736] px-3 py-1 text-[10px] text-[#00f0ff]">
            <Info className="h-3 w-3 shrink-0" />
            <span>SAR sees through clouds (microwave penetrate cloud moisture)</span>
          </div>
        </div>

        {/* Panel 3: Cloud Mask Preview */}
        <div className="flex flex-col rounded border border-[#243042] bg-[#0c1017]">
          <div className="flex items-center justify-between border-b border-[#243042] px-3 py-1.5 text-[11px]">
            <span className="font-mono font-medium text-slate-200">
              Cloud Mask Stand-In
            </span>
            <span className="font-mono text-[10px] text-slate-400">512 × 512 px</span>
          </div>
          <div className="relative aspect-square w-full overflow-hidden bg-black">
            <TransformWrapper
              ref={maskRef}
              onTransform={(ref, state) => syncTransforms(ref, state)}
              initialScale={1}
              minScale={1}
              maxScale={6}
            >
              <TransformComponent
                wrapperClass="!w-full !h-full"
                contentClass="!w-full !h-full"
              >
                <img
                  src={currentSample.previews.mask}
                  alt={`Cloud Mask ${currentSample.filename}`}
                  className={`h-full w-full object-contain ${
                    isZoomed ? 'pixelated' : ''
                  }`}
                />
              </TransformComponent>
            </TransformWrapper>
          </div>
          <div className="border-t border-[#1e2736] px-3 py-1 text-[10px] text-slate-400">
            Legend: <span className="font-mono text-slate-200">white = cloud</span>, black = clear surface
          </div>
        </div>
      </div>

      {/* Action Area at the bottom of the card (not sticky) */}
      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-[#243042] pt-4">
        <div className="text-xs text-slate-400">
          <span className="font-mono text-slate-300">Target Pipeline:</span> ECRformer Edge-Conditioned Cross-Attention + PatchGAN Discriminator
        </div>

        <button
          onClick={() => runRemovalForCurrent()}
          disabled={isRunning}
          className={`flex items-center gap-2 rounded px-5 py-2.5 font-mono text-xs font-bold uppercase tracking-wider transition-all ${
            isRunning
              ? 'cursor-not-allowed border border-slate-700 bg-slate-800 text-slate-500'
              : 'border border-[#00f0ff] bg-[#00f0ff] text-black shadow-[0_0_15px_rgba(0,240,255,0.35)] hover:bg-[#38f8ff] hover:shadow-[0_0_20px_rgba(0,240,255,0.6)] active:scale-98'
          }`}
        >
          <Sparkles className={`h-4 w-4 ${isRunning ? 'animate-spin' : ''}`} />
          <span>{isRunning ? 'Executing Removal Pipeline...' : 'Remove Clouds'}</span>
        </button>
      </div>
    </section>
  );
};
