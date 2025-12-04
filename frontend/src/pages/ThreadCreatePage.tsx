import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { createThread } from '../api/threads';
import { listCategories } from '../api/categories';
import { useAuth } from '../context/AuthContext';
import TagInput from '../components/TagInput';
import type { Category } from '../api/categories';

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

const ThreadCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const { isAnonymous, isAdmin, isStaff, isSuperuser } = useAuth() as any;
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [categoryId, setCategoryId] = useState<number | ''>('');
  const [tags, setTags] = useState<string[]>([]);

  useEffect(() => {
    (async () => {
      const cats = await listCategories();
      setCategories(cats);
    })();
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (!categoryId) {
        throw new Error('Please select a category');
      }
      const tag_names = tags;
      // Admin/Staff/Superuser should not post anonymously
      const shouldBeAnonymous = isAnonymous && !(isAdmin || isStaff || isSuperuser);
      const res = await createThread({ 
        title, 
        body, 
        category_id: Number(categoryId),
        is_anonymous: shouldBeAnonymous,
        tag_names
      });
      navigate(`/threads/${res.id}`, { replace: true });
    } catch (err: any) {
      setError(err.message || 'Failed to create');
    } finally {
      setBusy(false);
    }
  }

  const selectedCategory = categories.find(c => c.id === categoryId);
  const categoryColor = selectedCategory ? getCategoryColor(selectedCategory.name) : '#6c757d';

  return (
    <div className="py-4">
      {/* Navigation */}
      <div className="row mb-4">
        <div className="col-12">
          <div className="d-flex justify-content-between align-items-center">
            <Link to="/" className="btn btn-outline-secondary">
              <i className="bi bi-arrow-left"></i> Back to Threads
            </Link>
            {(isAdmin || isStaff || isSuperuser) && (
              <Link to="/admin" className="btn btn-outline-success btn-sm">
                <i className="bi bi-shield-check"></i> Admin Panel
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Page Header */}
      <div className="row mb-4">
        <div className="col-12">
          <div className="text-center">
            <h1 className="display-6 fw-bold text-primary mb-2">
              <i className="bi bi-plus-circle"></i> Create New Thread
            </h1>
            <p className="lead text-muted">Share your thoughts and start a conversation</p>
          </div>
        </div>
      </div>

      {/* Status Banner */}
      <div className="row mb-4">
        <div className="col-12">
          <div className={`alert ${(isAdmin||isStaff||isSuperuser) ? 'alert-info' : (isAnonymous ? 'alert-secondary' : 'alert-info')} border-0 shadow-sm`}>
            <div className="d-flex align-items-start">
              <div className="me-3 flex-shrink-0">
                {(isAdmin||isStaff||isSuperuser) ? 
                  <i className="bi bi-shield-check fs-4"></i> : 
                  (isAnonymous ? 
                    <i className="bi bi-person-x fs-4"></i> : 
                    <i className="bi bi-person fs-4"></i>
                  )
                }
              </div>
              <div className="flex-grow-1">
                <div className="fw-bold mb-1">
                  {(isAdmin||isStaff||isSuperuser) ? 
                    'Admin Mode' : 
                    (isAnonymous ? 
                      'Anonymous Mode' : 
                      'Normal Mode'
                    )
                  }
                </div>
                <div className="small text-muted">
                  {(isAdmin||isStaff||isSuperuser) ? 
                    'Posts will use your username' : 
                    (isAnonymous ? 
                      'This thread will be posted anonymously' : 
                      'This thread will be posted with your username'
                    )
                  }
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Create Thread Card */}
      <div className="row justify-content-center">
        <div className="col-12 col-lg-10 col-xl-8">
          <div className="card thread-create-card fade-in shadow-lg border-0" style={{ borderRadius: 'var(--radius-lg)' }}>
            {/* Category color bar preview */}
            {selectedCategory && (
              <div 
                className="category-color-bar" 
                style={{ 
                  backgroundColor: categoryColor,
                  height: '4px',
                  borderRadius: 'var(--radius-lg) var(--radius-lg) 0 0'
                }}
              />
            )}
            <div className="card-body p-5">
              
              <form onSubmit={onSubmit}>
                {/* Thread Title Section */}
                <div className="form-section mb-5">
                  <div className="form-section-header mb-3">
                    <h3 className="h5 fw-semibold text-dark mb-1">
                      <i className="bi bi-pencil-square text-primary me-2"></i>
                      Thread Title
                    </h3>
                    <p className="text-muted small mb-0">Give your thread a clear, descriptive title</p>
                  </div>
                  <input
                    id="title"
                    type="text"
                    className="form-control"
                    value={title}
                    onChange={e => setTitle(e.target.value)}
                    placeholder="Enter thread title"
                    required
                    maxLength={120}
                  />
                  <div className="form-text d-flex justify-content-between">
                    <span className="text-muted">Keep it concise and descriptive</span>
                    <span className={`fw-medium ${title.length > 100 ? 'text-warning' : 'text-muted'}`}>
                      {title.length}/120 characters
                    </span>
                  </div>
                </div>

                {/* Thread Content Section */}
                <div className="form-section mb-5">
                  <div className="form-section-header mb-3">
                    <h3 className="h5 fw-semibold text-dark mb-1">
                      <i className="bi bi-file-text text-primary me-2"></i>
                      Thread Content
                    </h3>
                    <p className="text-muted small mb-0">Share your thoughts, questions, or ideas</p>
                  </div>
                  <textarea
                    id="body"
                    className="form-control"
                    rows={8}
                    value={body}
                    onChange={e => setBody(e.target.value)}
                    placeholder="Write your thread content here..."
                    required
                    maxLength={2000}
                    style={{ minHeight: '200px' }}
                  />
                  <div className="form-text d-flex justify-content-between">
                    <span className="text-muted">Be clear and provide context</span>
                    <span className={`fw-medium ${body.length > 1800 ? 'text-warning' : 'text-muted'}`}>
                      {body.length}/2000 characters
                    </span>
                  </div>
                </div>

                {/* Category and Tags Row */}
                <div className="row mb-5">
                  {/* Category Section */}
                  <div className="col-md-6">
                    <div className="form-section">
                      <select
                        id="category"
                        className="form-select"
                        value={categoryId}
                        onChange={e => setCategoryId(e.target.value ? Number(e.target.value) : '')}
                        required
                      >
                        <option value="">Select a category</option>
                        {categories.map(c => (
                          <option key={c.id} value={c.id}>{c.name}</option>
                        ))}
                      </select>
                      {selectedCategory && (
                        <div className="mt-3">
                          <div className="d-flex align-items-center">
                            <span 
                              className="badge text-white me-2 fs-6" 
                              style={{ backgroundColor: categoryColor }}
                            >
                              {selectedCategory.name}
                            </span>
                            <small className="text-muted">Preview color</small>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Tags Section */}
                  <div className="col-md-6">
                    <div className="form-section">
                      <TagInput
                        value={tags}
                        onChange={setTags}
                        placeholder="Add tags"
                      />
                    </div>
                  </div>
                </div>

                {error && (
                  <div className="alert alert-danger alert-dismissible fade show border-0 shadow-sm" role="alert">
                    <div className="d-flex align-items-center">
                      <i className="bi bi-exclamation-triangle-fill me-3 fs-5"></i>
                      <div className="flex-grow-1">
                        <strong>Error creating thread</strong>
                        <div className="small">{error}</div>
                      </div>
                      <button type="button" className="btn-close" onClick={() => setError(null)}></button>
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="form-actions pt-4 border-top">
                  <div className="d-flex justify-content-between align-items-center gap-3">
                    <Link to="/" className="btn btn-outline-secondary px-3">
                      <i className="bi bi-x-circle me-2"></i>
                      Cancel
                    </Link>
                    <button 
                      type="submit" 
                      className="btn btn-primary px-4"
                      disabled={busy || !title.trim() || !body.trim() || !categoryId}
                    >
                      {busy ? (
                        <>
                          <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                          Creating...
                        </>
                      ) : (
                        <>
                          <i className="bi bi-plus-circle me-2"></i>
                          Create Thread
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ThreadCreatePage;