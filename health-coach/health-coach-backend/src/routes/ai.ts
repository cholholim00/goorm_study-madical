// src/routes/ai.ts
console.log('📦 ai router loaded');

import { Router } from 'express';
import { prisma } from '../lib/prisma';
import type { AuthRequest } from '../middleware/auth';
import { requireAuth } from '../middleware/auth';
import OpenAI from 'openai';

const router = Router();

// 🔑 OpenAI 클라이언트
const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
});

// 공통 헬퍼: 평균 계산
function calcAvg(nums: number[]): number | null {
    if (!nums.length) return null;
    const sum = nums.reduce((acc, n) => acc + n, 0);
    return sum / nums.length;
}

// 공통 헬퍼: rangeDays 파싱 (문자열/숫자 모두 허용, 기본값 fallback)
function parseRangeDays(raw: unknown, defaultValue: number): number {
    let days = defaultValue;

    if (typeof raw === 'number') {
        days = raw;
    } else if (typeof raw === 'string') {
        const parsed = Number(raw);
        if (!Number.isNaN(parsed)) {
            days = parsed;
        }
    }

    if (days <= 0 || days > 365) {
        days = defaultValue;
    }

    return days;
}

/**
 * 🤖 혈압 요약 기반 AI 코치
 * POST /api/ai/coach
 * body: { rangeDays?: number | string, userNote?: string }
 */
router.post(
    '/coach',
    requireAuth,
    async (req: AuthRequest, res) => {
        try {
            if (!process.env.OPENAI_API_KEY) {
                return res.status(500).json({
                    error: 'OPENAI_API_KEY 환경변수가 설정되지 않았습니다.',
                });
            }

            const userId = req.userId!;
            const { rangeDays: rawRangeDays, userNote } = req.body as {
                rangeDays?: number | string;
                userNote?: string;
            };

            const rangeDays = parseRangeDays(rawRangeDays, 7);

            const now = new Date();
            const from = new Date(
                now.getTime() - rangeDays * 24 * 60 * 60 * 1000,
            );

            // 🔹 최근 rangeDays 동안의 혈압/혈당 기록 가져오기
            const [bpRecords, sugarRecords, latestBp, profile] =
                await Promise.all([
                    prisma.healthRecord.findMany({
                        where: {
                            userId,
                            type: 'blood_pressure',
                            datetime: { gte: from },
                        },
                        orderBy: { datetime: 'asc' },
                    }),
                    prisma.healthRecord.findMany({
                        where: {
                            userId,
                            type: 'blood_sugar',
                            datetime: { gte: from },
                        },
                        orderBy: { datetime: 'asc' },
                    }),
                    prisma.healthRecord.findFirst({
                        where: { userId, type: 'blood_pressure' },
                        orderBy: { datetime: 'desc' },
                    }),
                    prisma.userProfile.findUnique({
                        where: { userId },
                    }),
                ]);

            if (bpRecords.length === 0 && sugarRecords.length === 0) {
                return res.status(400).json({
                    error:
                        'AI 코치를 위한 혈압/혈당 데이터가 아직 없습니다. 먼저 혈압이나 혈당을 몇 번 기록해 주세요.',
                });
            }

            const bpSysList = bpRecords.map((r) => r.value1);
            const bpDiaList = bpRecords
                .map((r) => r.value2)
                .filter((v): v is number => typeof v === 'number');
            const sugarList = sugarRecords.map((r) => r.value1);

            const avgSys = calcAvg(bpSysList);
            const avgDia = calcAvg(bpDiaList);
            const avgSugar = calcAvg(sugarList);

            const summaryForPrompt = `
[최근 ${rangeDays}일 혈압/혈당 요약]

- 혈압 기록 개수: ${bpRecords.length}개
- 평균 혈압: 수축기=${avgSys ?? 'N/A'}, 이완기=${avgDia ?? 'N/A'}
- 혈당 기록 개수: ${sugarRecords.length}개
- 평균 혈당: ${avgSugar ?? 'N/A'}

[가장 최근 혈압]
- 최근 혈압: ${
                latestBp
                    ? `${latestBp.value1} / ${latestBp.value2 ?? '-'}`
                    : '기록 없음'
            }
- 최근 측정 시각: ${
                latestBp ? latestBp.datetime.toISOString() : 'N/A'
            }
- 상태: ${
                latestBp?.state ?? '상태 메모 없음'
            }

[사용자 설정 목표 혈압]
- ${
                profile
                    ? `목표 수축기: ${profile.targetSys}, 목표 이완기: ${profile.targetDia}`
                    : '목표 혈압 아직 설정하지 않음'
            }

[사용자 메모]
- ${userNote ?? '(별도 메모 없음)'}
`.trim();

            const response = await openai.responses.create({
                model: 'gpt-4.1-mini',
                input: [
                    {
                        role: 'system',
                        content:
                            '너는 혈압과 생활 습관을 함께 바라보는 부드러운 건강 코치야. ' +
                            '절대 진단이나 치료 지시를 하지 말고, "이럴 가능성이 있어 보입니다", "참고용으로만 봐 주세요" 같은 톤으로 말해. ' +
                            '숫자(평균 혈압/혈당, 목표 혈압 등)를 기반으로 최근 경향을 설명하고, 생활 습관(수면, 운동, 식습관)을 중심으로 조언해 줘. ' +
                            '마지막에는 반드시 의료 전문가 상담을 권장해.',
                    },
                    {
                        role: 'user',
                        content: [
                            {
                                type: 'input_text',
                                text: summaryForPrompt,
                            },
                        ],
                    },
                ],
            });

            const aiMessage =
                (response.output[0]?.content[0] as any)?.text ??
                'AI 코멘트 생성에 성공했지만 메시지를 읽어오지 못했습니다.';

            // 🔹 코칭 로그 저장
            const log = await prisma.aiCoachLog.create({
                data: {
                    userId,
                    type: 'coach',
                    rangeDays,
                    userNote: userNote ?? null,
                    source: 'bp_summary',
                    aiMessage,
                },
            });

            return res.json({
                message: aiMessage,
                rangeDays,
                avg: {
                    blood_pressure: {
                        avg_sys: avgSys,
                        avg_dia: avgDia,
                        count: bpRecords.length,
                    },
                    blood_sugar: {
                        avg: avgSugar,
                        count: sugarRecords.length,
                    },
                },
                latestBp,
                targetProfile: profile,
                logId: log.id,
            });
        } catch (err) {
            console.error('POST /api/ai/coach error', err);
            return res.status(500).json({
                error: 'AI 코치 메시지 생성 중 서버 오류가 발생했습니다.',
            });
        }
    },
);

