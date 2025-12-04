import { fetchJson } from './client';
/**
 * API functions for tag management.
 */

export interface Tag {
  name: string;
  is_active: boolean;
}

export interface TagCreateRequest {
  name: string;
}

export interface TagUpdateRequest {
  is_active: boolean;
}

const API_BASE = '/api';

/**
 * List all active tags (for non-admin users) or all tags (for admin users).
 */
export async function listTags(): Promise<Tag[]> {
  const response = await fetch(`${API_BASE}/tags/`, {
    credentials: 'include',
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Failed to fetch tags' }));
    throw new Error(error.error || 'Failed to fetch tags');
  }
  
  const data = await response.json();
  // Handle paginated response from DRF
  return Array.isArray(data) ? data : (data.results || []);
}

/**
 * List only active tags (for tag input suggestions).
 */
export async function listActiveTags(): Promise<Tag[]> {
  const response = await fetch(`${API_BASE}/tags/`, {
    credentials: 'include',
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Failed to fetch tags' }));
    throw new Error(error.error || 'Failed to fetch tags');
  }
  
  const data = await response.json();
  const allTags = Array.isArray(data) ? data : (data.results || []);
  // Filter to only active tags
  return allTags.filter((tag: Tag) => tag.is_active);
}

/**
 * Create a new tag (admin only).
 */
export async function createTag(data: TagCreateRequest): Promise<Tag> {
  const response = await fetchJson(`${API_BASE}/tags/`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Failed to create tag' }));
    throw new Error(error.error || 'Failed to create tag');
  }
  
  return response.json();
}

/**
 * Update a tag (admin only).
 */
export async function updateTag(tagName: string, data: TagUpdateRequest): Promise<Tag> {
  const response = await fetchJson(`${API_BASE}/tags/${encodeURIComponent(tagName)}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Failed to update tag' }));
    throw new Error(error.error || 'Failed to update tag');
  }
  
  return response.json();
}

/**
 * Delete/disable a tag (admin only).
 */
export async function deleteTag(tagName: string): Promise<void> {
  const response = await fetchJson(`${API_BASE}/tags/${encodeURIComponent(tagName)}/`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Failed to delete tag' }));
    throw new Error(error.error || 'Failed to delete tag');
  }
}
