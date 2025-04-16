import { ProfileState } from '../services/profile';

// Action Types
export const PROFILE_ACTIONS = {
  SET_PROFILE: 'SET_PROFILE',
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR',
  RESET: 'RESET'
};

// Action interfaces
export interface SetProfileAction {
  type: typeof PROFILE_ACTIONS.SET_PROFILE;
  payload: ProfileState;
}

export interface SetLoadingAction {
  type: typeof PROFILE_ACTIONS.SET_LOADING;
  payload: boolean;
}

export interface SetErrorAction {
  type: typeof PROFILE_ACTIONS.SET_ERROR;
  payload: string;
}

export interface ClearErrorAction {
  type: typeof PROFILE_ACTIONS.CLEAR_ERROR;
}

export interface ResetAction {
  type: typeof PROFILE_ACTIONS.RESET;
}

export type ProfileAction = 
  | SetProfileAction
  | SetLoadingAction
  | SetErrorAction
  | ClearErrorAction
  | ResetAction;

// Store State
export interface ProfileStoreState {
  profile: ProfileState | null;
  loading: boolean;
  error: string | null;
}

// Initial state
export const initialState: ProfileStoreState = {
  profile: null,
  loading: true,
  error: null
};

// Action creators
export const setProfile = (profile: ProfileState): SetProfileAction => ({
  type: PROFILE_ACTIONS.SET_PROFILE,
  payload: profile
});

export const setLoading = (loading: boolean): SetLoadingAction => ({
  type: PROFILE_ACTIONS.SET_LOADING,
  payload: loading
});

export const setError = (error: string): SetErrorAction => ({
  type: PROFILE_ACTIONS.SET_ERROR,
  payload: error
});

export const clearError = (): ClearErrorAction => ({
  type: PROFILE_ACTIONS.CLEAR_ERROR
});

export const reset = (): ResetAction => ({
  type: PROFILE_ACTIONS.RESET
});

// Type guards
const isSetProfileAction = (action: ProfileAction): action is SetProfileAction => 
  action.type === PROFILE_ACTIONS.SET_PROFILE;

const isSetLoadingAction = (action: ProfileAction): action is SetLoadingAction => 
  action.type === PROFILE_ACTIONS.SET_LOADING;

const isSetErrorAction = (action: ProfileAction): action is SetErrorAction => 
  action.type === PROFILE_ACTIONS.SET_ERROR;

// Reducer
export const profileReducer = (state = initialState, action: ProfileAction): ProfileStoreState => {
  switch (action.type) {
    case PROFILE_ACTIONS.SET_PROFILE:
      return {
        ...state,
        profile: isSetProfileAction(action) ? action.payload : null,
        loading: false
      };
    case PROFILE_ACTIONS.SET_LOADING:
      return {
        ...state,
        loading: isSetLoadingAction(action) ? action.payload : false
      };
    case PROFILE_ACTIONS.SET_ERROR:
      return {
        ...state,
        loading: false,
        error: isSetErrorAction(action) ? action.payload : null
      };
    case PROFILE_ACTIONS.CLEAR_ERROR:
      return {
        ...state,
        error: null
      };
    case PROFILE_ACTIONS.RESET:
      return initialState;
    default:
      return state;
  }
};

// Simple store implementation
export class ProfileStore {
  private state: ProfileStoreState = initialState;
  private listeners: ((state: ProfileStoreState) => void)[] = [];

  getState(): ProfileStoreState {
    return this.state;
  }

  dispatch(action: ProfileAction): void {
    this.state = profileReducer(this.state, action);
    this.notifyListeners();
  }

  subscribe(listener: (state: ProfileStoreState) => void): () => void {
    this.listeners.push(listener);
    
    // Return unsubscribe function
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notifyListeners(): void {
    for (const listener of this.listeners) {
      listener(this.state);
    }
  }
} 