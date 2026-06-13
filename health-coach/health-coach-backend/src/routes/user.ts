// src/routes/user.ts
import { Router } from 'express';
import { prisma } from '../lib/prisma';
import type { AuthRequest } from '../middleware/auth';
import { requireAuth } from '../middleware/auth';

const router = Router();

// 이 라우터 밑은 모두 로그인 필요
router.use(requireAuth);

type ProfileBody = {
    targetSys?: number;
    targetDia?: number;
};

/**
 * GET /api/user/profile
 * 현재 로그인한 유저의 목표 혈압 정보 조회
 */
router.get('/profile', async (req: AuthRequest, res) => {
    try {
        const userId = req.userId!;

        const profile = await prisma.userProfile.findUnique({
            where: { userId },
        });

        if (!profile) {
            // 프론트에서 404를 보고 "아직 설정 안 함" 처리
            return res.status(404).json({ error: '목표 혈압 설정이 아직 없습니다.' });
        }

        return res.json(profile);
    } catch (err) {
        console.error('GET /api/user/profile error', err);
        return res
            .status(500)
            .json({ error: '목표 혈압 정보를 불러오는 중 서버 오류가 발생했습니다.' });
    }
});

/**
 * POST /api/user/profile
 * body: { targetSys, targetDia }
 * 있으면 업데이트, 없으면 새로 생성 (upsert)
 */
router.post('/profile', async (req: AuthRequest, res) => {
    try {
        const userId = req.userId!;
        const { targetSys, targetDia } = req.body as ProfileBody;

        if (typeof targetSys !== 'number' || typeof targetDia !== 'number') {
            return res
                .status(400)
                .json({ error: 'targetSys, targetDia는 숫자 타입이어야 합니다.' });
        }

        const profile = await prisma.userProfile.upsert({
            where: { userId },         // ✅ userId는 Prisma에서 unique 여야 함
            update: {
                targetSys,
                targetDia,
            },
            create: {
                userId,
                targetSys,
                targetDia,
            },
        });

        return res.json(profile);
    } catch (err) {
        console.error('POST /api/user/profile error', err);
        return res
            .status(500)
            .json({ error: '목표 혈압을 저장하는 중 서버 오류가 발생했습니다.' });
    }
});

export default router;
