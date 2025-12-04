import React, { useState, useMemo } from 'react';

interface TagInputProps {
  value: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

const TagInput: React.FC<TagInputProps> = ({
  value = [],
  onChange,
  placeholder = "Type # to start a tag, press Enter to confirm",
  className = "",
  disabled = false
}) => {
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

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (disabled) return;

    // If drafting, handle composing
    if (isTagging) {
      if (e.key === 'Enter') {
        e.preventDefault();
        const cleaned = tagDraft.trim().toLowerCase();
        if (cleaned && !value.includes(cleaned)) {
          const newTags = [...value, cleaned];
          onChange(newTags);
        }
        // Reset tagging state but keep input ready for next tag
        setIsTagging(false);
        setTagDraft('');
        e.currentTarget.value = '';
        // Focus back to input for next tag
        setTimeout(() => {
          e.currentTarget.focus();
        }, 0);
        return;
      }

      if (e.key === 'Escape') {
        e.preventDefault();
        setIsTagging(false);
        setTagDraft('');
        e.currentTarget.value = '';
        return;
      }

      if (e.key === 'Backspace' && tagDraft === '') {
        e.preventDefault();
        setIsTagging(false);
        e.currentTarget.value = '';
        return;
      }

      if (e.key.length === 1) {
        const ch = e.key;
        const valid = /[a-zA-Z0-9_-]/.test(ch);
        if (!valid) {
          e.preventDefault();
          return;
        }
      }
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (disabled) return;
    
    const inputValue = e.target.value;
    
    if (isTagging) {
      // When in tagging mode, filter out invalid characters
      const validChars = inputValue.replace(/[^a-zA-Z0-9_-]/g, '');
      setTagDraft(validChars);
      // Only update the input value if it's different to avoid cursor jumping
      if (e.target.value !== validChars) {
        e.target.value = validChars;
      }
    } else {
      // Check if user typed # to start tagging
      if (inputValue.includes('#')) {
        setIsTagging(true);
        const parts = inputValue.split('#');
        const lastPart = parts[parts.length - 1];
        const validChars = lastPart.replace(/[^a-zA-Z0-9_-]/g, '');
        setTagDraft(validChars);
        e.target.value = validChars;
      } else if (inputValue.length > 0) {
        // If user types anything without #, clear the input
        e.target.value = '';
      }
    }
  };

  const removeTag = (tagToRemove: string) => {
    if (disabled) return;
    onChange(value.filter(tag => tag !== tagToRemove));
  };

  return (
    <div className={`form-control tag-area ${className}`.trim()}>
      {value.map(t => (
        <span 
          key={t} 
          className="tag-pill" 
          title={`#${t}`} 
          style={{ backgroundColor: colorForTag(t) }}
        >
          #{t}
          {!disabled && (
            <button
              type="button"
              aria-label={`Remove tag ${t}`}
              onClick={() => removeTag(t)}
              className="tag-pill-close"
            >
              ×
            </button>
          )}
        </span>
      ))}

      {isTagging && (
        <span className="tag-draft">#{tagDraft || '…'}</span>
      )}

      <input
        type="text"
        className="input-unstyled"
        placeholder={isTagging ? 'Type tag content, press Enter to confirm' : placeholder}
        onKeyDown={handleKeyDown}
        onChange={handleInputChange}
        disabled={disabled}
      />
    </div>
  );
};

export default TagInput;
