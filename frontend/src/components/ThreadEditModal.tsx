import React, { useState, useEffect, useMemo } from 'react';
import { updateThread } from '../api/threads';
import type { ThreadDetail } from '../api/threads';

interface ThreadEditModalProps {
  thread: ThreadDetail;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (updatedThread: ThreadDetail) => void;
}

const ThreadEditModal: React.FC<ThreadEditModalProps> = ({
  thread,
  isOpen,
  onClose,
  onSuccess
}) => {
  const [title, setTitle] = useState(thread?.title ?? '');
  const [body, setBody] = useState(thread?.body ?? '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Enhanced tag input states
  const [tags, setTags] = useState<string[]>([]);
  const [isTagging, setIsTagging] = useState(false);
  const [tagDraft, setTagDraft] = useState('');

  const tagColors = useMemo(() => [
    '#0d6efd', // primary
    '#198754', // success
    '#6f42c1', // purple
    '#d63384', // pink
    '#fd7e14', // orange
    '#20c997', // teal
    '#6c757d', // secondary
    '#6610f2', // indigo
  ], []);

  function colorForTag(name: string): string {
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
    }
    return tagColors[hash % tagColors.length];
  }

  useEffect(() => {
    if (isOpen && thread) {
      setTitle(thread.title ?? '');
      setBody(thread.body ?? '');
      setTags((thread as any)?.tag_names || []);
      setError(null);
    }
  }, [isOpen, thread]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!thread) return;

    setLoading(true);
    setError(null);

    try {
      const updatedThread = await updateThread(thread.id, {
        title: title.trim(),
        body: body.trim(),
        category_id: thread.category_id,
        tag_names: tags
      });
      onSuccess(updatedThread);
      onClose();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setTitle(thread?.title || '');
    setBody(thread?.body || '');
    setTags((thread as any)?.tag_names || []);
    setError(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '24px',
        borderRadius: '8px',
        width: '90%',
        maxWidth: '600px',
        maxHeight: '80vh',
        overflow: 'auto'
      }}>
        <h2 style={{ marginTop: 0, marginBottom: '16px' }}>Edit Thread</h2>
        
        {error && (
          <div style={{
            backgroundColor: '#fee',
            color: '#c33',
            padding: '8px',
            borderRadius: '4px',
            marginBottom: '16px'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '16px' }}>
          <div>
            <label htmlFor="title" style={{ display: 'block', marginBottom: '4px', fontWeight: 'bold' }}>
              Title
            </label>
            <input
              id="title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              maxLength={120}
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '16px'
              }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
              {title.length}/120 characters
            </div>
          </div>

          <div>
            <label htmlFor="body" style={{ display: 'block', marginBottom: '4px', fontWeight: 'bold' }}>
              Content
            </label>
            <textarea
              id="body"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              required
              maxLength={2000}
              rows={8}
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '16px',
                resize: 'vertical'
              }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
              {(body?.length ?? 0)}/2000 characters
            </div>
          </div>

          <div>
            <label htmlFor="tags" style={{ display: 'block', marginBottom: '4px', fontWeight: 'bold' }}>
              Tags
            </label>
            <div style={{ 
              border: '1px solid #ddd', 
              borderRadius: '4px', 
              padding: '8px', 
              minHeight: '44px',
              display: 'flex',
              flexWrap: 'wrap',
              gap: '8px',
              alignItems: 'center'
            }}>
              {/* Existing tags as colored chips */}
              {tags.map(t => (
                <span
                  key={t}
                  style={{ 
                    backgroundColor: colorForTag(t), 
                    color: 'white', 
                    fontWeight: 600,
                    padding: '4px 8px',
                    borderRadius: '16px',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                  title={`#${t}`}
                >
                  <span>#{t}</span>
                  <button
                    type="button"
                    aria-label={`Remove tag ${t}`}
                    onClick={() => setTags(prev => prev.filter(x => x !== t))}
                    style={{ 
                      background: 'none',
                      border: 'none',
                      color: 'white',
                      cursor: 'pointer',
                      padding: '2px 4px',
                      fontSize: '14px',
                      lineHeight: 1
                    }}
                  >
                    ×
                  </button>
                </span>
              ))}

              {/* Draft chip while typing */}
              {isTagging && (
                <span
                  style={{ 
                    backgroundColor: '#adb5bd', 
                    color: 'white', 
                    fontWeight: 600,
                    padding: '4px 8px',
                    borderRadius: '16px',
                    display: 'inline-flex',
                    alignItems: 'center'
                  }}
                >
                  #{tagDraft || '…'}
                </span>
              )}

              {/* Invisible input just to capture key events */}
              <input
                id="tags"
                type="text"
                style={{ 
                  border: 'none', 
                  outline: 'none', 
                  flex: 1,
                  minWidth: '120px',
                  fontSize: '16px'
                }}
                placeholder={isTagging ? 'Type tag content, press Enter to confirm' : 'Type # to start a tag, press Enter to confirm'}
                onKeyDown={(e) => {
                  // Start tag mode when '#'
                  if (e.key === '#') {
                    if (!isTagging) {
                      setIsTagging(true);
                      setTagDraft('');
                    }
                    e.preventDefault();
                    return;
                  }

                  // If drafting, handle composing
                  if (isTagging) {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      const cleaned = tagDraft.trim().toLowerCase();
                      if (cleaned && !tags.includes(cleaned)) {
                        setTags(prev => [...prev, cleaned]);
                      }
                      setIsTagging(false);
                      setTagDraft('');
                      return;
                    }
                    if (e.key === 'Backspace') {
                      e.preventDefault();
                      setTagDraft(prev => prev.slice(0, -1));
                      return;
                    }
                    if (e.key === 'Escape') {
                      e.preventDefault();
                      setIsTagging(false);
                      setTagDraft('');
                      return;
                    }
                    // Allow valid characters only for tags
                    const isSingleChar = e.key.length === 1;
                    if (isSingleChar) {
                      const ch = e.key;
                      const valid = /[a-zA-Z0-9_-]/.test(ch);
                      if (valid) {
                        e.preventDefault();
                        setTagDraft(prev => (prev + ch));
                        return;
                      }
                      // ignore others while drafting
                      e.preventDefault();
                      return;
                    }
                  }
                }}
              />
            </div>
            <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
              Type "#" to start a tag, press Enter to confirm. Click "×" to remove.
            </div>
          </div>

          <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
            <button
              type="button"
              onClick={handleCancel}
              disabled={loading}
              style={{
                padding: '8px 16px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                backgroundColor: 'white',
                cursor: loading ? 'not-allowed' : 'pointer'
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !title.trim() || !body.trim()}
              style={{
                padding: '8px 16px',
                border: 'none',
                borderRadius: '4px',
                backgroundColor: loading ? '#ccc' : '#007bff',
                color: 'white',
                cursor: loading ? 'not-allowed' : 'pointer'
              }}
            >
              {loading ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ThreadEditModal;
