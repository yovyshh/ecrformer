import { Sample, Result, Metrics } from './types';

// MOCK-START
function xmur3(str: string) {
  let h = 1779033703 ^ str.length;
  for (let i = 0; i < str.length; i++) {
    h = Math.imul(h ^ str.charCodeAt(i), 3432918353);
    h = (h << 13) | (h >>> 19);
  }
  return function () {
    h = Math.imul(h ^ (h >>> 16), 2246822507);
    h = Math.imul(h ^ (h >>> 13), 3266489909);
    return (h ^= h >>> 16) >>> 0;
  };
}

function mulberry32(a: number) {
  return function () {
    let t = (a += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function createRng(seedString: string) {
  const seedGen = xmur3(seedString);
  return mulberry32(seedGen());
}

function roundTo(val: number, decimals: number): number {
  const factor = Math.pow(10, decimals);
  return Math.round(val * factor) / factor;
}
// MOCK-END

/**
 * Fetch all available satellite scene samples.
 */
export async function getSamples(): Promise<Sample[]> {
  // BACKEND-TODO: replace with fetch('/api/samples')
  // MOCK-START
  const samples: Sample[] = [];
  for (let i = 1; i <= 20; i++) {
    const id = `sample_${String(i).padStart(3, '0')}`;
    const rng = createRng(id);
    const n = Math.floor(rng() * 80) + 10;
    const m = Math.floor(rng() * 800) + 100;
    const cloudCoverage = Math.round(5 + rng() * 90);
    const filename = `ROIs1868_summer_s2_${n}_p${m}.tif`;

    samples.push({
      id,
      filename,
      cloudCoverage,
      previews: {
        cloudy: `https://picsum.photos/seed/${id}/512/512?blur=6`,
        sar: `https://picsum.photos/seed/${id}/512/512?grayscale`,
        mask: `https://picsum.photos/seed/${id}/512/512?grayscale&blur=10`,
      },
    });
  }
  return samples;
  // MOCK-END
}

/**
 * Run cloud removal pipeline for a designated sample image.
 */
export async function runRemoval(imageId: string): Promise<Result> {
  // BACKEND-TODO: replace with POST /api/remove-clouds with { imageId }
  // MOCK-START
  const rng = createRng(`${imageId}_results`);
  const delayMs = 3000 + Math.floor(rng() * 2000); // 3-5s fake delay

  await new Promise((resolve) => setTimeout(resolve, delayMs));

  // Ordering requirements:
  // PSNR: Cloudy < Baseline < Sharpened <= Final (range 12-32)
  // SAM: Cloudy > Baseline > Sharpened >= Final (range 0.05-0.5)
  // Edge correlation: Cloudy < Baseline < Sharpened <= Final (range 0-1)
  // HF retention: Cloudy < Baseline < Sharpened <= Final (range 0-1)

  const cloudyPsnr = roundTo(14.0 + rng() * 2.5, 2);
  const baselinePsnr = roundTo(cloudyPsnr + 4.0 + rng() * 2.0, 2);
  const sharpenedPsnr = roundTo(baselinePsnr + 3.0 + rng() * 1.8, 2);
  const finalPsnr = roundTo(Math.min(32.0, sharpenedPsnr + 1.8 + rng() * 1.5), 2);

  const cloudySam = roundTo(0.38 + rng() * 0.09, 3);
  const baselineSam = roundTo(cloudySam - (0.08 + rng() * 0.04), 3);
  const sharpenedSam = roundTo(baselineSam - (0.07 + rng() * 0.03), 3);
  const finalSam = roundTo(Math.max(0.05, sharpenedSam - (0.05 + rng() * 0.03)), 3);

  const cloudyEdge = roundTo(0.40 + rng() * 0.08, 3);
  const baselineEdge = roundTo(cloudyEdge + 0.16 + rng() * 0.05, 3);
  const sharpenedEdge = roundTo(baselineEdge + 0.14 + rng() * 0.05, 3);
  const finalEdge = roundTo(Math.min(0.98, sharpenedEdge + 0.08 + rng() * 0.04), 3);

  const cloudyHf = roundTo(0.34 + rng() * 0.08, 3);
  const baselineHf = roundTo(cloudyHf + 0.18 + rng() * 0.05, 3);
  const sharpenedHf = roundTo(baselineHf + 0.14 + rng() * 0.05, 3);
  const finalHf = roundTo(Math.min(0.97, sharpenedHf + 0.08 + rng() * 0.04), 3);

  const cloudyMetrics: Metrics = {
    psnr: cloudyPsnr,
    sam: cloudySam,
    edgeCorr: cloudyEdge,
    hfRetention: cloudyHf,
  };

  const baselineMetrics: Metrics = {
    psnr: baselinePsnr,
    sam: baselineSam,
    edgeCorr: baselineEdge,
    hfRetention: baselineHf,
  };

  const sharpenedMetrics: Metrics = {
    psnr: sharpenedPsnr,
    sam: sharpenedSam,
    edgeCorr: sharpenedEdge,
    hfRetention: sharpenedHf,
  };

  const finalMetrics: Metrics = {
    psnr: finalPsnr,
    sam: finalSam,
    edgeCorr: finalEdge,
    hfRetention: finalHf,
  };

  return {
    stages: {
      baseline: `https://picsum.photos/seed/${imageId}/512/512?blur=3`,
      sharpened: `https://picsum.photos/seed/${imageId}/512/512?blur=1`,
      final: `https://picsum.photos/seed/${imageId}/512/512`,
      target: `https://picsum.photos/seed/${imageId}/512/512`,
    },
    metrics: {
      cloudy: cloudyMetrics,
      baseline: baselineMetrics,
      sharpened: sharpenedMetrics,
      final: finalMetrics,
    },
  };
  // MOCK-END
}
