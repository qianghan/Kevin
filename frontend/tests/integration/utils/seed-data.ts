import mongoose from 'mongoose';
import { loadTestEnvironment } from './env';

/**
 * Sample test data for integration tests
 */
const testData = {
  users: [
    {
      _id: 'user1',
      name: 'Test User',
      email: 'test@example.com',
      password: 'hashedpassword123',
    },
    {
      _id: 'user2',
      name: 'Admin User',
      email: 'admin@example.com',
      password: 'hashedpassword456',
      isAdmin: true,
    },
  ],
  chatSessions: [
    {
      _id: 'session1',
      userId: 'user1',
      title: 'Test Session',
      messages: [
        {
          type: 'user',
          content: 'Hello KAI',
          timestamp: new Date().toISOString(),
        },
        {
          type: 'ai',
          content: 'Hello! How can I assist you today?',
          timestamp: new Date().toISOString(),
        },
      ],
    },
    {
      _id: 'session2',
      userId: 'user1',
      title: 'Another Session',
      messages: [
        {
          type: 'user',
          content: 'Tell me about KAI',
          timestamp: new Date().toISOString(),
        },
        {
          type: 'ai',
          content: 'KAI is an advanced AI assistant designed to help with various tasks.',
          timestamp: new Date().toISOString(),
        },
      ],
    },
  ],
  userSettings: [
    {
      userId: 'user1',
      settings: {
        theme: 'dark',
        language: 'en',
        notifications: true,
      },
    },
    {
      userId: 'user2',
      settings: {
        theme: 'light',
        language: 'en',
        notifications: false,
      },
    },
  ],
};

/**
 * Seeds the database with test data
 * 
 * @returns Promise that resolves when seeding is complete
 */
export async function seedTestData(): Promise<void> {
  const env = loadTestEnvironment();
  const dbUri = env.MONGODB_URI || 'mongodb://localhost:27017/kai-test';
  
  console.log(`Seeding test database at ${dbUri}`);
  
  try {
    // Connect to test database
    await mongoose.connect(dbUri);
    
    // Clear existing data
    const collections = Object.keys(mongoose.connection.collections);
    for (const collection of collections) {
      await mongoose.connection.collections[collection].deleteMany({});
      console.log(`Cleared collection: ${collection}`);
    }
    
    // Insert test data
    for (const [collection, documents] of Object.entries(testData)) {
      if (documents.length > 0) {
        await mongoose.connection.collection(collection).insertMany(documents);
        console.log(`Seeded ${documents.length} documents to ${collection}`);
      }
    }
    
    console.log('Test data seeding complete');
  } catch (error: any) {
    console.error('Error seeding test data:', error.message);
    throw error;
  } finally {
    await mongoose.disconnect();
  }
}

/**
 * Cleans up test data after tests
 * 
 * @returns Promise that resolves when cleanup is complete
 */
export async function cleanupTestData(): Promise<void> {
  const env = loadTestEnvironment();
  const dbUri = env.MONGODB_URI || 'mongodb://localhost:27017/kai-test';
  
  console.log(`Cleaning up test database at ${dbUri}`);
  
  try {
    await mongoose.connect(dbUri);
    
    const collections = Object.keys(mongoose.connection.collections);
    for (const collection of collections) {
      await mongoose.connection.collections[collection].deleteMany({});
      console.log(`Cleared collection: ${collection}`);
    }
    
    console.log('Test data cleanup complete');
  } catch (error: any) {
    console.error('Error cleaning up test data:', error.message);
  } finally {
    await mongoose.disconnect();
  }
}

// Command line interface for seeding test data
if (require.main === module) {
  (async () => {
    try {
      await seedTestData();
      process.exit(0);
    } catch (error) {
      console.error('Failed to seed test data:', error);
      process.exit(1);
    }
  })();
} 