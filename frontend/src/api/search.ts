export type SearchResultThread = {
  id: number;
  title: string;
  author_display_name?: string;
  create_time?: string;
  like_count?: number;
};

export type SearchResultReply = {
  id: number;
  body: string;
  thread_id?: number;
  create_time?: string;
  like_count?: number;
};

export type SearchResponse = {
  query: string;
  type: 'threads' | 'replies' | 'all';
  sort: 'recent' | 'popular' | 'relevance';
  page: number;
  limit: number;
  threads: SearchResultThread[];
  replies: SearchResultReply[];
  total_threads: number;
  total_replies: number;
  total_results: number;
};

export async function searchApi(params: {
  q: string;
  type?: 'threads' | 'replies' | 'all';
  sort?: 'recent' | 'popular' | 'relevance';
  page?: number;
  limit?: number;
}): Promise<SearchResponse> {
  const query = new URLSearchParams();
  query.set('q', params.q);
  if (params.type) query.set('type', params.type);
  if (params.sort) query.set('sort', params.sort);
  if (params.page) query.set('page', String(params.page));
  if (params.limit) query.set('limit', String(params.limit));

  const res = await fetch(`/api/search/?${query.toString()}`, { credentials: 'include' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Search failed');
  return data as SearchResponse;
}

 
