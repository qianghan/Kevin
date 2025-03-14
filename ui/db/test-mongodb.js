const { MongoClient } = require('mongodb');

// Try to load dotenv, but don't fail if it's not available
try {
  require('dotenv').config({ path: '../.env.local' });
} catch (error) {
  console.log('Note: dotenv module not found. Continuing without loading environment variables.');
}

// Using a hardcoded connection string for testing, or fall back to env if provided
const uri = process.env.MONGODB_URI || 'mongodb://kevinuser:kevin_password@localhost:27018/kevindb';

console.log('Connecting to UI MongoDB...');
console.log(`URI: ${uri}`);

// Set MongoDB connection options with timeout
const mongoOptions = {
  serverSelectionTimeoutMS: 5000, // 5 seconds
  connectTimeoutMS: 5000,
  socketTimeoutMS: 5000,
};

const client = new MongoClient(uri, mongoOptions);

async function run() {
  try {
    await client.connect();
    console.log('Connected successfully to UI MongoDB');
    
    // List databases
    const databasesList = await client.db().admin().listDatabases();
    console.log('Databases:');
    databasesList.databases.forEach(db => console.log(` - ${db.name}`));
    
    // Test kevindb database
    const db = client.db('kevindb');
    const collections = await db.listCollections().toArray();
    console.log('Collections in kevindb:');
    collections.forEach(collection => console.log(` - ${collection.name}`));
    
    // Test users collection
    try {
      const users = await db.collection('users').find({}).limit(10).toArray();
      console.log(`Found ${users.length} users:`);
      users.forEach(user => console.log(` - ${user.name} (${user.role})`));
    } catch (error) {
      console.log('Could not query users collection:', error.message);
    }
    
    // Test chat sessions collection
    try {
      const chatSessions = await db.collection('chatSessions').find({}).limit(10).toArray();
      console.log(`Found ${chatSessions.length} chat sessions:`);
      chatSessions.forEach(session => console.log(` - ${session.title} (${session.messages?.length || 0} messages)`));
    } catch (error) {
      console.log('Could not query chatSessions collection:', error.message);
    }
    
  } catch (err) {
    console.error('MongoDB connection error:', err);
    process.exit(1);
  } finally {
    try {
      await client.close();
      console.log('MongoDB connection closed');
    } catch (err) {
      console.error('Error closing MongoDB connection:', err);
    }
  }
}

run().catch(error => {
  console.error('Unhandled error:', error);
  process.exit(1);
}); 