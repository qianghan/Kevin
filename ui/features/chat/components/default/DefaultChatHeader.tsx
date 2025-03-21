'use client';

import React, { useState } from 'react';
import { ChatHeaderProps } from '../../types/chat-ui.types';

export function DefaultChatHeader({
  title,
  onStartNewChat,
  onUpdateTitle,
  className = ''
}: ChatHeaderProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedTitle, setEditedTitle] = useState(title);

  const handleStartEditing = () => {
    setEditedTitle(title);
    setIsEditing(true);
  };

  const handleSave = () => {
    if (onUpdateTitle && editedTitle.trim()) {
      onUpdateTitle(editedTitle);
    }
    setIsEditing(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSave();
    }
  };

  return (
    <div className={`py-3 px-4 flex justify-between items-center bg-white border-b border-gray-100 shadow-sm ${className}`}>
      {isEditing ? (
        <input
          type="text"
          value={editedTitle}
          onChange={(e) => setEditedTitle(e.target.value)}
          onBlur={handleSave}
          onKeyDown={handleKeyPress}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          autoFocus
        />
      ) : (
        <h2 
          className="text-xl font-semibold cursor-pointer hover:underline text-gray-800"
          onClick={handleStartEditing}
        >
          {title}
        </h2>
      )}
    </div>
  );
} 