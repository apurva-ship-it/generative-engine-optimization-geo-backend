import express from 'express';
import { authMiddleware } from './middleware/auth';
import { router as userRouter } from './routes/users';

const app = express();
app.use(express.json());

app.get('/health', (_req, res) => res.json({ status: 'ok' }));
app.use('/api/v1/users', authMiddleware, userRouter);

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`Server running on :${PORT}`));

export default app;
