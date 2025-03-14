const { MongoClient } = require('mongodb');
require('dotenv').config({ path: '../.env.local' });

// Using a hardcoded connection string for testing, or fall back to env if provided
const uri = process.env.MONGODB_URI || 'mongodb://kevinuser:kevin_password@localhost:27018/kevindb';
const client = new MongoClient(uri);

async function run() {
  try {
    console.log('Connecting to UI MongoDB...');
    console.log(`URI: ${uri}`);
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
    const users = await db.collection('users').find({}).limit(10).toArray();
    console.log(`Found ${users.length} users:`);
    users.forEach(user => console.log(` - ${user.name} (${user.role})`));
    
    // Test chat sessions collection
    const chatSessions = await db.collection('chatSessions').find({}).limit(10).toArray();
    console.log(`Found ${chatSessions.length} chat sessions:`);
    chatSessions.forEach(session => console.log(` - ${session.title} (${session.messages.length} messages)`));
    
  } catch (err) {
    console.error('MongoDB connection error:', err);
  } finally {
    await client.close();
    console.log('Connection closed');
  }
}

run().catch(console.dir); 