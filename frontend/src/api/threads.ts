import { fetchJson } from './client';
/**
 * Extract error message from Django REST Framework error response
 */
function extractErrorMessage(data: any, defaultMessage: string): string {
  if (data.error) {
    return data.error;
  } else if (data.tag_names && Array.isArray(data.tag_names)) {
    return data.tag_names.join('; ');
  } else if (data.non_field_errors && Array.isArray(data.non_field_errors)) {
    return data.non_field_errors.join('; ');
  } else if (typeof data === 'object') {
    // Handle field-specific errors
    const fieldErrors = Object.entries(data)
      .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(', ') : errors}`)
      .join('; ');
    if (fieldErrors) {
      return fieldErrors;
    }
  }
  return defaultMessage;
}

export type ThreadSummary = {
  id: number;
  title: string;
  author_display_name?: string;
  author?: { id: number; username: string };
  like_count?: number;
  reply_count?: number;
  create_time?: string;
  category?: { id: number; name: string };
  category_name?: string;
};

export type ThreadDetail = ThreadSummary & {
  body: string;
  category?: { id: number; name: string };
  category_id?: number;
  tags?: Array<{ tag: { name: string } }>;
  tag_names?: string[];
  edit_time?: string;
};

export async function listThreads(page: number = 1): Promise<{ results: ThreadSummary[]; count?: number; next?: string; previous?: string; }> {
  const res = await fetch(`/api/threads/?page=${page}`, {
    credentials: 'include'
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to load threads');
  return data;
}

export async function getThread(id: number): Promise<ThreadDetail> {
  const res = await fetch(`/api/threads/${id}/`, {
    credentials: 'include'
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to load thread');
  return data;
}

export async function createThread(payload: { title: string; body: string; category_id?: number; tag_names?: string[]; is_anonymous?: boolean; }): Promise<ThreadDetail> {
  const res = await fetchJson('/api/threads/', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(extractErrorMessage(data, 'Failed to create thread'));
  }
  return data;
}

export async function updateThread(id: number, payload: { title: string; body: string; category_id?: number; tag_names?: string[]; }): Promise<ThreadDetail> {
  const res = await fetchJson(`/api/threads/${id}/`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(extractErrorMessage(data, 'Failed to update thread'));
  }
  return data;
}

export async function deleteThread(id: number): Promise<void> {
  const res = await fetchJson(`/api/threads/${id}/`, {
    method: 'DELETE'
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.error || 'Failed to delete thread');
  }
}


