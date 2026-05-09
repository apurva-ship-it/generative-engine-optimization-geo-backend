import { Router, Request, Response } from 'express';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { getUserByEmail } from '../services/userService';

export const authRouter = Router();

// POST /api/v1/auth/login
authRouter.post('/login', async (req: Request, res: Response) => {
  const { email, password } = req.body;
  if (!email || !password) {
    return res.status(400).json({ error: 'Email and password are required' });
  }

  try {
    const user = await getUserByEmail(email);
    if (!user) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }
    const valid = await bcrypt.compare(password, user.passwordHash);
    if (!valid) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }
    const token = jwt.sign({ userId: user.id }, process.env.JWT_SECRET!, { expiresIn: '24h' });
    res.cookie('token', token, {
      httpOnly: true,
      secure: false,   // false for local HTTP dev
      sameSite: 'lax',
      maxAge: 24 * 60 * 60 * 1000,
    });
    return res.status(200).json({ message: 'Logged in', user: { id: user.id, fullName: user.fullName } });
  } catch {
    return res.status(500).json({ error: 'Internal server error' });
  }
});

// POST /api/v1/auth/logout
authRouter.post('/logout', (_req: Request, res: Response) => {
  res.clearCookie('token', { httpOnly: true, secure: false, sameSite: 'lax' });
  return res.status(200).json({ message: 'Logged out' });
});
