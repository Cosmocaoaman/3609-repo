import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { listThreads, type ThreadSummary, getThread, updateThread, deleteThread } from '../api/threads';
import { listReplies, type ReplyItem, updateReply, deleteReply } from '../api/replies';
import ThreadEditModal from '../components/ThreadEditModal';
import ReplyEditForm from '../components/ReplyEditForm';
import ConfirmDeleteModal from '../components/ConfirmDeleteModal';

export default function MyContentPage() {
  const { userId } = useAuth() as any;
  const [myThreads, setMyThreads] = useState<ThreadSummary[]>([]);
  const [myReplies, setMyReplies] = useState<ReplyItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // edit/delete state
  const [editingThreadId, setEditingThreadId] = useState<number | null>(null);
  const [editingReplyId, setEditingReplyId] = useState<number | null>(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleteType, setDeleteType] = useState<'thread' | 'reply'>('thread');
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  async function loadData() {
    if (!userId) return;
    try {
      setLoading(true);
      setError(null);
      // Load first page of threads and replies, then filter by author id
      const [threadsRes, repliesRes] = await Promise.all([
        listThreads(1) as any,
        fetch('/api/replies/?page=1', { credentials: 'include' }).then(r => r.json())
      ]);
      const threads: ThreadSummary[] = (threadsRes.results ?? threadsRes) as ThreadSummary[];
      const replies: ReplyItem[] = (repliesRes.results ?? repliesRes) as ReplyItem[];
      setMyThreads(threads.filter(t => (t as any).author?.id === userId));
      setMyReplies(replies.filter(r => (r as any).author?.id === userId));
    } catch (e: any) {
      setError(e?.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  const currentEditingThread = editingThreadId ? myThreads.find(t => t.id === editingThreadId) : undefined;

  async function handleDeleteConfirm() {
    if (!deleteId) return;
    setDeleteLoading(true);
    try {
      if (deleteType === 'thread') {
        await deleteThread(deleteId);
        setMyThreads(prev => prev.filter(t => t.id !== deleteId));
      } else {
        await deleteReply(deleteId);
        setMyReplies(prev => prev.filter(r => r.id !== deleteId));
      }
      setDeleteModalOpen(false);
    } catch (e: any) {
      setError(e?.message || 'Delete failed');
    } finally {
      setDeleteLoading(false);
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
                <i className="bi bi-file-text"></i>
              </span>
              <h1 className="h3 mb-0 fw-semibold">My Content</h1>
            </div>
            <Link to="/threads" className="btn btn-outline-secondary btn-sm">
              <i className="bi bi-arrow-left me-2"></i>Back to Threads
            </Link>
          </div>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="row mb-4">
          <div className="col-12">
            <div className="alert alert-danger">
              <i className="bi bi-exclamation-triangle me-2"></i>{error}
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="row mb-4">
          <div className="col-12">
            <div className="d-flex justify-content-center py-5">
              <div className="d-flex align-items-center text-muted">
                <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                Loading your content...
              </div>
            </div>
          </div>
        </div>
      )}

      {/* My Threads Section */}
      <div className="row mb-5">
        <div className="col-12">
          <div className="card fade-in shadow-sm border-0" style={{ borderRadius: 'var(--radius-lg)' }}>
            <div className="card-body p-4">
              <div className="d-flex align-items-center gap-2 mb-4">
                <span className="section-icon text-primary" aria-hidden="true">
                  <i className="bi bi-chat-dots"></i>
                </span>
                <h2 className="h4 mb-0 fw-semibold">My Threads</h2>
              </div>

              {!loading && myThreads.length === 0 && (
                <div className="empty-state">
                  <i className="bi bi-chat-dots text-muted" style={{ fontSize: '3rem' }}></i>
                  <h3 className="h5 text-muted mt-3">No threads yet</h3>
                  <p className="text-muted mb-0">Start a conversation by creating your first thread!</p>
                  <Link to="/threads/new" className="btn btn-primary mt-3">
                    <i className="bi bi-plus-circle me-2"></i>Create Thread
                  </Link>
                </div>
              )}

              {!loading && myThreads.length > 0 && (
                <div className="row g-3">
                  {myThreads.map(t => (
                    <div key={t.id} className="col-12">
                      <div className="card fade-in shadow-sm border-0 h-100" style={{ borderRadius: 'var(--radius-lg)' }}>
                        <div className="card-body p-3">
                          <div className="d-flex justify-content-between align-items-start">
                            <div className="flex-grow-1">
                              <h5 className="card-title mb-2">
                                <Link to={`/threads/${t.id}`} className="text-decoration-none">
                                  {t.title}
                                </Link>
                              </h5>
                              <div className="d-flex align-items-center gap-3 text-muted small">
                                <span><i className="bi bi-person me-1"></i>{t.author_display_name}</span>
                                <span><i className="bi bi-calendar me-1"></i>{t.create_time ? new Date(t.create_time).toLocaleDateString() : 'Unknown date'}</span>
                              </div>
                            </div>
                            <div className="d-flex gap-2">
                              <button 
                                className="btn btn-outline-primary btn-sm"
                                onClick={() => setEditingThreadId(t.id)}
                              >
                                <i className="bi bi-pencil me-1"></i>Edit
                              </button>
                              <button 
                                className="btn btn-outline-danger btn-sm"
                                onClick={() => { setDeleteType('thread'); setDeleteId(t.id); setDeleteModalOpen(true); }}
                              >
                                <i className="bi bi-trash me-1"></i>Delete
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* My Replies Section */}
      <div className="row">
        <div className="col-12">
          <div className="card fade-in shadow-sm border-0" style={{ borderRadius: 'var(--radius-lg)' }}>
            <div className="card-body p-4">
              <div className="d-flex align-items-center gap-2 mb-4">
                <span className="section-icon text-primary" aria-hidden="true">
                  <i className="bi bi-reply"></i>
                </span>
                <h2 className="h4 mb-0 fw-semibold">My Replies</h2>
              </div>

              {!loading && myReplies.length === 0 && (
                <div className="empty-state">
                  <i className="bi bi-reply text-muted" style={{ fontSize: '3rem' }}></i>
                  <h3 className="h5 text-muted mt-3">No replies yet</h3>
                  <p className="text-muted mb-0">Join the conversation by replying to threads!</p>
                </div>
              )}

              {!loading && myReplies.length > 0 && (
                <div className="row g-3">
                  {myReplies.map(r => (
                    <div key={r.id} className="col-12">
                      <div className="card fade-in shadow-sm border-0 h-100" style={{ borderRadius: 'var(--radius-lg)' }}>
                        <div className="card-body p-3">
                          {editingReplyId === r.id ? (
                            <ReplyEditForm
                              reply={r}
                              threadId={(r as any).thread?.id || 0}
                              onSuccess={(updated) => { setMyReplies(prev => prev.map(x => x.id === r.id ? updated : x)); setEditingReplyId(null); }}
                              onCancel={() => setEditingReplyId(null)}
                            />
                          ) : (
                            <div className="d-flex justify-content-between align-items-start">
                              <div className="flex-grow-1">
                                <div className="d-flex align-items-center gap-3 text-muted small mb-2">
                                  <span><i className="bi bi-person me-1"></i>{r.author_display_name}</span>
                                  <span><i className="bi bi-calendar me-1"></i>{r.create_time ? new Date(r.create_time).toLocaleDateString() : 'Unknown date'}</span>
                                </div>
                                <div className="reply-content">
                                  {r.body.length > 200 ? `${r.body.substring(0, 200)}...` : r.body}
                                </div>
                                {(r as any).thread?.title && (
                                  <div className="mt-2">
                                    <Link to={`/threads/${(r as any).thread?.id}`} className="text-decoration-none small">
                                      <i className="bi bi-arrow-up-right me-1"></i>
                                      Reply to: {(r as any).thread.title}
                                    </Link>
                                  </div>
                                )}
                              </div>
                              <div className="d-flex gap-2">
                                <button 
                                  className="btn btn-outline-primary btn-sm"
                                  onClick={() => setEditingReplyId(r.id)}
                                >
                                  <i className="bi bi-pencil me-1"></i>Edit
                                </button>
                                <button 
                                  className="btn btn-outline-danger btn-sm"
                                  onClick={() => { setDeleteType('reply'); setDeleteId(r.id); setDeleteModalOpen(true); }}
                                >
                                  <i className="bi bi-trash me-1"></i>Delete
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Modals */}
      {currentEditingThread && (
        <ThreadEditModal
          thread={currentEditingThread as any}
          isOpen={!!editingThreadId}
          onClose={() => setEditingThreadId(null)}
          onSuccess={(updated) => setMyThreads(prev => prev.map(t => t.id === updated.id ? updated : t))}
        />
      )}

      <ConfirmDeleteModal
        isOpen={deleteModalOpen}
        title={deleteType === 'thread' ? 'Delete Thread' : 'Delete Reply'}
        message={deleteType === 'thread' ? 'Are you sure you want to delete this thread?' : 'Are you sure you want to delete this reply?'}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeleteModalOpen(false)}
        loading={deleteLoading}
      />
    </div>
  );
}


