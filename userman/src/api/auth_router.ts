import express, { Request, Response } from 'express';
import { IUserService } from '../services/interfaces';
import { isAuthenticated } from '../middleware/auth';

/**
 * Factory function to create an authentication router
 * Dependency injection of the user service
 */
export const createAuthRouter = (userService: IUserService) => {
  const router = express.Router();
  
  /**
   * Register a new user
   */
  router.post('/register', async (req: Request, res: Response) => {
    try {
      const { email, password, role, firstName, lastName } = req.body;
      
      // Basic validation
      if (!email || !password) {
        return res.status(400).json({ message: 'Missing required fields' });
      }
      
      // Register user
      try {
        const user = await userService.register({
          email,
          firstName,
          lastName,
          role: role || 'student'
        }, password);
        
        res.status(201).json({ 
          message: 'User registered successfully',
          data: user
        });
      } catch (error: any) {
        res.status(409).json({ message: error.message || 'Registration failed' });
      }
    } catch (error) {
      console.error('Registration error:', error);
      res.status(500).json({ message: 'Internal server error' });
    }
  });
  
  /**
   * Login
   */
  router.post('/login', async (req: Request, res: Response) => {
    try {
      const { email, password } = req.body;
      
      // Basic validation
      if (!email || !password) {
        return res.status(400).json({ message: 'Missing email or password' });
      }
      
      try {
        // Authenticate user
        const { user, token } = await userService.authenticate(email, password);
        
        res.json({ 
          message: 'Login successful',
          data: {
            user,
            token
          }
        });
      } catch (authError) {
        return res.status(401).json({ message: 'Invalid email or password' });
      }
    } catch (error) {
      console.error('Login error:', error);
      res.status(500).json({ message: 'Internal server error' });
    }
  });
  
  /**
   * Request password reset
   */
  router.post('/forgot-password', async (req: Request, res: Response) => {
    try {
      const { email } = req.body;
      
      if (!email) {
        return res.status(400).json({ message: 'Email is required' });
      }
      
      // Always return success even if email doesn't exist (for security)
      await userService.requestPasswordReset(email);
      res.json({ message: 'Password reset instructions sent to your email' });
    } catch (error) {
      console.error('Error requesting password reset:', error);
      // Still return success for security
      res.json({ message: 'Password reset instructions sent to your email' });
    }
  });
  
  /**
   * Reset password with a token
   */
  router.post('/reset-password', async (req: Request, res: Response) => {
    try {
      const { token, newPassword } = req.body;
      
      if (!token || !newPassword) {
        return res.status(400).json({ message: 'Token and new password are required' });
      }
      
      const success = await userService.resetPassword(token, newPassword);
      
      if (success) {
        res.json({ message: 'Password reset successfully' });
      } else {
        res.status(400).json({ message: 'Invalid or expired token' });
      }
    } catch (error) {
      console.error('Error resetting password:', error);
      res.status(500).json({ message: 'Failed to reset password' });
    }
  });
  
  /**
   * Verify email with a verification token
   */
  router.get('/verify-email/:token', async (req, res) => {
    try {
      const { token } = req.params;
      
      const verified = await userService.verifyEmail(token);
      
      if (verified) {
        res.json({ message: 'Email verified successfully' });
      } else {
        res.status(400).json({ message: 'Invalid or expired token' });
      }
    } catch (error) {
      console.error('Error verifying email:', error);
      res.status(500).json({ message: 'Failed to verify email' });
    }
  });
  
  /**
   * Logout (invalidate current session)
   */
  router.post('/logout', isAuthenticated, async (req, res) => {
    try {
      const sessionId = req.headers['session-id'] as string;
      
      if (!sessionId) {
        return res.status(400).json({ message: 'Session ID is required' });
      }
      
      const success = await userService.invalidateSession(sessionId);
      
      if (success) {
        res.json({ message: 'Logged out successfully' });
      } else {
        res.status(400).json({ message: 'Failed to logout' });
      }
    } catch (error) {
      console.error('Error logging out:', error);
      res.status(500).json({ message: 'Failed to logout' });
    }
  });
  
  /**
   * Get all active sessions for the current user
   */
  router.get('/sessions', isAuthenticated, async (req, res) => {
    try {
      const userId = (req as any).userId;
      const sessions = await userService.getUserSessions(userId);
      res.json({ data: sessions });
    } catch (error) {
      console.error('Error getting sessions:', error);
      res.status(500).json({ message: 'Failed to get sessions' });
    }
  });
  
  /**
   * Logout from all devices (invalidate all sessions)
   */
  router.post('/logout-all', isAuthenticated, async (req, res) => {
    try {
      const userId = (req as any).userId;
      const success = await userService.invalidateAllSessions(userId);
      
      if (success) {
        res.json({ message: 'Logged out from all devices successfully' });
      } else {
        res.status(400).json({ message: 'Failed to logout from all devices' });
      }
    } catch (error) {
      console.error('Error logging out from all devices:', error);
      res.status(500).json({ message: 'Failed to logout from all devices' });
    }
  });
  
  return router;
}; 