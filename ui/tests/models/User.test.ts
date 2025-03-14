import mongoose from 'mongoose';
import { MongoMemoryServer } from 'mongodb-memory-server';
import { UserModel } from '../../models/User';

// Mock the connection
let mongoServer: MongoMemoryServer;

beforeAll(async () => {
  mongoServer = await MongoMemoryServer.create();
  const uri = mongoServer.getUri();
  await mongoose.connect(uri);
});

afterAll(async () => {
  await mongoose.disconnect();
  await mongoServer.stop();
});

describe('User Model', () => {
  it('should create a student user correctly', async () => {
    const userData = {
      email: 'student@example.com',
      name: 'Student User',
      role: 'student' as const,
      parentIds: [],
    };

    const user = new UserModel(userData);
    await user.save();

    const foundUser = await UserModel.findOne({ email: 'student@example.com' });
    expect(foundUser).toBeTruthy();
    expect(foundUser!.email).toBe(userData.email);
    expect(foundUser!.name).toBe(userData.name);
    expect(foundUser!.role).toBe('student');
    expect(foundUser!.parentIds).toHaveLength(0);
  });

  it('should create a parent user correctly', async () => {
    const userData = {
      email: 'parent@example.com',
      name: 'Parent User',
      role: 'parent' as const,
      studentIds: [],
      partnerIds: [],
    };

    const user = new UserModel(userData);
    await user.save();

    const foundUser = await UserModel.findOne({ email: 'parent@example.com' });
    expect(foundUser).toBeTruthy();
    expect(foundUser!.email).toBe(userData.email);
    expect(foundUser!.name).toBe(userData.name);
    expect(foundUser!.role).toBe('parent');
    expect(foundUser!.studentIds).toHaveLength(0);
    expect(foundUser!.partnerIds).toHaveLength(0);
  });

  it('should validate required fields', async () => {
    const invalidUser = new UserModel({
      name: 'Invalid User',
      // Missing required email
    });

    await expect(invalidUser.save()).rejects.toThrow();
  });

  it('should find or create user by provider', async () => {
    const providerData = {
      email: 'oauth@example.com',
      name: 'OAuth User',
      image: 'https://example.com/avatar.jpg',
      provider: 'google',
    };
    
    const user = await UserModel.findOrCreateByProvider(providerData);
    
    expect(user).toBeTruthy();
    expect(user.email).toBe(providerData.email);
    expect(user.name).toBe(providerData.name);
    expect(user.image).toBe(providerData.image);
    
    // Calling again should return the same user
    const existingUser = await UserModel.findOrCreateByProvider(providerData);
    expect(existingUser._id.toString()).toBe(user._id.toString());
  });
}); 