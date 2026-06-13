// app/ai-history/page.tsx
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getToken } from '@/lib/authStorage';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:5001';

type AiCoachLog = {
    id: number;
    userId: number;
    createdAt: string;
    type: string;        // "coach" | "lifestyle" 등
    rangeDays: number;
    userNote?: string | null;
    source?: string | null;
    aiMessage: string;
};

export default function AiHistoryPage() {
    const [needLogin, setNeedLogin] = useState(false);
    const [logs, setLogs] = useState<AiCoachLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchHistory = async (token: string) => {
        try {
            setLoading(true);
            setError(null);

            const res = await fetch(`${API_BASE}/api/ai/history?limit=50`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.error || `history API error: ${res.status}`);
            }

            const json = (await res.json()) as { logs: AiCoachLog[] } | AiCoachLog[];

            // 백엔드가 { logs: [...] } 형식으로 보내는 현재 버전에 맞추기
            if (Array.isArray(json)) {
                setLogs(json);
            } else if (Array.isArray(json.logs)) {
                setLogs(json.logs);
            } else {
                setLogs([]);
            }
        } catch (err: any) {
            setError(err.message ?? 'AI 코칭 히스토리를 불러오는 중 오류가 발생했습니다.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (typeof window === 'undefined') return;

        const token = getToken();
        if (!token) {
            setNeedLogin(true);
            setLoading(false);
            return;
        }

        fetchHistory(token);
    }, []);

    return (
        <main className="min-h-screen bg-slate-950 text-slate-100 flex justify-center">
            <div className="w-full max-w-5xl p-6 space-y-6">
                {/* 헤더 */}
                <header className="flex items-center justify-between gap-3">
                    <div>
                        <h1 className="text-2xl font-bold">🧾 AI 코치 히스토리</h1>
                        <p className="text-sm text-slate-300">
                            지금까지 받았던 AI 혈압 코치·라이프스타일 인사이트를
                            타임라인으로 다시 볼 수 있어요.
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
                            AI 코치 히스토리는 로그인 후에만 볼 수 있어요.
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
                    </section>
                ) : (
                    <section className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
                        {loading ? (
                            <p className="text-sm text-slate-300">히스토리를 불러오는 중...</p>
                        ) : error ? (
                            <p className="text-sm text-red-400 whitespace-pre-line">{error}</p>
                        ) : logs.length === 0 ? (
                            <p className="text-sm text-slate-300">
                                아직 저장된 AI 코칭 히스토리가 없습니다. <br />
                                <span className="text-slate-400">
                                    👉 먼저{' '}
                                    <span className="font-semibold">AI 코치 / 라이프스타일 인사이트</span>{' '}
                                    버튼을 눌러 코멘트를 한 번 받아보세요.
                                </span>
                            </p>
                        ) : (
                            <div className="space-y-3">
                                {logs.map((log) => {
                                    const created = new Date(log.createdAt);
                                    const dateStr = `${created.getFullYear()}-${String(
                                        created.getMonth() + 1,
                                    ).padStart(2, '0')}-${String(created.getDate()).padStart(
                                        2,
                                        '0',
                                    )} ${String(created.getHours()).padStart(2, '0')}:${String(
                                        created.getMinutes(),
                                    ).padStart(2, '0')}`;

                                    const typeLabel =
                                        log.type === 'coach'
                                            ? '혈압 요약 코치'
                                            : log.type === 'lifestyle'
                                                ? '라이프스타일 인사이트'
                                                : log.type;

                                    return (
                                        <article
                                            key={log.id}
                                            className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2"
                                        >
                                            <div className="flex items-center justify-between gap-2">
                                                <div className="flex flex-col">
                                                    <span className="text-xs text-slate-400">
                                                        {dateStr}
                                                    </span>
                                                    <span className="text-sm font-semibold">
                                                        {typeLabel} · 최근 {log.rangeDays}일 기준
                                                    </span>
                                                </div>
                                                {log.source && (
                                                    <span className="px-2 py-0.5 rounded-full bg-slate-800 text-[11px] text-slate-300 border border-slate-700">
                                                        {log.source}
                                                    </span>
                                                )}
                                            </div>

                                            {log.userNote && (
                                                <div className="mt-1 text-xs text-slate-300">
                                                    <span className="font-semibold text-slate-200">
                                                        사용자의 고민/메모:
                                                    </span>
                                                    <div className="mt-1 whitespace-pre-line">
                                                        {log.userNote}
                                                    </div>
                                                </div>
                                            )}

                                            <div className="mt-2 p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs whitespace-pre-line">
                                                {log.aiMessage}
                                            </div>
                                        </article>
                                    );
                                })}
                            </div>
                        )}

                        <p className="text-[11px] text-slate-500">
                            ※ 이 히스토리는 참고용 기록일 뿐, 의료적 진단이나 치료 지시가 아닙니다.
                            건강에 대한 중요한 결정은 반드시 의료 전문가와 상의해 주세요.
                        </p>
                    </section>
                )}
            </div>
        </main>
    );
}
