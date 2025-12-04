import { fetchJson } from './client';
export type ReplyItem = {
  id: number;
  body: string;
  author?: { id: number; username: string };
  author_display_name?: string;
  like_count?: number;
  create_time?: string;
  edit_time?: string;
};

export async function listReplies(threadId: number): Promise<ReplyItem[]> {
  const res = await fetch(`/api/threads/${threadId}/replies/`, { credentials: 'include' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to load replies');
  return data;
}

export async function createReply(threadId: number, body: string, is_anonymous?: boolean): Promise<ReplyItem> {
  const res = await fetchJson('/api/replies/', {
    method: 'POST',
    body: JSON.stringify({ thread_id: threadId, body, is_anonymous })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to create reply');
  return data;
}

export async function updateReply(id: number, body: string): Promise<ReplyItem> {
  const res = await fetchJson(`/api/replies/${id}/`, {
    method: 'PUT',
    body: JSON.stringify({ body })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to update reply');
  return data;
}

export async function deleteReply(id: number): Promise<void> {
  const res = await fetchJson(`/api/replies/${id}/`, {
    method: 'DELETE'
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.error || 'Failed to delete reply');
  }
}

export async function toggleThreadLike(threadId: number): Promise<{ liked: boolean; like_count: number }>{
  const res = await fetchJson(`/api/threads/${threadId}/like/`, {
    method: 'POST'
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to like thread');
  return data;
}

export async function toggleReplyLike(replyId: number): Promise<{ liked: boolean; like_count: number }>{
  const res = await fetchJson(`/api/replies/${replyId}/like/`, {
    method: 'POST'
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to like reply');
  return data;
}


