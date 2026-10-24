"use client";

import React, { useState } from "react";
import { Cpu, ShieldCheck, Binary, Eye, FileText, ChevronRight } from "lucide-react";

export function MethodologySection() {
  const [activeTab, setActiveTab] = useState<"pipeline" | "mask" | "math">("pipeline");

  return (
    <div className="w-full flex flex-col gap-6 bg-slate-900/40 rounded-2xl border border-slate-800 p-6">
      {/* Header with Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-cyan-400" />
            Architecture, Methodology & Math Formulation
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Understanding the SAR-Optical Cross-Attention Fusion & Conditional PatchGAN Critic
          </p>
        </div>

        <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
          <button
            onClick={() => setActiveTab("pipeline")}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
              activeTab === "pipeline"
                ? "bg-cyan-500 text-slate-950 font-bold shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Dual-Phase Pipeline
          </button>
          <button
            onClick={() => setActiveTab("mask")}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
              activeTab === "mask"
                ? "bg-cyan-500 text-slate-950 font-bold shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            5 Cloud Mask Roles
          </button>
          <button
            onClick={() => setActiveTab("math")}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
              activeTab === "math"
                ? "bg-cyan-500 text-slate-950 font-bold shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Mathematical Formulations
          </button>
        </div>
      </div>

      {/* Tab 1: Dual-Phase Pipeline Diagram & Description */}
      {activeTab === "pipeline" && (
        <div className="flex flex-col gap-4">
          <div className="relative w-full rounded-xl overflow-hidden border border-slate-800 bg-slate-950 shadow-xl">
            <img
              src="/pipeline_architecture.png"
              alt="Complete Dual-Phase Pipeline Architecture Diagram"
              className="w-full h-auto object-contain"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-300">
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 flex flex-col gap-2">
              <span className="font-bold text-cyan-400 flex items-center gap-1.5 text-sm">
                <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
                Phase 1: Training Mode (128 × 128 Random Crops)
              </span>
              <p className="text-slate-400 leading-relaxed">
                Trained on random 128×128 crops from SEN12MS-CR. Combines Sentinel-1 SAR (VV, VH) + Sentinel-2 Optical (4 bands) + Cloud Mask M into a 7-channel decoupled stem. Evaluated with our 11-channel Conditional PatchGAN Discriminator with Spectral Normalization, backpropagating sharpness gradients without memory overflow.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 flex flex-col gap-2">
              <span className="font-bold text-emerald-400 flex items-center gap-1.5 text-sm">
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                Phase 2: Inference Mode (Native 256 × 256 Full Scenes)
              </span>
              <p className="text-slate-400 leading-relaxed">
                At test time, the PatchGAN critic is discarded. Thanks to ECRformer&apos;s Multi-DConv Head Transposed Attention (MDTA), cross-channel covariance matrices are resolution-agnostic ([C, C] = 256×256 channels). The model executes natively on full 256×256 scenes in 0.04s per scene with zero tiling seams.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: The 5 Roles of the Cloud Mask */}
      {activeTab === "mask" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 flex flex-col gap-2">
            <div className="flex items-center justify-between text-cyan-400">
              <span className="font-bold text-sm">Role M1</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-800">Training Input</span>
            </div>
            <h4 className="font-bold text-slate-200 text-xs">Opaque Cloud Cutout (65% Probability)</h4>
            <p className="text-slate-400 text-xs leading-relaxed">
              Blinds semi-transparent haze by replacing cloudy optical pixels with mean clear reflectance. Forces the network to reconstruct true terrain geometry strictly from Sentinel-1 SAR.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 flex flex-col gap-2">
            <div className="flex items-center justify-between text-blue-400">
              <span className="font-bold text-sm">Role M2</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950/80 border border-blue-800">Training Loss</span>
            </div>
            <h4 className="font-bold text-slate-200 text-xs">Scale-Decoupled L1 Loss</h4>
            <p className="text-slate-400 text-xs leading-relaxed">
              De-escalates pixel-level L1 penalization inside clouds by average-pooling (4×4 and 8×8). Restricts L1 to enforcing macro color calibration rather than fighting high-frequency adversarial textures.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 flex flex-col gap-2">
            <div className="flex items-center justify-between text-purple-400">
              <span className="font-bold text-sm">Role M3</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-950/80 border border-purple-800">Perceptual Loss</span>
            </div>
            <h4 className="font-bold text-slate-200 text-xs">2.5× Cloud-Boosted VGG &amp; Sobel</h4>
            <p className="text-slate-400 text-xs leading-relaxed">
              Weights VGG-16 deep feature representations and Sobel edge loss 2.5× more heavily inside the cloud footprint, penalizing blurriness specifically where cloud occlusion occurred.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 flex flex-col gap-2">
            <div className="flex items-center justify-between text-amber-400">
              <span className="font-bold text-sm">Role M4</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/80 border border-amber-800">Critic Critic</span>
            </div>
            <h4 className="font-bold text-slate-200 text-xs">PatchGAN 4× Focus Weighting</h4>
            <p className="text-slate-400 text-xs leading-relaxed">
              Downsamples M to the 16×16 critic score grid: w_patch = 0.25 + 0.75 * M_down. Critic penalizes blurry terrain 4× more aggressively inside cloudy patches than clear ground.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 flex flex-col gap-2 md:col-span-2">
            <div className="flex items-center justify-between text-emerald-400">
              <span className="font-bold text-sm">Role M5</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-800">Inference Delivery</span>
            </div>
            <h4 className="font-bold text-slate-200 text-xs">Soft-Mask Radiometric Preservation Gate</h4>
            <p className="text-slate-400 text-xs leading-relaxed">
              At test time, fuses authentic clear-sky observations with the sharp PatchGAN reconstruction using Multi-Band Laplacian feathering: Y_hat = (1 - M) * X_clear + M * P_dir. Completely eliminates residual cloud fringes, shadow bleed-through, and boundary seams.
            </p>
          </div>
        </div>
      )}

      {/* Tab 3: Exact Mathematical Equations */}
      {activeTab === "math" && (
        <div className="flex flex-col gap-4 text-xs font-mono">
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col gap-2">
            <span className="text-cyan-400 font-bold uppercase tracking-wider text-[11px]">
              1. Spatial-Agnostic Channel-Transposed Attention (MDTA)
            </span>
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 overflow-x-auto">
              A_MDTA = Softmax( (Q · K^T) / τ ) ∈ R^(C × C)
            </div>
            <p className="text-slate-400 text-[11px] font-sans">
              Unlike standard Vision Transformers that compute (HW) × (HW) attention, MDTA computes cross-channel covariance. Spatial dimensions are contracted, guaranteeing resolution invariance between 128×128 training and 256×256 evaluation.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col gap-2">
            <span className="text-blue-400 font-bold uppercase tracking-wider text-[11px]">
              2. Explicit High-Pass Detail Residual for PatchGAN Critic
            </span>
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 overflow-x-auto">
              R_HP = 10.0 × [ P_dir - AvgPool_5x5( P_dir ) ]
            </div>
            <p className="text-slate-400 text-[11px] font-sans">
              Subtracting a 5×5 local average amplifies fine edge variations 10-fold, preventing the Discriminator from being fooled by low-frequency color shifts.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col gap-2">
            <span className="text-emerald-400 font-bold uppercase tracking-wider text-[11px]">
              3. Multi-Band Harmonized Final Delivery Gate
            </span>
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 overflow-x-auto">
              Y_hat(x,y) = [ 1.0 - M_soft(x,y) ] ⊙ X_clear(x,y) + M_soft(x,y) ⊙ P_dir_aligned(x,y)
            </div>
            <p className="text-slate-400 text-[11px] font-sans">
              Applies a 31×31 Gaussian feathering gate (σ = 8.0) and low-frequency radiometric alignment to guarantee continuous luminance with zero seams across cloud borders.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
