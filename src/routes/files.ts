import { Router, Response } from 'express';
import multer from 'multer';
import { authMiddleware, AuthRequest } from '../middleware/auth';

export const fileRouter = Router();

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 1 * 1024 * 1024 }, // 1 MB
  fileFilter: (_req, file, cb) => {
    const ext = file.originalname.split('.').pop()?.toLowerCase();
    if (file.mimetype !== 'text/plain' || ext !== 'txt') {
      cb(new Error('Only .txt files are allowed'));
    } else {
      cb(null, true);
    }
  },
});

// POST /api/v1/files/upload — protected
fileRouter.post('/upload', authMiddleware, upload.single('file'), (req: AuthRequest, res: Response) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file provided' });
  }
  const content = req.file.buffer.toString('utf-8');
  return res.json({ content });
});
