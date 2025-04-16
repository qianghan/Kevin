'use client';

import React from 'react';
import { ConnectionStatus as ConnectionStatusType } from '../../lib/services/types';

interface ConnectionStatusProps {
  status: ConnectionStatusType;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ status }) => {
  const getStatusColor = () => {
    switch (status) {
      case 'connected':
        return 'bg-green-500';
      case 'connecting':
        return 'bg-yellow-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'error':
        return 'Connection Error';
      default:
        return 'Disconnected';
    }
  };

  return (
    <div className="flex items-center space-x-2">
      <div className={`h-3 w-3 rounded-full ${getStatusColor()}`}></div>
      <span className="text-sm font-medium">{getStatusText()}</span>
    </div>
  );
};

export default ConnectionStatus; 