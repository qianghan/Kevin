import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/auth-options';
import connectToDatabase from '@/lib/db/connection';
import User, { UserPreferences } from '@/lib/models/User';
import { 
  createProtectedHandler, 
  createSuccessResponse, 
  createErrorResponse 
} from '@/lib/api/middleware';

/**
 * Handle GET request to retrieve user preferences
 */
async function handleGetPreferences(req: NextRequest, params: Record<string, any>) {
  // User is already authenticated via middleware
  const user = params.user;
  
  if (!user || !user.id) {
    console.error('Preferences requested but no user in session');
    return createErrorResponse('Authentication required', 401);
  }
  
  try {
    // Get user preferences directly from database
    await connectToDatabase();
    const userDoc = await User.findById(user.id);
    
    if (!userDoc) {
      return createErrorResponse('User not found', 404);
    }
    
    // Extract preferences or return defaults
    const userDocAny = userDoc as any;
    const preferences: UserPreferences = userDocAny.preferences || {
      theme: 'system',
      emailNotifications: true,
      language: 'en'
    };
    
    return createSuccessResponse(preferences);
  } catch (error) {
    console.error('Error fetching user preferences:', error);
    return createErrorResponse('Failed to fetch user preferences', 500);
  }
}

/**
 * Handle PUT request to update user preferences
 */
async function handleUpdatePreferences(req: NextRequest, params: Record<string, any>) {
  // User is already authenticated via middleware
  const user = params.user;
  
  if (!user || !user.id) {
    console.error('Preferences update requested but no user in session');
    return createErrorResponse('Authentication required', 401);
  }
  
  try {
    // Get request body
    const preferences: UserPreferences = await req.json();
    
    // Validate preferences
    const validatedPreferences: UserPreferences = {};
    
    // Theme must be one of the valid options
    if (preferences.theme && ['light', 'dark', 'system'].includes(preferences.theme as string)) {
      validatedPreferences.theme = preferences.theme;
    }
    
    // Email notifications must be boolean
    if (typeof preferences.emailNotifications === 'boolean') {
      validatedPreferences.emailNotifications = preferences.emailNotifications;
    }
    
    // Language must be a string
    if (preferences.language && typeof preferences.language === 'string') {
      validatedPreferences.language = preferences.language;
    }
    
    // Update preferences directly in the database
    await connectToDatabase();
    
    const userDoc = await User.findById(user.id);
    if (!userDoc) {
      return createErrorResponse('User not found', 404);
    }
    
    // Get current preferences and merge with new ones
    const userDocAny = userDoc as any;
    const currentPreferences = userDocAny.preferences || {};
    const updatedPreferences = {
      ...currentPreferences,
      ...validatedPreferences
    };
    
    // Update the user document with new preferences
    const updatedUser = await User.findByIdAndUpdate(
      user.id,
      { $set: { preferences: updatedPreferences } },
      { new: true }
    );
    
    if (!updatedUser) {
      return createErrorResponse('Failed to update preferences', 500);
    }
    
    const updatedDocAny = updatedUser as any;
    return createSuccessResponse(updatedDocAny.preferences || {});
  } catch (error) {
    console.error('Error updating user preferences:', error);
    return createErrorResponse('Failed to update user preferences', 500);
  }
}

// Export the handlers with middleware protection
export const GET = createProtectedHandler(handleGetPreferences);
export const PUT = createProtectedHandler(handleUpdatePreferences); 