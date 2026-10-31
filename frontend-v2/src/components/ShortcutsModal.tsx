'use client';

import React from 'react';
import { X, Keyboard } from 'lucide-react';

interface ShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ShortcutsModal: React.FC<ShortcutsModalProps> = ({
  isOpen,
  onClose,
}) => {
  if (!isOpen) return null;

  const shortcuts = [
    { key: '← / →', desc: 'Navigate to previous / next satellite scene' },
    { key: 'Enter', desc: 'Trigger SAR-guided cloud removal pipeline' },
    { key: '1 – 5', desc: 'Switch stage view: 1=Cloudy, 2=Baseline, 3=Sharpened, 4=Final, 5=Target' },
    { key: 'Space', desc: 'Toggle compare mode slider' },
    { key: 'Esc', desc: 'Close dialogs and modals' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-xs">
      <div className="w-full max-w-md rounded border border-[#243042] bg-[#121822] p-5 shadow-2xl">
        <div className="flex items-center justify-between border-b border-[#243042] pb-3">
          <div className="flex items-center gap-2">
            <Keyboard className="h-4 w-4 text-[#00f0ff]" />
            <h3 className="font-display text-sm font-bold uppercase tracking-wider text-slate-100">
              Telemetry Keyboard Shortcuts
            </h3>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 text-slate-400 hover:bg-[#1c2432] hover:text-white"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-4 space-y-2.5">
          {shortcuts.map((sc) => (
            <div
              key={sc.key}
              className="flex items-center justify-between rounded border border-[#1e2736] bg-[#0c1017] px-3 py-2 text-xs"
            >
              <span className="text-slate-300">{sc.desc}</span>
              <kbd className="rounded border border-slate-700 bg-[#19212d] px-2 py-0.5 font-mono text-[11px] font-bold text-[#00f0ff]">
                {sc.key}
              </kbd>
            </div>
          ))}
        </div>

        <div className="mt-5 text-right">
          <button
            onClick={onClose}
            className="rounded border border-[#243042] bg-[#192230] px-3.5 py-1.5 font-mono text-xs text-slate-200 hover:border-[#00f0ff]/50 hover:text-white"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );
};
