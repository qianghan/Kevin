import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/auth-options';
import { 
  createProtectedHandler, 
  createSuccessResponse, 
  createErrorResponse 
} from '@/lib/api/middleware';
import { UserProfile } from '@/services/UserService';
import connectToDatabase from '@/lib/db/connection';
import User, { UserDocument } from '@/lib/models/User';
import mongoose from 'mongoose';

/**
 * Handle GET request to retrieve current user profile
 */
async function handleGetProfile(req: NextRequest, params: Record<string, any>) {
  // User is already authenticated via middleware
  const user = params.user;
  
  if (!user || !user.id) {
    console.error('User profile requested but no user in session');
    return createErrorResponse('Authentication required', 401);
  }
  
  console.log('Returning profile for user:', user.id);
  
  // Get user data directly from database instead of using userService
  // to avoid circular dependency
  await connectToDatabase();
  const userDoc = await User.findById(user.id);
  
  if (!userDoc) {
    return createErrorResponse('User not found', 404);
  }
  
  // Format user data as UserProfile by treating document as any
  const userDocAny = userDoc as any;
  const userProfile: UserProfile = {
    id: userDocAny._id.toString(),
    name: userDocAny.name,
    email: userDocAny.email,
    image: userDocAny.image,
    role: userDocAny.role,
    createdAt: userDocAny.createdAt,
    updatedAt: userDocAny.updatedAt
  };
  
  return createSuccessResponse(userProfile);
}

/**
 * Handle PUT request to update user profile
 */
async function handleUpdateProfile(req: NextRequest, params: Record<string, any>) {
  // User is already authenticated via middleware
  const user = params.user;
  
  if (!user || !user.id) {
    console.error('Profile update requested but no user in session');
    return createErrorResponse('Authentication required', 401);
  }
  
  // Parse the request body
  let profileData;
  try {
    profileData = await req.json();
  } catch (error) {
    return createErrorResponse('Invalid JSON data', 400);
  }
  
  // Basic validation
  if (!profileData) {
    return createErrorResponse('Profile data is required', 400);
  }
  
  console.log('Updating profile for user:', user.id);
  
  // Update user data directly in the database
  const updateData: Partial<UserDocument> = {};
  if (profileData.name !== undefined) updateData.name = profileData.name;
  if (profileData.image !== undefined) updateData.image = profileData.image;
  
  // Only update if there are fields to update
  if (Object.keys(updateData).length > 0) {
    await connectToDatabase();
    
    const updatedUser = await User.findByIdAndUpdate(
      user.id,
      { $set: updateData },
      { new: true }
    );
    
    if (!updatedUser) {
      return createErrorResponse('Failed to update user', 500);
    }
    
    // Format updated user data as UserProfile
    const updatedDoc = updatedUser as any;
    const updatedProfile: UserProfile = {
      id: updatedDoc._id.toString(),
      name: updatedDoc.name,
      email: updatedDoc.email,
      image: updatedDoc.image,
      role: updatedDoc.role,
      createdAt: updatedDoc.createdAt,
      updatedAt: updatedDoc.updatedAt
    };
    
    return createSuccessResponse(updatedProfile);
  }
  
  return createErrorResponse('No fields to update', 400);
}

// Export the handlers with middleware protection
export const GET = createProtectedHandler(handleGetProfile);
export const PUT = createProtectedHandler(handleUpdateProfile); 