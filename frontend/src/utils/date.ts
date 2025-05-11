/**
 * Date Utility Functions
 * 
 * This file contains utility functions for formatting dates and timestamps.
 */

/**
 * Formats a timestamp into a readable format
 * 
 * @param timestamp - The timestamp to format (Date, string, or number)
 * @returns A formatted string representation of the timestamp
 */
export const formatTimestamp = (timestamp: Date | string | number): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  // Same day, show time
  if (diffDays < 1 && date.getDate() === now.getDate()) {
    return date.toLocaleTimeString(undefined, { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  }
  
  // Recent days
  if (diffDays < 7) {
    return `${date.toLocaleDateString(undefined, { weekday: 'short' })} ${date.toLocaleTimeString(undefined, { 
      hour: '2-digit', 
      minute: '2-digit' 
    })}`;
  }
  
  // Older dates
  return date.toLocaleDateString(undefined, { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  });
};

/**
 * Returns a relative time string (e.g., "2 hours ago")
 * 
 * @param timestamp - The timestamp to format (Date, string, or number)
 * @returns A relative time string
 */
export const getRelativeTime = (timestamp: Date | string | number): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  const diffMonths = Math.floor(diffDays / 30);
  const diffYears = Math.floor(diffDays / 365);
  
  if (diffSecs < 60) {
    return diffSecs <= 0 ? 'just now' : `${diffSecs} seconds ago`;
  }
  
  if (diffMins < 60) {
    return `${diffMins} minute${diffMins === 1 ? '' : 's'} ago`;
  }
  
  if (diffHours < 24) {
    return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
  }
  
  if (diffDays < 30) {
    return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
  }
  
  if (diffMonths < 12) {
    return `${diffMonths} month${diffMonths === 1 ? '' : 's'} ago`;
  }
  
  return `${diffYears} year${diffYears === 1 ? '' : 's'} ago`;
}; 