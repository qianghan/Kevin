const { MongoClient } = require('mongodb');

// Explicitly specifying port 27018 for the connection
const uri = 'mongodb://kevinuser:kevin_password@localhost:27018/kevindb';

console.log('Attempting to connect to MongoDB with:');
console.log(`URI: ${uri}`);

const client = new MongoClient(uri, {
  serverSelectionTimeoutMS: 5000,
  connectTimeoutMS: 5000,
  socketTimeoutMS: 5000
});

async function testConnection() {
  try {
    await client.connect();
    console.log('✅ Successfully connected to MongoDB on port 27018');
    
    // Basic test to verify we can access the database
    const adminDb = client.db().admin();
    const databasesList = await adminDb.listDatabases();
    console.log('Available databases:');
    databasesList.databases.forEach(db => console.log(` - ${db.name}`));
    
    return true;
  } catch (error) {
    console.error('❌ MongoDB connection error:', error);
    return false;
  } finally {
    await client.close();
    console.log('Connection closed');
  }
}

// Execute the test
testConnection()
  .then(success => {
    if (!success) {
      console.log('\nTroubleshooting tips:');
      console.log('1. Verify the MongoDB container is running: docker ps');
      console.log('2. Check container port mapping: docker port kevin-ui-mongodb');
      console.log('3. Ensure the username/password matches what was configured in init-mongo.js');
    }
    process.exit(success ? 0 : 1);
  }); 