// src/server.ts
console.log('🌟🌟🌟 BACKEND ENTRY FROM src/server.ts 🌟🌟🌟');

import express from 'express';
import cors from 'cors';
import authRouter from './routes/auth';
import recordsRouter from './routes/records';
import userRouter from './routes/user';
import aiRouter from './routes/ai';

console.log('🚀 health-coach backend STARTED (server.ts 로딩됨)');

const app = express();
const PORT = 5001;

app.use(cors());
app.use(express.json());

// 🔍 들어오는 모든 요청 한 번 로깅
app.use((req, _res, next) => {
    console.log(`➡️  ${req.method} ${req.url}`);
    next();
});

// ✅ 여기서 auth 라우터를 /api/auth 로 연결
app.use('/api/auth', authRouter);

// 헬스 체크
app.get('/health-check', (req, res) => {
    res.json({ status: 'ok', message: 'health-coach API is running' });
});

// 기록/유저/AI 라우터 연결
app.use('/api/records', recordsRouter);
app.use('/api/user', userRouter);
app.use('/api/ai', aiRouter);

// 404 로깅 + 응답
app.use((req, res) => {
    console.log('⚠️  404 Not Found:', req.method, req.url);
    res.status(404).json({ error: 'Not Found' });
});

app.listen(PORT, () => {
    console.log(`✅ Server is running on http://localhost:${PORT}`);
});
