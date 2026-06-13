// app/insights/page.tsx
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getToken } from '@/lib/authStorage';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:5001';

type GroupStats = {
    count: number;
    avg_sys: number | null;
    avg_dia: number | null;
};

type LifestyleStats = {
    rangeDays: number;
    sleep: {
        short: GroupStats;
        enough: GroupStats;
    };
    exercise: {
        yes: GroupStats;
        no: GroupStats;
    };
    stress: {
        low: GroupStats;
        mid: GroupStats;
        high: GroupStats;
    };
};

export default function InsightsPage() {
    const [needLogin, setNeedLogin] = useState(false);
    const [rangeDays, setRangeDays] = useState<7 | 14 | 30>(30);
    const [stats, setStats] = useState<LifestyleStats | null>(null);
    const [loadingStats, setLoadingStats] = useState(true);
    const [statsError, setStatsError] = useState<string | null>(null);

    const [aiMessage, setAiMessage] = useState<string | null>(null);
    const [aiLoading, setAiLoading] = useState(false);
    const [aiError, setAiError] = useState<string | null>(null);

    const fetchStats = async (token: string, days: number) => {
        try {
            setLoadingStats(true);
            setStatsError(null);

            const res = await fetch(
                `${API_BASE}/api/records/stats/lifestyle?rangeDays=${days}`,
                {
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: `Bearer ${token}`,
                    },
                },
            );

            if (!res.ok) {
                throw new Error(`lifestyle stats API error: ${res.status}`);
            }

            const json = await res.json() as LifestyleStats;
            setStats(json);
        } catch (err: any) {
            setStatsError(
                err.message ?? '라이프스타일 인사이트를 불러오는 중 오류가 발생했습니다.',
            );
        } finally {
            setLoadingStats(false);
        }
    };

    useEffect(() => {
        if (typeof window === 'undefined') return;

        const token = getToken();
        if (!token) {
            setNeedLogin(true);
            setLoadingStats(false);
            return;
        }

        fetchStats(token, rangeDays);
    }, []);

    useEffect(() => {
        if (needLogin) return;
        const token = getToken();
        if (!token) {
            setNeedLogin(true);
            setLoadingStats(false);
            return;
        }
        fetchStats(token, rangeDays);
    }, [rangeDays, needLogin]);

    const handleAskInsights = async () => {
        setAiError(null);
        setAiMessage(null);

        const token = getToken();
        if (!token) {
            setNeedLogin(true);
            setAiError('AI 인사이트를 보려면 로그인해야 합니다.');
            return;
        }

        try {
            setAiLoading(true);

            const res = await fetch(`${API_BASE}/api/ai/lifestyle`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ rangeDays }),
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.error || `AI 인사이트 호출 실패: ${res.status}`);
            }

            const json = await res.json() as { aiMessage?: string; message?: string };
            setAiMessage(json.aiMessage ?? json.message ?? '(응답 본문 없음)');
        } catch (err: any) {
            setAiError(err.message ?? 'AI 인사이트 호출 중 오류가 발생했습니다.');
        } finally {
            setAiLoading(false);
        }
    };

    const renderGroupRow = (label: string, g: GroupStats) => (
        <tr key={label}>
            <td className="border border-slate-800 px-2 py-1 text-xs">{label}</td>
            <td className="border border-slate-800 px-2 py-1 text-xs text-center">
                {g.count}
            </td>
            <td className="border border-slate-800 px-2 py-1 text-xs text-center">
                {g.avg_sys != null && g.avg_dia != null
                    ? `${Math.round(g.avg_sys)} / ${Math.round(g.avg_dia)}`
                    : '-'}
            </td>
        </tr>
    );

    return (
        <main className="min-h-screen bg-slate-950 text-slate-100 flex justify-center">
            <div className="w-full max-w-5xl p-6 space-y-6">
                <header className="flex items-center justify-between gap-3">
                    <div>
                        <h1 className="text-2xl font-bold">📊 라이프스타일 인사이트</h1>
                        <p className="text-sm text-slate-300">
                            수면·운동·스트레스와 혈압 사이의 관계를 통계와 AI 코멘트로 확인해요.
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Link
                            href="/"
                            className="px-3 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold"
                        >
                            ⬅ 대시보드로
                        </Link>
                    </div>
                </header>

                {needLogin ? (
                    <section className="p-4 rounded-xl bg-slate-900 border border-slate-800">
                        <p className="text-sm text-slate-300">
                            라이프스타일 인사이트는 로그인 후에 볼 수 있어요.
                        </p>
                        <div className="mt-3 flex gap-2">
                            <Link
                                href="/auth/login"
                                className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-sm font-semibold"
                            >
                                로그인 하기
                            </Link>
                            <Link
                                href="/auth/register"
                                className="px-4 py-2 rounded-xl bg-slate-700 hover:bg-slate-600 text-sm font-semibold"
                            >
                                회원가입
                            </Link>
                        </div>
                        {aiError && (
                            <p className="mt-3 text-xs text-red-400 whitespace-pre-line">
                                {aiError}
                            </p>
                        )}
                    </section>
                ) : (
                    <>
                        {/* 통계 표 영역 */}
                        <section className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
                            <div className="flex items-center justify-between text-sm">
                                <div className="flex items-center gap-2">
                                    <span className="text-slate-300">분석 기간:</span>
                                    <select
                                        value={rangeDays}
                                        onChange={e =>
                                            setRangeDays(Number(e.target.value) as 7 | 14 | 30)
                                        }
                                        className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1 text-sm"
                                    >
                                        <option value={7}>최근 7일</option>
                                        <option value={14}>최근 14일</option>
                                        <option value={30}>최근 30일</option>
                                    </select>
                                </div>
                            </div>

                            {loadingStats ? (
                                <p className="text-xs text-slate-300">통계를 불러오는 중...</p>
                            ) : statsError ? (
                                <p className="text-xs text-red-400 whitespace-pre-line">
                                    {statsError}
                                </p>
                            ) : stats ? (
                                <div className="space-y-4 text-xs">
                                    {/* 수면 */}
                                    <div>
                                        <h2 className="text-sm font-semibold mb-1">
                                            😴 수면 시간 vs 혈압
                                        </h2>
                                        <div className="overflow-x-auto">
                                            <table className="w-full border-collapse">
                                                <thead>
                                                <tr className="bg-slate-800">
                                                    <th className="border border-slate-700 px-2 py-1 text-left">
                                                        구분
                                                    </th>
                                                    <th className="border border-slate-700 px-2 py-1">
                                                        측정 횟수
                                                    </th>
                                                    <th className="border border-slate-700 px-2 py-1">
                                                        평균 혈압 (수축기/이완기)
                                                    </th>
                                                </tr>
                                                </thead>
                                                <tbody>
                                                {renderGroupRow('6시간 미만 수면', stats.sleep.short)}
                                                {renderGroupRow('6시간 이상 수면', stats.sleep.enough)}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>

                                    {/* 운동 */}
                                    <div>
                                        <h2 className="text-sm font-semibold mb-1">
                                            🏃 운동 여부 vs 혈압
                                        </h2>
                                        <div className="overflow-x-auto">
                                            <table className="w-full border-collapse">
                                                <thead>
                                                <tr className="bg-slate-800">
                                                    <th className="border border-slate-700 px-2 py-1 text-left">
                                                        구분
                                                    </th>
                                                    <th className="border border-slate-700 px-2 py-1">
                                                        측정 횟수
                                                    </th>
                                                    <th className="border border-slate-700 px-2 py-1">
                                                        평균 혈압 (수축기/이완기)
                                                    </th>
                                                </tr>
                                                </thead>
                                                <tbody>
                                                {renderGroupRow('운동한 날', stats.exercise.yes)}
                                                {renderGroupRow('운동하지 않은 날', stats.exercise.no)}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>

                                    {/* 스트레스 */}
                                    <div>
                                        <h2 className="text-sm font-semibold mb-1">
                                            😵 스트레스 vs 혈압
                                        </h2>
                                        <div className="overflow-x-auto">
                                            <table className="w-full border-collapse">
                                                <thead>
                                                <tr className="bg-slate-800">
                                                    <th className="border border-slate-700 px-2 py-1 text-left">
                                                        구분
                                                    </th>
                                                    <th className="border border-slate-700 px-2 py-1">
                                                        측정 횟수
                                                    </th>
                                                    <th className="border border-slate-700 px-2 py-1">
                                                        평균 혈압 (수축기/이완기)
                                                    </th>
                                                </tr>
                                                </thead>
                                                <tbody>
                                                {renderGroupRow('스트레스 낮음 (1~2)', stats.stress.low)}
                                                {renderGroupRow('스트레스 보통 (3)', stats.stress.mid)}
                                                {renderGroupRow('스트레스 높음 (4~5)', stats.stress.high)}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <p className="text-xs text-slate-400">
                                    아직 라이프스타일 인사이트를 계산할 수 있는 데이터가 충분하지 않습니다.
                                    수면·운동·스트레스 정보를 포함해서 기록을 조금 더 쌓아 주세요.
                                </p>
                            )}
                        </section>

                        {/* AI 인사이트 영역 */}
                        <section className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                            <div className="flex items-center justify-between">
                                <h2 className="text-sm font-semibold">
                                    🧠 AI 라이프스타일 인사이트
                                </h2>
                            </div>
                            <p className="text-xs text-slate-300">
                                위 통계를 바탕으로, 수면·운동·스트레스와 혈압 사이의 경향을 조심스럽게 분석해 드려요.
                            </p>

                            {aiError && (
                                <p className="text-xs text-red-400 whitespace-pre-line">
                                    {aiError}
                                </p>
                            )}

                            <button
                                type="button"
                                onClick={handleAskInsights}
                                disabled={aiLoading}
                                className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-xs font-semibold disabled:opacity-60"
                            >
                                {aiLoading ? 'AI 인사이트 분석 중...' : 'AI 인사이트 받기'}
                            </button>

                            {aiMessage && (
                                <div className="mt-3 p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs whitespace-pre-line">
                                    {aiMessage}
                                </div>
                            )}

                            <p className="text-[11px] text-slate-500">
                                ※ 이 분석은 통계를 바탕으로 한 참고용 설명이며, 인과관계를 단정하지 않습니다.
                                건강 관련 결정은 반드시 의료 전문가와 상의해 주세요.
                            </p>
                        </section>
                    </>
                )}
            </div>
        </main>
    );
}
