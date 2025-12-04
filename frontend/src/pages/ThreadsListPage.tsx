import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
// import { listThreads } from '../api/threads';
import { searchApi } from '../api/search';
import { useAuth } from '../context/AuthContext';
import { AnonymousToggle } from '../components/AnonymousToggle';
import TagInput from '../components/TagInput';
import { listCategories } from '../api/categories';
import type { ThreadSummary } from '../api/threads';
import type { Category } from '../api/categories';

// Category color mapping
const categoryColors = [
  '#0d6efd', // primary blue
  '#198754', // success green
  '#6f42c1', // purple
  '#d63384', // pink
  '#fd7e14', // orange
  '#20c997', // teal
  '#6c757d', // secondary gray
  '#6610f2', // indigo
  '#dc3545', // danger red
  '#ffc107', // warning yellow
  '#17a2b8', // info cyan
  '#28a745', // success green
];

function getCategoryColor(categoryName: string): string {
  let hash = 0;
  for (let i = 0; i < categoryName.length; i++) {
    hash = (hash * 31 + categoryName.charCodeAt(i)) >>> 0;
  }
  return categoryColors[hash % categoryColors.length];
}

const ThreadsListPage: React.FC = () => {
  const { isAnonymous, isAdmin, isStaff, isSuperuser, loggedIn } = useAuth() as any;
  const [threads, setThreads] = useState<ThreadSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [category, setCategory] = useState('');
  const [categories, setCategories] = useState<Category[]>([]);
  const location = useLocation();
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState<number | null>(null); // Total number of threads
  const PAGE_SIZE = 20; // keep same as backend
  const [isSearching, setIsSearching] = useState(false);

  async function loadAllThreads(targetPage: number = 1) {
    // If we have a search query, use search with filters
    if (q.trim()) {
      await doSearch(targetPage);
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams();
      params.set('page', String(targetPage));
      if (tags.length > 0) params.set('tag', tags.join(','));
      if (category.trim()) params.set('category', category.trim());
      const res = await fetch(`/api/threads/?${params.toString()}`, { credentials: 'include' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to load threads');
      const results = (data as any).results ?? (data as any);
      setThreads(results);
      const totalThreads = (data as any).count ?? (Array.isArray(results) ? results.length : null);
      setTotal(totalThreads);
      setPage(targetPage);
      setIsSearching(false);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadThreadsWithFilters(tagsToUse: string[], categoryToUse: string, targetPage: number = 1) {
    try {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams();
      params.set('page', String(targetPage));
      if (tagsToUse.length > 0) params.set('tag', tagsToUse.join(','));
      if (categoryToUse.trim()) params.set('category', categoryToUse.trim());
      
      const res = await fetch(`/api/threads/?${params.toString()}`, { credentials: 'include' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to load threads');
      const results = (data as any).results ?? (data as any);
      
      setThreads(results);
      const totalThreads = (data as any).count ?? (Array.isArray(results) ? results.length : null);
      setTotal(totalThreads);
      setPage(targetPage);
      setIsSearching(false);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // Only load threads if user is logged in
    if (!loggedIn) return;
    
    // Load categories
    (async () => {
      try {
        const cats = await listCategories();
        setCategories(cats);
      } catch (err) {
        console.error('Failed to load categories:', err);
      }
    })();
    
    // Initialize filters from URL query params when changing location
    const params = new URLSearchParams(location.search);
    const tagParam = params.get('tag') || '';
    const categoryParam = params.get('category') || '';
    const searchParam = params.get('q') || '';
    
    // Update state from URL params
    setTags(tagParam ? tagParam.split(',').map(t => t.trim()) : []);
    setCategory(categoryParam);
    setQ(searchParam);
    
    // Load threads based on current filters
    if (searchParam.trim()) {
      doSearch(1);
    } else {
      loadAllThreads(1);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.search, isAdmin, isStaff, isSuperuser, loggedIn]);

  async function doSearch(targetPage: number = 1) {
    await doSearchWithFilters(q, tags, category, targetPage);
  }

  async function doSearchWithFilters(keyword: string, tagsToUse: string[], categoryToUse: string, targetPage: number = 1) {
    if (!keyword.trim()) {
      await loadThreadsWithFilters(tagsToUse, categoryToUse, targetPage);
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      const res = await searchApi({ q: keyword, type: 'threads', sort: 'relevance', page: targetPage, limit: PAGE_SIZE });
      let searchResults = res.threads.map(t => ({ 
        id: t.id, 
        title: t.title, 
        author_display_name: t.author_display_name,
        reply_count: (t as any).reply_count,
        like_count: (t as any).like_count,
        category_name: (t as any).category_name,
        category: (t as any).category,
        tags: (t as any).tags,
        tags_flat: (t as any).tags_flat
      } as ThreadSummary));
      
      if (categoryToUse.trim() || tagsToUse.length > 0) {
        const threadIds = searchResults.map(t => t.id);
        if (threadIds.length > 0) {
          const params = new URLSearchParams();
          params.set('ids', threadIds.join(','));
          if (tagsToUse.length > 0) params.set('tag', tagsToUse.join(','));
          if (categoryToUse.trim()) params.set('category', categoryToUse.trim());
          
          const filterRes = await fetch(`/api/threads/?${params.toString()}`, { credentials: 'include' });
          const filterData = await filterRes.json();
          if (filterRes.ok) {
            const filteredResults = (filterData as any).results ?? (filterData as any);
            searchResults = filteredResults.map((t: any) => ({ 
              id: t.id, 
              title: t.title, 
              author_display_name: t.author_display_name,
              reply_count: t.reply_count,
              like_count: t.like_count,
              category_name: t.category_name,
              category: t.category,
              tags: t.tags,
              tags_flat: t.tags_flat
            } as ThreadSummary));
          }
        }
      }
      
      setThreads(searchResults);
      setTotal(res.total_threads || 0);
      setPage(targetPage);
      setIsSearching(true);
    } catch (e: any) {
      setError(e?.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleClear() {
    setQ('');
    setTags([]);
    setCategory('');
    setIsSearching(false);
    
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`/api/threads/?page=1`, { credentials: 'include' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to load threads');
      const results = (data as any).results ?? (data as any);
      setThreads(results);
      setTotal((data as any).count ?? (Array.isArray(results) ? results.length : null));
      setPage(1);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="py-4">
      {/* Header */}
      <div className="row mb-4">
        <div className="col-12">
          <div className="d-flex align-items-center gap-3 section-header">
            <div className="d-flex align-items-center gap-2">
              <span className="section-icon text-primary" aria-hidden="true">
                {/* Bootstrap-like chat icon (inline SVG), inherits currentColor */}
                <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg" role="img">
                  <path d="M2 2a2 2 0 0 0-2 2v8.293A1 1 0 0 0 1.707 13l2.147-2.147A2 2 0 0 1 5.121 10H14a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H2z" />
                  <circle cx="5" cy="6.5" r="1" />
                  <circle cx="8" cy="6.5" r="1" />
                  <circle cx="11" cy="6.5" r="1" />
                </svg>
              </span>
              <div>
                <h1 className="page-title m-0">Threads</h1>
                <div className="text-muted small section-subtitle">All discussions and latest posts</div>
              </div>
            </div>
            <div className="flex-grow-1" />
            {/* Right: Create Thread styled like profile link (longer) */}
            <Link to="/threads/new" className="nav-link px-4">Create a New Thread</Link>
            <div className="d-flex align-items-center gap-3">
              {/* Anonymous toggle moved to header */}
          <Link to="/me" className="btn btn-outline-primary btn-sm">User Profile</Link>
              {(isAdmin || isStaff || isSuperuser) && (
                <Link to="/admin" className="btn btn-outline-success btn-sm">Admin Panel</Link>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Search and Filter Section */}
      <div className="row mb-4">
        <div className="col-12">
          <div className="card">
            <div className="card-body">
              <div className="row g-3">
                <div className="col-md-6">
                  <label htmlFor="searchInput" className="form-label">Search Threads</label>
                  <div className="input-group">
                    <input
                      id="searchInput"
                      type="text"
                      className="form-control"
                      placeholder="Search threads by title or body..."
                      value={q}
                      onChange={(e) => setQ(e.target.value)}
                      onKeyDown={async (e) => { 
                        if (e.key === 'Enter') {
                          const currentTags = tags;
                          const currentCategory = category;
                          const currentQuery = q;
                          
                          setTags(currentTags);
                          setCategory(currentCategory);
                          setQ(currentQuery);
                          
                          await doSearchWithFilters(currentQuery, currentTags, currentCategory, 1);
                        }
                      }}
                    />
                    <button 
                      className="btn btn-primary" 
                      type="button"
                      onClick={async () => {
                        const currentTags = tags;
                        const currentCategory = category;
                        const currentQuery = q;
                        
                        setTags(currentTags);
                        setCategory(currentCategory);
                        setQ(currentQuery);
                        
                        await doSearchWithFilters(currentQuery, currentTags, currentCategory, 1);
                      }} 
                      disabled={loading}
                    >
                      {loading ? <span className="spinner-border spinner-border-sm"></span> : 'Search'}
                    </button>
                    {(q || tags.length > 0 || category) && (
                      <button className="btn btn-outline-secondary" onClick={handleClear}>
                        Clear
                      </button>
                    )}
                  </div>
                </div>
                <div className="col-md-3">
                  <label htmlFor="categoryFilter" className="form-label">Filter by Category</label>
                  <select
                    id="categoryFilter"
                    className="form-select"
                    value={category}
                    onChange={async (e) => {
                      const newCategory = e.target.value;
                      setCategory(newCategory);
                      // Use newCategory directly instead of relying on state update
                      if (q.trim()) {
                        await doSearchWithFilters(q, tags, newCategory, 1);
                      } else {
                        await loadThreadsWithFilters(tags, newCategory, 1);
                      }
                    }}
                  >
                    <option value="">All Categories</option>
                    {categories.map(cat => (
                      <option key={cat.id} value={cat.id}>{cat.name}</option>
                    ))}
                  </select>
                </div>
                <div className="col-md-3">
                  <label htmlFor="tagFilter" className="form-label">Filter by Tags</label>
                  <TagInput
                    value={tags}
                    onChange={(newTags) => {
                      setTags(newTags);
                      // Auto-apply filter when tags change (but not during initial load)
                      if (newTags.length > 0 || tags.length > 0) {
                        // Use newTags directly instead of relying on state update
                        setTimeout(async () => {
                          if (q.trim()) {
                            await doSearchWithFilters(q, newTags, category, 1);
                          } else {
                            await loadThreadsWithFilters(newTags, category, 1);
                          }
                        }, 100);
                      }
                    }}
                    placeholder="Type # to start a tag, press Enter to confirm"
                    className="mb-2"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="row mb-4">
          <div className="col-12">
            <div className="alert alert-danger alert-dismissible fade show" role="alert">
              {error}
              <button type="button" className="btn-close" aria-label="Close alert" title="Close" onClick={() => setError(null)}></button>
            </div>
          </div>
        </div>
      )}

      {/* Threads List */}
      <div className="row">
        <div className="col-12">
          <div className="row g-4">
            {threads.map(thread => {
              const categoryName = thread.category_name || (thread as any).category?.name;
              const categoryColor = categoryName ? getCategoryColor(categoryName) : '#6c757d';
              
              return (
                <div key={thread.id} className="col-12">
                  <div className="card h-100 fade-in thread-card" style={{ borderRadius: 'var(--radius-lg)' }}>
                    {/* Category color bar */}
                    {categoryName && (
                      <div 
                        className="category-color-bar" 
                        style={{ 
                          backgroundColor: categoryColor,
                          height: '4px',
                          borderRadius: 'var(--radius-lg) var(--radius-lg) 0 0'
                        }}
                      />
                    )}
                    <div className="card-body">
                    <div className="d-flex justify-content-between align-items-start mb-2">
                      <div className="flex-grow-1">
                        <h5 className="card-title" style={{ marginBottom: 'var(--space-2)' }}>
                          <Link to={`/threads/${thread.id}`} className="text-decoration-none break-words d-inline-block w-100">
                            {thread.title}
                          </Link>
                        </h5>
                        <div className="text-muted small mb-3">
                          <span className="me-3">By {(thread as any).author_display_name || (thread as any).author?.username || 'Unknown'}</span>
                          <span className="me-3">{thread.reply_count ?? 0} replies</span>
                          <span className="me-3">{thread.like_count ?? 0} likes</span>
                          {categoryName && (
                            <span className="me-3">
                              <span 
                                className="badge text-white category-badge" 
                                style={{ backgroundColor: categoryColor }}
                              >
                                {categoryName}
                              </span>
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    {/* Tags Display */}
                    {Array.isArray((thread as any).tags) && (thread as any).tags.length > 0 && (
                      <div className="mb-2">
                        {(thread as any).tags.map((tt: any, idx: number) => (
                          <button
                            key={idx}
                            onClick={() => {
                              const tagName = tt.tag?.name || '';
                              if (tagName && !tags.includes(tagName)) {
                                const newTags = [...tags, tagName];
                                setTags(newTags);
                                loadThreadsWithFilters(newTags, category, 1);
                              }
                            }}
                            className="text-decoration-none chip chip-primary me-2 mb-2 border-0 bg-transparent"
                            style={{ cursor: 'pointer' }}
                          >
                            #{tt.tag?.name}
                          </button>
                        ))}
                      </div>
                    )}
                    {Array.isArray((thread as any).tags_flat) && (thread as any).tags_flat.length > 0 && (
                      <div className="mb-2">
                        {(thread as any).tags_flat.map((name: string, idx: number) => (
                          <button
                            key={idx}
                            onClick={() => {
                              if (name && !tags.includes(name)) {
                                const newTags = [...tags, name];
                                setTags(newTags);
                                loadThreadsWithFilters(newTags, category, 1);
                              }
                            }}
                            className="text-decoration-none chip chip-primary me-2 mb-2 border-0 bg-transparent"
                            style={{ cursor: 'pointer' }}
                          >
                            #{name}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
              );
            })}
          </div>

          {/* Create Thread Button moved to header */}

          {/* Pagination */}
          <nav className="mt-5" aria-label="Thread pagination">
            <div className="d-flex justify-content-center align-items-center">
              <button
                className="btn btn-outline-primary me-2"
                disabled={loading || page <= 1}
                onClick={() => {
                  if (isSearching) {
                    doSearch(page - 1);
                  } else if (tags.length > 0 || category.trim()) {
                    loadThreadsWithFilters(tags, category, page - 1);
                  } else {
                    loadAllThreads(page - 1);
                  }
                }}
              >
                Previous
              </button>
              <span className="mx-3 text-muted">
                Page {page}{total !== null ? ` of ${Math.ceil(total / PAGE_SIZE)}` : ''}
              </span>
              <button
                className="btn btn-outline-primary ms-2"
                disabled={loading || (total !== null && page >= Math.ceil(total / PAGE_SIZE))}
                onClick={() => {
                  if (isSearching) {
                    doSearch(page + 1);
                  } else if (tags.length > 0 || category.trim()) {
                    loadThreadsWithFilters(tags, category, page + 1);
                  } else {
                    loadAllThreads(page + 1);
                  }
                }}
              >
                Next
              </button>
              {total !== null && (
                <span className="ms-3 text-muted">({total} threads)</span>
              )}
            </div>
          </nav>
        </div>
      </div>
    </div>
  );
};

export default ThreadsListPage;


