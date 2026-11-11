export const DEFAULT_BACKEND_URL = 'http://127.0.0.1:7860';

/**
 * Returns the backend URL, preferring process.env.BACKEND_URL (or HF_SPACE_URL for backward compat).
 * Strips any trailing slashes. Never exposes credentials to client code.
 */
export function getBackendUrl(): string {
  const url = process.env.BACKEND_URL || process.env.HF_SPACE_URL || DEFAULT_BACKEND_URL;
  return url.replace(/\/+$/, '');
}

/**
 * Executes a server-side fetch to the local FastAPI backend with timeout and auth headers.
 * 
 * @param path Endpoint path, e.g. '/samples' or '/remove-clouds'
 * @param options RequestInit options
 * @param timeoutMs Timeout in milliseconds (defaults: 120s for remove-clouds, 30s elsewhere)
 */
export async function fetchFromBackend(
  path: string,
  options: RequestInit = {},
  timeoutMs: number = 30000
): Promise<Response> {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const url = `${getBackendUrl()}${normalizedPath}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const existingHeaders = options.headers
    ? options.headers instanceof Headers
      ? Object.fromEntries(options.headers.entries())
      : Array.isArray(options.headers)
      ? Object.fromEntries(options.headers)
      : (options.headers as Record<string, string>)
    : {};

  const headers: Record<string, string> = {
    ...existingHeaders,
  };

  const token = process.env.BACKEND_TOKEN || process.env.HF_API_TOKEN;
  if (token && token.trim() && !headers['Authorization'] && !headers['authorization']) {
    headers['Authorization'] = `Bearer ${token.trim()}`;
  }

  try {
    return await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
      cache: 'no-store',
    });
  } finally {
    clearTimeout(timeoutId);
  }
}

