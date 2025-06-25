import { connectToDatabase, closeDatabaseConnection } from '../utils/db';
import { generateHash } from '../utils/password';
import { User, UserRole } from '../models/user_model';

const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017/kevin';

async function seedAdminUser() {
  await connectToDatabase({ uri: MONGO_URI });

  const email = 'qiang@kevin.ai';
  const password = 'kevin';
  const firstName = 'Qiang';
  const lastName = 'Han';
  const name = 'Qiang Han';
  const role = UserRole.ADMIN;

  const existing = await User.findOne({ email });
  if (existing) {
    console.log(`Admin user '${email}' already exists.`);
    await closeDatabaseConnection();
    return;
  }

  const hashedPassword = await generateHash(password);
  await User.create({
    email,
    password: hashedPassword,
    firstName,
    lastName,
    name,
    role,
    emailVerified: true,
    preferences: {},
    createdAt: new Date(),
    updatedAt: new Date(),
  });
  console.log(`Admin user '${email}' created with password '${password}'.`);
  await closeDatabaseConnection();
}

seedAdminUser().catch((err) => {
  console.error('Error seeding admin user:', err);
  closeDatabaseConnection();
}); 