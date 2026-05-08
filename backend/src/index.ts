import express from 'express';
import { authMiddleware } from './middleware/auth';
import { router as userRouter } from './routes/users';
import { router as fileRouter } from './routes/files';

const app = express();
app.use(express.json());

app.get('/health', (_req, res) => res.json({ status: 'ok' }));
app.use('/api/v1/users', authMiddleware, userRouter);
app.use('/api/v1/files', fileRouter);

app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  if (err instanceof multer.MulterError) {
    return res.status(400).json({ error: err.message });
  }
  if (err.message && err.message.includes('Only .txt')) {
    return res.status(400).json({ error: err.message });
  }
  res.status(500).json({ error: 'Internal server error' });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`Server running on :${PORT}`));

export default app;