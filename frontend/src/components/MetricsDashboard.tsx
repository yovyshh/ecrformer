"use client";

import React from "react";
import { SceneData } from "@/data/scenes";
import { BarChart3, TrendingUp, Sparkles, Shield, Compass, Activity } from "lucide-react";

interface MetricsDashboardProps {
  scene: SceneData;
  allScenes: SceneData[];
}

export function MetricsDashboard({ scene, allScenes }: MetricsDashboardProps) {
  const m = scene.metrics;

  return (
    <div className="w-full flex flex-col gap-6">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-cyan-400" />
            Quantitative Reconstruction Evaluation Matrices
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Objective metrics measured on {scene.name} vs Ground Truth Clear Target Reference
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 text-xs font-mono font-bold rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            Convergence PSNR: {m.blended.psnr} dB
          </span>
        </div>
      </div>

      {/* 4 Primary Metric Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: PSNR */}
        <div className="flex flex-col p-4 rounded-xl bg-slate-900/70 border border-slate-800 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">PSNR (Fidelity)</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-100 font-mono">
              {m.blended.psnr} <span className="text-sm font-normal text-slate-400">dB</span>
            </span>
            <span className="text-xs font-semibold text-emerald-400">
              +{Math.max(0, Number((m.blended.psnr - m.pregan.psnr).toFixed(1)))} dB vs Pre-GAN
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
            Peak Signal-to-Noise Ratio. Values above 35 dB indicate radiometrically indistinguishable optical reconstruction.
          </p>
          <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3 overflow-hidden">
            <div
              className="bg-emerald-400 h-full rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, (m.blended.psnr / 45) * 100)}%` }}
            ></div>
          </div>
        </div>

        {/* Metric 2: Spectral Angle Mapper (SAM) */}
        <div className="flex flex-col p-4 rounded-xl bg-slate-900/70 border border-slate-800 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">SAM (Spectral Purity)</span>
            <Compass className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-100 font-mono">
              {m.blended.sam}°
            </span>
            <span className="text-xs font-semibold text-cyan-400">
              {(m.pregan.sam - m.blended.sam).toFixed(1)}° Improvement
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
            Measures 4-band spectral angle deviation (B04, B03, B02, B08). Lower is better (&lt;3.0° confirms natural terrain colors).
          </p>
          <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3 overflow-hidden">
            <div
              className="bg-cyan-400 h-full rounded-full transition-all duration-500"
              style={{ width: `${Math.max(10, 100 - (m.blended.sam / 6) * 100)}%` }}
            ></div>
          </div>
        </div>

        {/* Metric 3: Edge Correlation */}
        <div className="flex flex-col p-4 rounded-xl bg-slate-900/70 border border-slate-800 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Edge Correlation</span>
            <Activity className="w-4 h-4 text-purple-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-100 font-mono">
              {m.blended.edgeCorr.toFixed(3)}
            </span>
            <span className="text-xs font-semibold text-purple-400">
              +{(m.blended.edgeCorr - m.pregan.edgeCorr).toFixed(3)} Gain
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
            Gradient vector covariance. Quantifies alignment of road boundaries, field borders, and geological fault lines.
          </p>
          <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3 overflow-hidden">
            <div
              className="bg-purple-400 h-full rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, m.blended.edgeCorr * 100)}%` }}
            ></div>
          </div>
        </div>

        {/* Metric 4: High-Frequency Detail Retention */}
        <div className="flex flex-col p-4 rounded-xl bg-slate-900/70 border border-slate-800 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Detail Retention</span>
            <Sparkles className="w-4 h-4 text-amber-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-100 font-mono">
              {m.blended.detailRetention}%
            </span>
            <span className="text-xs font-semibold text-amber-400">
              +{Math.round(m.blended.detailRetention - m.pregan.detailRetention)}% Sharper
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
            Ratio of high-pass Laplacian energy retained inside cloud core. Overcomes Pre-GAN L1 smoothing collapse (was only ~13%).
          </p>
          <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3 overflow-hidden">
            <div
              className="bg-amber-400 h-full rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, m.blended.detailRetention)}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Comparative Matrix Table */}
      <div className="w-full flex flex-col gap-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Stage-by-Stage Performance Comparison ({scene.title})
        </h4>

        <div className="w-full overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/50">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4 font-semibold">Pipeline Stage</th>
                <th className="py-3 px-4 font-semibold">PSNR (dB) ↑</th>
                <th className="py-3 px-4 font-semibold">SAM (Deg) ↓</th>
                <th className="py-3 px-4 font-semibold">Edge Corr ↑</th>
                <th className="py-3 px-4 font-semibold">Detail Retention ↑</th>
                <th className="py-3 px-4 font-semibold">Visual Characteristics</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              <tr className="hover:bg-slate-800/30">
                <td className="py-3 px-4 font-sans font-medium text-slate-300 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-orange-400"></span>
                  Stage 3: Pre-GAN Baseline (L1+SSIM)
                </td>
                <td className="py-3 px-4">{m.pregan.psnr} dB</td>
                <td className="py-3 px-4">{m.pregan.sam}°</td>
                <td className="py-3 px-4">{m.pregan.edgeCorr}</td>
                <td className="py-3 px-4 text-orange-400">{m.pregan.detailRetention}%</td>
                <td className="py-3 px-4 font-sans text-slate-400 text-[11px]">
                  Severely smoothed inside clouds; lost fine streets/ridges
                </td>
              </tr>
              <tr className="hover:bg-slate-800/30">
                <td className="py-3 px-4 font-sans font-medium text-slate-300 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-blue-400"></span>
                  Stage 4: PatchGAN Direct Output (P_dir)
                </td>
                <td className="py-3 px-4">{m.patchgan.psnr} dB</td>
                <td className="py-3 px-4">{m.patchgan.sam}°</td>
                <td className="py-3 px-4">{m.patchgan.edgeCorr}</td>
                <td className="py-3 px-4 text-blue-400 font-bold">{m.patchgan.detailRetention}%</td>
                <td className="py-3 px-4 font-sans text-slate-400 text-[11px]">
                  Adversarially sharpened; roads & forest texture crisp
                </td>
              </tr>
              <tr className="bg-emerald-950/20 hover:bg-emerald-950/30 text-emerald-300 font-bold">
                <td className="py-3 px-4 font-sans flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                  Stage 5: Final Harmonized Cloud-Blended (Y_hat)
                </td>
                <td className="py-3 px-4">{m.blended.psnr} dB</td>
                <td className="py-3 px-4">{m.blended.sam}°</td>
                <td className="py-3 px-4">{m.blended.edgeCorr}</td>
                <td className="py-3 px-4 text-emerald-400">{m.blended.detailRetention}%</td>
                <td className="py-3 px-4 font-sans text-emerald-300 font-normal text-[11px]">
                  100% authentic clear sky preserved; zero boundary seams
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Multi-Strata Benchmark Summary Across All Scenes */}
      <div className="w-full flex flex-col gap-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Cross-Scene Validation Benchmark (All 6 Representative Strata)
        </h4>

        <div className="w-full overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/50">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Landscape Type</th>
                <th className="py-2.5 px-3">ROI Patch</th>
                <th className="py-2.5 px-3">Cloud Cover</th>
                <th className="py-2.5 px-3">Pre-GAN PSNR</th>
                <th className="py-2.5 px-3">PatchGAN PSNR</th>
                <th className="py-2.5 px-3">Final PSNR ↑</th>
                <th className="py-2.5 px-3">Final SAM ↓</th>
                <th className="py-2.5 px-3">Detail Retention</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
              {allScenes.map((s) => (
                <tr
                  key={s.id}
                  className={`hover:bg-slate-800/40 ${
                    s.id === scene.id ? "bg-cyan-950/30 font-semibold" : ""
                  }`}
                >
                  <td className="py-2.5 px-3 font-sans font-medium text-slate-200">
                    {s.title}
                  </td>
                  <td className="py-2.5 px-3 text-slate-400">{s.name}</td>
                  <td className="py-2.5 px-3">{s.cloudPct.toFixed(1)}%</td>
                  <td className="py-2.5 px-3 text-slate-400">{s.metrics.pregan.psnr} dB</td>
                  <td className="py-2.5 px-3 text-slate-300">{s.metrics.patchgan.psnr} dB</td>
                  <td className="py-2.5 px-3 text-emerald-400 font-bold">{s.metrics.blended.psnr} dB</td>
                  <td className="py-2.5 px-3 text-cyan-400">{s.metrics.blended.sam}°</td>
                  <td className="py-2.5 px-3 text-amber-400">{s.metrics.blended.detailRetention}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
