// app/page.tsx
'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
    getToken,
    getUser,
    clearAuth,
    type StoredUser,
} from '@/lib/authStorage';

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

function levelColor(level: Level): string {
    switch (level) {
        case 'normal':
            return 'bg-emerald-500/15 text-emerald-200 border-emerald-500/60';
        case 'elevated':
            return 'bg-yellow-500/15 text-yellow-200 border-yellow-500/60';
        case 'stage1':
            return 'bg-orange-500/15 text-orange-200 border-orange-500/60';
        case 'stage2':
            return 'bg-red-500/15 text-red-200 border-red-500/60';
        default:
            return 'bg-slate-700/40 text-slate-300 border-slate-600';
    }
}

export default function Home() {
    const router = useRouter();

    const [summary, setSummary] = useState<SummaryResponse | null>(null);
    const [records, setRecords] = useState<HealthRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [seeding, setSeeding] = useState(false);
    const [clearing, setClearing] = useState(false);
    const [needLogin, setNeedLogin] = useState(false);
    const [user, setUser] = useState<StoredUser | null>(null);

    const handleLogout = () => {
        clearAuth();
        setUser(null);
        setSummary(null);
        setRecords([]);
        setNeedLogin(true);
        setError(null);
        router.push('/auth/login');
    };

    // 토큰을 인자로 받아서 데이터 로딩
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
                fetch(`${API_BASE}/api/records?type=blood_pressure`, {
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

            const sorted = [...recordsJson].sort(
                (a, b) =>
                    new Date(b.datetime).getTime() - new Date(a.datetime).getTime(),
            );

            setSummary(summaryJson);
            setRecords(sorted.slice(0, 10));
        } catch (err: any) {
            setError(err.message ?? '알 수 없는 오류');
        } finally {
            setLoading(false);
        }
    };

    // 샘플 데이터 생성 (로그인 필요)
    const handleSeed = async () => {
        const token = getToken();
        if (!token) {
            setNeedLogin(true);
            setError('샘플 데이터를 생성하려면 먼저 로그인해야 합니다.');
            return;
        }

        try {
            setSeeding(true);
            setError(null);
            const res = await fetch(`${API_BASE}/api/records/dev/seed-bp`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                    days: 14,
                    perDay: 5,
                }),
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.error || `seed API error: ${res.status}`);
            }

            await fetchData(token);
        } catch (err: any) {
            setError(err.message ?? '샘플 데이터 생성 중 오류');
        } finally {
            setSeeding(false);
        }
    };

    // 전체 삭제 (로그인 필요)
    const handleClearAll = async () => {
        const token = getToken();
        if (!token) {
            setNeedLogin(true);
            setError('모든 기록을 삭제하려면 먼저 로그인해야 합니다.');
            return;
        }

        const ok = window.confirm(
            '정말 모든 혈압 기록을 삭제할까요?\n(샘플 데이터뿐 아니라 지금까지 넣은 실제 기록도 모두 지워집니다.)',
        );
        if (!ok) return;

        try {
            setClearing(true);
            setError(null);

            const res = await fetch(`${API_BASE}/api/records/dev/clear-all`, {
                method: 'DELETE',
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.error || `clear API error: ${res.status}`);
            }

            await fetchData(token);
        } catch (err: any) {
            setError(err.message ?? '데이터 삭제 중 오류가 발생했습니다.');
        } finally {
            setClearing(false);
        }
    };

    // 마운트 시 토큰 확인 → 없으면 로그인 안내, 있으면 데이터 로딩
    useEffect(() => {
        if (typeof window === 'undefined') return;

        const token = getToken();
        if (!token) {
            setNeedLogin(true);
            setLoading(false);
            return;
        }

        const u = getUser();
        if (u) {
            setUser(u);
        }

        fetchData(token);
    }, [router]);

    const latest = records.length > 0 ? records[0] : null;
    const latestSys =
        latest && typeof latest.value1 === 'number' ? latest.value1 : null;
    const latestDia =
        latest && typeof latest.value2 === 'number' ? latest.value2 : null;

    const latestLevel = classifyBloodPressure(latestSys, latestDia);

    return (
        <main className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100 flex justify-center">
            <div className="w-full max-w-6xl px-4 py-6 md:px-8 md:py-10 space-y-6 md:space-y-8">
                {/* 헤더 */}
                <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div className="space-y-3">
                        <div className="inline-flex items-center gap-2 rounded-full border border-sky-500/40 bg-sky-500/10 px-3 py-1 text-[11px] font-medium text-sky-200 shadow-sm">
                            <span>🧪 Beta</span>
                            <span>AI 혈압 · 혈당 라이프 코치</span>
                        </div>
                        <div>
                            <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
                                AI 혈압 코치
                            </h1>
                            <p className="mt-1 text-sm text-slate-300">
                                최근 혈압·혈당 추이를 한눈에 보고,
                                AI 코치와 라이프스타일까지 함께 관리해요.
                            </p>
                        </div>
                        <p className="text-[11px] text-slate-500">
                            계정 설정과 <span className="font-semibold">회원 탈퇴</span>는 상단 메뉴의{' '}
                            <span className="font-semibold">목표 혈압 설정</span> 화면에서 할 수 있어요.
                        </p>
                    </div>

                    <div className="flex flex-col items-end gap-3">
                        {/* 로그인 상태 표시 영역 */}
                        <div className="text-xs text-slate-300 flex items-center gap-2">
                            {user ? (
                                <>
                  <span className="px-2 py-1 rounded-lg bg-slate-900/80 border border-slate-700">
                    {user.name ?? user.email} 님, 환영해요 🐻
                  </span>
                                    <button onClick={handleLogout} className="px-2 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-600 text-[11px] font-semibold transition">
                                        로그아웃
                                    </button>
                                </>
                            ) : (
                                <>
                                    <span>로그인이 필요합니다.</span>
                                    <Link href="/auth/login" className="px-2 py-1 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-[11px] font-semibold transition">
                                        로그인
                                    </Link>
                                </>
                            )}
                        </div>

                        {/* 네비게이션 버튼들 */}
                        <div className="flex flex-wrap gap-2 justify-end">
                            <Link href="/records/new" className="px-3 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-xs md:text-sm font-semibold shadow-sm">
                                ➕ 혈압 기록 추가하기
                            </Link>
                            <Link href="/mobile/checkin" className="px-3 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-xs md:text-sm font-semibold shadow-sm">
                                📱 모바일 체크인
                            </Link>
                            <Link href="/ai-coach" className="px-3 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-xs md:text-sm font-semibold shadow-sm">
                                🤖 AI 코치 요약 보기
                            </Link>
                            <Link href="/charts" className="px-3 py-2 rounded-xl bg-indigo-500 hover:bg-indigo-400 text-xs md:text-sm font-semibold shadow-sm">
                                📈 혈압 추이 차트
                            </Link>
                            <Link href="/settings" className="px-3 py-2 rounded-xl bg-slate-700 hover:bg-slate-600 text-xs md:text-sm font-semibold shadow-sm">
                                🎯 목표 혈압설정
                            </Link>
                            <Link href="/records" className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs md:text-sm font-semibold shadow-sm">
                                📋 전체 기록 관리
                            </Link>
                            <Link href="/insights" className="px-3 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-xs md:text-sm font-semibold shadow-sm">
                                📊 라이프스타일 인사이트
                            </Link>
                            <Link href="/account" className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-sm font-semibold border border-slate-600">
                                👤 계정 관리
                            </Link>
                        </div>
                    </div>
                </header>

                <div className="flex justify-end">
                    <Link href="/mobile" className="text-[11px] text-slate-400 underline underline-offset-2 hover:text-slate-200">
                        📱 모바일 전용 대시보드로 보기
                    </Link>
                </div>

                {/* 샘플 생성 / 전체 삭제 섹션 */}
                <section className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 flex flex-col md:flex-row md:items-center md:justify-between gap-3 shadow-lg shadow-slate-950/40">
                    <div className="space-y-1">
                        <p className="text-sm text-slate-200 font-medium">
                            빠르게 그래프와 인사이트를 확인해 보고 싶다면?
                        </p>
                        <p className="text-xs text-slate-400">
                            샘플 데이터를 생성해서 전체 흐름을 테스트할 수 있고, 필요하면 한 번에
                            초기화할 수 있어요.
                        </p>
                    </div>
                    <div className="flex flex-wrap gap-2 justify-end">
                        <button
                            onClick={handleSeed}
                            disabled={seeding || clearing}
                            className="px-4 py-2 rounded-xl bg-purple-500 hover:bg-purple-400 text-sm font-semibold disabled:opacity-60 disabled:cursor-not-allowed shadow-sm"
                        >
                            {seeding ? '생성 중...' : '🧪 샘플 데이터 생성'}
                        </button>
                        <button
                            onClick={handleClearAll}
                            disabled={clearing || seeding}
                            className="px-4 py-2 rounded-xl bg-rose-500 hover:bg-rose-400 text-sm font-semibold disabled:opacity-60 disabled:cursor-not-allowed shadow-sm"
                        >
                            {clearing ? '삭제 중...' : '🧹 모든 기록 삭제'}
                        </button>
                    </div>
                </section>

                {/* 로그인 여부에 따라 */}
                {needLogin ? (
                    <section className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800/80 shadow-lg shadow-slate-950/40">
                        <p className="text-sm text-slate-200">
                            이 대시보드는 로그인 후에만 볼 수 있어요.
                        </p>
                        <p className="mt-1 text-xs text-slate-400">
                            계정을 만들면 혈압·혈당 기록을 안전하게 저장하고, AI 코치 피드백도 받을 수
                            있어요.
                        </p>
                        <div className="mt-4 flex gap-2">
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
                    <>
                        {loading && (
                            <p className="text-sm text-slate-300">데이터를 불러오는 중입니다...</p>
                        )}
                        {error && (
                            <p className="text-sm text-red-400 whitespace-pre-line">에러: {error}</p>
                        )}

                        {!loading && !error && (
                            <div className="grid md:grid-cols-3 gap-4 md:gap-6">
                                {/* 왼쪽: 최근 상태 + 평균 카드들 */}
                                <section className="md:col-span-1 space-y-4">
                                    <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 shadow-lg shadow-slate-950/40 space-y-3">
                                        <div className="flex items-center justify-between">
                                            <h2 className="font-semibold text-sm">최근 {summary?.rangeDays ?? 7}일 요약</h2>
                                            <span
                                                className={`inline-flex items-center px-2 py-0.5 rounded-full border text-[11px] font-medium ${levelColor(
                                                    latestLevel,
                                                )}`}
                                            >
                        {latest ? levelText(latestLevel) : '기록 없음'}
                      </span>
                                        </div>

                                        <div className="space-y-2">
                                            <p className="text-xs text-slate-400">가장 최근 혈압</p>
                                            <p className="text-xl font-bold">
                                                {latestSys !== null && latestDia !== null
                                                    ? `${latestSys} / ${latestDia} mmHg`
                                                    : '기록 없음'}
                                            </p>
                                            {latest && (
                                                <p className="text-xs text-slate-400">
                                                    상태:{' '}
                                                    <span className="font-medium text-slate-100">
                            {latest.state ?? '표시 없음'}
                          </span>
                                                </p>
                                            )}
                                        </div>
                                    </div>

                                    {/* 평균 카드 2개 */}
                                    <div className="grid grid-cols-1 gap-3">
                                        <div className="p-3 rounded-2xl bg-slate-900/80 border border-slate-800/80 text-sm shadow">
                                            <p className="text-xs text-slate-400 mb-1">
                                                최근 {summary?.rangeDays ?? 7}일 평균 혈압
                                            </p>
                                            <p className="text-lg font-bold">
                                                {summary?.blood_pressure.avg_sys !== null &&
                                                summary?.blood_pressure.avg_dia !== null
                                                    ? `${Math.round(
                                                        summary.blood_pressure.avg_sys,
                                                    )} / ${Math.round(
                                                        summary.blood_pressure.avg_dia,
                                                    )} mmHg`
                                                    : '데이터 없음'}
                                            </p>
                                            <p className="mt-1 text-[11px] text-slate-400">
                                                측정 횟수: {summary?.blood_pressure.count ?? 0}회
                                            </p>
                                        </div>

                                        <div className="p-3 rounded-2xl bg-slate-900/80 border border-slate-800/80 text-sm shadow">
                                            <p className="text-xs text-slate-400 mb-1">
                                                최근 {summary?.rangeDays ?? 7}일 평균 혈당
                                            </p>
                                            <p className="text-lg font-bold">
                                                {summary?.blood_sugar.avg !== null
                                                    ? `${Math.round(summary.blood_sugar.avg)} mg/dL`
                                                    : '데이터 없음'}
                                            </p>
                                            <p className="mt-1 text-[11px] text-slate-400">
                                                측정 횟수: {summary?.blood_sugar.count ?? 0}회
                                            </p>
                                        </div>
                                    </div>

                                    <p className="text-[11px] text-slate-500">
                                        ※ 이 분류는 일반적인 혈압 범위를 참고한 것이며, 의료적 진단이나 치료 지시가
                                        아닙니다. 걱정되는 수치가 계속된다면 의료 전문가와 상담하세요.
                                    </p>
                                </section>

                                {/* 오른쪽: 최근 기록 리스트 */}
                                <section className="md:col-span-2 p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 shadow-lg shadow-slate-950/40">
                                    <div className="flex items-center justify-between mb-3">
                                        <h2 className="font-semibold text-sm">
                                            최근 혈압 기록 <span className="text-xs text-slate-400">(최대 10개)</span>
                                        </h2>
                                        <Link
                                            href="/records"
                                            className="text-[11px] text-sky-300 hover:text-sky-200 underline underline-offset-2"
                                        >
                                            전체 기록 보러가기
                                        </Link>
                                    </div>

                                    {records.length === 0 ? (
                                        <div className="rounded-xl border border-dashed border-slate-700/80 bg-slate-950/60 p-6 text-center space-y-2">
                                            <p className="text-sm text-slate-300 font-medium">
                                                아직 혈압 기록이 없어요.
                                            </p>
                                            <p className="text-xs text-slate-400">
                                                상단의 <span className="font-semibold">“혈압 기록 추가하기”</span>{' '}
                                                버튼을 눌러 첫 기록을 남겨보세요. 또는 샘플 데이터를 생성해서 UI를 먼저
                                                확인할 수 있어요.
                                            </p>
                                        </div>
                                    ) : (
                                        <div className="overflow-x-auto rounded-xl border border-slate-800/80">
                                            <table className="w-full text-sm border-collapse">
                                                <thead>
                                                <tr className="bg-slate-900/90">
                                                    <th className="border-b border-slate-800 px-3 py-2 text-left text-xs font-medium text-slate-300">
                                                        날짜/시간
                                                    </th>
                                                    <th className="border-b border-slate-800 px-3 py-2 text-xs font-medium text-slate-300">
                                                        혈압
                                                    </th>
                                                    <th className="border-b border-slate-800 px-3 py-2 text-xs font-medium text-slate-300">
                                                        상태
                                                    </th>
                                                    <th className="border-b border-slate-800 px-3 py-2 text-xs font-medium text-slate-300">
                                                        메모
                                                    </th>
                                                </tr>
                                                </thead>
                                                <tbody>
                                                {records.map((r, idx) => {
                                                    const date = new Date(r.datetime);
                                                    const dateStr = `${date.getFullYear()}-${String(
                                                        date.getMonth() + 1,
                                                    ).padStart(2, '0')}-${String(date.getDate()).padStart(
                                                        2,
                                                        '0',
                                                    )} ${String(date.getHours()).padStart(
                                                        2,
                                                        '0',
                                                    )}:${String(date.getMinutes()).padStart(2, '0')}`;

                                                    const rowBg =
                                                        idx % 2 === 0 ? 'bg-slate-950/40' : 'bg-slate-900/40';

                                                    return (
                                                        <tr key={r.id} className={rowBg}>
                                                            <td className="border-t border-slate-800 px-3 py-2 whitespace-nowrap text-xs">
                                                                {dateStr}
                                                            </td>
                                                            <td className="border-t border-slate-800 px-3 py-2 text-center text-xs">
                                                                {r.value1}
                                                                {r.value2 !== undefined ? ` / ${r.value2}` : ''}
                                                            </td>
                                                            <td className="border-t border-slate-800 px-3 py-2 text-center text-xs">
                                                                {r.state ?? '-'}
                                                            </td>
                                                            <td className="border-t border-slate-800 px-3 py-2 text-xs">
                                                                {r.memo ?? ''}
                                                            </td>
                                                        </tr>
                                                    );
                                                })}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}
                                </section>
                            </div>
                        )}
                    </>
                )}
            </div>
        </main>
    );
}