// src/routes/records.ts
import { Router, Response } from 'express';
import type { AuthRequest } from '../middleware/auth';
import { requireAuth } from '../middleware/auth';
import { prisma } from '../lib/prisma';

const router = Router();

// 평균 계산 헬퍼
function calcAvg(nums: number[]): number | null {
    if (!nums.length) return null;
    const sum = nums.reduce((acc, n) => acc + n, 0);
    return sum / nums.length;
}

type RecordType = 'blood_pressure' | 'blood_sugar';

type GroupStats = {
    count: number;
    avg_sys: number | null;
    avg_dia: number | null;
};

// =========================
// 1. 기록 목록 조회
// GET /api/records?type=blood_pressure
// =========================
router.get('/', requireAuth, async (req: AuthRequest, res: Response) => {
    try {
        const userId = req.user!.id;  // ✅ 수정

        const type = req.query.type as RecordType | undefined;
        const limitParam = req.query.limit as string | undefined;
        const limit =
            limitParam && !Number.isNaN(Number(limitParam))
                ? Math.min(Number(limitParam), 500)
                : undefined;

        const records = await prisma.healthRecord.findMany({
            where: {
                userId,
                ...(type ? { type } : {}),
            },
            orderBy: { datetime: 'desc' },
            ...(limit ? { take: limit } : {}),
        });

        return res.json(records);
    } catch (error) {
        console.error('GET /api/records error', error);
        return res
            .status(500)
            .json({ error: '기록 목록을 불러오는 중 오류가 발생했습니다.' });
    }
});

// =========================
// 2. 통계 요약
// GET /api/records/stats/summary?rangeDays=7
// =========================
router.get(
    '/stats/summary',
    requireAuth,
    async (req: AuthRequest, res: Response) => {
        try {
            console.log('➡️  GET /api/records/stats/summary', req.query);

            const userId = req.user!.id;  // ✅ 수정
            const rangeParam = req.query.rangeDays as string | undefined;
            const rangeDays = rangeParam ? parseInt(rangeParam, 10) : 7;

            const now = new Date();
            const from = new Date(now.getTime() - rangeDays * 24 * 60 * 60 * 1000);

            const [bpRecords, sugarRecords] = await Promise.all([
                prisma.healthRecord.findMany({
                    where: {
                        userId,
                        type: 'blood_pressure',
                        datetime: { gte: from },
                    },
                }),
                prisma.healthRecord.findMany({
                    where: {
                        userId,
                        type: 'blood_sugar',
                        datetime: { gte: from },
                    },
                }),
            ]);

            const sysList = bpRecords.map((r) => r.value1);
            const diaList = bpRecords
                .map((r) => r.value2)
                .filter((v): v is number => typeof v === 'number');

            const avgSys = calcAvg(sysList);
            const avgDia = calcAvg(diaList);

            const sugarList = sugarRecords.map((r) => r.value1);
            const avgSugar = calcAvg(sugarList);

            return res.json({
                rangeDays,
                blood_pressure: {
                    count: bpRecords.length,
                    avg_sys: avgSys,
                    avg_dia: avgDia,
                },
                blood_sugar: {
                    count: sugarRecords.length,
                    avg: avgSugar,
                },
            });
        } catch (error) {
            console.error('GET /api/records/stats/summary error', error);
            return res
                .status(500)
                .json({
                    error: '혈압/혈당 요약 통계를 불러오는 중 오류가 발생했습니다.',
                });
        }
    },
);

