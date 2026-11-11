'use client';

import React from 'react';
import { useAppStore } from '@/lib/store';
import { AlertTriangle, RotateCw } from 'lucide-react';

export const ProcessingSection: React.FC = () => {
  const {
    samples,
    selectedId,
    statusMap,
    errorMessage,
    retryRemoval,
  } = useAppStore();

  const currentSample = samples.find((s) => s.id === selectedId);
  const currentStatus = selectedId ? statusMap[selectedId] || 'idle' : 'idle';

  // 1. ERROR STATE
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

  // 2. RUNNING STATE (CSS-only animation)
  if (currentStatus === 'running') {
    return (
      <section className="rounded border border-[#243042] bg-[#0e131b] p-6 text-center sm:p-8">
        <style>{`
          @keyframes light-sweep {
            0% {
              transform: translateX(-120%) skewX(-20deg);
            }
            100% {
              transform: translateX(220%) skewX(-20deg);
            }
          }
          @keyframes pulse-gentle {
            0%, 100% {
              opacity: 0.88;
            }
            50% {
              opacity: 1;
            }
          }
          .animate-pulse-gentle {
            animation: pulse-gentle 2.4s ease-in-out infinite;
          }
          .animate-light-sweep {
            animation: light-sweep 2s ease-in-out infinite;
          }
          @media (prefers-reduced-motion: reduce) {
            .animate-pulse-gentle,
            .animate-light-sweep {
              animation: none !important;
              transform: none !important;
              opacity: 1 !important;
            }
          }
        `}</style>

        <div className="relative mx-auto aspect-square w-56 sm:w-64 overflow-hidden rounded-lg border border-[#243042] bg-black shadow-lg">
          {currentSample?.previews?.cloudy ? (
            <img
              src={currentSample.previews.cloudy}
              alt={`Cloudy preview for ${currentSample.filename}`}
              className="h-full w-full object-contain animate-pulse-gentle"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center bg-slate-900 text-xs text-slate-500 font-mono">
              Cloudy Preview
            </div>
          )}

          {/* Light sweep highlight overlay */}
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 overflow-hidden"
          >
            <div
              className="animate-light-sweep h-full w-full"
              style={{
                background:
                  'linear-gradient(105deg, transparent 20%, rgba(255, 255, 255, 0.25) 50%, transparent 80%)',
              }}
            />
          </div>
        </div>

        <p className="mt-4 font-mono text-xs sm:text-sm font-medium text-slate-300">
          Running the model...
        </p>
      </section>
    );
  }

  // 3. IDLE / DONE (Transition straight to results)
  return null;
};
