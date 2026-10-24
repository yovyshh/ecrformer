"use client";

import React, { useState } from "react";
import { SCENES_DATA, SceneData } from "@/data/scenes";
import { ImageComparisonSlider } from "@/components/ImageComparisonSlider";
import { StageProgressionMatrix } from "@/components/StageProgressionMatrix";
import { SceneSelector } from "@/components/SceneSelector";
import { MetricsDashboard } from "@/components/MetricsDashboard";
import { MethodologySection } from "@/components/MethodologySection";
import {
  Satellite,
  FileDown,
  Sparkles,
  Layers,
  ArrowRight,
  ShieldCheck,
  Cpu,
  BarChart2,
  ExternalLink,
  Code2,
} from "lucide-react";

function GithubIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="currentColor"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <path
        fillRule="evenodd"
        d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
        clipRule="evenodd"
      />
    </svg>
  );
}

export default function Home() {
  const [selectedSceneId, setSelectedSceneId] = useState<string>("scene-suburban");
  const [leftView, setLeftView] = useState<"cloudy" | "sar" | "mask" | "pregan">("cloudy");
  const [rightView, setRightView] = useState<"blended" | "patchgan" | "clear">("blended");

  const currentScene: SceneData =
    SCENES_DATA.find((s) => s.id === selectedSceneId) || SCENES_DATA[0];

  const leftImageMap = {
    cloudy: {
      url: currentScene.paths.cloudy,
      label: "Cloudy Optical Input (Sentinel-2)",
    },
    sar: {
      url: currentScene.paths.sar,
      label: "Sentinel-1 SAR Radar (VV/VH)",
    },
    mask: {
      url: currentScene.paths.mask,
      label: "Cloud Mask (s2cloudless)",
    },
    pregan: {
      url: currentScene.paths.pregan,
      label: "Pre-GAN Baseline (Smooth)",
    },
  };

  const rightImageMap = {
    blended: {
      url: currentScene.paths.blended,
      label: "Final Cloud-Blended Output (Ours)",
    },
    patchgan: {
      url: currentScene.paths.patchgan,
      label: "PatchGAN Direct Output (P_dir)",
    },
    clear: {
      url: currentScene.paths.clear,
      label: "Ground Truth Target (100% Clear)",
    },
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-slate-950">
      {/* Top Banner Navigation */}
      <header className="sticky top-0 z-50 w-full backdrop-blur-xl bg-slate-950/80 border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 text-slate-950">
              <Satellite className="w-5 h-5 stroke-[2.2]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-black text-sm tracking-tight text-slate-100">
                  ECRformer + PatchGAN
                </span>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                  v2.0 Native
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">
                SAR-Guided Optical Satellite Cloud Removal · CUSAT AI Project
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <a
              href="https://github.com/yovyshh/ecrformer"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs text-slate-300 font-medium transition-colors"
            >
              <GithubIcon className="w-3.5 h-3.5" />
              <span className="hidden md:inline">GitHub</span>
            </a>

            <a
              href="/ECRformer_Final_Report.pdf"
              download="ECRformer_Final_Report.pdf"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 text-xs font-bold shadow-md shadow-cyan-500/20 transition-all active:scale-95"
            >
              <FileDown className="w-3.5 h-3.5" />
              <span>Report PDF</span>
            </a>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8 flex flex-col gap-10">
        {/* Hero Title & Researcher Info */}
        <div className="flex flex-col gap-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-500/30 text-cyan-300 text-xs font-medium w-fit">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>M.Sc. Computer Science (Artificial Intelligence) · CUSAT</span>
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black tracking-tight text-slate-100 max-w-4xl">
            Optical Satellite Cloud Removal via{" "}
            <span className="bg-gradient-to-r from-cyan-400 via-sky-300 to-blue-500 bg-clip-text text-transparent">
              ECRformer &amp; PatchGAN
            </span>
          </h1>

          <p className="text-sm sm:text-base text-slate-400 max-w-3xl leading-relaxed">
            Fusing cloud-penetrating Sentinel-1 SAR microwave radar with corrupted Sentinel-2 optical imagery.
            Trained on 128×128 patch crops using an 11-channel Conditional PatchGAN Critic and evaluated natively on full 256×256 scenes at 10m/pixel.
          </p>
        </div>

        {/* Scene Gallery Selector */}
        <section className="w-full">
          <SceneSelector
            scenes={SCENES_DATA}
            selectedSceneId={selectedSceneId}
            onSelectScene={setSelectedSceneId}
          />
        </section>

        {/* Interactive Comparison Split Viewer Section */}
        <section className="w-full grid grid-cols-1 lg:grid-cols-12 gap-8 items-start bg-slate-900/30 rounded-3xl border border-slate-800/80 p-5 sm:p-7 shadow-xl">
          {/* Left Column: Interactive Slider */}
          <div className="lg:col-span-7 flex flex-col items-center">
            <ImageComparisonSlider
              leftImage={leftImageMap[leftView].url}
              rightImage={rightImageMap[rightView].url}
              leftLabel={leftImageMap[leftView].label}
              rightLabel={rightImageMap[rightView].label}
              sceneTitle={currentScene.title}
              sceneName={currentScene.name}
              cloudPct={currentScene.cloudPct}
            />

            {/* View Layer Selector Controls */}
            <div className="w-full max-w-[620px] grid grid-cols-2 gap-3 mt-4 pt-4 border-t border-slate-800/80">
              <div className="flex flex-col gap-1.5">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  Left Layer:
                </span>
                <div className="grid grid-cols-2 gap-1.5">
                  <button
                    onClick={() => setLeftView("cloudy")}
                    className={`px-2 py-1 text-xs rounded-md border font-medium transition-all ${
                      leftView === "cloudy"
                        ? "bg-slate-800 text-cyan-300 border-cyan-500/50"
                        : "bg-slate-950/60 text-slate-400 border-slate-800 hover:text-slate-200"
                    }`}
                  >
                    Cloudy S2
                  </button>
                  <button
                    onClick={() => setLeftView("sar")}
                    className={`px-2 py-1 text-xs rounded-md border font-medium transition-all ${
                      leftView === "sar"
                        ? "bg-slate-800 text-teal-300 border-teal-500/50"
                        : "bg-slate-950/60 text-slate-400 border-slate-800 hover:text-slate-200"
                    }`}
                  >
                    SAR Radar
                  </button>
                  <button
                    onClick={() => setLeftView("mask")}
                    className={`px-2 py-1 text-xs rounded-md border font-medium transition-all ${
                      leftView === "mask"
                        ? "bg-slate-800 text-red-300 border-red-500/50"
                        : "bg-slate-950/60 text-slate-400 border-slate-800 hover:text-slate-200"
                    }`}
                  >
                    Cloud Mask
                  </button>
                  <button
                    onClick={() => setLeftView("pregan")}
                    className={`px-2 py-1 text-xs rounded-md border font-medium transition-all ${
                      leftView === "pregan"
                        ? "bg-slate-800 text-orange-300 border-orange-500/50"
                        : "bg-slate-950/60 text-slate-400 border-slate-800 hover:text-slate-200"
                    }`}
                  >
                    Pre-GAN (Blur)
                  </button>
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  Right Layer:
                </span>
                <div className="grid grid-cols-3 gap-1.5">
                  <button
                    onClick={() => setRightView("blended")}
                    className={`px-2 py-1 text-xs rounded-md border font-medium transition-all ${
                      rightView === "blended"
                        ? "bg-emerald-950 text-emerald-300 border-emerald-500 font-bold"
                        : "bg-slate-950/60 text-slate-400 border-slate-800 hover:text-slate-200"
                    }`}
                  >
                    Final Blend
                  </button>
                  <button
                    onClick={() => setRightView("patchgan")}
                    className={`px-2 py-1 text-xs rounded-md border font-medium transition-all ${
                      rightView === "patchgan"
                        ? "bg-blue-950 text-blue-300 border-blue-500 font-bold"
                        : "bg-slate-950/60 text-slate-400 border-slate-800 hover:text-slate-200"
                    }`}
                  >
                    PatchGAN
                  </button>
                  <button
                    onClick={() => setRightView("clear")}
                    className={`px-2 py-1 text-xs rounded-md border font-medium transition-all ${
                      rightView === "clear"
                        ? "bg-indigo-950 text-indigo-300 border-indigo-500 font-bold"
                        : "bg-slate-950/60 text-slate-400 border-slate-800 hover:text-slate-200"
                    }`}
                  >
                    Target GT
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Live Scene Metrics & Technical Narrative */}
          <div className="lg:col-span-5 flex flex-col gap-5">
            <div className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800/80 flex flex-col gap-3">
              <span className="text-xs font-bold uppercase tracking-wider text-cyan-400">
                Terrain Context &amp; Objective
              </span>
              <h2 className="text-lg font-bold text-slate-100">
                {currentScene.title}
              </h2>
              <p className="text-xs text-slate-300 leading-relaxed">
                {currentScene.description}
              </p>

              <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-slate-800 text-xs">
                <div>
                  <span className="text-[11px] text-slate-400">Native Resolution:</span>
                  <p className="font-mono text-slate-200 font-bold">256 × 256 px</p>
                </div>
                <div>
                  <span className="text-[11px] text-slate-400">Ground Sampling:</span>
                  <p className="font-mono text-slate-200 font-bold">10 m / pixel</p>
                </div>
                <div>
                  <span className="text-[11px] text-slate-400">Input Modalities:</span>
                  <p className="font-mono text-slate-200 font-bold">7 Channels (SAR+Opt)</p>
                </div>
                <div>
                  <span className="text-[11px] text-slate-400">Inference Latency:</span>
                  <p className="font-mono text-emerald-400 font-bold">0.04s / scene</p>
                </div>
              </div>
            </div>

            {/* Live Performance Comparison */}
            <div className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800/80 flex flex-col gap-3">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                Live Performance Matrices
              </span>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                  <span className="text-[11px] text-slate-400">Final PSNR</span>
                  <p className="text-xl font-mono font-black text-emerald-400 mt-0.5">
                    {currentScene.metrics.blended.psnr} dB
                  </p>
                  <span className="text-[10px] text-slate-400">
                    +{Math.max(0, Number((currentScene.metrics.blended.psnr - currentScene.metrics.pregan.psnr).toFixed(1)))} dB vs Pre-GAN
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                  <span className="text-[11px] text-slate-400">Detail Retention</span>
                  <p className="text-xl font-mono font-black text-amber-400 mt-0.5">
                    {currentScene.metrics.blended.detailRetention}%
                  </p>
                  <span className="text-[10px] text-slate-400">
                    High-pass Laplacian energy
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                  <span className="text-[11px] text-slate-400">Spectral Angle (SAM)</span>
                  <p className="text-xl font-mono font-black text-cyan-400 mt-0.5">
                    {currentScene.metrics.blended.sam}°
                  </p>
                  <span className="text-[10px] text-slate-400">
                    Color purity (&lt;3.0° ideal)
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                  <span className="text-[11px] text-slate-400">Edge Correlation</span>
                  <p className="text-xl font-mono font-black text-purple-400 mt-0.5">
                    {currentScene.metrics.blended.edgeCorr}
                  </p>
                  <span className="text-[10px] text-slate-400">
                    Road &amp; border alignment
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 5-Stage Progression Matrix Section */}
        <section className="w-full">
          <StageProgressionMatrix scene={currentScene} />
        </section>

        {/* Quantitative Metrics & Comparative Matrix Dashboard */}
        <section className="w-full">
          <MetricsDashboard scene={currentScene} allScenes={SCENES_DATA} />
        </section>

        {/* Architecture, Methodology & Mathematical Formulation */}
        <section className="w-full">
          <MethodologySection />
        </section>

        {/* Project Guide Presentation Information Card */}
        <section className="w-full p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900/90 to-cyan-950/40 border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex flex-col gap-2">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <FileDown className="w-5 h-5 text-cyan-400" />
              Need the Full Technical Defense Documentation?
            </h3>
            <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
              Download the official 3-page Project Guide Output Report or the complete 14-page Question &amp; Answer Handbook containing architectural derivations, loss formulas, and tensor diagrams.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <a
              href="/ECRformer_Final_Report.pdf"
              download
              className="px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 transition-all flex items-center gap-1.5"
            >
              <FileDown className="w-4 h-4" />
              <span>Project Guide Report PDF</span>
            </a>
            <a
              href="/ECRformer_Complete_QA_Guide.pdf"
              download
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 transition-all flex items-center gap-1.5"
            >
              <FileDown className="w-4 h-4" />
              <span>14-Page Q&amp;A Handbook</span>
            </a>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-slate-800/80 bg-slate-950 py-8 px-4 text-xs text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex flex-col sm:flex-row items-center gap-2 sm:gap-4 text-center sm:text-left">
            <span className="font-bold text-slate-300">
              Vaishnav T Prakash
            </span>
            <span className="hidden sm:inline text-slate-600">·</span>
            <span>M.Sc. Computer Science (AI Specialization), CUSAT</span>
            <span className="hidden sm:inline text-slate-600">·</span>
            <span>Dataset: SEN12MS-CR (ROIs1970_fall)</span>
          </div>

          <div className="flex items-center gap-4 text-slate-400">
            <a
              href="https://github.com/yovyshh/ecrformer"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-cyan-400 transition-colors flex items-center gap-1"
            >
              <GithubIcon className="w-4 h-4" />
              <span>yovyshh/ecrformer</span>
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
