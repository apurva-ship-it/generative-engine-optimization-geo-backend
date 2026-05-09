import { Router, Response } from 'express';
import { AuthRequest } from '../middleware/auth';
import { getUserById } from '../services/userService';

export const router = Router();

router.get('/', async (req: AuthRequest, res: Response) => {
  const user = await getUserById(req.userId!);
  if (!user) return res.status(404).json({ error: 'User not found' });
  res.json(user);
});
