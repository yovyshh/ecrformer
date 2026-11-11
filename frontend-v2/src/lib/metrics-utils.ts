import { Metrics, StageKey } from './types';

export interface MetricDelta {
  diff: number;
  diffText: string;
  isImproved: boolean;
  arrow: 'up' | 'down' | 'neutral';
}

export const METRIC_TOOLTIPS = {
  psnr: 'Peak Signal-to-Noise Ratio (dB) — Higher is better; measured over cloud-covered pixels (full image when little or no cloud)',
  sam: 'Spectral Angle Mapper (°) — Lower is better; measured over cloud-covered pixels (full image when little or no cloud)',
  edgeCorr: 'Edge Correlation Coefficient [0–1] — Higher is better (preserves structural land boundaries)',
  hfRetention: 'High-Frequency Retention (ratio) — Closer to 1.0 is better (1.0 matches ground truth detail, values can exceed 1.0)',
};

export const METRIC_LABELS = {
  psnr: 'PSNR (dB)',
  sam: 'SAM (°)',
  edgeCorr: 'Edge Corr',
  hfRetention: 'HF Retention',
};

/**
 * Calculates direction-aware delta between test and reference metric.
 * - PSNR, edgeCorr: higher is better (positive diff = improvement).
 * - SAM: lower is better (in degrees; negative diff = improvement).
 * - HF Retention: ratio where 1.0 is ground truth; closer to 1.0 is better (|test - 1.0| < |ref - 1.0|).
 */
export function calculateDelta(
  testVal: number,
  refVal: number,
  metricKey: keyof Metrics
): MetricDelta {
  const diff = Math.round((testVal - refVal) * 1000) / 1000;

  let isImproved = false;
  if (metricKey === 'sam') {
    isImproved = testVal < refVal;
  } else if (metricKey === 'hfRetention') {
    const testDist = Math.abs(testVal - 1.0);
    const refDist = Math.abs(refVal - 1.0);
    isImproved = testDist < refDist;
  } else {
    isImproved = testVal > refVal;
  }

  let arrow: 'up' | 'down' | 'neutral' = 'neutral';
  if (diff > 0) arrow = 'up';
  else if (diff < 0) arrow = 'down';

  const sign = diff > 0 ? '+' : '';
  const decimals = metricKey === 'psnr' ? 2 : (metricKey === 'sam' ? 2 : 4);
  const diffText = `${sign}${diff.toFixed(decimals)}`;

  return { diff, diffText, isImproved, arrow };
}

/**
 * Identify which stage holds the optimal (best) value for each metric.
 * Stages can legitimately have identical metric values (e.g. final == cloudy at 0% cloud,
 * final == sharpened at 100% cloud); later stages are favored gracefully.
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
    if (metrics[s].psnr >= maxPsnr) {
      maxPsnr = metrics[s].psnr;
      bestStages.psnr = s;
    }
  });

  // Best SAM is lowest (degrees)
  let minSam = Infinity;
  stages.forEach((s) => {
    if (metrics[s].sam <= minSam) {
      minSam = metrics[s].sam;
      bestStages.sam = s;
    }
  });

  // Best EdgeCorr is highest
  let maxEdge = -Infinity;
  stages.forEach((s) => {
    if (metrics[s].edgeCorr >= maxEdge) {
      maxEdge = metrics[s].edgeCorr;
      bestStages.edgeCorr = s;
    }
  });

  // Best HF Retention is closest to 1.0 (ground truth ratio)
  let minHfDist = Infinity;
  stages.forEach((s) => {
    const dist = Math.abs(metrics[s].hfRetention - 1.0);
    if (dist <= minHfDist) {
      minHfDist = dist;
      bestStages.hfRetention = s;
    }
  });

  return bestStages;
}
