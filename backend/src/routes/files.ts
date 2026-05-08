import { Router, Response, Request } from 'express';
import multer from 'multer';

const router = Router();

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 1 * 1024 * 1024 }, // 1MB
  fileFilter: (req, file, cb) => {
    const mime = file.mimetype;
    const ext = file.originalname.split('.').pop();
    if (mime !== 'text/plain' || ext?.toLowerCase() !== 'txt') {
      cb(new Error('Only .txt files are allowed'));
    } else {
      cb(null, true);
    }
  },
});

router.post('/upload', upload.single('file'), (req: Request, res: Response) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file provided' });
  }
  try {
    const content = req.file.buffer.toString('utf-8');
    res.json({ content });
  } catch (err) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

export { router as fileRouter };