// =========================
// 2-1. 라이프스타일 인사이트 통계
// GET /api/records/stats/lifestyle?rangeDays=30
// =========================
router.get(
    '/stats/lifestyle',
    requireAuth,
    async (req: AuthRequest, res: Response) => {
        try {
            const userId = req.user!.id;  // ✅ 수정

            const rangeParam = req.query.rangeDays as string | undefined;
            const rangeDays = rangeParam ? parseInt(rangeParam, 10) : 30;

            const now = new Date();
            const from = new Date(now.getTime() - rangeDays * 24 * 60 * 60 * 1000);

            const records = await prisma.healthRecord.findMany({
                where: {
                    userId,
                    type: 'blood_pressure',
                    datetime: { gte: from },
                },
                orderBy: { datetime: 'asc' },
            });

            const calcAvgLocal = (nums: number[]): number | null => {
                if (!nums.length) return null;
                const sum = nums.reduce((acc, n) => acc + n, 0);
                return sum / nums.length;
            };

            const makeStats = (list: typeof records): GroupStats => {
                const sys = list.map((r) => r.value1);
                const dia = list
                    .map((r) => r.value2)
                    .filter((v): v is number => typeof v === 'number');
                return {
                    count: list.length,
                    avg_sys: calcAvgLocal(sys),
                    avg_dia: calcAvgLocal(dia),
                };
            };

            // 수면 시간 (<6, >=6)
            const sleepShort = records.filter(
                (r) => typeof r.sleepHours === 'number' && r.sleepHours! < 6,
            );
            const sleepEnough = records.filter(
                (r) => typeof r.sleepHours === 'number' && r.sleepHours! >= 6,
            );

            // 운동 여부
            const exerciseYes = records.filter((r) => r.exercise === true);
            const exerciseNo = records.filter((r) => r.exercise === false);

            // 스트레스 (1~2 low, 3 mid, 4~5 high)
            const stressLow = records.filter(
                (r) =>
                    typeof r.stressLevel === 'number' &&
                    r.stressLevel! >= 1 &&
                    r.stressLevel! <= 2,
            );
            const stressMid = records.filter(
                (r) => typeof r.stressLevel === 'number' && r.stressLevel === 3,
            );
            const stressHigh = records.filter(
                (r) =>
                    typeof r.stressLevel === 'number' &&
                    r.stressLevel! >= 4 &&
                    r.stressLevel! <= 5,
            );

            return res.json({
                rangeDays,
                sleep: {
                    short: makeStats(sleepShort),
                    enough: makeStats(sleepEnough),
                },
                exercise: {
                    yes: makeStats(exerciseYes),
                    no: makeStats(exerciseNo),
                },
                stress: {
                    low: makeStats(stressLow),
                    mid: makeStats(stressMid),
                    high: makeStats(stressHigh),
                },
            });
        } catch (error) {
            console.error('GET /api/records/stats/lifestyle error', error);
            return res
                .status(500)
                .json({
                    error: '라이프스타일 인사이트 계산 중 오류가 발생했습니다.',
                });
        }
    },
);

