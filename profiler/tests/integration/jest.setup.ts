// Mock ProfileService methods that don't exist in the test environment
jest.mock('../../app/ui/src/services/profile', () => {
  // Get the actual module first
  const originalModule = jest.requireActual('../../app/ui/src/services/profile');
  
  // Add any missing methods for testing
  return {
    ...originalModule,
    ProfileService: class MockProfileService extends originalModule.ProfileService {
      onError(handler: (error: string) => void) {
        // Add an error handler implementation
        this.onMessage('error', (data: any) => {
          if (data && data.error) {
            handler(data.error);
          }
        });
      }
    }
  };
});

// Add global fetch for node environment
global.fetch = jest.fn();

// Mock window location
Object.defineProperty(window, 'location', {
  value: {
    href: 'http://localhost:3000',
    origin: 'http://localhost:3000'
  },
  writable: true
}); 