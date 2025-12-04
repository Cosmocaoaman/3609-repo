import React, { useState } from 'react';
import { updateReply } from '../api/replies';
import type { ReplyItem } from '../api/replies';

interface ReplyEditFormProps {
  reply: ReplyItem;
  threadId: number;
  onSuccess: (updatedReply: ReplyItem) => void;
  onCancel: () => void;
}

const ReplyEditForm: React.FC<ReplyEditFormProps> = ({
  reply,
  threadId,
  onSuccess,
  onCancel
}) => {
  const [body, setBody] = useState(reply.body);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    setLoading(true);
    setError(null);

    try {
      const updatedReply = await updateReply(reply.id, body.trim());
      onSuccess(updatedReply);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setBody(reply.body);
    setError(null);
    onCancel();
  };

  return (
    <div style={{ border: '1px solid #007bff', padding: '12px', borderRadius: '4px', backgroundColor: '#f8f9fa' }}>
      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '8px' }}>
        {error && (
          <div style={{
            backgroundColor: '#fee',
            color: '#c33',
            padding: '8px',
            borderRadius: '4px',
            fontSize: '14px'
          }}>
            {error}
          </div>
        )}

        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          required
          maxLength={2000}
          rows={4}
          aria-label="Reply content"
          style={{
            width: '100%',
            padding: '8px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            fontSize: '14px',
            resize: 'vertical'
          }}
        />
        
        <div style={{ fontSize: '12px', color: '#666' }}>
          {body.length}/2000 characters
        </div>

        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
          <button
            type="button"
            onClick={handleCancel}
            disabled={loading}
            style={{
              padding: '6px 12px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              backgroundColor: 'white',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '14px'
            }}
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading || !body.trim()}
            style={{
              padding: '6px 12px',
              border: 'none',
              borderRadius: '4px',
              backgroundColor: loading ? '#ccc' : '#007bff',
              color: 'white',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '14px'
            }}
          >
            {loading ? 'Saving...' : 'Save'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ReplyEditForm;
