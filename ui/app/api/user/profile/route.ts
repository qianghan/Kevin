import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth/auth-options';
import { UserProfile } from '@/services/UserService';
import connectToDatabase from '@/lib/db/connection';
import User, { UserDocument } from '@/lib/models/User';
import mongoose from 'mongoose';

// GET /api/user/profile - Get current user profile
export async function GET(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    // Get user data directly from database instead of using userService
    // to avoid circular dependency
    await connectToDatabase();
    const user = await User.findById(session.user.id);
    
    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 });
    }
    
    // Format user data as UserProfile by treating document as any
    const userDoc = user as any;
    const userProfile: UserProfile = {
      id: userDoc._id.toString(),
      name: userDoc.name,
      email: userDoc.email,
      image: userDoc.image,
      role: userDoc.role,
      createdAt: userDoc.createdAt,
      updatedAt: userDoc.updatedAt
    };
    
    return NextResponse.json(userProfile);
  } catch (error) {
    console.error('Error fetching user profile:', error);
    return NextResponse.json(
      { error: 'Failed to fetch user profile' },
      { status: 500 }
    );
  }
}

// PUT /api/user/profile - Update user profile
export async function PUT(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    // Get request body
    const data = await req.json();
    const { name, image } = data;
    
    // Update user data directly in the database
    const updateData: Partial<UserDocument> = {};
    if (name !== undefined) updateData.name = name;
    if (image !== undefined) updateData.image = image;
    
    // Only update if there are fields to update
    if (Object.keys(updateData).length > 0) {
      await connectToDatabase();
      
      const updatedUser = await User.findByIdAndUpdate(
        session.user.id,
        { $set: updateData },
        { new: true }
      );
      
      if (!updatedUser) {
        return NextResponse.json({ error: 'Failed to update user' }, { status: 500 });
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
      
      return NextResponse.json(updatedProfile);
    }
    
    return NextResponse.json(
      { error: 'No fields to update' },
      { status: 400 }
    );
  } catch (error) {
    console.error('Error updating user profile:', error);
    return NextResponse.json(
      { error: 'Failed to update user profile' },
      { status: 500 }
    );
  }
} 