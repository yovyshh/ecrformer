"use client";

import React, { useState, useRef, useCallback, useEffect } from "react";
import Image from "next/image";
import { SlidersHorizontal, Eye, Maximize2, Sparkles, Layers } from "lucide-react";

interface ImageComparisonSliderProps {
  leftImage: string;
  rightImage: string;
  leftLabel: string;
  rightLabel: string;
  sceneTitle: string;
  sceneName: string;
  cloudPct: number;
}

export function ImageComparisonSlider({
  leftImage,
  rightImage,
  leftLabel,
  rightLabel,
  sceneTitle,
  sceneName,
  cloudPct,
}: ImageComparisonSliderProps) {
  const [sliderPos, setSliderPos] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMove = useCallback(
    (clientX: number) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const x = clientX - rect.left;
      const pct = Math.max(0, Math.min(100, (x / rect.width) * 100));
      setSliderPos(pct);
    },
    []
  );

  const handleTouchMove = useCallback(
    (e: TouchEvent) => {
      if (!isDragging) return;
      handleMove(e.touches[0].clientX);
    },
    [isDragging, handleMove]
  );

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isDragging) return;
      handleMove(e.clientX);
    },
    [isDragging, handleMove]
  );

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
      window.addEventListener("touchmove", handleTouchMove);
      window.addEventListener("touchend", handleMouseUp);
    }
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
      window.removeEventListener("touchmove", handleTouchMove);
      window.removeEventListener("touchend", handleMouseUp);
    };
  }, [isDragging, handleMouseMove, handleMouseUp, handleTouchMove]);

  return (
    <div className="w-full flex flex-col items-center">
      {/* Viewer Header */}
      <div className="w-full flex flex-wrap items-center justify-between gap-3 mb-3 px-1">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-slate-100">{sceneTitle}</h3>
            <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              {cloudPct.toFixed(1)}% Cloud
            </span>
          </div>
          <p className="text-xs font-mono text-slate-400 mt-0.5">{sceneName}</p>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
          <SlidersHorizontal className="w-3.5 h-3.5 text-cyan-400" />
          <span>Drag slider to reveal ground under cloud</span>
        </div>
      </div>

      {/* Main Interactive Split View Container */}
      <div
        ref={containerRef}
        className="relative w-full aspect-square max-w-[620px] rounded-2xl overflow-hidden border-2 border-slate-800 shadow-2xl shadow-cyan-950/20 cursor-ew-resize select-none bg-slate-950 group"
        onMouseDown={(e) => {
          setIsDragging(true);
          handleMove(e.clientX);
        }}
        onTouchStart={(e) => {
          setIsDragging(true);
          handleMove(e.touches[0].clientX);
        }}
      >
        {/* Right Base Image (Clear Declouded Output) */}
        <div className="absolute inset-0 w-full h-full">
          <img
            src={rightImage}
            alt={rightLabel}
            className="w-full h-full object-cover select-none pointer-events-none"
          />
          {/* Label Badge Right */}
          <div className="absolute bottom-4 right-4 z-10 px-3 py-1.5 rounded-lg bg-emerald-950/80 backdrop-blur-md border border-emerald-500/40 text-emerald-300 text-xs font-bold tracking-wide shadow-lg flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
            {rightLabel}
          </div>
        </div>

        {/* Left Clipped Image (Original Cloudy Optical) */}
        <div
          className="absolute inset-0 w-full h-full overflow-hidden"
          style={{ clipPath: `inset(0 ${100 - sliderPos}% 0 0)` }}
        >
          <img
            src={leftImage}
            alt={leftLabel}
            className="w-full h-full object-cover select-none pointer-events-none"
          />
          {/* Label Badge Left */}
          <div className="absolute bottom-4 left-4 z-10 px-3 py-1.5 rounded-lg bg-slate-950/80 backdrop-blur-md border border-slate-700/60 text-slate-300 text-xs font-bold tracking-wide shadow-lg flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-slate-400" />
            {leftLabel}
          </div>
        </div>

        {/* Vertical Split Divider Line */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-cyan-400 z-20 shadow-[0_0_12px_rgba(34,211,238,0.8)]"
          style={{ left: `${sliderPos}%` }}
        >
          {/* Draggable Circular Knob */}
          <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-9 h-9 rounded-full bg-slate-900 border-2 border-cyan-400 flex items-center justify-center shadow-xl shadow-cyan-500/30 text-cyan-300 transition-transform active:scale-95 group-hover:scale-105">
            <div className="flex items-center gap-0.5">
              <span className="text-[10px] leading-none">◀</span>
              <span className="text-[10px] leading-none">▶</span>
            </div>
          </div>
        </div>

        {/* Resolution Watermark */}
        <div className="absolute top-3 right-3 z-10 px-2 py-1 rounded bg-black/60 backdrop-blur-sm text-[11px] font-mono text-slate-400 border border-slate-800">
          256 × 256 px · 10m/px
        </div>
      </div>

      {/* Preset View Switcher Bar */}
      <div className="w-full max-w-[620px] flex items-center justify-between gap-2 mt-3 text-xs text-slate-400">
        <button
          onClick={() => setSliderPos(0)}
          className="hover:text-cyan-400 transition-colors py-1 px-2 rounded hover:bg-slate-900/60"
        >
          Show 100% Declouded
        </button>
        <button
          onClick={() => setSliderPos(50)}
          className="hover:text-cyan-400 transition-colors py-1 px-2 rounded bg-slate-900 border border-slate-800 font-medium text-slate-300"
        >
          Center Split (50/50)
        </button>
        <button
          onClick={() => setSliderPos(100)}
          className="hover:text-cyan-400 transition-colors py-1 px-2 rounded hover:bg-slate-900/60"
        >
          Show 100% Cloudy Input
        </button>
      </div>
    </div>
  );
}
