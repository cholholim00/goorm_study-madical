// app/mobile/page.tsx
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { getToken, getUser, clearAuth } from '@/lib/authStorage';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:5001';

type SummaryResponse = {
    rangeDays: number;
    blood_sugar: {
        count: number;
        avg: number | null;
    };
    blood_pressure: {
        count: number;
        avg_sys: number | null;
        avg_dia: number | null;
    };
};

type HealthRecord = {
    id: number;
    datetime: string;
    type: 'blood_sugar' | 'blood_pressure';
    value1: number;
    value2?: number;
    state?: string | null;
    memo?: string | null;
};

type Level = 'normal' | 'elevated' | 'stage1' | 'stage2' | 'unknown';

function classifyBloodPressure(sys: number | null, dia: number | null): Level {
    if (sys == null || dia == null) return 'unknown';

    if (sys < 120 && dia < 80) return 'normal';
    if (sys >= 120 && sys <= 129 && dia < 80) return 'elevated';
    if ((sys >= 130 && sys <= 139) || (dia >= 80 && dia <= 89)) return 'stage1';
    if (sys >= 140 || dia >= 90) return 'stage2';

    return 'unknown';
}

function levelText(level: Level): string {
    switch (level) {
        case 'normal':
            return '정상 범위';
        case 'elevated':
            return '주의 (상승)';
        case 'stage1':
            return '고혈압 1단계 의심';
        case 'stage2':
            return '고혈압 2단계 의심';
        default:
            return '분류 불가';
    }
}

function levelBadge(level: Level): string {
    switch (level) {
        case 'normal':
            return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/60';
        case 'elevated':
            return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/60';
        case 'stage1':
            return 'bg-orange-500/20 text-orange-300 border-orange-500/60';
        case 'stage2':
            return 'bg-red-500/20 text-red-300 border-red-500/60';
        default:
            return 'bg-slate-700/40 text-slate-300 border-slate-600';
    }
}

