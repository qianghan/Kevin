import { Request, Response, NextFunction } from 'express';
import { IAuthenticationService } from '../services/interfaces';

/**
 * Middleware to check if the user is authenticated
 */
export const authenticate = (authService: IAuthenticationService) => {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      // Get token from header
      const token = req.headers.authorization?.split(' ')[1];
      
      if (!token) {
        return res.status(401).json({
          success: false,
          message: 'Authentication required'
        });
      }
      
      // Validate token
      const validation = await authService.validateToken(token);
      
      if (!validation.isValid || !validation.userId) {
        return res.status(401).json({
          success: false,
          message: 'Invalid or expired token'
        });
      }
      
      // Set user ID on request
      req.userId = validation.userId;
      
      next();
    } catch (error) {
      console.error('Authentication error:', error);
      res.status(401).json({
        success: false,
        message: 'Authentication failed'
      });
    }
  };
};

/**
 * Middleware to check if the user has admin role
 */
export const checkAdminRole = async (req: Request, res: Response, next: NextFunction) => {
  try {
    if (!req.user || req.user.role !== 'admin') {
      return res.status(403).json({
        success: false,
        message: 'Admin privileges required'
      });
    }
    
    next();
  } catch (error) {
    console.error('Admin authorization error:', error);
    res.status(500).json({
      success: false,
      message: 'Authorization check failed'
    });
  }
};

/**
 * Middleware to check if the user has support role
 */
export const checkSupportRole = async (req: Request, res: Response, next: NextFunction) => {
  try {
    if (!req.user || (req.user.role !== 'support' && req.user.role !== 'admin')) {
      return res.status(403).json({
        success: false,
        message: 'Support privileges required'
      });
    }
    
    next();
  } catch (error) {
    console.error('Support authorization error:', error);
    res.status(500).json({
      success: false,
      message: 'Authorization check failed'
    });
  }
}; 