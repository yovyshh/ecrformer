import { Sample, Result } from './types';

/**
 * Fetch all available satellite scene samples from local Next.js proxy route.
 */
export async function getSamples(): Promise<Sample[]> {
  const res = await fetch('/api/samples', {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(
      errorData.error || `Failed to fetch samples from model server (status ${res.status})`
    );
  }

  return res.json();
}

/**
 * Run cloud removal pipeline for a designated sample image.
 */
export async function runRemoval(imageId: string): Promise<Result> {
  const res = await fetch('/api/remove-clouds', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({ imageId }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(
      errorData.error || `Inference failed on model server (status ${res.status})`
    );
  }

  return res.json();
}