// =========================
// 3. 샘플 혈압 데이터 생성 (개발용)
// POST /api/records/dev/seed-bp
// =========================
router.post(
    '/dev/seed-bp',
    requireAuth,
    async (req: AuthRequest, res: Response) => {
        try {
            const userId = req.user!.id;  // ✅ 수정

            const { days, perDay } = req.body as {
                days?: number;
                perDay?: number;
            };

            const totalDays = days && days > 0 ? Math.min(days, 60) : 14;
            const countPerDay = perDay && perDay > 0 ? Math.min(perDay, 20) : 5;

            const now = new Date();

            const states = [
                '아침 공복',
                '점심 식사 후',
                '저녁 식사 후',
                '운동 후',
                '야근 후',
                '취침 전',
            ];
            const memoSamples = [
                '컨디션은 보통이에요.',
                '전날 잠을 잘 못 잤어요.',
                '오늘 커피를 좀 많이 마셨어요.',
                '가벼운 운동을 했어요.',
                '스트레스가 좀 있었던 날이에요.',
                '식사를 늦게 했어요.',
            ];

            const getRandomInt = (min: number, max: number) => {
                return Math.floor(Math.random() * (max - min + 1)) + min;
            };

            const data: any[] = [];

            for (let d = totalDays - 1; d >= 0; d--) {
                const baseDate = new Date(
                    now.getFullYear(),
                    now.getMonth(),
                    now.getDate() - d,
                );

                for (let i = 0; i < countPerDay; i++) {
                    const hour = getRandomInt(6, 22);
                    const minute = getRandomInt(0, 59);

                    const datetime = new Date(
                        baseDate.getFullYear(),
                        baseDate.getMonth(),
                        baseDate.getDate(),
                        hour,
                        minute,
                    );

                    const bucket = Math.random();
                    let sys: number;
                    let dia: number;

                    if (bucket < 0.6) {
                        sys = getRandomInt(110, 129);
                        dia = getRandomInt(70, 84);
                    } else if (bucket < 0.85) {
                        sys = getRandomInt(130, 139);
                        dia = getRandomInt(80, 89);
                    } else {
                        sys = getRandomInt(140, 160);
                        dia = getRandomInt(90, 100);
                    }

                    const pulse = getRandomInt(60, 100);
                    const state = states[getRandomInt(0, states.length - 1)];
                    const memo = memoSamples[getRandomInt(0, memoSamples.length - 1)];

                    const sleepHours = getRandomInt(4, 8) + Math.random();
                    const exercise = state === '운동 후' ? true : Math.random() < 0.4;
                    const stressLevel = getRandomInt(1, 5);

                    data.push({
                        userId,
                        type: 'blood_pressure',
                        datetime,
                        value1: sys,
                        value2: dia,
                        pulse,
                        state,
                        memo,
                        sleepHours,
                        exercise,
                        stressLevel,
                    });
                }
            }

            const result = await prisma.healthRecord.createMany({ data });

            return res.json({
                inserted: result.count,
                days: totalDays,
                perDay: countPerDay,
            });
        } catch (error) {
            console.error('POST /api/records/dev/seed-bp error', error);
            return res
                .status(500)
                .json({
                    error: '샘플 혈압 데이터를 생성하는 중 오류가 발생했습니다.',
                });
        }
    },
);

// =========================
// 4. 전체 기록 삭제 (개발용)
// DELETE /api/records/dev/clear-all
// =========================
router.delete(
    '/dev/clear-all',
    requireAuth,
    async (req: AuthRequest, res: Response) => {
        try {
            const userId = req.user!.id;  // ✅ 수정

            const result = await prisma.healthRecord.deleteMany({
                where: { userId },
            });

            return res.json({ deleted: result.count });
        } catch (error) {
            console.error('DELETE /api/records/dev/clear-all error', error);
            return res
                .status(500)
                .json({ error: '기록을 삭제하는 중 오류가 발생했습니다.' });
        }
    },
);

// =========================
// 5. 단일 기록 조회
// GET /api/records/:id
// =========================
router.get('/:id', requireAuth, async (req: AuthRequest, res: Response) => {
    try {
        const userId = req.user!.id;  // ✅ 수정

        const id = Number(req.params.id);
        if (Number.isNaN(id)) {
            return res.status(400).json({ error: '잘못된 id 입니다.' });
        }

        const record = await prisma.healthRecord.findFirst({
            where: { id, userId },
        });

        if (!record) {
            return res.status(404).json({ error: '기록을 찾을 수 없습니다.' });
        }

        return res.json(record);
    } catch (error) {
        console.error('GET /api/records/:id error', error);
        return res
            .status(500)
            .json({ error: '기록을 조회하는 중 오류가 발생했습니다.' });
    }
});

