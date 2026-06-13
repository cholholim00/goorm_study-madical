// app/records/page.tsx
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getToken } from '@/lib/authStorage';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:5001';

type HealthRecord = {
    id: number;
    datetime: string;
    type: 'blood_sugar' | 'blood_pressure';
    value1: number;
    value2?: number;
    pulse?: number | null;
    state?: string | null;
    memo?: string | null;
    sleepHours?: number | null;
    exercise?: boolean | null;
    stressLevel?: number | null;
};

export default function RecordsPage() {
    const [records, setRecords] = useState<HealthRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [needLogin, setNeedLogin] = useState(false);
    const [deletingId, setDeletingId] = useState<number | null>(null);

    // 전체 기록 불러오기
    const fetchRecords = async (token: string) => {
        try {
            setLoading(true);
            setError(null);

            const res = await fetch(
                `${API_BASE}/api/records?type=blood_pressure&limit=500`,
                {
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: `Bearer ${token}`, // 🔐 로그인 토큰
                    },
                }
            );

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.error || `records API error: ${res.status}`);
            }

            const json = (await res.json()) as HealthRecord[];

            // 최신순 정렬
            const sorted = [...json].sort(
                (a, b) =>
                    new Date(b.datetime).getTime() - new Date(a.datetime).getTime()
            );

            setRecords(sorted);
        } catch (err: any) {
            setError(err.message ?? '기록을 불러오는 중 오류가 발생했습니다.');
            setRecords([]);
        } finally {
            setLoading(false);
        }
    };

    // 삭제 핸들러
    const handleDelete = async (id: number) => {
        const ok = window.confirm('이 기록을 정말 삭제할까요?');
        if (!ok) return;

        const token = getToken();
        if (!token) {
            setNeedLogin(true);
            setError('기록을 삭제하려면 먼저 로그인해야 합니다.');
            return;
        }

        try {
            setDeletingId(id);
            setError(null);

            const res = await fetch(`${API_BASE}/api/records/${id}`, {
                method: 'DELETE',
                headers: {
                    Authorization: `Bearer ${token}`, // 🔐 삭제에도 토큰 필수
                },
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.error || `delete API error: ${res.status}`);
            }

            // 프론트 상태에서 바로 제거
            setRecords((prev) => prev.filter((r) => r.id !== id));
        } catch (err: any) {
            setError(err.message ?? '기록을 삭제하는 중 오류가 발생했습니다.');
        } finally {
            setDeletingId(null);
        }
    };

    // 마운트 시 토큰 체크 & 데이터 로드
    useEffect(() => {
        const token = getToken();
        if (!token) {
            setNeedLogin(true);
            setLoading(false);
            return;
        }
        setNeedLogin(false);
        fetchRecords(token);
    }, []);

    return (
        <main className="min-h-screen bg-slate-950 text-slate-100 flex justify-center">
            <div className="w-full max-w-5xl p-6 space-y-6">
                {/* 헤더 */}
                <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                    <div>
                        <h1 className="text-2xl font-bold">📋 전체 혈압 기록 관리</h1>
                        <p className="text-sm text-slate-300">
                            기록을 한눈에 보고, 필요하면 개별 기록을 삭제할 수 있어요.
                        </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        <Link
                            href="/"
                            className="px-3 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold"
                        >
                            ⬅ 대시보드로
                        </Link>
                        <Link
                            href="/records/new"
                            className="px-3 py-1 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-xs font-semibold"
                        >
                            ➕ 새 기록 추가
                        </Link>
                        <Link
                            href="/mobile/checkin"
                            className="px-3 py-1 rounded-xl bg-indigo-500 hover:bg-indigo-400 text-xs font-semibold"
                        >
                            📱 모바일 체크인
                        </Link>
                    </div>
                </header>

                {/* 로그인 필요 안내 */}
                {needLogin ? (
                    <section className="p-4 rounded-xl bg-slate-900 border border-slate-800">
                        <p className="text-sm text-slate-300 mb-3">
                            전체 기록은 로그인 후에만 확인할 수 있어요.
                        </p>
                        <div className="flex gap-2">
                            <Link
                                href="/auth/login"
                                className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-sm font-semibold text-center"
                            >
                                로그인 하기
                            </Link>
                            <Link
                                href="/auth/register"
                                className="px-4 py-2 rounded-xl bg-slate-700 hover:bg-slate-600 text-sm font-semibold text-center"
                            >
                                회원가입
                            </Link>
                        </div>
                    </section>
                ) : (
                    <>
                        {loading && (
                            <p className="text-sm text-slate-300">기록 불러오는 중...</p>
                        )}

                        {error && (
                            <p className="text-sm text-red-400 whitespace-pre-line">
                                에러: {error}
                            </p>
                        )}

                        {!loading && !error && (
                            <section className="p-4 rounded-xl bg-slate-900 border border-slate-800">
                                {records.length === 0 ? (
                                    <p className="text-sm text-slate-400">
                                        아직 혈압 기록이 없습니다.
                                        <br />
                                        대시보드에서 샘플 데이터를 생성하거나, 새 기록을 추가해 보세요.
                                    </p>
                                ) : (
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm border-collapse">
                                            <thead>
                                            <tr className="bg-slate-800">
                                                <th className="border border-slate-700 px-2 py-1 text-left">
                                                    날짜/시간
                                                </th>
                                                <th className="border border-slate-700 px-2 py-1">
                                                    수축기
                                                </th>
                                                <th className="border border-slate-700 px-2 py-1">
                                                    이완기
                                                </th>
                                                <th className="border border-slate-700 px-2 py-1">
                                                    상태
                                                </th>
                                                <th className="border border-slate-700 px-2 py-1">
                                                    메모
                                                </th>
                                                <th className="border border-slate-700 px-2 py-1">
                                                    액션
                                                </th>
                                            </tr>
                                            </thead>
                                            <tbody>
                                            {records.map((r) => {
                                                const d = new Date(r.datetime);
                                                const label = `${d.getFullYear()}-${String(
                                                    d.getMonth() + 1
                                                ).padStart(2, '0')}-${String(d.getDate()).padStart(
                                                    2,
                                                    '0'
                                                )} ${String(d.getHours()).padStart(2, '0')}:${String(
                                                    d.getMinutes()
                                                ).padStart(2, '0')}`;

                                                return (
                                                    <tr key={r.id}>
                                                        <td className="border border-slate-800 px-2 py-1 whitespace-nowrap">
                                                            {label}
                                                        </td>
                                                        <td className="border border-slate-800 px-2 py-1 text-center">
                                                            {r.value1}
                                                        </td>
                                                        <td className="border border-slate-800 px-2 py-1 text-center">
                                                            {r.value2 ?? '-'}
                                                        </td>
                                                        <td className="border border-slate-800 px-2 py-1 text-center">
                                                            {r.state ?? '-'}
                                                        </td>
                                                        <td className="border border-slate-800 px-2 py-1 max-w-[200px]">
                                <span className="line-clamp-2">
                                  {r.memo ?? ''}
                                </span>
                                                        </td>
                                                        <td className="border border-slate-800 px-2 py-1 text-center">
                                                            <button
                                                                type="button"
                                                                onClick={() => handleDelete(r.id)}
                                                                disabled={deletingId === r.id}
                                                                className="px-2 py-1 rounded-lg bg-rose-500 hover:bg-rose-400 text-xs font-semibold disabled:opacity-60"
                                                            >
                                                                {deletingId === r.id ? '삭제 중...' : '삭제'}
                                                            </button>
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </section>
                        )}
                    </>
                )}
            </div>
        </main>
    );
}
