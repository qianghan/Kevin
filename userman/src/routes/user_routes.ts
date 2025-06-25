import { Router } from 'express';
import { UserService } from '../services/user_service';
import { validateToken } from '../middleware/auth_middleware';
import { NotFoundError } from '../utils/errors';
import { MongoUserRepository } from '../services/user_repository';

const router = Router();
const userService = new UserService(new MongoUserRepository());

/**
 * Get user profile
 */
router.get('/profile', validateToken, async (req, res, next) => {
  try {
    const userId = req.userId;
    if (!userId) {
      throw new NotFoundError('User ID not found in request');
    }

    const user = await userService.getUserById(userId);
    if (!user) {
      throw new NotFoundError('User not found');
    }

    res.status(200).json(user);
  } catch (error) {
    next(error);
  }
});

/**
 * Update user profile
 */
router.put('/profile', validateToken, async (req, res, next) => {
  try {
    const userId = req.userId;
    if (!userId) {
      throw new NotFoundError('User ID not found in request');
    }

    const updatedUser = await userService.updateUser(userId, {
      firstName: req.body.firstName,
      lastName: req.body.lastName,
      email: req.body.email
    });

    res.status(200).json(updatedUser);
  } catch (error) {
    next(error);
  }
});

/**
 * Delete user account
 */
router.delete('/profile', validateToken, async (req, res, next) => {
  try {
    const userId = req.userId;
    if (!userId) {
      throw new NotFoundError('User ID not found in request');
    }

    await userService.deleteUser(userId);
    res.status(200).json({ message: 'User account deleted successfully' });
  } catch (error) {
    next(error);
  }
});

export default router; 