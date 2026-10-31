// KEEP-CONTRACT: components depend on these shapes. Do not change them; adapt the backend instead.

export interface SamplePreviews {
  cloudy: string;
  sar: string;
  mask: string;
}

export interface Sample {
  id: string;
  filename: string;
  cloudCoverage: number;
  previews: SamplePreviews;
}

export interface Metrics {
  psnr: number;
  sam: number;
  edgeCorr: number;
  hfRetention: number;
}

export interface ResultStages {
  baseline: string;
  sharpened: string;
  final: string;
  target: string;
}

export interface ResultMetrics {
  cloudy: Metrics;
  baseline: Metrics;
  sharpened: Metrics;
  final: Metrics;
}

export interface Result {
  stages: ResultStages;
  metrics: ResultMetrics;
}

export type StageKey = 'cloudy' | 'baseline' | 'sharpened' | 'final' | 'target';
export type ProcessStatus = 'idle' | 'running' | 'done' | 'error';
