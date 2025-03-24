import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth/auth-options';
import connectToDatabase from '@/lib/db/connection';
import User, { UserPreferences } from '@/lib/models/User';

// GET /api/user/preferences - Get user preferences
export async function GET(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    // Get user preferences directly from database
    // to avoid circular dependency with userService
    await connectToDatabase();
    const user = await User.findById(session.user.id);
    
    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 });
    }
    
    // Extract preferences or return defaults
    const userDoc = user as any;
    const preferences: UserPreferences = userDoc.preferences || {
      theme: 'system',
      emailNotifications: true,
      language: 'en'
    };
    
    return NextResponse.json(preferences);
  } catch (error) {
    console.error('Error fetching user preferences:', error);
    return NextResponse.json(
      { error: 'Failed to fetch user preferences' },
      { status: 500 }
    );
  }
}

// PUT /api/user/preferences - Update user preferences
export async function PUT(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
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
    
    const user = await User.findById(session.user.id);
    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 });
    }
    
    // Get current preferences and merge with new ones
    const userDoc = user as any;
    const currentPreferences = userDoc.preferences || {};
    const updatedPreferences = {
      ...currentPreferences,
      ...validatedPreferences
    };
    
    // Update the user document with new preferences
    const updatedUser = await User.findByIdAndUpdate(
      session.user.id,
      { $set: { preferences: updatedPreferences } },
      { new: true }
    );
    
    if (!updatedUser) {
      return NextResponse.json({ error: 'Failed to update preferences' }, { status: 500 });
    }
    
    const updatedDoc = updatedUser as any;
    return NextResponse.json(updatedDoc.preferences || {});
  } catch (error) {
    console.error('Error updating user preferences:', error);
    return NextResponse.json(
      { error: 'Failed to update user preferences' },
      { status: 500 }
    );
  }
} 