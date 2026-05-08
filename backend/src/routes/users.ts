import { Router, Response } from 'express';
import { AuthRequest } from '../middleware/auth';
import { getUserById, updateUser } from '../services/userService';

export const router = Router();

// GET /api/v1/users/:id
router.get('/:id', async (req: AuthRequest, res: Response) => {
  try {
    const user = await getUserById(req.params.id);
    if (!user) return res.status(404).json({ error: 'User not found' });
    res.json(user);
  } catch (err) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

// PUT /api/v1/users/:id
router.put('/:id', async (req: AuthRequest, res: Response) => {
  if (req.userId !== req.params.id) {
    return res.status(403).json({ error: 'Forbidden' });
  }
  try {
    const user = await updateUser(req.params.id, req.body);
    res.json(user);
  } catch (err) {
    res.status(500).json({ error: 'Internal server error' });
  }
});
