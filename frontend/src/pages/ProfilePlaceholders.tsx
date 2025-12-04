import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { fetchHistory, clearHistory, type HistoryItem } from '../api/users'
import { fetchJson } from '../api/client'

export function BrowsingHistoryPage() {
  const { userId } = useAuth() as any
  const [items, setItems] = useState<HistoryItem[]>([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const LIMIT = 10

  async function load(p = 1) {
    if (!userId) return
    try {
      setLoading(true)
      setError(null)
      const data = await fetchHistory(userId, p, LIMIT)
      setItems(data.results)
      setTotal(data.total)
      setPage(p)
    } catch (e: any) {
      setError(e?.message || 'Failed to load history')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load(1) }, [userId])

  return (
    <div className="py-4">
      {/* Header */}
      <div className="row mb-4">
        <div className="col-12">
          <div className="d-flex align-items-center justify-content-between">
            <div className="d-flex align-items-center gap-2">
              <span className="section-icon text-primary" aria-hidden="true">
                <i className="bi bi-clock-history"></i>
              </span>
              <h1 className="h3 mb-0 fw-semibold">Browsing History</h1>
            </div>
            <button 
              className="btn btn-outline-danger btn-sm" 
              disabled={loading || items.length === 0} 
              onClick={async () => {
                if (!confirm('Are you sure you want to clear your browsing history?')) return
                try {
                  await clearHistory(userId)
                  await load(1)
                } catch (e: any) {
                  setError(e?.message || 'Failed to clear')
                }
              }}
            >
              <i className="bi bi-trash me-2"></i>Clear History
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="row">
        <div className="col-12">
          {error && (
            <div className="alert alert-danger mb-4">
              <i className="bi bi-exclamation-triangle me-2"></i>{error}
            </div>
          )}
          
          {loading && (
            <div className="d-flex justify-content-center py-5">
              <div className="d-flex align-items-center text-muted">
                <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                Loading history...
              </div>
            </div>
          )}

          {!loading && items.length === 0 && (
            <div className="card fade-in shadow-sm border-0" style={{ borderRadius: 'var(--radius-lg)' }}>
              <div className="card-body p-5 text-center">
                <i className="bi bi-clock-history text-muted" style={{ fontSize: '3rem' }}></i>
                <h3 className="h5 text-muted mt-3">No browsing history yet</h3>
                <p className="text-muted mb-0">Start exploring threads to build your browsing history!</p>
              </div>
            </div>
          )}

          {!loading && items.length > 0 && (
            <div className="row g-3">
              {items.map(it => (
                <div key={`${it.thread_id}-${it.viewed_at}`} className="col-12">
                  <div className="card fade-in shadow-sm border-0 h-100" style={{ borderRadius: 'var(--radius-lg)' }}>
                    <div className="card-body p-3">
                      <div className="d-flex justify-content-between align-items-start">
                        <div className="flex-grow-1">
                          <h5 className="card-title mb-2">
                            <Link to={`/threads/${it.thread_id}`} className="text-decoration-none">
                              {it.title}
                            </Link>
                          </h5>
                          <div className="d-flex align-items-center gap-3 text-muted small">
                            <span><i className="bi bi-person me-1"></i>{it.author_display_name}</span>
                            <span><i className="bi bi-clock me-1"></i>{new Date(it.viewed_at).toLocaleString()}</span>
                          </div>
                        </div>
                        <Link className="btn btn-outline-primary btn-sm" to={`/threads/${it.thread_id}`}>
                          <i className="bi bi-arrow-right me-1"></i>Open
                        </Link>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {!loading && items.length > 0 && (
            <div className="d-flex align-items-center justify-content-center gap-3 mt-4">
              <button 
                className="btn btn-outline-secondary btn-sm" 
                disabled={loading || page <= 1} 
                onClick={() => load(page - 1)}
              >
                <i className="bi bi-chevron-left me-1"></i>Previous
              </button>
              <span className="text-muted">Page {page}</span>
              <button 
                className="btn btn-outline-secondary btn-sm" 
                disabled={loading || page * LIMIT >= total} 
                onClick={() => load(page + 1)}
              >
                Next<i className="bi bi-chevron-right ms-1"></i>
              </button>
              <span className="text-muted small">Total {total}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export function LikedPostsPage() {
  const { userId } = useAuth() as any
  const [items, setItems] = useState<{ thread_id: number; title: string; author_display_name?: string; liked_at: string; }[]>([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const LIMIT = 10

  async function load(p = 1) {
    if (!userId) return
    try {
      setLoading(true)
      setError(null)
      const data = await (await import('../api/users')).fetchLikedThreads(userId, p, LIMIT)
      setItems(data.results)
      setTotal(data.total)
      setPage(p)
    } catch (e: any) {
      setError(e?.message || 'Failed to load liked posts')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load(1) }, [userId])

  return (
    <div className="py-4">
      {/* Header */}
      <div className="row mb-4">
        <div className="col-12">
          <div className="d-flex align-items-center gap-2">
            <span className="section-icon text-primary" aria-hidden="true">
              <i className="bi bi-heart"></i>
            </span>
            <h1 className="h3 mb-0 fw-semibold">Liked Posts</h1>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="row">
        <div className="col-12">
          {error && (
            <div className="alert alert-danger mb-4">
              <i className="bi bi-exclamation-triangle me-2"></i>{error}
            </div>
          )}
          
          {loading && (
            <div className="d-flex justify-content-center py-5">
              <div className="d-flex align-items-center text-muted">
                <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                Loading liked posts...
              </div>
            </div>
          )}

          {!loading && items.length === 0 && (
            <div className="card fade-in shadow-sm border-0" style={{ borderRadius: 'var(--radius-lg)' }}>
              <div className="card-body p-5 text-center">
                <i className="bi bi-heart text-muted" style={{ fontSize: '3rem' }}></i>
                <h3 className="h5 text-muted mt-3">No liked posts yet</h3>
                <p className="text-muted mb-0">Start liking posts to see them here!</p>
              </div>
            </div>
          )}

          {!loading && items.length > 0 && (
            <div className="row g-3">
              {items.map(it => (
                <div key={`${it.thread_id}-${it.liked_at}`} className="col-12">
                  <div className="card fade-in shadow-sm border-0 h-100" style={{ borderRadius: 'var(--radius-lg)' }}>
                    <div className="card-body p-3">
                      <div className="d-flex justify-content-between align-items-start">
                        <div className="flex-grow-1">
                          <h5 className="card-title mb-2">
                            <Link to={`/threads/${it.thread_id}`} className="text-decoration-none">
                              {it.title}
                            </Link>
                          </h5>
                          <div className="d-flex align-items-center gap-3 text-muted small">
                            <span><i className="bi bi-person me-1"></i>{it.author_display_name}</span>
                            <span><i className="bi bi-heart me-1"></i>Liked {new Date(it.liked_at).toLocaleString()}</span>
                          </div>
                        </div>
                        <Link className="btn btn-outline-primary btn-sm" to={`/threads/${it.thread_id}`}>
                          <i className="bi bi-arrow-right me-1"></i>Open
                        </Link>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {!loading && items.length > 0 && (
            <div className="d-flex align-items-center justify-content-center gap-3 mt-4">
              <button 
                className="btn btn-outline-secondary btn-sm" 
                disabled={loading || page <= 1} 
                onClick={() => load(page - 1)}
              >
                <i className="bi bi-chevron-left me-1"></i>Previous
              </button>
              <span className="text-muted">Page {page}</span>
              <button 
                className="btn btn-outline-secondary btn-sm" 
                disabled={loading || page * LIMIT >= total} 
                onClick={() => load(page + 1)}
              >
                Next<i className="bi bi-chevron-right ms-1"></i>
              </button>
              <span className="text-muted small">Total {total}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export function ProfileSettingsPage() {
  const { userId, refreshUser } = useAuth() as any
  const [username, setUsername] = useState('')
  const [bio, setBio] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [ok, setOk] = useState<string | null>(null)

  // Load current user info on component mount
  useEffect(() => {
    const loadUserInfo = async () => {
      if (!userId) return
      try {
        const res = await fetch(`/api/users/${userId}/stats/`, {
          credentials: 'include'
        })
        if (res.ok) {
          const data = await res.json()
          setUsername(data.username || '')
          setBio(data.bio || '')
        }
      } catch (error) {
        console.error('Failed to load user info:', error)
      }
    }
    loadUserInfo()
  }, [userId])

  async function submit() {
    setError(null); setOk(null)
    try {
      if (username && username.length > 50) throw new Error('Username too long (max 50)')
      if (bio && bio.length > 300) throw new Error('Bio too long (max 300)')
      setLoading(true)
      const res = await fetchJson('/api/users/update_profile/', {
        method: 'POST',
        body: JSON.stringify({ username, bio })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Failed to update')
      setOk('Profile updated successfully')
      // Refresh auth context so new username shows up immediately
      try { await refreshUser(); } catch {}
    } catch (e: any) {
      setError(e?.message || 'Failed to update')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="py-4">
      {/* Header */}
      <div className="row mb-4">
        <div className="col-12">
          <div className="d-flex align-items-center gap-2">
            <span className="section-icon text-primary" aria-hidden="true">
              <i className="bi bi-gear"></i>
            </span>
            <h1 className="h3 mb-0 fw-semibold">Profile Settings</h1>
          </div>
        </div>
      </div>

      {/* Settings Form */}
      <div className="row">
        <div className="col-12 col-md-8 col-lg-6">
          <div className="card fade-in shadow-sm border-0" style={{ borderRadius: 'var(--radius-lg)' }}>
            <div className="card-body p-4">
              {error && (
                <div className="alert alert-danger mb-4">
                  <i className="bi bi-exclamation-triangle me-2"></i>{error}
                </div>
              )}
              
              {ok && (
                <div className="alert alert-success mb-4">
                  <i className="bi bi-check-circle me-2"></i>{ok}
                </div>
              )}

              <form onSubmit={(e) => { e.preventDefault(); submit(); }}>
                <div className="mb-4">
                  <label className="form-label fw-semibold">
                    <i className="bi bi-person me-2"></i>Username
                  </label>
                  <input 
                    className="form-control" 
                    value={username} 
                    onChange={e => setUsername(e.target.value)} 
                    placeholder="Enter your username" 
                    maxLength={50}
                  />
                  <div className="form-text">
                    <span className="text-muted">Maximum 50 characters</span>
                    <span className="float-end text-muted">{username.length}/50</span>
                  </div>
                </div>

                <div className="mb-4">
                  <label className="form-label fw-semibold">
                    <i className="bi bi-card-text me-2"></i>Bio
                  </label>
                  <textarea 
                    className="form-control" 
                    value={bio} 
                    onChange={e => setBio(e.target.value)} 
                    rows={4} 
                    placeholder="Tell us something about yourself..." 
                    maxLength={300}
                  />
                  <div className="form-text">
                    <span className="text-muted">Maximum 300 characters</span>
                    <span className="float-end text-muted">{bio.length}/300</span>
                  </div>
                </div>

                <div className="d-flex gap-2">
                  <button 
                    type="submit" 
                    className="btn btn-primary" 
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                        Saving...
                      </>
                    ) : (
                      <>
                        <i className="bi bi-check-lg me-2"></i>Save Changes
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}


