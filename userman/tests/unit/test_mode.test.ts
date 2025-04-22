import { UserService } from '../../src/services/user_service';
import { IUserRepository } from '../../src/services/interfaces';
import { UserDocument } from '../../src/models/user_model';

// Mock repository implementation
const createMockRepository = (): jest.Mocked<IUserRepository> => ({
  findById: jest.fn(),
  findByEmail: jest.fn(),
  create: jest.fn(),
  update: jest.fn(),
  delete: jest.fn(),
  findLinkedUsers: jest.fn(),
  search: jest.fn(),
  findAll: jest.fn()
});

// Helper to create mock user documents
const createMockUser = (id: string, testMode: boolean = false): Partial<UserDocument> => ({
  _id: { toString: () => id },
  name: 'Test User',
  email: `test-${id}@example.com`,
  role: 'student',
  testMode,
  createdAt: new Date(),
  updatedAt: new Date()
});

describe('Test Mode Management', () => {
  let mockRepository: jest.Mocked<IUserRepository>;
  let userService: UserService;

  beforeEach(() => {
    mockRepository = createMockRepository();
    userService = new UserService(mockRepository as any);
  });

  describe('setTestMode', () => {
    it('should set test mode to true for a user', async () => {
      // Arrange
      const mockUser = createMockUser('123', false);
      mockRepository.update.mockResolvedValue({ ...mockUser, testMode: true } as any);
      
      // Act
      const result = await userService.setTestMode('123', true);
      
      // Assert
      expect(mockRepository.update).toHaveBeenCalledWith('123', { testMode: true });
      expect(result.testMode).toBe(true);
    });

    it('should set test mode to false for a user', async () => {
      // Arrange
      const mockUser = createMockUser('123', true);
      mockRepository.update.mockResolvedValue({ ...mockUser, testMode: false } as any);
      
      // Act
      const result = await userService.setTestMode('123', false);
      
      // Assert
      expect(mockRepository.update).toHaveBeenCalledWith('123', { testMode: false });
      expect(result.testMode).toBe(false);
    });

    it('should throw an error if user is not found', async () => {
      // Arrange
      mockRepository.update.mockResolvedValue(null);
      
      // Act & Assert
      await expect(userService.setTestMode('not-exists', true)).rejects.toThrow('User not found');
    });
  });

  describe('getTestModeUsers', () => {
    it('should retrieve all users in test mode', async () => {
      // Arrange
      const mockUsers = [
        createMockUser('123', true),
        createMockUser('456', true)
      ];
      mockRepository.findAll.mockResolvedValue(mockUsers as any[]);
      
      // Act
      const result = await userService.getTestModeUsers();
      
      // Assert
      expect(mockRepository.findAll).toHaveBeenCalledWith({ testMode: true });
      expect(result.length).toBe(2);
      expect(result[0].testMode).toBe(true);
      expect(result[1].testMode).toBe(true);
    });

    it('should return empty array if no users in test mode', async () => {
      // Arrange
      mockRepository.findAll.mockResolvedValue([]);
      
      // Act
      const result = await userService.getTestModeUsers();
      
      // Assert
      expect(mockRepository.findAll).toHaveBeenCalledWith({ testMode: true });
      expect(result).toEqual([]);
    });

    it('should handle errors gracefully', async () => {
      // Arrange
      mockRepository.findAll.mockRejectedValue(new Error('Database error'));
      
      // Act & Assert
      await expect(userService.getTestModeUsers()).rejects.toThrow('Failed to get test mode users');
    });
  });

  describe('getAllUsers', () => {
    it('should get all users with no filter', async () => {
      // Arrange
      const mockUsers = [
        createMockUser('123', false),
        createMockUser('456', true)
      ];
      mockRepository.findAll.mockResolvedValue(mockUsers as any[]);
      
      // Act
      const result = await userService.getAllUsers();
      
      // Assert
      expect(mockRepository.findAll).toHaveBeenCalledWith({});
      expect(result.length).toBe(2);
    });

    it('should filter users by test mode', async () => {
      // Arrange
      const mockUsers = [createMockUser('123', true)];
      mockRepository.findAll.mockResolvedValue(mockUsers as any[]);
      
      // Act
      const result = await userService.getAllUsers({ testMode: true });
      
      // Assert
      expect(mockRepository.findAll).toHaveBeenCalledWith({ testMode: true });
      expect(result.length).toBe(1);
      expect(result[0].testMode).toBe(true);
    });

    it('should filter users by role', async () => {
      // Arrange
      const mockUsers = [
        { ...createMockUser('123'), role: 'admin' } as any
      ];
      mockRepository.findAll.mockResolvedValue(mockUsers);
      
      // Act
      const result = await userService.getAllUsers({ role: 'admin' });
      
      // Assert
      expect(mockRepository.findAll).toHaveBeenCalledWith({ role: 'admin' });
      expect(result.length).toBe(1);
      expect(result[0].role).toBe('admin');
    });
  });
}); 