// This script will find any user with _id: "1" and migrate it to a new ObjectId
// Usage: node scripts/fix_user_ids.js

const { MongoClient, ObjectId } = require('mongodb');

const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017';
const DB_NAME = process.env.DB_NAME || 'kevin';
const COLLECTION = 'users';

async function run() {
  const client = new MongoClient(MONGO_URI);
  try {
    await client.connect();
    const db = client.db(DB_NAME);
    const users = db.collection(COLLECTION);

    const user = await users.findOne({ _id: "1" });
    if (!user) {
      console.log('No user with _id: "1" found.');
      return;
    }
    // Remove the old _id and assign a new ObjectId
    const newId = new ObjectId();
    user._id = newId;
    await users.insertOne(user);
    await users.deleteOne({ _id: "1" });
    console.log(`Migrated user with old _id "1" to new ObjectId: ${newId}`);
  } finally {
    await client.close();
  }
}

run().catch(err => {
  console.error('Migration failed:', err);
  process.exit(1);
});
