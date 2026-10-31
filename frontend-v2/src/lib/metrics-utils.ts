import { Metrics, StageKey } from './types';

export interface MetricDelta {
  diff: number;
  diffText: string;
  isImproved: boolean;
  arrow: 'up' | 'down' | 'neutral';
}

export const METRIC_TOOLTIPS = {
  psnr: 'Peak Signal-to-Noise Ratio (dB) — Higher is better (greater optical reconstruction fidelity)',
  sam: 'Spectral Angle Mapper (rad) — Lower is better (smaller spectral distortion angle vs target)',
  edgeCorr: 'Edge Correlation Coefficient [0–1] — Higher is better (preserves structural land boundaries)',
  hfRetention: 'High-Frequency Retention [0–1] — Higher is better (retains fine textures & spatial detail)',
};

export const METRIC_LABELS = {
  psnr: 'PSNR (dB)',
  sam: 'SAM',
  edgeCorr: 'Edge Corr',
  hfRetention: 'HF Retention',
};

/**
 * Calculates direction-aware delta between test and reference metric.
 * For PSNR, edgeCorr, hfRetention: higher is better (positive diff = improvement).
 * For SAM: lower is better (negative diff = improvement, i.e., spectral error reduced).
 */
export function calculateDelta(
  testVal: number,
  refVal: number,
  metricKey: keyof Metrics
): MetricDelta {
  const diff = Math.round((testVal - refVal) * 1000) / 1000;
  const isSam = metricKey === 'sam';

  let isImproved = false;
  if (isSam) {
    isImproved = diff < 0;
  } else {
    isImproved = diff > 0;
  }

  let arrow: 'up' | 'down' | 'neutral' = 'neutral';
  if (diff > 0) arrow = 'up';
  else if (diff < 0) arrow = 'down';

  const sign = diff > 0 ? '+' : '';
  const decimals = metricKey === 'psnr' ? 2 : 3;
  const diffText = `${sign}${diff.toFixed(decimals)}`;

  return { diff, diffText, isImproved, arrow };
}

/**
 * Identify which stage holds the optimal (best) value for each metric.
 */
export function getBestMetricStages(metrics: {
  cloudy: Metrics;
  baseline: Metrics;
  sharpened: Metrics;
  final: Metrics;
}): Record<keyof Metrics, StageKey> {
  const stages: ('cloudy' | 'baseline' | 'sharpened' | 'final')[] = [
    'cloudy',
    'baseline',
    'sharpened',
    'final',
  ];

  const bestStages: Record<keyof Metrics, StageKey> = {
    psnr: 'final',
    sam: 'final',
    edgeCorr: 'final',
    hfRetention: 'final',
  };

  // Best PSNR is highest
  let maxPsnr = -Infinity;
  stages.forEach((s) => {
    if (metrics[s].psnr > maxPsnr) {
      maxPsnr = metrics[s].psnr;
      bestStages.psnr = s;
    }
  });

  // Best SAM is lowest
  let minSam = Infinity;
  stages.forEach((s) => {
    if (metrics[s].sam < minSam) {
      minSam = metrics[s].sam;
      bestStages.sam = s;
    }
  });

  // Best EdgeCorr is highest
  let maxEdge = -Infinity;
  stages.forEach((s) => {
    if (metrics[s].edgeCorr > maxEdge) {
      maxEdge = metrics[s].edgeCorr;
      bestStages.edgeCorr = s;
    }
  });

  // Best HF Retention is highest
  let maxHf = -Infinity;
  stages.forEach((s) => {
    if (metrics[s].hfRetention > maxHf) {
      maxHf = metrics[s].hfRetention;
      bestStages.hfRetention = s;
    }
  });

  return bestStages;
}