export default function MobileHomePage() {
    const router = useRouter();

    const [summary, setSummary] = useState<SummaryResponse | null>(null);
    const [records, setRecords] = useState<HealthRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [needLogin, setNeedLogin] = useState(false);
    const [user, setUser] = useState<ReturnType<typeof getUser>>(null);

    const fetchData = async (token: string) => {
        try {
            setLoading(true);
            setError(null);

            const [summaryRes, recordsRes] = await Promise.all([
                fetch(`${API_BASE}/api/records/stats/summary?rangeDays=7`, {
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: `Bearer ${token}`,
                    },
                }),
                fetch(`${API_BASE}/api/records?type=blood_pressure&limit=5`, {
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: `Bearer ${token}`,
                    },
                }),
            ]);

            if (!summaryRes.ok) {
                throw new Error(`summary API error: ${summaryRes.status}`);
            }
            if (!recordsRes.ok) {
                throw new Error(`records API error: ${recordsRes.status}`);
            }

            const summaryJson = (await summaryRes.json()) as SummaryResponse;
            const recordsJson = (await recordsRes.json()) as HealthRecord[];

            setSummary(summaryJson);
            setRecords(recordsJson);
        } catch (err: any) {
            setError(err.message ?? '데이터를 불러오는 중 오류가 발생했습니다.');
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = () => {
        clearAuth();
        setUser(null);
        setSummary(null);
        setRecords([]);
        setNeedLogin(true);
        setError(null);
        router.push('/auth/login');
    };

    useEffect(() => {
        if (typeof window === 'undefined') return;

        const token = getToken();
        if (!token) {
            setNeedLogin(true);
            setLoading(false);
            return;
        }

        const u = getUser();
        if (u) setUser(u);

        fetchData(token);
    }, []);

    const latest = records.length > 0 ? records[0] : null;
    const latestSys =
        latest && typeof latest.value1 === 'number' ? latest.value1 : null;
    const latestDia =
        latest && typeof latest.value2 === 'number' ? latest.value2 : null;

    const latestLevel = classifyBloodPressure(latestSys, latestDia);

    return (
        <main className="min-h-screen bg-slate-950 text-slate-100 flex justify-center">
            <div className="w-full max-w-md p-4 space-y-4">
                {/* 상단 헤더 */}
                <header className="flex items-center justify-between gap-3">
                    <div>
                        <h1 className="text-xl font-bold">📱 모바일 혈압 코치</h1>
                        <p className="text-xs text-slate-300">
                            휴대폰으로 빠르게 기록하고, 최근 상태만 가볍게 확인해요.
                        </p>
                    </div>
                    <div className="flex flex-col items-end gap-1">
            <span className="text-[11px] text-slate-300">
              {user
                  ? `${user.name ?? user.email}님`
                  : '로그인이 필요합니다.'}
            </span>
                        {user ? (
                            <button
                                onClick={handleLogout}
                                className="px-2 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-600 text-[11px] font-semibold"
                            >
                                로그아웃
                            </button>
                        ) : (
                            <Link
                                href="/auth/login"
                                className="px-2 py-1 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-[11px] font-semibold"
                            >
                                로그인
                            </Link>
                        )}
                    </div>
                </header>

                {/* 데스크톱 대시보드로 이동 링크 */}
                <div className="flex justify-end">
                    <Link
                        href="/"
                        className="text-[11px] text-slate-400 underline underline-offset-2"
                    >
                        🖥 데스크톱 대시보드로 보기
                    </Link>
                </div>

                {/* 로그인 안된 경우 안내 */}
                {needLogin ? (
                    <section className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                        <p className="text-sm text-slate-200">
                            모바일 대시보드는 로그인 후에 사용할 수 있어요.
                        </p>
                        <div className="flex gap-2">
                            <Link
                                href="/auth/login"
                                className="flex-1 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-sm font-semibold text-center"
                            >
                                로그인
                            </Link>
                            <Link
                                href="/auth/register"
                                className="flex-1 px-4 py-2 rounded-xl bg-slate-700 hover:bg-slate-600 text-sm font-semibold text-center"
                            >
                                회원가입
                            </Link>
                        </div>
                    </section>
                ) : (
                    <>
                        {/* 오늘 기록하기 버튼 */}
                        <section className="p-4 rounded-xl bg-sky-900/40 border border-sky-700 space-y-3">
                            <p className="text-sm text-slate-200">
                                오늘 혈압 아직 안 쟀다면, 지금 바로 기록해둘까요?
                            </p>
                            <Link
                                href="/mobile/checkin"
                                className="block w-full text-center px-4 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-sm font-semibold"
                            >
                                ✍️ 오늘 혈압 기록하기
                            </Link>
                        </section>

                        {/* 로딩 / 에러 */}
                        {loading && <p className="text-sm">불러오는 중...</p>}
                        {error && (
                            <p className="text-sm text-red-400 whitespace-pre-line">
                                에러: {error}
                            </p>
                        )}

                        {/* 데이터가 있을 때 요약 카드 */}
                        {!loading && !error && (
                            <section className="space-y-3">
                                {/* 최근 혈압 카드 */}
                                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                                    <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400">
                      가장 최근 혈압
                    </span>
                                        <span
                                            className={`inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-medium ${levelBadge(
                                                latestLevel,
                                            )}`}
                                        >
                      {latest ? levelText(latestLevel) : '기록 없음'}
                    </span>
                                    </div>

                                    <div className="text-2xl font-bold">
                                        {latestSys !== null && latestDia !== null
                                            ? `${latestSys} / ${latestDia}`
                                            : '기록 없음'}
                                        <span className="text-xs text-slate-400 ml-1">mmHg</span>
                                    </div>

                                    {latest && (
                                        <div className="text-[11px] text-slate-400 space-y-1">
                                            <p>
                                                상태:{' '}
                                                <span className="text-slate-200">
                          {latest.state ?? '표시 없음'}
                        </span>
                                            </p>
                                            <p>
                                                메모:{' '}
                                                <span className="text-slate-200">
                          {latest.memo ?? '—'}
                        </span>
                                            </p>
                                        </div>
                                    )}
                                </div>

                                {/* 최근 7일 평균 카드 */}
                                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                                    <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400">
                      최근 7일 평균 혈압
                    </span>
                                        <span className="text-[10px] text-slate-400">
                      측정 {summary?.blood_pressure.count ?? 0}회
                    </span>
                                    </div>

                                    <div className="text-lg font-bold">
                                        {summary?.blood_pressure.avg_sys !== null &&
                                        summary?.blood_pressure.avg_dia !== null
                                            ? `${Math.round(
                                                summary.blood_pressure.avg_sys,
                                            )} / ${Math.round(
                                                summary.blood_pressure.avg_dia,
                                            )} mmHg`
                                            : '데이터 없음'}
                                    </div>

                                    <div className="text-[11px] text-slate-400">
                                        최근 7일 평균 혈당:{' '}
                                        {summary?.blood_sugar.avg !== null
                                            ? `${Math.round(summary.blood_sugar.avg)} mg/dL`
                                            : '데이터 없음'}{' '}
                                        (측정{' '}
                                        {summary?.blood_sugar.count != null
                                            ? summary.blood_sugar.count
                                            : 0}
                                        회)
                                    </div>
                                </div>

                                {/* 최근 기록 리스트 (간단 버전) */}
                                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                                    <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-200">
                      최근 기록 (최대 5개)
                    </span>
                                        <Link
                                            href="/records"
                                            className="text-[11px] text-slate-400 underline underline-offset-2"
                                        >
                                            전체 보기
                                        </Link>
                                    </div>

                                    {records.length === 0 ? (
                                        <p className="text-xs text-slate-400">
                                            아직 기록이 없어요. 위의 버튼으로 오늘 혈압부터 기록해볼까요?
                                        </p>
                                    ) : (
                                        <ul className="space-y-2">
                                            {records.map((r) => {
                                                const date = new Date(r.datetime);
                                                const dateStr = `${String(
                                                    date.getMonth() + 1,
                                                ).padStart(2, '0')}/${String(
                                                    date.getDate(),
                                                ).padStart(2, '0')} ${String(
                                                    date.getHours(),
                                                ).padStart(2, '0')}:${String(
                                                    date.getMinutes(),
                                                ).padStart(2, '0')}`;

                                                return (
                                                    <li
                                                        key={r.id}
                                                        className="flex items-center justify-between text-xs border-b border-slate-800 pb-1 last:border-b-0 last:pb-0"
                                                    >
                                                        <div className="flex-1">
                                                            <div className="font-medium text-slate-100">
                                                                {r.value1}
                                                                {r.value2 != null ? ` / ${r.value2}` : ''} mmHg
                                                            </div>
                                                            <div className="text-[11px] text-slate-400">
                                                                {dateStr} · {r.state ?? '상태 미입력'}
                                                            </div>
                                                        </div>
                                                    </li>
                                                );
                                            })}
                                        </ul>
                                    )}
                                </div>

                                <p className="text-[10px] text-slate-500">
                                    ※ 이 서비스는 건강 자가 관리 참고용 도구이며, 의학적 진단이나 치료를
                                    대신할 수 없습니다. 이상 수치가 반복되면 꼭 의료 전문가와 상담하세요.
                                </p>
                            </section>
                        )}
                    </>
                )}
            </div>
        </main>
    );
}
