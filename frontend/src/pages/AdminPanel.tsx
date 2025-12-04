import { fetchJson } from '../api/client';
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Types aligned with frontend_previous
 type TabType = 'users' | 'threads' | 'tags';

 interface User {
  id: number;
  username: string;
  email: string;
  is_admin: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  is_banned: boolean;
  date_joined: string;
  thread_count?: number;
  reply_count?: number;
 }

 interface Thread {
  id: number;
  title: string;
  body: string;
  user_id: number;
  username: string;
  category_id: number;
  category_name: string;
  is_deleted: boolean;
  is_anonymous: boolean;
  create_time: string;
  edit_time: string;
  reply_count: number;
  like_count: number;
 }

 interface Tag {
  name: string;
  is_active: boolean;
  thread_count?: number;
 }

const AdminPanel: React.FC = () => {
  const { isAdmin, isStaff, isSuperuser } = useAuth() as any;
  const [activeTab, setActiveTab] = useState<TabType>('users');
  const [users, setUsers] = useState<User[]>([]);
  const [threads, setThreads] = useState<Thread[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const PAGE_SIZE = 20;

  // Check if user has admin privileges
  const hasAdminPrivileges = isAdmin || isStaff || isSuperuser;

  // Load users
  const loadUsers = async (page: number = 1, search: string = '') => {
    try {
      setLoading(true);
      setError(null);
      const searchParam = search.trim() ? `&search=${encodeURIComponent(search.trim())}` : '';
      const response = await fetch(`/api/users/?page=${page}&page_size=${PAGE_SIZE}${searchParam}`, { credentials: 'include' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Failed to load users');
      setUsers(data.results || []);
      setTotalPages(Math.ceil((data.count || 0) / PAGE_SIZE));
      setTotalCount(data.count || 0);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Load threads
  const loadThreads = async (page: number = 1, search: string = '') => {
    try {
      setLoading(true);
      setError(null);
      const searchParam = search.trim() ? `&search=${encodeURIComponent(search.trim())}` : '';
      const response = await fetch(`/api/threads/?page=${page}&page_size=${PAGE_SIZE}&include_deleted=true${searchParam}`, { credentials: 'include' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Failed to load threads');
      setThreads(data.results || []);
      setTotalPages(Math.ceil((data.count || 0) / PAGE_SIZE));
      setTotalCount(data.count || 0);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Load tags
  const loadTags = async (page: number = 1, search: string = '') => {
    try {
      setLoading(true);
      setError(null);
      const searchParam = search.trim() ? `&search=${encodeURIComponent(search.trim())}` : '';
      const response = await fetch(`/api/tags/?page=${page}&page_size=${PAGE_SIZE}${searchParam}`, { credentials: 'include' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Failed to load tags');
      setTags(data.results || []);
      setTotalPages(Math.ceil((data.count || 0) / PAGE_SIZE));
      setTotalCount(data.count || 0);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Load data when tab changes
  useEffect(() => {
    setCurrentPage(1);
    setSearchQuery('');
    switch (activeTab) {
      case 'users':
        loadUsers(1, '');
        break;
      case 'threads':
        loadThreads(1, '');
        break;
      case 'tags':
        loadTags(1, '');
        break;
    }
  }, [activeTab]);

  // Handle page change
  const handlePageChange = (newPage: number) => {
    if (newPage < 1 || newPage > totalPages) return;
    setCurrentPage(newPage);
    switch (activeTab) {
      case 'users':
        loadUsers(newPage, searchQuery);
        break;
      case 'threads':
        loadThreads(newPage, searchQuery);
        break;
      case 'tags':
        loadTags(newPage, searchQuery);
        break;
    }
  };

  // Handle search
  const handleSearch = () => {
    setCurrentPage(1);
    switch (activeTab) {
      case 'users':
        loadUsers(1, searchQuery);
        break;
      case 'threads':
        loadThreads(1, searchQuery);
        break;
      case 'tags':
        loadTags(1, searchQuery);
        break;
    }
  };

  // Clear search
  const clearSearch = () => {
    const emptyQuery = '';
    setSearchQuery(emptyQuery);
    setCurrentPage(1);
    switch (activeTab) {
      case 'users':
        loadUsers(1, emptyQuery);
        break;
      case 'threads':
        loadThreads(1, emptyQuery);
        break;
      case 'tags':
        loadTags(1, emptyQuery);
        break;
    }
  };

  if (!hasAdminPrivileges) {
    return (
      <div className="p-3">
        <h2>Access Denied</h2>
        <p>You don't have permission to access the admin panel.</p>
        <Link to="/">← Back to Home</Link>
      </div>
    );
  }

  const renderContent = () => {
    if (loading) {
      return <div className="text-center p-4">Loading...</div>;
    }

    if (error) {
      return (
        <div className="text-danger p-3">
          <h3>Error: {error}</h3>
          <p>Please check the browser console for more details.</p>
        </div>
      );
    }

    switch (activeTab) {
      case 'users':
        return (
          <div>
            <div className="admin-content-header">
              <h3 className="admin-content-title">User Management ({totalCount} users)</h3>
            </div>
            {/* Search UI */}
            <div className="admin-search-container">
              <input
                className="admin-search-input"
                placeholder="Search users by username or email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
              <button 
                className="admin-search-btn"
                onClick={handleSearch}
              >
                Search
              </button>
              {searchQuery && (
                <button 
                  className="admin-clear-btn"
                  onClick={clearSearch}
                >
                  Clear
                </button>
              )}
            </div>
            <div className="admin-scroll-box">
              {users.map(user => (
                <div key={user.id} className="admin-content-item">
                  <div className="admin-content-item-body">
                    <div className="admin-content-item-title">
                      {user.is_admin && <span className="admin-status-admin"><i className="bi bi-shield-check"></i> </span>}
                      {user.is_staff && <span className="admin-status-staff"><i className="bi bi-person-badge"></i> </span>}
                      {user.is_banned && <span className="admin-status-banned"><i className="bi bi-ban"></i> </span>}
                      {user.username}
                    </div>
                    <div className="admin-content-item-meta">
                      {user.email} • Joined {new Date(user.date_joined).toLocaleDateString()}
                    </div>
                    <div className="admin-content-item-stats">
                      Threads: {user.thread_count || 0} • Replies: {user.reply_count || 0}
                    </div>
                  </div>
                  <div className="admin-content-item-actions">
                    {!user.is_admin && !user.is_staff && (
                      <button 
                        className={`admin-action-btn ${user.is_banned ? 'admin-unban-btn' : 'admin-ban-btn'}`}
                        onClick={async () => {
                          try {
                            const action = user.is_banned ? 'unban' : 'ban';
                            const response = await fetchJson(`/api/users/${user.id}/${action}/`, {
                              method: 'POST'
                            });
                            if (response.ok) {
                              // Reload users to reflect the change
                              loadUsers(currentPage, searchQuery);
                            } else {
                              const error = await response.json();
                              alert(`Failed to ${action} user: ${error.error || 'Unknown error'}`);
                            }
                          } catch (err) {
                            alert(`Failed to ${user.is_banned ? 'unban' : 'ban'} user`);
                          }
                        }}
                      >
                        {user.is_banned ? 'Unban' : 'Ban'}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      case 'threads':
        return (
          <div>
            <div className="admin-content-header">
              <h3 className="admin-content-title">Thread Management ({totalCount} threads)</h3>
            </div>
            {/* Search UI */}
            <div className="admin-search-container">
              <input
                className="admin-search-input"
                placeholder="Search threads by title or content..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
              <button 
                className="admin-search-btn"
                onClick={handleSearch}
              >
                Search
              </button>
              {searchQuery && (
                <button 
                  className="admin-clear-btn"
                  onClick={clearSearch}
                >
                  Clear
                </button>
              )}
            </div>
            <div className="admin-scroll-box">
              {threads.length === 0 ? (
                <div className="admin-empty-state">
                  No threads found
                </div>
              ) : (
                threads.map(thread => (
                  <div key={thread.id} className="admin-content-item-thread">
                    <div className="admin-content-item-body">
                      <div className="admin-content-item-title">
                        <Link to={`/threads/${thread.id}`} style={{ textDecoration: 'none', color: '#007bff' }}>
                          {thread.title || 'No Title'}
                        </Link>
                        {thread.is_deleted && <span className="admin-status-deleted">[Deleted]</span>}
                      </div>
                      <div className="admin-content-item-meta">
                        Author: {thread.is_anonymous ? `Anonymous#${thread.user_id}` : (thread.username || 'Unknown User')} • 
                        Category: {thread.category_name || 'Uncategorized'} • 
                        {thread.create_time ? new Date(thread.create_time).toLocaleDateString() : 'Unknown Date'}
                      </div>
                      <div className="admin-content-item-stats">
                        Replies: {thread.reply_count || 0} • Likes: {thread.like_count || 0}
                      </div>
                      <div className="admin-content-item-preview">
                        {thread.body ? thread.body.substring(0, 100) + '...' : 'No content'}
                      </div>
                    </div>
                  <div className="admin-content-item-actions">
                    <button 
                      className={`admin-action-btn ${thread.is_deleted ? 'admin-restore-btn' : 'admin-delete-btn'}`}
                      onClick={async () => {
                        try {
                          if (thread.is_deleted) {
                            // Restore thread
                            const response = await fetchJson(`/api/threads/${thread.id}/restore/`, {
                              method: 'POST'
                            });
                            if (response.ok) {
                              loadThreads(currentPage, searchQuery);
                            } else {
                              const error = await response.json();
                              alert(`Failed to restore thread: ${error.error || 'Unknown error'}`);
                            }
                          } else {
                            // Delete thread
                            const response = await fetchJson(`/api/threads/${thread.id}/`, {
                              method: 'DELETE'
                            });
                            if (response.ok) {
                              loadThreads(currentPage, searchQuery);
                            } else {
                              const error = await response.json();
                              alert(`Failed to delete thread: ${error.error || 'Unknown error'}`);
                            }
                          }
                        } catch (err) {
                          alert(`Failed to ${thread.is_deleted ? 'restore' : 'delete'} thread`);
                        }
                      }}
                    >
                      {thread.is_deleted ? 'Restore' : 'Delete'}
                    </button>
                  </div>
                  </div>
                ))
              )}
            </div>
          </div>
        );

      case 'tags':
        return (
          <div>
            <div className="admin-content-header">
              <h3 className="admin-content-title">Tag Management ({totalCount} tags)</h3>
            </div>
            {/* Search UI */}
            <div className="admin-search-container">
              <input
                className="admin-search-input"
                placeholder="Search tags by name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
              <button 
                className="admin-search-btn"
                onClick={handleSearch}
              >
                Search
              </button>
              {searchQuery && (
                <button 
                  className="admin-clear-btn"
                  onClick={clearSearch}
                >
                  Clear
                </button>
              )}
            </div>
            <div className="admin-scroll-box">
              {tags.map(tag => (
                <div key={tag.name} className="admin-content-item">
                  <div className="admin-content-item-body">
                    <div className="admin-content-item-title">
                      #{tag.name}
                    </div>
                    <div className="admin-content-item-stats">
                      Usage: {tag.thread_count || 0} • 
                      Status: {tag.is_active ? 'Active' : 'Disabled'}
                    </div>
                  </div>
                  <div className="admin-content-item-actions">
                    <button 
                      className={`admin-action-btn ${tag.is_active ? 'admin-disable-btn' : 'admin-enable-btn'}`}
                      onClick={async () => {
                        try {
                          const action = tag.is_active ? 'disable' : 'enable';
                          const response = await fetchJson(`/api/tags/${tag.name}/${action}/`, {
                            method: 'POST'
                          });
                          if (response.ok) {
                            // Reload tags to reflect the change
                            loadTags(currentPage, searchQuery);
                          } else {
                            const error = await response.json();
                            alert(`Failed to ${action} tag: ${error.error || 'Unknown error'}`);
                          }
                        } catch (err) {
                          alert(`Failed to ${tag.is_active ? 'disable' : 'enable'} tag`);
                        }
                      }}
                    >
                      {tag.is_active ? 'Disable' : 'Enable'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="admin-layout">
      {/* Left sidebar with buttons */}
      <div className="admin-sidebar">
        <div className="admin-sidebar-title">
          <h3 className="m-0 admin-title-sm"><i className="bi bi-shield-check"></i> Admin Panel</h3>
        </div>
        
        <button
          onClick={() => setActiveTab('users')}
          className={`admin-sidebar-btn ${activeTab === 'users' ? 'active' : 'inactive'}`}
        >
          👥 User Management
        </button>
        
        <button
          onClick={() => setActiveTab('threads')}
          className={`admin-sidebar-btn ${activeTab === 'threads' ? 'active' : 'inactive'}`}
        >
          📝 Thread Management
        </button>
        
        <button
          onClick={() => setActiveTab('tags')}
          className={`admin-sidebar-btn ${activeTab === 'tags' ? 'active' : 'inactive'}`}
        >
          <i className="bi bi-tags"></i> Tag Management
        </button>

        <div className="admin-sidebar-footer">
          <Link to="/" className="d-block text-info text-decoration-underline small mb-2">← Back to Home</Link>
          <Link to="/me" className="d-block text-info text-decoration-underline small"><i className="bi bi-file-text"></i> My Content</Link>
        </div>
      </div>

      {/* Right content area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {renderContent()}
        
        {/* Pagination */}
        {totalPages > 1 && (
          <div className="admin-pagination">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage <= 1}
              className="btn btn-outline-primary"
            >
              Previous
            </button>
            
            <span>
              Page {currentPage} of {totalPages}
            </span>
            
            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage >= totalPages}
              className="btn btn-outline-primary"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminPanel;
