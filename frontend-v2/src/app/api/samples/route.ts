import { NextResponse } from 'next/server';
import { fetchFromBackend } from '@/lib/space';
import { Sample } from '@/lib/types';

export const dynamic = 'force-dynamic';

const UNREACHABLE_MSG = "Can't reach the model server. Start it with hf_deploy/local/run_backend (see hf_deploy/local/LOCAL_SETUP.md) and check BACKEND_URL.";

export async function GET() {
  try {
    const backendRes = await fetchFromBackend('/samples', { method: 'GET' }, 30000);

    if (!backendRes.ok) {
      if (backendRes.status === 503) {
        return NextResponse.json({ error: UNREACHABLE_MSG }, { status: 503 });
      }
      return NextResponse.json(
        { error: `Model server returned status ${backendRes.status}` },
        { status: 502 }
      );
    }

    const rawSamples = (await backendRes.json()) as Sample[];

    // Rewrite preview URLs to local Next.js proxy routes
    const rewrittenSamples: Sample[] = rawSamples.map((sample) => ({
      ...sample,
      previews: {
        cloudy: `/api/samples/${sample.id}/preview/cloudy`,
        sar: `/api/samples/${sample.id}/preview/sar`,
        mask: `/api/samples/${sample.id}/preview/mask`,
      },
    }));

    return NextResponse.json(rewrittenSamples, { status: 200 });
  } catch (err: unknown) {
    if (err instanceof Error && err.name === 'AbortError') {
      return NextResponse.json(
        { error: 'Connection to model server timed out after 30 seconds.' },
        { status: 504 }
      );
    }
    return NextResponse.json({ error: UNREACHABLE_MSG }, { status: 503 });
  }
}
