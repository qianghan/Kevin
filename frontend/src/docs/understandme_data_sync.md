# Data Synchronization Architecture

## Overview

The data synchronization system provides a robust mechanism for keeping client and server data in sync, even in unstable network conditions. It supports offline operations, conflict resolution, and real-time updates.

## Core Components

### 1. Interfaces

The system uses the Interface Segregation Principle (ISP) to define clear boundaries:

- **ISyncEntity**: Base interface for all synchronizable entities
- **ISyncOperation**: Represents a create/update/delete operation
- **IOfflineQueue**: Manages pending operations during offline mode
- **IDiffCalculator**: Calculates differences between entity versions
- **IRealTimeSync**: Handles real-time updates via WebSockets
- **ISyncService**: Main service interface for synchronization

### 2. Offline Queue

The offline queue stores operations that couldn't be immediately sent to the server:

- Persists to localStorage for recovery after page refresh/app restart
- Processes operations in order when network connectivity is restored
- Handles different operation types (create, update, delete)

### 3. Difference Calculation

The difference calculator compares entity versions:

- Calculates precise differences between entity versions
- Supports nested object structures
- Optimizes network traffic by sending only changed fields

### 4. Conflict Resolution

Multiple conflict resolution strategies are available:

- **Last-Write-Wins**: Uses timestamps to determine the latest version
- **Merge**: Intelligently combines changes from both client and server
- **Client-Wins**: Always uses the client version
- **Server-Wins**: Always uses the server version

### 5. Real-Time Updates

WebSocket-based real-time synchronization:

- Subscribes to entity-specific channels
- Handles reconnection on network failure
- Filters out self-generated messages to avoid loops

## Data Flow

### Normal Operation (Online)

1. User modifies an entity
2. The modification is immediately stored in the local entity store
3. The change is sent to the server via API
4. Upon successful update, a real-time notification is sent to other clients
5. Other clients receive the update and apply it to their local store

### Offline Operation

1. User modifies an entity while offline
2. The modification is stored in the local entity store
3. The operation is added to the offline queue
4. When connection is restored, the queue is processed in order
5. Any conflicts with server data are resolved using the configured strategy

### Conflict Resolution Process

1. Client attempts to update an entity that has been modified on the server
2. Both versions (client and server) are passed to the conflict resolver
3. The resolver produces a merged/resolved version
4. The resolved version is saved to both the server and local store

## Usage Examples

### Basic Synchronization

```typescript
// Initialize the sync service
const syncService = createSyncService(apiClient);

// Sync a user entity
const updatedUser = await syncService.syncEntity('users', user);
```

### Handling Offline Mode

```typescript
// Check if currently online
if (!syncService.isOnline()) {
  // Show offline indicator
  showOfflineIndicator();
}

// Handle going offline
window.addEventListener('offline', () => {
  showOfflineIndicator();
});

// Handle going back online
window.addEventListener('online', () => {
  hideOfflineIndicator();
  // Sync will happen automatically
});
```

### Real-Time Updates

```typescript
// Enable real-time updates
syncService.enableRealTime();

// Listen for updates to a specific entity
const unsubscribe = realTimeSync.subscribe('users', (updatedUser) => {
  // Update UI with the new user data
  updateUserUI(updatedUser);
});

// Disable real-time when component unmounts
onUnmount(() => {
  unsubscribe();
});
```

## Best Practices

1. **Entity Design**: Ensure all synchronizable entities have unique IDs and updatedAt timestamps
2. **Optimistic Updates**: Update the UI immediately, don't wait for server confirmation
3. **Error Handling**: Provide clear feedback when sync operations fail
4. **Version Tracking**: Consider adding version numbers to entities for better conflict detection
5. **Batching**: Group multiple operations together when syncing after being offline

## Performance Considerations

1. The sync process prioritizes consistency over network traffic
2. For large entity collections, consider implementing pagination or chunking
3. Use the diff calculator to minimize the payload size for updates
4. Entity data is cached locally to reduce redundant server requests
5. Real-time updates should only contain the minimal necessary data

## Security Considerations

1. All entities must go through proper authorization checks on the server
2. The client ID is used for tracking purposes, not for security
3. WebSocket connections should use authentication tokens
4. Sensitive operations should verify user permissions server-side
5. Local storage of entity data should exclude sensitive fields 