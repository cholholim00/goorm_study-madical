// src/middleware/auth.ts
import type { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET || 'dev-secret-key';

// 컨트롤러에서 쓸 타입
export interface AuthRequest extends Request {
    userId?: number;
    user?: {
        id: number;
        email: string;
    };
}

// 모든 보호된 API에서 사용할 미들웨어
export function requireAuth(req: AuthRequest, res: Response, next: NextFunction) {
    try {
        const authHeader = req.headers.authorization;

        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return res.status(401).json({ error: '인증 정보가 없습니다. 다시 로그인해 주세요.' });
        }

        const token = authHeader.substring('Bearer '.length).trim();

        if (!token) {
            return res.status(401).json({ error: '인증 토큰이 없습니다.' });
        }

        // 토큰 검증
        const payload = jwt.verify(token, JWT_SECRET) as {
            id: number;
            email: string;
        };

        // ✅ 두 군데 다 세팅해 줌 (예전 코드 호환용)
        req.userId = payload.id;
        req.user = { id: payload.id, email: payload.email };

        next();
    } catch (err) {
        console.error('requireAuth error:', err);
        return res
            .status(401)
            .json({ error: '유효하지 않은 토큰입니다. 다시 로그인해 주세요.' });
    }
}