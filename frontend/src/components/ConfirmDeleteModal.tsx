import React from 'react';

interface ConfirmDeleteModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

const ConfirmDeleteModal: React.FC<ConfirmDeleteModalProps> = ({
  isOpen,
  title,
  message,
  onConfirm,
  onCancel,
  loading = false
}) => {
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
        maxWidth: '400px'
      }}>
        <h3 style={{ marginTop: 0, marginBottom: '16px', color: '#dc3545' }}>
          {title}
        </h3>
        
        <p style={{ marginBottom: '24px', lineHeight: '1.5' }}>
          {message}
        </p>

        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
          <button
            onClick={onCancel}
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
            onClick={onConfirm}
            disabled={loading}
            style={{
              padding: '8px 16px',
              border: 'none',
              borderRadius: '4px',
              backgroundColor: loading ? '#ccc' : '#dc3545',
              color: 'white',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Deleting...' : 'Confirm Delete'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmDeleteModal;