// =========================
// 6. 기록 생성
// POST /api/records
// =========================
router.post('/', requireAuth, async (req: AuthRequest, res: Response) => {
    try {
        const userId = req.user!.id;  // ✅ 수정

        const {
            type,
            datetime,
            value1,
            value2,
            pulse,
            state,
            memo,
            sleepHours,
            exercise,
            stressLevel,
        } = req.body as {
            type: RecordType;
            datetime: string;
            value1: number;
            value2?: number;
            pulse?: number;
            state?: string;
            memo?: string;
            sleepHours?: number;
            exercise?: boolean;
            stressLevel?: number;
        };

        if (!type || !datetime || typeof value1 !== 'number') {
            return res
                .status(400)
                .json({ error: 'type, datetime, value1는 필수입니다.' });
        }

        const created = await prisma.healthRecord.create({
            data: {
                userId,
                type,
                datetime: new Date(datetime),
                value1,
                value2: typeof value2 === 'number' ? value2 : null,
                pulse: typeof pulse === 'number' ? pulse : null,
                state: state ?? null,
                memo: memo ?? null,
                sleepHours: typeof sleepHours === 'number' ? sleepHours : null,
                exercise: typeof exercise === 'boolean' ? exercise : false,
                stressLevel: typeof stressLevel === 'number' ? stressLevel : null,
            },
        });

        return res.status(201).json(created);
    } catch (error) {
        console.error('POST /api/records error', error);
        return res
            .status(500)
            .json({ error: '기록을 생성하는 중 오류가 발생했습니다.' });
    }
});

// =========================
// 7. 기록 수정
// PUT /api/records/:id
// =========================
router.put('/:id', requireAuth, async (req: AuthRequest, res: Response) => {
    try {
        const userId = req.user!.id;  // ✅ 수정

        const id = Number(req.params.id);
        if (Number.isNaN(id)) {
            return res.status(400).json({ error: '잘못된 id 입니다.' });
        }

        const {
            type,
            datetime,
            value1,
            value2,
            pulse,
            state,
            memo,
            sleepHours,
            exercise,
            stressLevel,
        } = req.body as {
            type?: RecordType;
            datetime?: string;
            value1?: number;
            value2?: number;
            pulse?: number;
            state?: string;
            memo?: string;
            sleepHours?: number;
            exercise?: boolean;
            stressLevel?: number;
        };

        const existing = await prisma.healthRecord.findFirst({
            where: { id, userId },
        });

        if (!existing) {
            return res.status(404).json({ error: '기록을 찾을 수 없습니다.' });
        }

        const updated = await prisma.healthRecord.update({
            where: { id },
            data: {
                type: type ?? existing.type,
                datetime: datetime ? new Date(datetime) : existing.datetime,
                value1: typeof value1 === 'number' ? value1 : existing.value1,
                value2:
                    typeof value2 === 'number' ? value2 : existing.value2,
                pulse:
                    typeof pulse === 'number' ? pulse : existing.pulse,
                state: typeof state === 'string' ? state : existing.state,
                memo: typeof memo === 'string' ? memo : existing.memo,
                sleepHours:
                    typeof sleepHours === 'number'
                        ? sleepHours
                        : existing.sleepHours,
                exercise:
                    typeof exercise === 'boolean'
                        ? exercise
                        : existing.exercise,
                stressLevel:
                    typeof stressLevel === 'number'
                        ? stressLevel
                        : existing.stressLevel,
            },
        });

        return res.json(updated);
    } catch (error) {
        console.error('PUT /api/records/:id error', error);
        return res
            .status(500)
            .json({ error: '기록을 수정하는 중 오류가 발생했습니다.' });
    }
});

// =========================
// 8. 기록 삭제
// DELETE /api/records/:id
// =========================
router.delete(
    '/:id',
    requireAuth,
    async (req: AuthRequest, res: Response) => {
        try {
            const userId = req.user!.id;  // ✅ 수정

            const id = Number(req.params.id);
            if (Number.isNaN(id)) {
                return res.status(400).json({ error: '잘못된 id 입니다.' });
            }

            const existing = await prisma.healthRecord.findFirst({
                where: { id, userId },
            });

            if (!existing) {
                return res.status(404).json({ error: '기록을 찾을 수 없습니다.' });
            }

            await prisma.healthRecord.delete({ where: { id } });

            return res.json({ ok: true });
        } catch (error) {
            console.error('DELETE /api/records/:id error', error);
            return res
                .status(500)
                .json({ error: '기록을 삭제하는 중 오류가 발생했습니다.' });
        }
    },
);

export default router;
