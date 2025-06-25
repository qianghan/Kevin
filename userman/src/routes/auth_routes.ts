import express from 'express';
import { AuthService } from '../services/auth_service';
import { getAuthService } from '../services';
import { validateServiceAccess } from '../middleware/service_auth_middleware';

const router = express.Router();
const authService = getAuthService();

/**
 * Register a new user
 */
router.post('/register', async (req, res, next) => {
  try {
    const { email, password, firstName, lastName, role } = req.body;

    // Validate required fields
    if (!email || !password || !firstName || !lastName || !role) {
      return res.status(400).json({
        success: false,
        message: 'Missing required fields'
      });
    }

    // Register the user
    const user = await authService.register(
      {
        email,
        firstName,
        lastName,
        role
      },
      password,
      {
        ipAddress: req.ip,
        userAgent: req.get('user-agent')
      }
    );

    res.status(201).json({
      success: true,
      user
    });
  } catch (error) {
    next(error);
  }
});

/**
 * Login user
 */
router.post('/login', async (req, res, next) => {
  try {
    const { email, password } = req.body;

    // Validate required fields
    if (!email || !password) {
      return res.status(400).json({
        success: false,
        message: 'Email and password are required'
      });
    }

    // Authenticate user
    const result = await authService.authenticate(
      email,
      password,
      {
        device: req.get('user-agent'),
        ipAddress: req.ip,
        userAgent: req.get('user-agent')
      }
    );

    // Defensive: ensure user.id is ObjectId string
    if (result.user && result.user._id) {
      result.user.id = result.user._id.toString();
    }
    if (result.user && result.user.id && typeof result.user.id !== 'string') {
      result.user.id = String(result.user.id);
    }

    res.status(200).json({
      success: true,
      ...result
    });
  } catch (error) {
    next(error);
  }
});

/**
 * Verify email
 */
router.post('/verify-email', async (req, res, next) => {
  try {
    const { token } = req.body;

    if (!token) {
      return res.status(400).json({
        success: false,
        message: 'Verification token is required'
      });
    }

    const verified = await authService.verifyEmail(token);

    res.status(200).json({
      success: verified,
      message: verified ? 'Email verified successfully' : 'Invalid or expired token'
    });
  } catch (error) {
    next(error);
  }
});

/**
 * Request password reset
 */
router.post('/forgot-password', async (req, res, next) => {
  try {
    const { email } = req.body;

    if (!email) {
      return res.status(400).json({
        success: false,
        message: 'Email is required'
      });
    }

    await authService.requestPasswordReset(email);

    res.status(200).json({
      success: true,
      message: 'Password reset instructions sent to email'
    });
  } catch (error) {
    next(error);
  }
});

/**
 * Reset password
 */
router.post('/reset-password', async (req, res, next) => {
  try {
    const { token, newPassword } = req.body;

    if (!token || !newPassword) {
      return res.status(400).json({
        success: false,
        message: 'Token and new password are required'
      });
    }

    const reset = await authService.resetPassword(
      token,
      newPassword,
      {
        ipAddress: req.ip,
        userAgent: req.get('user-agent')
      }
    );

    res.status(200).json({
      success: reset,
      message: reset ? 'Password reset successfully' : 'Invalid or expired token'
    });
  } catch (error) {
    next(error);
  }
});

export default router; 