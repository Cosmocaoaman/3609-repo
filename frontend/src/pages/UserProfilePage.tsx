import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import MyContentPage from './MyContentPage'
import { useEffect, useState } from 'react'
import { fetchUserStats, type UserStats } from '../api/users'

export default function UserProfilePage() {
  const { userId, username, logout } = useAuth() as any
  const nav = useNavigate()
  const [stats, setStats] = useState<UserStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    (async () => {
      if (!userId) return
      try {
        setLoading(true)
        setError(null)
        const s = await fetchUserStats(userId)
        setStats(s)
      } catch (e: any) {
        setError(e?.message || 'Failed to load stats')
      } finally {
        setLoading(false)
      }
    })()
  }, [userId])

  return (
    <div className="py-4">
      {/* Header */}
      <div className="row mb-4">
        <div className="col-12">
          <div className="d-flex align-items-center gap-3 section-header">
            <div className="d-flex align-items-center gap-2">
              <span className="section-icon text-primary" aria-hidden="true">
                <i className="bi bi-person-circle"></i>
              </span>
              <h1 className="h3 mb-0 fw-semibold">User Profile</h1>
            </div>
            <Link to="/threads" className="btn btn-outline-secondary btn-sm">
              <i className="bi bi-arrow-left me-2"></i>Back to Threads
            </Link>
          </div>
        </div>
      </div>

      {/* Profile Card */}
      <div className="row mb-4">
        <div className="col-12">
          <div className="card fade-in shadow-sm border-0" style={{ borderRadius: 'var(--radius-lg)' }}>
            <div className="card-body p-4">
              <div className="d-flex align-items-center gap-3">
                <div className="profile-avatar">
                  <div className="avatar-placeholder">
                    <i className="bi bi-person-fill"></i>
                  </div>
                </div>
                <div className="flex-grow-1">
                  <h2 className="h4 mb-1 fw-semibold">{username || 'User'}</h2>
                  <p className="text-muted mb-2">{(stats as any)?.bio || 'Bio: (Tell something about yourself...)'}</p>
                  
                  {error && (
                    <div className="alert alert-danger alert-sm mb-0">
                      <i className="bi bi-exclamation-triangle me-2"></i>{error}
                    </div>
                  )}
                  
                  {loading && (
                    <div className="d-flex align-items-center text-muted">
                      <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                      Loading stats...
                    </div>
                  )}
                  
                  {stats && (
                    <div className="d-flex gap-4 mt-3">
                      <div className="stat-item">
                        <span className="stat-number text-primary fw-bold">{stats.thread_count}</span>
                        <span className="stat-label text-muted small">Threads</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-number text-success fw-bold">{stats.reply_count}</span>
                        <span className="stat-label text-muted small">Replies</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-number text-warning fw-bold">{stats.received_likes.total}</span>
                        <span className="stat-label text-muted small">Likes Received</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="row">
        <div className="col-12">
          <div className="card fade-in shadow-sm border-0" style={{ borderRadius: 'var(--radius-lg)' }}>
            <div className="card-body p-4">
              <h3 className="h5 mb-3 fw-semibold">Quick Actions</h3>
              <div className="d-flex gap-2 flex-wrap">
                <button className="btn btn-outline-primary btn-sm" onClick={() => nav('/me/content')}>
                  <i className="bi bi-file-text me-2"></i>My Content
                </button>
                <Link to="/profile/history" className="btn btn-outline-primary btn-sm">
                  <i className="bi bi-clock-history me-2"></i>Browsing History
                </Link>
                <Link to="/profile/likes" className="btn btn-outline-primary btn-sm">
                  <i className="bi bi-heart me-2"></i>Liked Posts
                </Link>
                <Link to="/profile/settings" className="btn btn-outline-primary btn-sm">
                  <i className="bi bi-gear me-2"></i>Profile Settings
                </Link>
                <button className="btn btn-outline-danger btn-sm" onClick={async () => {
                  try {
                    await logout();
                    nav('/login');
                  } catch {}
                }}>
                  <i className="bi bi-box-arrow-right me-2"></i>Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}


