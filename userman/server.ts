/**
 * User Management System Express Server
 * 
 * This is a standalone server for the User Management System.
 */

import express from 'express';
import cors from 'cors';
import mongoose from 'mongoose';
import { createUserManagementSystem } from './src';
import { UserService } from './src/services/user_service';
import User, { UserRole } from './src/models/user_model';
import { MongoUserRepository } from './src/repositories/mongo_user_repository';
import { IUserRepository } from './src/services/interfaces';

// Create Express app
const app = express();
const PORT = process.env.PORT || 8000;

// Middleware
app.use(express.json());
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:8000'],
  credentials: true
}));

// Connect to MongoDB
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://admin:secure_password@localhost:27018/kevindb?authSource=admin';

const createDefaultAdmin = async () => {
  try {
    const userRepository: IUserRepository = new MongoUserRepository();
    const userService = new UserService(userRepository);
    
    const defaultEmail = 'admin@example.com';
    const defaultPassword = 'admin123';
    
    const existingUser = await userService.getUserByEmail(defaultEmail);
    if (!existingUser) {
      await userService.register({
        firstName: 'Admin',
        lastName: 'User',
        email: defaultEmail,
        role: UserRole.ADMIN
      }, defaultPassword);
      console.log('Default admin user created successfully');
    } else {
      console.log('Default admin user already exists');
    }
  } catch (error) {
    console.error('Error creating default admin:', error);
  }
};

const initializeServer = async () => {
  try {
    // Connect to MongoDB
    await mongoose.connect(MONGODB_URI);
    console.log('Connected to MongoDB');
    
    // Create default admin user
    await createDefaultAdmin();
    
    // Create user management system
    const { userRouter, authRouter } = createUserManagementSystem();
    
    // Mount routers
    app.use('/api/auth', authRouter);
    app.use('/api/user', userRouter);
    
    // Start server
    app.listen(PORT, () => {
      console.log(`User Management API running on port ${PORT}`);
      console.log(`Access at http://localhost:${PORT}`);
    });
  } catch (error) {
    console.error('Failed to initialize server:', error);
    process.exit(1);
  }
};

// Root route
app.get('/', (req, res) => {
  res.json({
    name: 'User Management API',
    version: '1.0.0',
    endpoints: {
      auth: '/api/auth',
      user: '/api/user'
    }
  });
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: Date.now() / 1000
  });
});

// Initialize server
initializeServer(); 