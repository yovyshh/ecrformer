"use client";

import React, { useState } from "react";
import { SceneData } from "@/data/scenes";
import { Info, Sparkles, CheckCircle2, ShieldCheck, Zap } from "lucide-react";

interface StageProgressionMatrixProps {
  scene: SceneData;
}

export function StageProgressionMatrix({ scene }: StageProgressionMatrixProps) {
  const [activeStage, setActiveStage] = useState<string>("blended");

  const stages = [
    {
      id: "cloudy",
      title: "1. Cloudy Input",
      subtitle: "Sentinel-2 Optical",
      tag: `${scene.cloudPct.toFixed(1)}% Cloud`,
      tagColor: "bg-amber-500/10 text-amber-400 border-amber-500/30",
      image: scene.paths.cloudy,
      desc: "Corrupted optical reflectance in 4 bands (B04, B03, B02, B08). Complete information blackout under dense cumulus clouds.",
    },
    {
      id: "sar",
      title: "2. Sentinel-1 SAR",
      subtitle: "Radar (VV/VH Backscatter)",
      tag: "Cloud-Penetrating",
      tagColor: "bg-teal-500/10 text-teal-400 border-teal-500/30",
      image: scene.paths.sar,
      desc: "Cloud-penetrating active microwave radar. VV measures ground roughness; VH volume-scatters inside vegetation canopies.",
      insetMask: scene.paths.mask,
    },
    {
      id: "pregan",
      title: "3. Pre-GAN Baseline",
      subtitle: "ECRformer (L1+SSIM)",
      tag: `PSNR ${scene.metrics.pregan.psnr} dB`,
      tagColor: "bg-orange-500/10 text-orange-400 border-orange-500/30",
      image: scene.paths.pregan,
      detail: `${scene.metrics.pregan.detailRetention}% Detail`,
      desc: "Trained strictly on L1 + SSIM losses. Suffers from conditional-mean averaging, creating over-smoothed blurry terrain inside clouds.",
    },
    {
      id: "patchgan",
      title: "4. PatchGAN Direct",
      subtitle: "Generator Raw P_dir",
      tag: `PSNR ${scene.metrics.patchgan.psnr} dB`,
      tagColor: "bg-blue-500/10 text-blue-400 border-blue-500/30",
      image: scene.paths.patchgan,
      detail: `${scene.metrics.patchgan.detailRetention}% Detail`,
      desc: "Adversarially sharpened by our 11-channel PatchGAN critic. High-frequency roads, crop boundaries, and forest textures restored.",
    },
    {
      id: "blended",
      title: "5. Final Blended",
      subtitle: "Harmonized Soft-Mask",
      tag: `PSNR ${scene.metrics.blended.psnr} dB`,
      tagColor: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30 font-bold",
      image: scene.paths.blended,
      detail: `${scene.metrics.blended.detailRetention}% Detail`,
      desc: "Multi-Band Laplacian preservation: keeps 100% authentic clear sky pixels with zero cloud-fringe or shadow seam artifacts.",
    },
    {
      id: "clear",
      title: "Ground Truth",
      subtitle: "Cloud-Free Reference Target",
      tag: "100% Clear Reference",
      tagColor: "bg-indigo-500/10 text-indigo-400 border-indigo-500/30",
      image: scene.paths.clear,
      desc: "Temporally co-registered cloud-free acquisition from SEN12MS-CR used strictly as ground-truth evaluation benchmark.",
    },
  ];

  return (
    <div className="w-full flex flex-col gap-4">
      {/* Section Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Zap className="w-4 h-4 text-cyan-400" />
            Complete Multi-Stage Reconstruction Progression
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Compare each step of the pipeline on {scene.name} (Native 256×256 Scene)
          </p>
        </div>

        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-400"></span>
          <span>Click any stage card to focus</span>
        </div>
      </div>

      {/* Grid of 6 Progression Stages */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {stages.map((st) => {
          const isSelected = activeStage === st.id;
          return (
            <div
              key={st.id}
              onClick={() => setActiveStage(st.id)}
              className={`flex flex-col rounded-xl overflow-hidden border transition-all cursor-pointer bg-slate-900/60 hover:bg-slate-900 ${
                isSelected
                  ? "border-cyan-400 shadow-lg shadow-cyan-950/40 ring-1 ring-cyan-400"
                  : "border-slate-800 hover:border-slate-700"
              }`}
            >
              {/* Card Header */}
              <div className="p-2.5 pb-2 border-b border-slate-800/80">
                <div className="flex items-center justify-between gap-1 mb-1">
                  <span className="text-xs font-bold text-slate-200 truncate">
                    {st.title}
                  </span>
                  <span
                    className={`px-1.5 py-0.5 text-[10px] font-medium rounded border ${st.tagColor}`}
                  >
                    {st.tag}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 truncate">{st.subtitle}</p>
              </div>

              {/* Image Preview */}
              <div className="relative aspect-square w-full bg-slate-950 overflow-hidden">
                <img
                  src={st.image}
                  alt={st.title}
                  className="w-full h-full object-cover transition-transform duration-300 hover:scale-105"
                />

                {/* Optional Mask Inset for SAR */}
                {st.insetMask && (
                  <div className="absolute bottom-1.5 right-1.5 w-1/3 aspect-square rounded border border-red-500/80 overflow-hidden shadow-md">
                    <img
                      src={st.insetMask}
                      alt="Cloud Mask"
                      className="w-full h-full object-cover"
                    />
                    <span className="absolute bottom-0 right-0 bg-red-600 text-white text-[8px] font-bold px-1">
                      Mask
                    </span>
                  </div>
                )}

                {/* Detail Retention Pill */}
                {st.detail && (
                  <div className="absolute top-1.5 left-1.5 px-1.5 py-0.5 rounded bg-black/75 backdrop-blur-sm text-[10px] font-mono text-cyan-300 border border-slate-800">
                    {st.detail}
                  </div>
                )}
              </div>

              {/* Brief Explanatory Footer */}
              <div className="p-2 text-[11px] text-slate-400 leading-tight">
                {st.desc}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
