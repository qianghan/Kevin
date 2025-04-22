// Mock MongoDB connection for tests
jest.mock('../src/utils/db', () => ({
  connectToDatabase: jest.fn().mockResolvedValue(true),
  disconnectFromDatabase: jest.fn().mockResolvedValue(true)
}));

// Mock Mongoose models
jest.mock('../src/models/user_model', () => {
  const mockUserDocument = {
    _id: { toString: () => 'mock-id' },
    email: 'test@example.com',
    name: 'Test User',
    role: 'student',
    testMode: false,
    createdAt: new Date(),
    updatedAt: new Date()
  };

  const mockUserModel = {
    findOne: jest.fn().mockResolvedValue(mockUserDocument),
    findById: jest.fn().mockResolvedValue(mockUserDocument),
    find: jest.fn().mockResolvedValue([mockUserDocument]),
    findByIdAndUpdate: jest.fn().mockResolvedValue(mockUserDocument),
    findByIdAndDelete: jest.fn().mockResolvedValue(mockUserDocument),
    findByEmail: jest.fn().mockResolvedValue(mockUserDocument),
    findByIds: jest.fn().mockResolvedValue([mockUserDocument]),
    findStudents: jest.fn().mockResolvedValue([mockUserDocument]),
    findParents: jest.fn().mockResolvedValue([mockUserDocument])
  };

  return {
    getUserModel: jest.fn().mockReturnValue(mockUserModel),
    __esModule: true,
    UserModel: mockUserModel
  };
});

// Set test environment
process.env.NODE_ENV = 'test'; 