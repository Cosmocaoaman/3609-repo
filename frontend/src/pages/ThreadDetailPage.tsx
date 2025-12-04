import { fetchJson } from '../api/client';
import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getThread, deleteThread } from '../api/threads';
import type { ThreadDetail } from '../api/threads';
import { listReplies, createReply, deleteReply, toggleThreadLike, toggleReplyLike } from '../api/replies';
import type { ReplyItem } from '../api/replies';
import { useAuth } from '../context/AuthContext';

// Category color mapping (same as ThreadsListPage)
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

async function recordViewed(threadId: number) {
  try {
    await fetchJson(`/api/threads/${threadId}/viewed/`, { method: 'POST' })
  } catch {}
}

import ThreadEditModal from '../components/ThreadEditModal';
import ReplyEditForm from '../components/ReplyEditForm';
import ConfirmDeleteModal from '../components/ConfirmDeleteModal';

const ThreadDetailPage: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { userId, isAnonymous, isAdmin, isStaff, isSuperuser } = useAuth() as any;
  const [thread, setThread] = useState<ThreadDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [replies, setReplies] = useState<ReplyItem[]>([]);
  const [replyBody, setReplyBody] = useState('');
  const [likeCount, setLikeCount] = useState<number | null>(null);
  
  // Edit and delete states
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingReplyId, setEditingReplyId] = useState<number | null>(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleteType, setDeleteType] = useState<'thread' | 'reply'>('thread');
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const data = await getThread(Number(id));
        setThread(data);
        setLikeCount((data as any).like_count ?? null);
        const rs = await listReplies(Number(id));
        setReplies(rs);
        // Record viewing (dedup is handled on server side)
        await recordViewed(Number(id));
      } catch (err: any) {
        setError(err.message);
      }
    })();
  }, [id]);

  // Handle thread edit success
  const handleThreadEditSuccess = (updatedThread: ThreadDetail) => {
    setThread(updatedThread);
  };

  // Handle reply edit success
  const handleReplyEditSuccess = (updatedReply: ReplyItem) => {
    setReplies(prev => prev.map(r => r.id === updatedReply.id ? updatedReply : r));
    setEditingReplyId(null);
  };

  // Handle delete confirmation
  const handleDeleteConfirm = async () => {
    if (!deleteId) return;
    setDeleteLoading(true);
    try {
      if (deleteType === 'thread') {
        await deleteThread(deleteId);
        navigate('/', { replace: true });
      } else {
        await deleteReply(deleteId);
        setReplies(prev => prev.filter(r => r.id !== deleteId));
      }
      setDeleteModalOpen(false);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setDeleteLoading(false);
    }
  };

  // Open delete modal
  const openDeleteModal = (type: 'thread' | 'reply', id: number) => {
    setDeleteType(type);
    setDeleteId(id);
    setDeleteModalOpen(true);
  };

  // Handle reply submission
  const handleReplySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!replyBody.trim() || !id) return;
    try {
      // Admin/Staff/Superuser should not post anonymously
      const shouldBeAnonymous = isAnonymous && !(isAdmin || isStaff || isSuperuser);
      const newReply = await createReply(Number(id), replyBody.trim(), shouldBeAnonymous);
      setReplies(prev => [...prev, newReply]);
      setReplyBody('');
    } catch (err: any) {
      setError(err.message);
    }
  };

  // Check if user is author
  const isAuthor = (authorId?: number) => {
    return userId && authorId && userId === authorId;
  };

  if (error) return <div className="text-danger">{error}</div>;
  if (!thread) return <div className="p-3">Loading...</div>;

  const categoryName = thread.category_name || (thread as any).category?.name;
  const categoryColor = categoryName ? getCategoryColor(categoryName) : '#6c757d';

  return (
    <div className="py-4">
      {/* Navigation */}
      <div className="row mb-4">
        <div className="col-12">
          <div className="d-flex justify-content-between align-items-center">
            <Link to="/" className="btn btn-outline-secondary">
              ← Back to Threads
            </Link>
            {(isAdmin || isStaff || isSuperuser) && (
              <Link to="/admin" className="btn btn-outline-success btn-sm">
                Admin Panel
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Thread Detail Card */}
      <div className="row mb-4">
        <div className="col-12">
          <div className="card thread-detail-card fade-in" style={{ borderRadius: 'var(--radius-lg)' }}>
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
            <div className="card-body p-4">
              {/* Thread header */}
              <div className="d-flex justify-content-between align-items-start mb-4">
                <div className="flex-grow-1">
                  <h1 className="thread-title mb-3">{thread.title}</h1>
                  <div className="thread-meta mb-3">
                    <span className="text-muted me-3">
                      By {thread.author_display_name || thread.author?.username || 'Unknown'}
                    </span>
                    <span className="text-muted me-3">
                      {new Date(thread.create_time || '').toLocaleString()}
                    </span>
                    {thread.edit_time && thread.edit_time !== thread.create_time && (
                      <span className="text-muted small">
                        (edited at {new Date(thread.edit_time).toLocaleString()})
                      </span>
                    )}
                    {categoryName && (
                      <span className="ms-3">
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
                {(isAuthor(thread.author?.id) || isAdmin || isStaff || isSuperuser) && (
                  <div className="d-flex gap-2">
                    {isAuthor(thread.author?.id) && (
                      <button
                        onClick={() => setIsEditModalOpen(true)}
                        className="btn btn-outline-primary btn-sm"
                      >
                        Edit
                      </button>
                    )}
                    <button
                      onClick={() => openDeleteModal('thread', thread.id)}
                      className="btn btn-outline-danger btn-sm"
                    >
                      Delete
                    </button>
                  </div>
                )}
              </div>

              {/* Thread content */}
              <div className="thread-content mb-4">{thread.body}</div>

              {/* Tags */}
              {Array.isArray((thread as any).tags) && (thread as any).tags.length > 0 && (
                <div className="mb-3 d-flex gap-1 flex-wrap">
                  {(thread as any).tags.map((tt: any, idx: number) => (
                    <Link 
                      key={idx} 
                      to={`/threads?tag=${encodeURIComponent(tt.tag?.name || '')}`} 
                      className="text-decoration-none chip chip-primary"
                    >
                      #{tt.tag?.name}
                    </Link>
                  ))}
                </div>
              )}
              {Array.isArray((thread as any).tags_flat) && (thread as any).tags_flat.length > 0 && (
                <div className="mb-3 d-flex gap-1 flex-wrap">
                  {(thread as any).tags_flat.map((name: string, idx: number) => (
                    <Link 
                      key={idx} 
                      to={`/threads?tag=${encodeURIComponent(name)}`} 
                      className="text-decoration-none chip chip-primary"
                    >
                      #{name}
                    </Link>
                  ))}
                </div>
              )}

              {/* Like button */}
              <div className="d-flex justify-content-between align-items-center">
                <button 
                  className="btn btn-outline-primary btn-sm" 
                  onClick={async () => {
                    const res = await toggleThreadLike(Number(id));
                    setLikeCount(res.like_count);
                  }}
                >
                  <i className="bi bi-heart"></i> Like ({likeCount ?? (thread as any).like_count ?? 0})
                </button>
                <span className="text-muted small">
                  {replies.length} {replies.length === 1 ? 'reply' : 'replies'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Reply Form */}
      <div className="row mb-4">
        <div className="col-12">
          <div className="card fade-in" style={{ borderRadius: 'var(--radius-lg)' }}>
            <div className="card-body p-4">
              <h5 className="card-title mb-3">Add a Reply</h5>
              <form onSubmit={handleReplySubmit}>
                <div className="mb-3">
                  <textarea
                    className="form-control"
                    rows={4}
                    placeholder="Write your reply..."
                    value={replyBody}
                    onChange={(e) => setReplyBody(e.target.value)}
                    required
                  />
                </div>
                <div className="d-flex justify-content-end">
                  <button 
                    type="submit" 
                    className="btn btn-primary"
                    disabled={!replyBody.trim()}
                  >
                    Post Reply
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>

      {/* Replies Section */}
      <div className="row">
        <div className="col-12">
          <h4 className="mb-4">Replies ({replies.length})</h4>
          <div className="d-grid gap-3">
            {replies.map(r => (
              <div key={r.id} className="card reply-card fade-in" style={{ borderRadius: 'var(--radius-lg)' }}>
                <div className="card-body p-4">
                  {editingReplyId === r.id ? (
                    <ReplyEditForm
                      reply={r}
                      threadId={Number(id)}
                      onSuccess={handleReplyEditSuccess}
                      onCancel={() => setEditingReplyId(null)}
                    />
                  ) : (
                    <>
                      <div className="d-flex justify-content-between align-items-start mb-3">
                        <div className="text-muted small">
                          <strong>{r.author_display_name || r.author?.username || 'Unknown'}</strong>
                          <span className="ms-2">
                            {new Date(r.create_time || '').toLocaleString()}
                          </span>
                          {r.edit_time && r.edit_time !== r.create_time && (
                            <span className="small ms-2">
                              (edited at {new Date(r.edit_time).toLocaleString()})
                            </span>
                          )}
                        </div>
                        {(isAuthor(r.author?.id) || isAdmin || isStaff || isSuperuser) && (
                          <div className="d-flex gap-2">
                            {isAuthor(r.author?.id) && (
                              <button
                                onClick={() => setEditingReplyId(r.id)}
                                className="btn btn-outline-primary btn-sm"
                              >
                                Edit
                              </button>
                            )}
                            <button
                              onClick={() => openDeleteModal('reply', r.id)}
                              className="btn btn-outline-danger btn-sm"
                            >
                              Delete
                            </button>
                          </div>
                        )}
                      </div>
                      <div className="reply-content mb-3">{r.body}</div>
                      <div className="d-flex justify-content-between align-items-center">
                        <button 
                          className="btn btn-outline-primary btn-sm" 
                          onClick={async () => {
                            const res = await toggleReplyLike(r.id);
                            setReplies(prev => prev.map(x => x.id === r.id ? { ...x, like_count: res.like_count } : x));
                          }}
                        >
                          <i className="bi bi-heart"></i> Like ({r.like_count ?? 0})
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </div>
            ))}
            {replies.length === 0 && (
              <div className="text-center text-muted py-4">
                No replies yet. Be the first to reply!
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      <ThreadEditModal
        thread={thread}
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        onSuccess={handleThreadEditSuccess}
      />

      <ConfirmDeleteModal
        isOpen={deleteModalOpen}
        title={deleteType === 'thread' ? 'Delete Thread' : 'Delete Reply'}
        message={deleteType === 'thread' 
          ? 'Are you sure you want to delete this thread? This action cannot be undone.' 
          : 'Are you sure you want to delete this reply? This action cannot be undone.'
        }
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeleteModalOpen(false)}
        loading={deleteLoading}
      />
    </div>
  );
};

export default ThreadDetailPage;