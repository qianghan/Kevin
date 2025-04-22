import express from 'express';
import request from 'supertest';
import { createUserRouter } from '../../src/api/user_router';
import { UserService } from '../../src/services/user_service';
import { IUserRepository } from '../../src/services/interfaces';
import { UserDocument } from '../../src/models/user_model';

// Mock JWT verification middleware
jest.mock('../../src/api/middleware/auth', () => ({
  isAuthenticated: (req: express.Request, res: express.Response, next: express.NextFunction) => {
    // Add user info from Authorization header
    const authHeader = req.headers.authorization;
    if (authHeader && authHeader.startsWith('Bearer ')) {
      try {
        const token = authHeader.split(' ')[1];
        const decodedToken = JSON.parse(Buffer.from(token, 'base64').toString());
        (req as any).user = decodedToken;
        (req as any).userId = decodedToken.id;
      } catch (error) {
        console.error('Invalid token:', error);
      }
    }
    next();
  }
}));

// Helper to create JWT tokens for testing
const createTestToken = (userData: any): string => {
  return Buffer.from(JSON.stringify(userData)).toString('base64');
};

// Mock user service implementation
class MockUserService implements Partial<UserService> {
  private users: Map<string, any> = new Map();

  constructor() {
    // Add some test users
    this.users.set('user1', {
      id: 'user1',
      email: 'user1@example.com',
      name: 'Test User',
      role: 'student',
      testMode: false
    });

    this.users.set('admin1', {
      id: 'admin1',
      email: 'admin@example.com',
      name: 'Admin User',
      role: 'admin',
      testMode: false
    });

    this.users.set('test1', {
      id: 'test1',
      email: 'test1@example.com',
      name: 'Test Mode User',
      role: 'student',
      testMode: true
    });
  }

  async getAllUsers() {
    return Array.from(this.users.values());
  }

  async getTestModeUsers() {
    return Array.from(this.users.values()).filter(user => user.testMode);
  }

  async setTestMode(userId: string, enabled: boolean) {
    const user = this.users.get(userId);
    if (!user) {
      throw new Error('User not found');
    }
    
    user.testMode = enabled;
    this.users.set(userId, user);
    return user;
  }

  // Other methods would be implemented here in a real test
}

describe('Test Mode API Endpoints', () => {
  let app: express.Application;
  let mockUserService: MockUserService;

  beforeEach(() => {
    app = express();
    app.use(express.json());
    
    mockUserService = new MockUserService();
    const userRouter = createUserRouter(mockUserService as any);
    
    app.use('/api/user', userRouter);
  });

  describe('GET /api/user/admin/users/test-mode', () => {
    it('should return all test mode users for admin', async () => {
      // Admin token
      const adminToken = createTestToken({ id: 'admin1', role: 'admin' });
      
      const response = await request(app)
        .get('/api/user/admin/users/test-mode')
        .set('Authorization', `Bearer ${adminToken}`);
      
      expect(response.status).toBe(200);
      expect(response.body.data).toHaveLength(1);
      expect(response.body.data[0].id).toBe('test1');
    });

    it('should reject access for non-admin users', async () => {
      // Student token
      const userToken = createTestToken({ id: 'user1', role: 'student' });
      
      const response = await request(app)
        .get('/api/user/admin/users/test-mode')
        .set('Authorization', `Bearer ${userToken}`);
      
      expect(response.status).toBe(403);
    });
  });

  describe('POST /api/user/admin/users/:userId/test-mode', () => {
    it('should allow admin to enable test mode', async () => {
      // Admin token
      const adminToken = createTestToken({ id: 'admin1', role: 'admin' });
      
      const response = await request(app)
        .post('/api/user/admin/users/user1/test-mode')
        .set('Authorization', `Bearer ${adminToken}`)
        .send({ enabled: true });
      
      expect(response.status).toBe(200);
      expect(response.body.data.testMode).toBe(true);
    });

    it('should allow admin to disable test mode', async () => {
      // Admin token
      const adminToken = createTestToken({ id: 'admin1', role: 'admin' });
      
      const response = await request(app)
        .post('/api/user/admin/users/test1/test-mode')
        .set('Authorization', `Bearer ${adminToken}`)
        .send({ enabled: false });
      
      expect(response.status).toBe(200);
      expect(response.body.data.testMode).toBe(false);
    });

    it('should reject access for non-admin users', async () => {
      // Student token
      const userToken = createTestToken({ id: 'user1', role: 'student' });
      
      const response = await request(app)
        .post('/api/user/admin/users/user1/test-mode')
        .set('Authorization', `Bearer ${userToken}`)
        .send({ enabled: true });
      
      expect(response.status).toBe(403);
    });

    it('should require enabled flag to be a boolean', async () => {
      // Admin token
      const adminToken = createTestToken({ id: 'admin1', role: 'admin' });
      
      const response = await request(app)
        .post('/api/user/admin/users/user1/test-mode')
        .set('Authorization', `Bearer ${adminToken}`)
        .send({ enabled: 'yes' }); // Not a boolean
      
      expect(response.status).toBe(400);
    });
  });
}); 