import {
  ProfileStore,
  setProfile,
  setLoading,
  setError,
  clearError,
  reset,
  initialState
} from '../../../app/ui/src/store/profileStore';

describe('ProfileStore', () => {
  let store: ProfileStore;

  beforeEach(() => {
    store = new ProfileStore();
  });

  it('should initialize with the correct initial state', () => {
    const state = store.getState();
    expect(state).toEqual(initialState);
  });

  it('should update state when setProfile is dispatched', () => {
    const mockProfile = {
      userId: 'test-user-1',
      status: 'processing',
      progress: 50
    };

    store.dispatch(setProfile(mockProfile));
    
    const state = store.getState();
    expect(state.profile).toEqual(mockProfile);
    expect(state.loading).toBe(false);
  });

  it('should update loading state when setLoading is dispatched', () => {
    store.dispatch(setLoading(true));
    
    let state = store.getState();
    expect(state.loading).toBe(true);
    
    store.dispatch(setLoading(false));
    
    state = store.getState();
    expect(state.loading).toBe(false);
  });

  it('should set error state when setError is dispatched', () => {
    const errorMessage = 'Test error message';
    store.dispatch(setError(errorMessage));
    
    const state = store.getState();
    expect(state.error).toBe(errorMessage);
    expect(state.loading).toBe(false);
  });

  it('should clear error state when clearError is dispatched', () => {
    // First set an error
    store.dispatch(setError('Test error'));
    
    // Then clear it
    store.dispatch(clearError());
    
    const state = store.getState();
    expect(state.error).toBe(null);
  });

  it('should reset state to initial state when reset is dispatched', () => {
    // Change the state
    store.dispatch(setProfile({
      userId: 'test-user-1',
      status: 'completed',
      progress: 100
    }));
    
    store.dispatch(setError('Test error'));
    
    // Then reset
    store.dispatch(reset());
    
    const state = store.getState();
    expect(state).toEqual(initialState);
  });

  it('should notify subscribers when state changes', () => {
    const mockListener = jest.fn();
    
    // Subscribe to changes
    const unsubscribe = store.subscribe(mockListener);
    
    // Dispatch an action
    store.dispatch(setLoading(true));
    
    // Check if listener was called
    expect(mockListener).toHaveBeenCalledWith(store.getState());
    
    // Unsubscribe
    unsubscribe();
    
    // Dispatch another action
    store.dispatch(setLoading(false));
    
    // Listener should have been called only once
    expect(mockListener).toHaveBeenCalledTimes(1);
  });
}); 