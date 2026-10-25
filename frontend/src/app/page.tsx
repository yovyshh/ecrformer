"use client";

import React, { useState } from "react";
import { SCENES_DATA, SceneData } from "@/data/scenes";

export default function Home() {
  const [selectedSceneId, setSelectedSceneId] = useState<string>(SCENES_DATA[0].id);

  const currentScene: SceneData =
    SCENES_DATA.find((s) => s.id === selectedSceneId) || SCENES_DATA[0];

  const stages = [
    {
      step: "1",
      title: "Original Cloudy Input",
      subtitle: `Sentinel-2 Optical (${currentScene.cloudPct.toFixed(1)}% Cloud)`,
      image: currentScene.paths.cloudy,
      metric: `Cloud Cover: ${currentScene.cloudPct.toFixed(1)}%`,
      border: "border-slate-700",
    },
    {
      step: "2",
      title: "Ground Truth",
      subtitle: "Clear Reference Target",
      image: currentScene.paths.clear,
      metric: "100% Clear Target (256×256)",
      border: "border-slate-700",
    },
    {
      step: "3",
      title: "ECRformer Output",
      subtitle: "Pre-GAN Baseline (L1 + SSIM)",
      image: currentScene.paths.pregan,
      metric: `PSNR: ${currentScene.metrics.pregan.psnr} dB | Detail: ${currentScene.metrics.pregan.detailRetention}%`,
      border: "border-amber-500/50",
    },
    {
      step: "4",
      title: "PatchGAN Output",
      subtitle: "Adversarially Sharpened (P_dir)",
      image: currentScene.paths.patchgan,
      metric: `PSNR: ${currentScene.metrics.patchgan.psnr} dB | Detail: ${currentScene.metrics.patchgan.detailRetention}%`,
      border: "border-blue-500/60",
    },
    {
      step: "5",
      title: "Cloud-Blended Final Output",
      subtitle: "Final Output: (1 - M)·X + M·P_dir",
      image: currentScene.paths.blended,
      metric: `PSNR: ${currentScene.metrics.blended.psnr} dB | Detail: ${currentScene.metrics.blended.detailRetention}%`,
      border: "border-emerald-500 ring-1 ring-emerald-500/50",
    },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans">
      {/* Simple Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 py-5 px-6">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-white">
              SAR-Guided Optical Satellite Cloud Removal (ECRformer + PatchGAN)
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
              Vaishnav T Prakash · M.Sc. Computer Science (AI), CUSAT
            </p>
          </div>
          <div className="text-xs font-mono text-slate-300 bg-slate-900 border border-slate-800 px-3 py-2 rounded-lg">
            <div>Dataset: SEN12MS-CR (ROIs1970_fall)</div>
            <div className="text-cyan-400 mt-0.5">
              Trained: 128×128 Crops → Evaluated: 256×256 Native
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 flex flex-col gap-8">
        {/* 1. Preloaded Cloudy Image Selector */}
        <section className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
              1. Select a Preloaded Cloudy Satellite Patch to Clear
            </h2>
            <span className="text-xs text-slate-400 font-mono">
              Click any patch below
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {SCENES_DATA.map((scene) => {
              const isSelected = scene.id === selectedSceneId;
              return (
                <button
                  key={scene.id}
                  onClick={() => setSelectedSceneId(scene.id)}
                  className={`flex flex-col text-left p-2.5 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? "bg-slate-800 border-cyan-400 ring-2 ring-cyan-400/40"
                      : "bg-slate-900/60 border-slate-800 hover:border-slate-700"
                  }`}
                >
                  <div className="relative aspect-square w-full rounded-lg overflow-hidden bg-slate-950 mb-2 border border-slate-800">
                    <img
                      src={scene.paths.cloudy}
                      alt={scene.name}
                      className="w-full h-full object-cover"
                    />
                    <span className="absolute top-1.5 right-1.5 bg-black/80 text-amber-300 text-[10px] font-mono font-bold px-1.5 py-0.5 rounded">
                      {scene.cloudPct.toFixed(1)}% Cloud
                    </span>
                  </div>
                  <div className="text-xs font-bold text-white truncate">
                    {scene.title}
                  </div>
                  <div className="text-[10px] font-mono text-cyan-400 truncate mt-0.5">
                    {scene.name}
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        {/* 2. Selected Input Preview (Cloudy Optical + SAR + Cloud Mask) */}
        <section className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 flex flex-col lg:flex-row items-center justify-between gap-6">
          <div className="flex flex-col gap-1.5 max-w-xl">
            <div className="text-xs font-mono text-cyan-400 uppercase">
              Selected ROI Patch Preview
            </div>
            <h3 className="text-lg font-bold text-white">
              {currentScene.name} — {currentScene.title}
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              {currentScene.description}
            </p>
            <div className="flex flex-wrap gap-3 mt-2 text-xs font-mono">
              <span className="bg-slate-950 border border-slate-800 px-2.5 py-1 rounded text-slate-300">
                Training Crop: <strong>128 × 128 px</strong>
              </span>
              <span className="bg-slate-950 border border-slate-800 px-2.5 py-1 rounded text-slate-300">
                Evaluation Scene: <strong>256 × 256 px (10m/px)</strong>
              </span>
              <span className="bg-slate-950 border border-slate-800 px-2.5 py-1 rounded text-amber-300">
                Cloud Cover: <strong>{currentScene.cloudPct.toFixed(1)}%</strong>
              </span>
            </div>
          </div>

          {/* 3 Input Modalities Preview */}
          <div className="grid grid-cols-3 gap-3 shrink-0">
            <div className="flex flex-col items-center gap-1">
              <img
                src={currentScene.paths.cloudy}
                alt="Cloudy S2"
                className="w-24 h-24 sm:w-28 sm:h-28 rounded-lg border border-slate-700 object-cover"
              />
              <span className="text-[11px] font-medium text-slate-300">
                Cloudy S2 (4-Ch)
              </span>
            </div>
            <div className="flex flex-col items-center gap-1">
              <img
                src={currentScene.paths.sar}
                alt="Sentinel-1 SAR"
                className="w-24 h-24 sm:w-28 sm:h-28 rounded-lg border border-teal-500/50 object-cover"
              />
              <span className="text-[11px] font-medium text-teal-300">
                SAR S1 (2-Ch)
              </span>
            </div>
            <div className="flex flex-col items-center gap-1">
              <img
                src={currentScene.paths.mask}
                alt="Cloud Mask M"
                className="w-24 h-24 sm:w-28 sm:h-28 rounded-lg border border-red-500/50 object-cover"
              />
              <span className="text-[11px] font-medium text-red-300">
                Cloud Mask M (1-Ch)
              </span>
            </div>
          </div>
        </section>

        {/* 3. Side-by-Side 5-Stage Output Comparison */}
        <section className="flex flex-col gap-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
              2. Multi-Stage Cloud Removal Outputs (256 × 256 Resolution)
            </h2>
            <span className="text-xs font-mono text-slate-400">
              ROI Patch: {currentScene.name}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {stages.map((st) => (
              <div
                key={st.step}
                className={`flex flex-col rounded-xl bg-slate-900/70 border ${st.border} overflow-hidden`}
              >
                <div className="p-3 border-b border-slate-800">
                  <div className="text-xs font-bold text-white">
                    {st.step}. {st.title}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    {st.subtitle}
                  </div>
                </div>

                <div className="aspect-square w-full bg-slate-950">
                  <img
                    src={st.image}
                    alt={st.title}
                    className="w-full h-full object-cover"
                  />
                </div>

                <div className="p-2.5 bg-slate-950/80 border-t border-slate-800 text-center font-mono text-[11px] text-cyan-300">
                  {st.metric}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* 4. Evaluation Metrics Table */}
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
            3. Quantitative Evaluation Metrics — {currentScene.name}
          </h2>

          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/50">
            <table className="w-full text-left text-xs text-slate-200">
              <thead className="bg-slate-900 text-slate-400 uppercase border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Model Stage</th>
                  <th className="py-3 px-4">Resolution (Train → Eval)</th>
                  <th className="py-3 px-4">PSNR (dB) ↑</th>
                  <th className="py-3 px-4">SAM (°) ↓</th>
                  <th className="py-3 px-4">Edge Correlation ↑</th>
                  <th className="py-3 px-4">High-Freq Detail Retention ↑</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-mono">
                <tr>
                  <td className="py-3 px-4 font-sans font-medium">
                    3. ECRformer Output (Pre-GAN Baseline)
                  </td>
                  <td className="py-3 px-4 text-slate-400">128×128 → 256×256</td>
                  <td className="py-3 px-4">{currentScene.metrics.pregan.psnr} dB</td>
                  <td className="py-3 px-4">{currentScene.metrics.pregan.sam}°</td>
                  <td className="py-3 px-4">{currentScene.metrics.pregan.edgeCorr}</td>
                  <td className="py-3 px-4 text-amber-400">
                    {currentScene.metrics.pregan.detailRetention}%
                  </td>
                </tr>
                <tr>
                  <td className="py-3 px-4 font-sans font-medium">
                    4. PatchGAN Direct Output (P_dir)
                  </td>
                  <td className="py-3 px-4 text-slate-400">128×128 → 256×256</td>
                  <td className="py-3 px-4">{currentScene.metrics.patchgan.psnr} dB</td>
                  <td className="py-3 px-4">{currentScene.metrics.patchgan.sam}°</td>
                  <td className="py-3 px-4">{currentScene.metrics.patchgan.edgeCorr}</td>
                  <td className="py-3 px-4 text-blue-400 font-bold">
                    {currentScene.metrics.patchgan.detailRetention}%
                  </td>
                </tr>
                <tr className="bg-emerald-950/25 text-emerald-300 font-bold">
                  <td className="py-3 px-4 font-sans">
                    5. Cloud-Blended Final Output (Y_hat)
                  </td>
                  <td className="py-3 px-4">128×128 → 256×256</td>
                  <td className="py-3 px-4">{currentScene.metrics.blended.psnr} dB</td>
                  <td className="py-3 px-4">{currentScene.metrics.blended.sam}°</td>
                  <td className="py-3 px-4">{currentScene.metrics.blended.edgeCorr}</td>
                  <td className="py-3 px-4">
                    {currentScene.metrics.blended.detailRetention}%
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* 5. Summary Table Across All 6 Preloaded ROI Patches */}
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
            4. All Preloaded ROI Patches Summary (ROIs1970_fall Subset)
          </h2>

          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/50">
            <table className="w-full text-left text-xs text-slate-200">
              <thead className="bg-slate-900 text-slate-400 uppercase border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">ROI Patch Name</th>
                  <th className="py-3 px-4">Terrain Type</th>
                  <th className="py-3 px-4">Cloud %</th>
                  <th className="py-3 px-4">ECRformer PSNR</th>
                  <th className="py-3 px-4">PatchGAN PSNR</th>
                  <th className="py-3 px-4">Final Blended PSNR ↑</th>
                  <th className="py-3 px-4">SAM (°) ↓</th>
                  <th className="py-3 px-4">Edge Corr ↑</th>
                  <th className="py-3 px-4">Detail Retention ↑</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-mono">
                {SCENES_DATA.map((s) => (
                  <tr
                    key={s.id}
                    onClick={() => setSelectedSceneId(s.id)}
                    className={`cursor-pointer transition-colors ${
                      s.id === currentScene.id
                        ? "bg-cyan-950/40 font-bold text-white"
                        : "hover:bg-slate-800/40 text-slate-300"
                    }`}
                  >
                    <td className="py-2.5 px-4 text-cyan-400">{s.name}</td>
                    <td className="py-2.5 px-4 font-sans">{s.title}</td>
                    <td className="py-2.5 px-4">{s.cloudPct.toFixed(1)}%</td>
                    <td className="py-2.5 px-4">{s.metrics.pregan.psnr} dB</td>
                    <td className="py-2.5 px-4">{s.metrics.patchgan.psnr} dB</td>
                    <td className="py-2.5 px-4 text-emerald-400">
                      {s.metrics.blended.psnr} dB
                    </td>
                    <td className="py-2.5 px-4">{s.metrics.blended.sam}°</td>
                    <td className="py-2.5 px-4">{s.metrics.blended.edgeCorr}</td>
                    <td className="py-2.5 px-4 text-amber-300">
                      {s.metrics.blended.detailRetention}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}
