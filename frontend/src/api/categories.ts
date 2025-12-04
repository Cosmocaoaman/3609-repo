export type Category = {
  id: number;
  name: string;
};

export async function listCategories(): Promise<Category[]> {
  const res = await fetch('/api/categories/', { credentials: 'include' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to load categories');
  // DRF list may be paginated; support both shapes
  return (data && Array.isArray(data)) ? data : (data?.results ?? []);
}


