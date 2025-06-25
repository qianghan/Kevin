import { Request, Response, NextFunction } from 'express';
import { IAuthenticationService } from '../services/interfaces';
import { getAuthService } from '../services';
import { UserRole } from '../models/user_model';

declare global {
  namespace Express {
    interface Request {
      userId?: string;
      user?: {
        id: string;
        role: UserRole;
      };
    }
  }
}

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
    if (!req.user || req.user.role !== UserRole.ADMIN) {
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
    if (!req.user || (req.user.role !== UserRole.ADMIN)) {
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

/**
 * Middleware to validate JWT token
 */
export const validateToken = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        success: false,
        message: 'No token provided'
      });
    }

    const token = authHeader.split(' ')[1];
    const authService = getAuthService();
    const validation = await authService.validateToken(token);

    if (!validation.isValid) {
      return res.status(401).json({
        success: false,
        message: 'Invalid or expired token'
      });
    }

    req.userId = validation.userId;
    next();
  } catch (error) {
    console.error('Token validation error:', error);
    res.status(401).json({
      success: false,
      message: 'Token validation failed'
    });
  }
}; 