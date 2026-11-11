import { NextResponse } from 'next/server';
import { fetchFromBackend } from '@/lib/space';

const ID_PATTERN = /^[A-Za-z0-9_-]+$/;
const VALID_KINDS = new Set(['cloudy', 'sar', 'mask']);

export async function GET(
  _request: Request,
  context: { params: Promise<{ id: string; kind: string }> }
) {
  const { id, kind } = await context.params;

  if (!id || !ID_PATTERN.test(id)) {
    return NextResponse.json(
      { error: 'Invalid sample ID format' },
      { status: 400 }
    );
  }

  if (!kind || !VALID_KINDS.has(kind)) {
    return NextResponse.json(
      { error: 'Invalid preview kind. Must be cloudy, sar, or mask.' },
      { status: 400 }
    );
  }

  try {
    const backendRes = await fetchFromBackend(
      `/samples/${id}/preview/${kind}`,
      { method: 'GET' },
      30000
    );

    if (backendRes.status === 404) {
      return NextResponse.json({ error: `Sample ${id} preview not found` }, { status: 404 });
    }

    if (backendRes.status === 400) {
      return NextResponse.json({ error: `Bad request for sample ${id}` }, { status: 400 });
    }

    if (!backendRes.ok) {
      return NextResponse.json(
        { error: `Backend returned status ${backendRes.status}` },
        { status: 502 }
      );
    }

    const imageBuffer = await backendRes.arrayBuffer();

    return new Response(imageBuffer, {
      status: 200,
      headers: {
        'Content-Type': 'image/png',
        'Cache-Control': 'public, max-age=3600',
      },
    });
  } catch (err: unknown) {
    if (err instanceof Error && err.name === 'AbortError') {
      return NextResponse.json(
        { error: 'Preview request timed out after 30 seconds.' },
        { status: 504 }
      );
    }
    return NextResponse.json(
      {
        error:
          "Can't reach the model server. Start it with hf_deploy/local/run_backend (see hf_deploy/local/LOCAL_SETUP.md) and check BACKEND_URL.",
      },
      { status: 503 }
    );
  }
}