/**
 * 🤖 라이프스타일 기반 AI 인사이트
 * POST /api/ai/lifestyle
 * body: { rangeDays?: number | string }
 */
router.post(
    '/lifestyle',
    requireAuth,
    async (req: AuthRequest, res) => {
        try {
            if (!process.env.OPENAI_API_KEY) {
                return res.status(500).json({
                    error: 'OPENAI_API_KEY 환경변수가 설정되지 않았습니다.',
                });
            }

            console.log('➡️ POST /api/ai/lifestyle body =', req.body);

            const userId = req.userId!;
            const { rangeDays: rawRangeDays } = req.body as {
                rangeDays?: number | string;
            };

            const rangeDays = parseRangeDays(rawRangeDays, 30);

            const now = new Date();
            const from = new Date(
                now.getTime() - rangeDays * 24 * 60 * 60 * 1000,
            );

            const records = await prisma.healthRecord.findMany({
                where: {
                    userId,
                    type: 'blood_pressure',
                    datetime: { gte: from },
                },
                orderBy: { datetime: 'asc' },
            });

            if (records.length === 0) {
                return res.status(400).json({
                    error:
                        '라이프스타일 인사이트를 계산할 혈압 데이터가 아직 없습니다. 수면·운동·스트레스 정보를 포함해서 혈압을 몇 번 더 기록해 주세요.',
                });
            }

            const makeStats = (list: typeof records) => {
                const sys = list.map((r) => r.value1);
                const dia = list
                    .map((r) => r.value2)
                    .filter((v): v is number => typeof v === 'number');

                return {
                    count: list.length,
                    avg_sys: calcAvg(sys),
                    avg_dia: calcAvg(dia),
                };
            };

            // 수면 그룹
            const sleepShort = records.filter(
                (r) => typeof r.sleepHours === 'number' && r.sleepHours! < 6,
            );
            const sleepEnough = records.filter(
                (r) => typeof r.sleepHours === 'number' && r.sleepHours! >= 6,
            );

            // 운동 그룹
            const exerciseYes = records.filter((r) => r.exercise === true);
            const exerciseNo = records.filter((r) => r.exercise === false);

            // 스트레스 그룹
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

            const statsForAI = {
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
            };

            const summaryForPrompt = `
[수면 시간]
- 6시간 미만: count=${statsForAI.sleep.short.count}, avg=${statsForAI.sleep.short.avg_sys}/${statsForAI.sleep.short.avg_dia}
- 6시간 이상: count=${statsForAI.sleep.enough.count}, avg=${statsForAI.sleep.enough.avg_sys}/${statsForAI.sleep.enough.avg_dia}

[운동 여부]
- 운동한 날: count=${statsForAI.exercise.yes.count}, avg=${statsForAI.exercise.yes.avg_sys}/${statsForAI.exercise.yes.avg_dia}
- 운동 안 한 날: count=${statsForAI.exercise.no.count}, avg=${statsForAI.exercise.no.avg_sys}/${statsForAI.exercise.no.avg_dia}

[스트레스 수준]
- 낮음(1~2): count=${statsForAI.stress.low.count}, avg=${statsForAI.stress.low.avg_sys}/${statsForAI.stress.low.avg_dia}
- 보통(3): count=${statsForAI.stress.mid.count}, avg=${statsForAI.stress.mid.avg_sys}/${statsForAI.stress.mid.avg_dia}
- 높음(4~5): count=${statsForAI.stress.high.count}, avg=${statsForAI.stress.high.avg_sys}/${statsForAI.stress.high.avg_dia}
`.trim();

            const response = await openai.responses.create({
                model: 'gpt-4.1-mini',
                input: [
                    {
                        role: 'system',
                        content:
                            '너는 혈압과 생활 습관의 경향을 부드럽게 설명해 주는 건강 코치야. ' +
                            '절대 인과관계를 단정하지 말고, "그럴 가능성이 있어 보입니다", "경향상 이런 모습이 보입니다" 수준으로만 말해. ' +
                            '수면/운동/스트레스 각각에 대해 요약해 주고, 마지막에는 반드시 의료 전문가 상담을 권장해.',
                    },
                    {
                        role: 'user',
                        content: [
                            {
                                type: 'input_text',
                                text:
                                    `최근 ${rangeDays}일 동안의 혈압 + 라이프스타일 통계 요약입니다.\n\n` +
                                    summaryForPrompt +
                                    '\n\n이 데이터를 바탕으로 수면, 운동, 스트레스와 혈압 사이의 "경향"을 조심스럽게 설명해 주세요.',
                            },
                        ],
                    },
                ],
            });

            const aiMessage =
                (response.output[0]?.content[0] as any)?.text ??
                'AI 코멘트 생성에 성공했지만 메시지를 읽어오지 못했습니다.';

            // 🔹 코칭 로그 저장
            const log = await prisma.aiCoachLog.create({
                data: {
                    userId,
                    type: 'lifestyle',
                    rangeDays,
                    userNote: null,
                    source: 'lifestyle_stats',
                    aiMessage,
                },
            });

            return res.json({
                message: aiMessage,
                rangeDays,
                stats: statsForAI,
                logId: log.id,
            });
        } catch (err) {
            console.error('POST /api/ai/lifestyle error', err);
            return res.status(500).json({
                error: '라이프스타일 AI 인사이트 생성 중 서버 오류가 발생했습니다.',
            });
        }
    },
);

/**
 * 🧾 AI 코치 히스토리
 * GET /api/ai/history?limit=50
 */
router.get(
    '/history',
    requireAuth,
    async (req: AuthRequest, res) => {
        try {
            const userId = req.userId!;
            const limitParam = req.query.limit as string | undefined;

            let limit = 20;
            if (limitParam && !Number.isNaN(Number(limitParam))) {
                limit = Math.min(Number(limitParam), 100);
            }

            const logs = await prisma.aiCoachLog.findMany({
                where: { userId },
                orderBy: { createdAt: 'desc' },
                take: limit,
            });

            return res.json({ logs });
        } catch (err) {
            console.error('GET /api/ai/history error', err);
            return res.status(500).json({
                error: 'AI 코치 히스토리를 불러오는 중 서버 오류가 발생했습니다.',
            });
        }
    },
);

export default router;
