import React, { useState, useEffect } from 'react';
import { listTags, createTag, updateTag, deleteTag, type Tag } from '../api/tags';

const TagManagement: React.FC = () => {
  const [tags, setTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newTagName, setNewTagName] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    loadTags();
  }, []);

  const loadTags = async () => {
    try {
      setLoading(true);
      setError(null);
      const tagList = await listTags();
      setTags(tagList);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTag = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTagName.trim()) return;

    try {
      setIsCreating(true);
      setError(null);
      const newTag = await createTag({ name: newTagName.trim() });
      setTags(prev => Array.isArray(prev) ? [...prev, newTag].sort((a, b) => a.name.localeCompare(b.name)) : [newTag]);
      setNewTagName('');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsCreating(false);
    }
  };

  const handleToggleTag = async (tag: Tag) => {
    try {
      setError(null);
      const updatedTag = await updateTag(tag.name, { is_active: !tag.is_active });
      setTags(prev => Array.isArray(prev) ? prev.map(t => t.name === tag.name ? updatedTag : t) : [updatedTag]);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteTag = async (tag: Tag) => {
    if (!window.confirm(`Are you sure you want to disable the tag "${tag.name}"?`)) {
      return;
    }

    try {
      setError(null);
      await deleteTag(tag.name);
      setTags(prev => Array.isArray(prev) ? prev.map(t => t.name === tag.name ? { ...t, is_active: false } : t) : []);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const activeTags = Array.isArray(tags) ? tags.filter(tag => tag.is_active) : [];
  const inactiveTags = Array.isArray(tags) ? tags.filter(tag => !tag.is_active) : [];

  return (
    <div style={{ padding: '16px' }}>
      <h2>Tag Management</h2>
      
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

      {/* Create new tag */}
      <div style={{ marginBottom: '24px', padding: '16px', border: '1px solid #ddd', borderRadius: '8px' }}>
        <h3 style={{ marginTop: 0 }}>Create New Tag</h3>
        <form onSubmit={handleCreateTag} style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <input
            type="text"
            placeholder="Tag name (e.g., python, react)"
            value={newTagName}
            onChange={(e) => setNewTagName(e.target.value)}
            style={{
              padding: '8px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              flex: 1,
              maxWidth: '300px'
            }}
            disabled={isCreating}
          />
          <button
            type="submit"
            disabled={isCreating || !newTagName.trim()}
            style={{
              padding: '8px 16px',
              backgroundColor: isCreating ? '#ccc' : '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: isCreating ? 'not-allowed' : 'pointer'
            }}
          >
            {isCreating ? 'Creating...' : 'Create'}
          </button>
        </form>
        <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
          Tag names should be lowercase letters, numbers, hyphens, and underscores only.
        </div>
      </div>

      {/* Active tags */}
      <div style={{ marginBottom: '24px' }}>
        <h3>Active Tags ({activeTags.length})</h3>
        <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
          Active tags can be used by users when creating or editing posts.
        </div>
        {loading ? (
          <div>Loading...</div>
        ) : activeTags.length === 0 ? (
          <div style={{ color: '#666', fontStyle: 'italic' }}>No active tags</div>
        ) : (
          <div style={{ display: 'grid', gap: '8px' }}>
            {activeTags.map(tag => (
              <div
                key={tag.name}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '12px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  backgroundColor: '#f8f9fa'
                }}
              >
                <div style={{ fontWeight: 'bold' }}>#{tag.name}</div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={() => handleToggleTag(tag)}
                    style={{
                      padding: '4px 8px',
                      backgroundColor: '#ffc107',
                      color: 'black',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '12px'
                    }}
                    title="Disable this tag. Users won't be able to use it in new posts."
                  >
                    Disable
                  </button>
                  <button
                    onClick={() => handleDeleteTag(tag)}
                    style={{
                      padding: '4px 8px',
                      backgroundColor: '#dc3545',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '12px'
                    }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Inactive tags */}
      {inactiveTags.length > 0 && (
        <div>
          <h3>Inactive Tags ({inactiveTags.length})</h3>
          <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
            Inactive tags cannot be used in new posts. Existing posts with these tags will still display them.
          </div>
          <div style={{ display: 'grid', gap: '8px' }}>
            {inactiveTags.map(tag => (
              <div
                key={tag.name}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '12px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  backgroundColor: '#f8f8f8',
                  opacity: 0.7
                }}
              >
                <div style={{ fontWeight: 'bold', textDecoration: 'line-through' }}>#{tag.name}</div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={() => handleToggleTag(tag)}
                    style={{
                      padding: '4px 8px',
                      backgroundColor: '#28a745',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '12px'
                    }}
                    title="Enable this tag. Users will be able to use it in new posts."
                  >
                    Enable
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TagManagement;
