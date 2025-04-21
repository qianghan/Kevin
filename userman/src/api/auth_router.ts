import express, { Request, Response } from 'express';
import { IUserService } from '../services/interfaces';

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
      const { name, email, password, role } = req.body;
      
      // Basic validation
      if (!name || !email || !password) {
        return res.status(400).json({ message: 'Missing required fields' });
      }
      
      // Register user
      try {
        const user = await userService.register({
          name,
          email,
          role: role || 'student'
        }, password);
        
        // Remove sensitive data from response
        const userResponse = { ...user };
        delete (userResponse as any).password;
        
        res.status(201).json({ 
          message: 'User registered successfully',
          data: userResponse
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
      
      // Authenticate user
      const user = await userService.authenticate(email, password);
      
      if (!user) {
        return res.status(401).json({ message: 'Invalid email or password' });
      }
      
      // In a real implementation, this is where you would generate JWT tokens
      // or set up sessions
      
      res.json({ 
        message: 'Login successful',
        data: {
          user,
          // token: 'jwt-token-would-go-here'
        }
      });
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
      
      await userService.requestPasswordReset(email);
      
      // Don't reveal if the user exists for security
      res.json({ message: 'If your email is registered, you will receive reset instructions' });
    } catch (error) {
      console.error('Password reset request error:', error);
      res.status(500).json({ message: 'Internal server error' });
    }
  });
  
  /**
   * Reset password with token
   */
  router.post('/reset-password', async (req: Request, res: Response) => {
    try {
      const { token, newPassword } = req.body;
      
      if (!token || !newPassword) {
        return res.status(400).json({ message: 'Missing required fields' });
      }
      
      const success = await userService.resetPassword(token, newPassword);
      
      if (!success) {
        return res.status(400).json({ message: 'Invalid or expired token' });
      }
      
      res.json({ message: 'Password reset successful' });
    } catch (error) {
      console.error('Password reset error:', error);
      res.status(500).json({ message: 'Internal server error' });
    }
  });
  
  /**
   * Verify email
   */
  router.get('/verify-email/:token', async (req: Request, res: Response) => {
    try {
      const { token } = req.params;
      
      if (!token) {
        return res.status(400).json({ message: 'Token is required' });
      }
      
      const success = await userService.verifyEmail(token);
      
      if (!success) {
        return res.status(400).json({ message: 'Invalid or expired token' });
      }
      
      res.json({ message: 'Email verified successfully' });
    } catch (error) {
      console.error('Email verification error:', error);
      res.status(500).json({ message: 'Internal server error' });
    }
  });
  
  return router;
}; 