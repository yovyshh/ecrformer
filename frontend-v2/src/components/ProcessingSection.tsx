'use client';

import React from 'react';
import { useAppStore } from '@/lib/store';
import { motion } from 'framer-motion';
import {
  Cpu,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
  Sparkles,
  Layers,
  Zap,
} from 'lucide-react';

export const ProcessingSection: React.FC = () => {
  const {
    selectedId,
    statusMap,
    processingDurationMap,
    activeStepIndex,
    errorMessage,
    retryRemoval,
  } = useAppStore();

  const currentStatus = selectedId ? statusMap[selectedId] || 'idle' : 'idle';
  const duration = selectedId ? processingDurationMap[selectedId] : null;

  const steps = [
    {
      id: 'baseline',
      name: 'Baseline Reconstruction',
      desc: 'ECRformer spatial-frequency fusion & SAR edge priors',
      icon: Layers,
    },
    {
      id: 'sharpened',
      name: 'Texture Sharpening',
      desc: 'Wavelet-guided high-frequency detail synthesis',
      icon: Zap,
    },
    {
      id: 'final',
      name: 'Adversarial Refinement',
      desc: 'PatchGAN discriminator scoring & spectral correction',
      icon: Sparkles,
    },
  ];

  // 1. COLLAPSED DONE STATE
  if (currentStatus === 'done') {
    return (
      <div className="rounded border border-[#243042] bg-[#101620] px-4 py-2.5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2.5">
            <div className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-950 text-emerald-400 ring-1 ring-emerald-500/40">
              <CheckCircle2 className="h-3.5 w-3.5" />
            </div>
            <span className="font-mono font-semibold uppercase tracking-wider text-slate-300">
              2. Pipeline Telemetry
            </span>
            <div className="h-3 w-px bg-slate-700" />
            <span className="font-mono text-emerald-400">
              Completed in {duration ?? '3.8'} s
            </span>
          </div>

          <div className="flex items-center gap-2 font-mono text-[11px] text-slate-400">
            <span className="flex items-center gap-1 text-slate-300">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              ECRformer + PatchGAN
            </span>
            <span>•</span>
            <span>All 3 synthesis passes converged</span>
          </div>
        </div>
      </div>
    );
  }

  // 2. ERROR STATE
  if (currentStatus === 'error') {
    return (
      <section className="rounded border border-rose-500/40 bg-rose-950/20 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded bg-rose-900/50 text-rose-400">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-mono text-xs font-bold text-rose-300">
                Pipeline Inference Error
              </h3>
              <p className="text-xs text-rose-200/80">
                {errorMessage || 'Model inference failed or timed out during patch generation.'}
              </p>
            </div>
          </div>

          <button
            onClick={() => retryRemoval()}
            className="flex items-center gap-1.5 rounded border border-rose-500/50 bg-rose-900/40 px-3 py-1.5 font-mono text-xs font-semibold text-rose-200 transition hover:bg-rose-900/60"
          >
            <RotateCw className="h-3.5 w-3.5" />
            Retry Pipeline
          </button>
        </div>
      </section>
    );
  }

  // 3. WAITING STATE (idle)
  // Must NOT collapse or hide so the page doesn't jump!
  if (currentStatus === 'idle') {
    return (
      <section className="relative rounded border border-dashed border-[#243042] bg-[#0e131b]/60 p-4 text-center sm:p-5">
        <div className="mb-3 flex items-center justify-between text-xs text-slate-500">
          <span className="font-mono uppercase tracking-wider">
            Stage 2: Model Inference Pipeline
          </span>
          <span className="font-mono text-[10px]">Standby Mode</span>
        </div>

        {/* 3 Dimmed Skeleton Steps */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {steps.map((st, i) => (
            <div
              key={st.id}
              className="flex flex-col items-center rounded border border-[#1e2634] bg-[#121822]/40 p-4 opacity-40"
            >
              <div className="mb-2 flex h-8 w-8 items-center justify-center rounded-full border border-slate-700 bg-slate-800 text-slate-500 font-mono text-xs">
                {i + 1}
              </div>
              <span className="font-mono text-xs font-medium text-slate-400">
                {st.name}
              </span>
              <p className="mt-1 text-[11px] text-slate-600">{st.desc}</p>
              <div className="mt-3 h-1.5 w-16 rounded bg-slate-800/80" />
            </div>
          ))}
        </div>

        <div className="mt-4 flex items-center justify-center gap-2 font-mono text-xs text-slate-400">
          <Cpu className="h-3.5 w-3.5 text-slate-500" />
          <span>Run cloud removal to see processing telemetry & stages</span>
        </div>
      </section>
    );
  }

  // 4. RUNNING ACTIVE STATE
  return (
    <section className="rounded border border-[#00f0ff]/40 bg-[#131923] p-4 shadow-[0_0_20px_rgba(0,240,255,0.1)] sm:p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-[#243042] pb-3">
        <div className="flex items-center gap-2">
          <div className="flex h-5 w-5 items-center justify-center rounded bg-[#00f0ff]/10 text-[#00f0ff]">
            <Cpu className="h-3.5 w-3.5 animate-spin" />
          </div>
          <span className="font-mono text-xs font-bold uppercase tracking-wider text-[#00f0ff]">
            Stage 2: Processing Neural Pipeline
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex h-2 w-2 animate-ping rounded-full bg-[#00f0ff]" />
          <span className="font-mono text-[11px] text-slate-300">
            Step {activeStepIndex + 1} of 3 in progress
          </span>
        </div>
      </div>

      {/* Horizontal Animated Stepper */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {steps.map((step, idx) => {
          const isCurrent = idx === activeStepIndex;
          const isDoneStep = idx < activeStepIndex;
          const isPending = idx > activeStepIndex;
          const IconComponent = step.icon;

          return (
            <motion.div
              key={step.id}
              initial={{ opacity: 0.8 }}
              animate={{ opacity: 1 }}
              className={`relative flex flex-col rounded border p-4 transition-all ${
                isCurrent
                  ? 'border-[#00f0ff] bg-[#162232] shadow-[0_0_12px_rgba(0,240,255,0.25)] ring-1 ring-[#00f0ff]/60'
                  : isDoneStep
                  ? 'border-emerald-500/40 bg-emerald-950/20'
                  : 'border-[#243042] bg-[#10151d] opacity-50'
              }`}
            >
              {/* Step indicator header */}
              <div className="flex items-center justify-between">
                <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Pass 0{idx + 1}
                </span>
                {isDoneStep ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                ) : isCurrent ? (
                  <span className="flex h-2.5 w-2.5">
                    <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-[#00f0ff]" />
                  </span>
                ) : (
                  <span className="font-mono text-[10px] text-slate-600">Pending</span>
                )}
              </div>

              {/* Title & Icon */}
              <div className="mt-2.5 flex items-center gap-2">
                <IconComponent
                  className={`h-4 w-4 ${
                    isCurrent
                      ? 'text-[#00f0ff]'
                      : isDoneStep
                      ? 'text-emerald-400'
                      : 'text-slate-600'
                  }`}
                />
                <h4 className="font-mono text-xs font-semibold text-slate-200">
                  {step.name}
                </h4>
              </div>

              <p className="mt-1 text-[11px] text-slate-400">{step.desc}</p>

              {/* Animated progress skeleton bar */}
              <div className="mt-3.5 h-1.5 w-full overflow-hidden rounded-full bg-[#1b2432]">
                {isDoneStep && <div className="h-full w-full bg-emerald-400" />}
                {isCurrent && (
                  <motion.div
                    className="h-full bg-[#00f0ff]"
                    initial={{ width: '0%' }}
                    animate={{ width: '100%' }}
                    transition={{
                      duration: 1.1,
                      ease: 'easeOut',
                    }}
                  />
                )}
                {isPending && <div className="h-full w-0 bg-slate-700" />}
              </div>
            </motion.div>
          );
        })}
      </div>
    </section>
  );
};
