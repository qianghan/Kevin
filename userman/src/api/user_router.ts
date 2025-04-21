import express, { Request, Response, NextFunction } from 'express';
import { IUserService } from '../services/interfaces';
import { UserProfileDTO } from '../services/interfaces';

/**
 * Factory function to create a user router
 * Dependency injection of the user service
 */
export const createUserRouter = (userService: IUserService) => {
  const router = express.Router();
  
  /**
   * Middleware to check if a user is authenticated
   */
  const isAuthenticated = (req: Request, res: Response, next: NextFunction) => {
    const userId = req.headers['user-id'] as string || (req.user as any)?.id;
    
    if (!userId) {
      return res.status(401).json({ message: 'Authentication required' });
    }
    
    // Add userId to request for easy access
    (req as any).userId = userId;
    next();
  };
  
  /**
   * Get current user profile
   */
  router.get('/profile', isAuthenticated, async (req: Request, res: Response) => {
    try {
      const userId = (req as any).userId;
      const user = await userService.getUserById(userId);
      
      if (!user) {
        return res.status(404).json({ message: 'User not found' });
      }
      
      res.json({ data: user });
    } catch (error) {
      console.error('Error getting user profile:', error);
      res.status(500).json({ message: 'Internal server error' });
    }
  });
  
  /**
   * Update user profile
   */
  router.put('/profile', isAuthenticated, async (req: Request, res: Response) => {
    try {
      const userId = (req as any).userId;
      const profileData = req.body;
      
      const updatedProfile = await userService.updateProfile(userId, profileData);
      res.json({ data: updatedProfile });
    } catch (error: any) {
      console.error('Error updating profile:', error);
      res.status(400).json({ message: error.message || 'Failed to update profile' });
    }
  });
  
  /**
   * Get user preferences
   */
  router.get('/preferences', isAuthenticated, async (req: Request, res: Response) => {
    try {
      const userId = (req as any).userId;
      const preferences = await userService.getPreferences(userId);
      
      res.json({ data: preferences });
    } catch (error: any) {
      console.error('Error getting preferences:', error);
      res.status(400).json({ message: error.message || 'Failed to get preferences' });
    }
  });
  
  /**
   * Update user preferences
   */
  router.put('/preferences', isAuthenticated, async (req: Request, res: Response) => {
    try {
      const userId = (req as any).userId;
      const preferences = req.body;
      
      const updatedPreferences = await userService.updatePreferences(userId, preferences);
      res.json({ data: updatedPreferences });
    } catch (error: any) {
      console.error('Error updating preferences:', error);
      res.status(400).json({ message: error.message || 'Failed to update preferences' });
    }
  });
  
  /**
   * Search for users
   */
  router.get('/search', isAuthenticated, async (req: Request, res: Response) => {
    try {
      const userId = (req as any).userId;
      const query = req.query.q as string;
      
      if (!query || query.length < 2) {
        return res.status(400).json({ message: 'Search query must be at least 2 characters' });
      }
      
      const users = await userService.searchUsers(query, userId);
      res.json({ data: users });
    } catch (error) {
      console.error('Error searching users:', error);
      res.status(500).json({ message: 'Internal server error' });
    }
  });
  
  /**
   * Link accounts
   */
  router.post('/link', isAuthenticated, async (req: Request, res: Response) => {
    try {
      const userId = (req as any).userId;
      const { targetUserId, relationship } = req.body;
      
      if (!targetUserId || !relationship) {
        return res.status(400).json({ message: 'Missing required fields' });
      }
      
      const result = await userService.linkAccounts(userId, targetUserId, relationship);
      res.json({ data: result });
    } catch (error: any) {
      console.error('Error linking accounts:', error);
      res.status(400).json({ message: error.message || 'Failed to link accounts' });
    }
  });
  
  /**
   * Unlink accounts
   */
  router.delete('/link', isAuthenticated, async (req: Request, res: Response) => {
    try {
      const userId = (req as any).userId;
      const { targetUserId, relationship } = req.body;
      
      if (!targetUserId || !relationship) {
        return res.status(400).json({ message: 'Missing required fields' });
      }
      
      const result = await userService.unlinkAccounts(userId, targetUserId, relationship);
      res.json({ data: result });
    } catch (error: any) {
      console.error('Error unlinking accounts:', error);
      res.status(400).json({ message: error.message || 'Failed to unlink accounts' });
    }
  });
  
  /**
   * Get linked users
   */
  router.get('/linked/:relationship', isAuthenticated, async (req: Request, res: Response) => {
    try {
      const userId = (req as any).userId;
      const relationship = req.params.relationship as 'students' | 'parents' | 'partners';
      
      if (!['students', 'parents', 'partners'].includes(relationship)) {
        return res.status(400).json({ message: 'Invalid relationship type' });
      }
      
      const users = await userService.getLinkedUsers(userId, relationship);
      res.json({ data: users });
    } catch (error) {
      console.error('Error getting linked users:', error);
      res.status(500).json({ message: 'Internal server error' });
    }
  });
  
  /**
   * Change password
   */
  router.post('/password', isAuthenticated, async (req: Request, res: Response) => {
    try {
      const userId = (req as any).userId;
      const { currentPassword, newPassword } = req.body;
      
      if (!currentPassword || !newPassword) {
        return res.status(400).json({ message: 'Missing required fields' });
      }
      
      const result = await userService.changePassword(userId, currentPassword, newPassword);
      
      if (!result) {
        return res.status(400).json({ message: 'Invalid current password' });
      }
      
      res.json({ data: { success: true } });
    } catch (error) {
      console.error('Error changing password:', error);
      res.status(500).json({ message: 'Internal server error' });
    }
  });
  
  /**
   * Change email
   */
  router.post('/email', isAuthenticated, async (req: Request, res: Response) => {
    try {
      const userId = (req as any).userId;
      const { newEmail, password } = req.body;
      
      if (!newEmail || !password) {
        return res.status(400).json({ message: 'Missing required fields' });
      }
      
      try {
        const result = await userService.changeEmail(userId, newEmail, password);
        
        if (!result) {
          return res.status(400).json({ message: 'Invalid password' });
        }
        
        res.json({ data: { success: true } });
      } catch (error: any) {
        res.status(400).json({ message: error.message || 'Failed to change email' });
      }
    } catch (error) {
      console.error('Error changing email:', error);
      res.status(500).json({ message: 'Internal server error' });
    }
  });
  
  return router;
}; 