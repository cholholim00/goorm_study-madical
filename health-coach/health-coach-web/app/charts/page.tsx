// app/charts/page.tsx
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { getToken } from '@/lib/authStorage';
import {
    LineChart,
    Line,
    CartesianGrid,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
} from 'recharts';

const API_BASE =
    process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:5001';

type BPRecord = {
    id: number;
    datetime: string;
    type: 'blood_pressure';
    value1: number; // sys
    value2?: number; // dia
};

type ChartPoint = {
    id: number;
    dateLabel: string;
    sys: number;
    dia: number | null;
};

export default function ChartsPage() {
    const router = useRouter();

    const [data, setData] = useState<ChartPoint[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [needLogin, setNeedLogin] = useState(false);
    const [rangeDays, setRangeDays] = useState<7 | 14 | 30>(7);

    const fetchData = async (token: string, days: number) => {
        try {
            setLoading(true);
            setError(null);

            const res = await fetch(
                `${API_BASE}/api/records?type=blood_pressure&limit=500`,
                {
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: `Bearer ${token}`, // 🔐 토큰
                    },
                },
            );

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.error || `records API error: ${res.status}`);
            }

            const json = (await res.json()) as BPRecord[];

            // 최근 N일 필터링
            const now = new Date();
            const from = new Date(
                now.getTime() - days * 24 * 60 * 60 * 1000,
            ).getTime();

            const filtered = json.filter((r) => {
                const t = new Date(r.datetime).getTime();
                return t >= from;
            });

            // 오래된 것부터 보이게 정렬
            const sorted = filtered.sort(
                (a, b) =>
                    new Date(a.datetime).getTime() - new Date(b.datetime).getTime(),
            );

            const mapped: ChartPoint[] = sorted.map((r) => {
                const d = new Date(r.datetime);
                const mm = String(d.getMonth() + 1).padStart(2, '0');
                const dd = String(d.getDate()).padStart(2, '0');
                const hh = String(d.getHours()).padStart(2, '0');
                const mi = String(d.getMinutes()).padStart(2, '0');
                return {
                    id: r.id,
                    dateLabel: `${mm}-${dd} ${hh}:${mi}`,
                    sys: r.value1,
                    dia:
                        typeof r.value2 === 'number' && !Number.isNaN(r.value2)
                            ? r.value2
                            : null,
                };
            });

            setData(mapped);
        } catch (err: any) {
            setError(err.message ?? '추이 데이터를 불러오는 중 오류가 발생했습니다.');
            setData([]);
        } finally {
            setLoading(false);
        }
    };

    // 첫 로딩 시 로그인 체크 + 데이터 로드
    useEffect(() => {
        const token = getToken();
        if (!token) {
            setNeedLogin(true);
            setLoading(false);
            return;
        }
        fetchData(token, rangeDays);
    }, []);

    // rangeDays 변경 시 다시 로딩
    useEffect(() => {
        const token = getToken();
        if (!token) {
            setNeedLogin(true);
            setLoading(false);
            return;
        }
        fetchData(token, rangeDays);
    }, [rangeDays]);

    return (
        <main className="min-h-screen bg-slate-950 text-slate-100 flex justify-center">
            <div className="w-full max-w-4xl p-4 space-y-4">
                {/* 헤더 */}
                <header className="flex items-center justify-between gap-3">
                    <div>
                        <h1 className="text-xl font-bold">📈 혈압 추이 차트</h1>
                        <p className="text-xs sm:text-sm text-slate-300">
                            최근 일정 기간 동안의 수축기/이완기 변화를 한눈에 확인할 수 있어요.
                        </p>
                    </div>
                    <Link
                        href="/"
                        className="px-3 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold"
                    >
                        ⬅ 대시보드로
                    </Link>
                </header>

                {/* 로그인 안내 */}
                {needLogin ? (
                    <section className="p-4 rounded-xl bg-slate-900 border border-slate-800">
                        <p className="text-sm text-slate-300">
                            혈압 추이 차트는 로그인 후에만 볼 수 있어요.
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
                    <>
                        {/* 기간 선택 */}
                        <section className="p-3 rounded-xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                            <p className="text-xs sm:text-sm text-slate-300">
                                보고 싶은 기간을 선택하면, 그 기간 안의 혈압만 차트에 표시돼요.
                            </p>
                            <div className="flex gap-2 text-xs">
                                <button
                                    type="button"
                                    onClick={() => setRangeDays(7)}
                                    className={`px-3 py-1 rounded-lg border ${
                                        rangeDays === 7
                                            ? 'bg-emerald-500/20 border-emerald-500 text-emerald-200'
                                            : 'bg-slate-950 border-slate-700 text-slate-300'
                                    }`}
                                >
                                    최근 7일
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setRangeDays(14)}
                                    className={`px-3 py-1 rounded-lg border ${
                                        rangeDays === 14
                                            ? 'bg-emerald-500/20 border-emerald-500 text-emerald-200'
                                            : 'bg-slate-950 border-slate-700 text-slate-300'
                                    }`}
                                >
                                    최근 14일
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setRangeDays(30)}
                                    className={`px-3 py-1 rounded-lg border ${
                                        rangeDays === 30
                                            ? 'bg-emerald-500/20 border-emerald-500 text-emerald-200'
                                            : 'bg-slate-950 border-slate-700 text-slate-300'
                                    }`}
                                >
                                    최근 30일
                                </button>
                            </div>
                        </section>

                        {/* 로딩 / 에러 */}
                        {loading && <p className="text-sm">불러오는 중...</p>}
                        {error && (
                            <p className="text-sm text-red-400 whitespace-pre-line">
                                에러: {error}
                            </p>
                        )}

                        {/* 차트 영역 */}
                        {!loading && !error && (
                            <section className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                                {data.length === 0 ? (
                                    <p className="text-sm text-slate-400">
                                        선택한 기간 안에 혈압 기록이 없어요. 기록을 추가하거나 샘플
                                        데이터를 생성해보세요.
                                    </p>
                                ) : (
                                    <div className="h-[260px] sm:h-[320px] w-full">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart data={data} margin={{ left: 4, right: 12 }}>
                                                <CartesianGrid strokeDasharray="3 3" />
                                                <XAxis
                                                    dataKey="dateLabel"
                                                    tick={{ fontSize: 10 }}
                                                    angle={-30}
                                                    textAnchor="end"
                                                    height={50}
                                                />
                                                <YAxis
                                                    tick={{ fontSize: 10 }}
                                                    width={40}
                                                    domain={['dataMin - 10', 'dataMax + 10']}
                                                    unit=""
                                                />
                                                <Tooltip
                                                    contentStyle={{
                                                        backgroundColor: '#020617',
                                                        borderColor: '#1e293b',
                                                        fontSize: 12,
                                                    }}
                                                />
                                                <Line
                                                    type="monotone"
                                                    dataKey="sys"
                                                    name="수축기"
                                                    stroke="#22c55e"
                                                    strokeWidth={2}
                                                    dot={{ r: 2 }}
                                                    activeDot={{ r: 4 }}
                                                />
                                                <Line
                                                    type="monotone"
                                                    dataKey="dia"
                                                    name="이완기"
                                                    stroke="#38bdf8"
                                                    strokeWidth={2}
                                                    dot={{ r: 2 }}
                                                    activeDot={{ r: 4 }}
                                                />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>
                                )}
                            </section>
                        )}

                        <p className="text-[11px] text-slate-500">
                            ※ 이 차트는 경향을 보는 용도이며, 의료적 진단이나 치료 지시가
                            아닙니다. 수치가 지속적으로 높거나 불안하다면 반드시 의료
                            전문가와 상담하세요.
                        </p>
                    </>
                )}
            </div>
        </main>
    );
}
