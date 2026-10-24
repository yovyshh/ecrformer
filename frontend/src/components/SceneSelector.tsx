"use client";

import React from "react";
import { SceneData } from "@/data/scenes";
import { Cloud, MapPin, Check } from "lucide-react";

interface SceneSelectorProps {
  scenes: SceneData[];
  selectedSceneId: string;
  onSelectScene: (id: string) => void;
}

export function SceneSelector({
  scenes,
  selectedSceneId,
  onSelectScene,
}: SceneSelectorProps) {
  return (
    <div className="w-full flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <MapPin className="w-3.5 h-3.5 text-cyan-400" />
          Preloaded Validation Scenes (SEN12MS-CR Fall Subset)
        </h4>
        <span className="text-[11px] text-slate-500 font-mono">
          6 Representative Strata
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
        {scenes.map((scene) => {
          const isSelected = scene.id === selectedSceneId;
          return (
            <button
              key={scene.id}
              onClick={() => onSelectScene(scene.id)}
              className={`flex flex-col text-left p-2.5 rounded-xl border transition-all relative overflow-hidden group ${
                isSelected
                  ? "bg-cyan-950/30 border-cyan-400 shadow-md shadow-cyan-950/30 ring-1 ring-cyan-400"
                  : "bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900"
              }`}
            >
              {/* Selected Check Pill */}
              {isSelected && (
                <div className="absolute top-2 right-2 w-4 h-4 rounded-full bg-cyan-400 text-slate-950 flex items-center justify-center z-10 shadow-sm">
                  <Check className="w-2.5 h-2.5 stroke-[3]" />
                </div>
              )}

              {/* Thumbnail Pair */}
              <div className="grid grid-cols-2 gap-1 mb-2 aspect-[2/1] rounded-lg overflow-hidden border border-slate-800 bg-slate-950">
                <div className="relative w-full h-full">
                  <img
                    src={scene.paths.cloudy}
                    alt="Cloudy preview"
                    className="w-full h-full object-cover"
                  />
                  <span className="absolute bottom-0 left-0 bg-black/70 text-[8px] text-slate-300 px-1 font-mono">
                    Cloud
                  </span>
                </div>
                <div className="relative w-full h-full">
                  <img
                    src={scene.paths.blended}
                    alt="Declouded preview"
                    className="w-full h-full object-cover"
                  />
                  <span className="absolute bottom-0 right-0 bg-emerald-950/80 text-[8px] text-emerald-300 px-1 font-mono font-bold">
                    Clear
                  </span>
                </div>
              </div>

              {/* Scene Metadata */}
              <span className="text-[10px] font-semibold uppercase tracking-wider text-cyan-400 truncate">
                {scene.category}
              </span>
              <span className="text-xs font-bold text-slate-200 truncate mt-0.5">
                {scene.title}
              </span>

              <div className="flex items-center justify-between gap-1 mt-1.5 pt-1.5 border-t border-slate-800/80 text-[11px]">
                <span className="flex items-center gap-1 text-slate-400">
                  <Cloud className="w-3 h-3 text-slate-400" />
                  {scene.cloudPct.toFixed(0)}%
                </span>
                <span className="font-mono text-emerald-400 font-bold">
                  {scene.metrics.blended.psnr} dB
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
