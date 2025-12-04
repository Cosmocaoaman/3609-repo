import { fetchJson } from './client';
export type UserStats = {
  user_id: number;
  username: string;
  thread_count: number;
  reply_count: number;
  given_likes: { threads: number; replies: number; total: number };
  received_likes: { threads: number; replies: number; total: number };
}

export async function fetchUserStats(userId: number): Promise<UserStats> {
  const res = await fetch(`/api/users/${userId}/stats/`, { credentials: 'include' })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || 'Failed to load user stats')
  return data as UserStats
}

export type HistoryItem = {
  thread_id: number;
  title: string;
  author_display_name?: string;
  viewed_at: string;
}

export async function fetchHistory(userId: number, page: number, limit = 10): Promise<{ results: HistoryItem[]; total: number; page: number; limit: number; }> {
  const res = await fetch(`/api/users/${userId}/history/?page=${page}&limit=${limit}`, { credentials: 'include' })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || 'Failed to load history')
  return data
}

export async function clearHistory(userId: number): Promise<void> {
  const res = await fetchJson(`/api/users/${userId}/history/`, { method: 'DELETE' })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error((data as any).error || 'Failed to clear history')
  }
}

export type LikedItem = {
  thread_id: number;
  title: string;
  author_display_name?: string;
  liked_at: string;
}

export async function fetchLikedThreads(userId: number, page: number, limit = 10): Promise<{ results: LikedItem[]; total: number; page: number; limit: number; }> {
  const res = await fetch(`/api/users/${userId}/likes/?page=${page}&limit=${limit}`, { credentials: 'include' })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || 'Failed to load liked threads')
  return data
}


