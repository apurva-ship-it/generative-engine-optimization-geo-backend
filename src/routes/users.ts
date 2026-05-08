import { Router, Request, Response } from 'express';
import { registerUser, getUserById } from '../services/userService';
import { authMiddleware, AuthRequest } from '../middleware/auth';
import jwt from 'jsonwebtoken';

export const userRouter = Router();

// POST /api/v1/users — public registration
userRouter.post('/', async (req: Request, res: Response) => {
  const { fullName, email, mobile, age, sex, password } = req.body;

  if (!fullName || !email || !mobile || !age || !sex || !password) {
    return res.status(400).json({ error: 'All fields are required' });
  }
  if (!/^\d{10}$/.test(mobile)) {
    return res.status(400).json({ error: 'Mobile must be exactly 10 digits' });
  }
  if (password.length < 6) {
    return res.status(400).json({ error: 'Password must be at least 6 characters' });
  }
  const ageNum = Number(age);
  if (!Number.isInteger(ageNum) || ageNum < 1 || ageNum > 120) {
    return res.status(400).json({ error: 'Age must be between 1 and 120' });
  }

  try {
    const user = await registerUser({ fullName, email, mobile, age: ageNum, sex, password });
    const token = jwt.sign({ userId: user.id }, process.env.JWT_SECRET!, { expiresIn: '24h' });
    res.cookie('token', token, {
      httpOnly: true,
      secure: false,   // false for local HTTP dev
      sameSite: 'lax',
      maxAge: 24 * 60 * 60 * 1000,
    });
    return res.status(201).json({ message: 'Registered', user: { id: user.id, fullName: user.fullName } });
  } catch (err: any) {
    if (err?.code === 'P2002') {
      return res.status(409).json({ error: 'Email or mobile already registered' });
    }
    return res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/v1/users/me — protected
userRouter.get('/me', authMiddleware, async (req: AuthRequest, res: Response) => {
  const user = await getUserById(req.userId!);
  if (!user) return res.status(404).json({ error: 'User not found' });
  const { passwordHash: _, ...safe } = user;
  res.json(safe);
});
