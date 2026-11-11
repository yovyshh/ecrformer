import { NextResponse } from 'next/server';
import { fetchFromBackend } from '@/lib/space';

export const maxDuration = 120;

const ID_PATTERN = /^[A-Za-z0-9_-]+$/;
const UNREACHABLE_MSG = "Can't reach the model server. Start it with hf_deploy/local/run_backend (see hf_deploy/local/LOCAL_SETUP.md) and check BACKEND_URL.";

interface RequestBody {
  imageId?: string;
}

export async function POST(request: Request) {
  let body: RequestBody;
  try {
    body = (await request.json()) as RequestBody;
  } catch {
    return NextResponse.json({ error: 'Invalid JSON request body' }, { status: 400 });
  }

  const imageId = body?.imageId;
  if (!imageId || typeof imageId !== 'string' || !ID_PATTERN.test(imageId)) {
    return NextResponse.json(
      { error: 'Invalid or missing imageId. Must match ^[A-Za-z0-9_-]+$' },
      { status: 400 }
    );
  }

  try {
    const backendRes = await fetchFromBackend(
      '/remove-clouds',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ imageId }),
      },
      120000
    );

    if (backendRes.status === 200) {
      const data = await backendRes.json();
      return NextResponse.json(data, { status: 200 });
    }

    if (backendRes.status === 400 || backendRes.status === 404) {
      const errData = (await backendRes.json().catch(() => ({}))) as { detail?: string };
      return NextResponse.json(
        { error: errData.detail || `Backend error: ${backendRes.status}` },
        { status: backendRes.status }
      );
    }

    if (backendRes.status === 503) {
      return NextResponse.json(
        { error: UNREACHABLE_MSG },
        { status: 503 }
      );
    }

    // Generic backend error
    const errText = await backendRes.text().catch(() => '');
    return NextResponse.json(
      { error: `Model server returned unexpected status ${backendRes.status}: ${errText}` },
      { status: 502 }
    );
  } catch (err: unknown) {
    if (err instanceof Error && err.name === 'AbortError') {
      return NextResponse.json(
        { error: 'Model inference request timed out after 120 seconds.' },
        { status: 504 }
      );
    }
    return NextResponse.json(
      { error: UNREACHABLE_MSG },
      { status: 503 }
    );
  }
}
