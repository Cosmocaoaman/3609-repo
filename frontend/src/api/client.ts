// Minimal fetch helper that always sends credentials and CSRF token when needed

function getCookie(name: string): string {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()!.split(';').shift() || '';
  return '';
}

export type HttpMethod = 'GET' | 'HEAD' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export async function fetchJson(url: string, options: RequestInit = {}) {
  const method = (options.method || 'GET').toString().toUpperCase() as HttpMethod;
  const headers: Record<string, string> = {
    'Accept': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  // For non-GET methods, attach CSRF token
  if (method !== 'GET' && method !== 'HEAD') {
    const token = getCookie('csrftoken');
    if (token) headers['X-CSRFToken'] = token;
    if (!headers['Content-Type'] && options.body && !(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }
  }

  const resp = await fetch(url, {
    credentials: 'include',
    ...options,
    headers,
  });
  return resp;
}


