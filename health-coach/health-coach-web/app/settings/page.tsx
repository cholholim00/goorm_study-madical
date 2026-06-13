// app/settings/page.tsx
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getToken } from '@/lib/authStorage';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:5001';

type UserProfile = {
    id: number;
    userId: number;
    targetSys: number;
    targetDia: number;
};

export default function SettingsPage() {
    const [needLogin, setNeedLogin] = useState(false);
    const [profile, setProfile] = useState<UserProfile | null>(null);
    const [targetSys, setTargetSys] = useState<string>('');
    const [targetDia, setTargetDia] = useState<string>('');
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const fetchProfile = async (token: string) => {
        try {
            setLoading(true);
            setError(null);

            const res = await fetch(`${API_BASE}/api/user/profile`, {
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                },
            });

            if (res.status === 404) {
                setProfile(null);
                setTargetSys('');
                setTargetDia('');
                return;
            }

            if (!res.ok) {
                throw new Error(`profile API error: ${res.status}`);
            }

            const json = (await res.json()) as UserProfile | null;
            setProfile(json);
            if (json) {
                setTargetSys(String(json.targetSys));
                setTargetDia(String(json.targetDia));
            }
        } catch (err: any) {
            setError(
                err.message ??
                '목표 혈압 정보를 불러오는 중 오류가 발생했습니다.',
            );
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

        fetchProfile(token);
    }, []);

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setSuccess(null);

        const token = getToken();
        if (!token) {
            setNeedLogin(true);
            setError('목표 혈압을 저장하려면 먼저 로그인해야 합니다.');
            return;
        }

        if (!targetSys || !targetDia) {
            setError('수축기/이완기 목표 값을 모두 입력해 주세요.');
            return;
        }

        try {
            setSaving(true);

            const body = {
                targetSys: Number(targetSys),
                targetDia: Number(targetDia),
            };

            const res = await fetch(`${API_BASE}/api/user/profile`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify(body),
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.error || `목표 혈압 저장 실패: ${res.status}`);
            }

            const json = (await res.json()) as UserProfile;
            setProfile(json);
            setSuccess('목표 혈압이 저장되었습니다.');
        } catch (err: any) {
            setError(
                err.message ?? '목표 혈압을 저장하는 중 오류가 발생했습니다.',
            );
        } finally {
            setSaving(false);
        }
    };

    return (
        <main className="min-h-screen bg-slate-950 text-slate-100 flex justify-center">
            <div className="w-full max-w-md p-6 space-y-6">
                <header className="flex items-center justify-between gap-3">
                    <div>
                        <h1 className="text-2xl font-bold">🎯 목표 혈압 설정</h1>
                        <p className="text-xs text-slate-300">
                            AI 코치가 참고할 나만의 목표 혈압 범위를 설정할 수 있어요.
                        </p>
                    </div>
                    <Link
                        href="/"
                        className="px-3 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold"
                    >
                        ⬅ 대시보드로
                    </Link>
                </header>

                {needLogin ? (
                    <section className="p-4 rounded-xl bg-slate-900 border border-slate-800">
                        <p className="text-sm text-slate-300">
                            목표 혈압을 설정하려면 로그인이 필요합니다.
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
                            <p className="text-sm text-slate-300">불러오는 중...</p>
                        ) : (
                            <>
                                {profile && (
                                    <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-300 space-y-1">
                                        <p>
                                            현재 목표:{' '}
                                            <span className="font-semibold">
                        {profile.targetSys} / {profile.targetDia} mmHg
                      </span>
                                        </p>
                                    </div>
                                )}

                                <form onSubmit={handleSave} className="space-y-4">
                                    <div className="grid grid-cols-2 gap-2">
                                        <div className="space-y-1">
                                            <label className="text-sm text-slate-300">
                                                목표 수축기 (위 혈압)
                                            </label>
                                            <input
                                                type="number"
                                                value={targetSys}
                                                onChange={e => setTargetSys(e.target.value)}
                                                className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
                                                required
                                            />
                                        </div>
                                        <div className="space-y-1">
                                            <label className="text-sm text-slate-300">
                                                목표 이완기 (아래 혈압)
                                            </label>
                                            <input
                                                type="number"
                                                value={targetDia}
                                                onChange={e => setTargetDia(e.target.value)}
                                                className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
                                                required
                                            />
                                        </div>
                                    </div>

                                    {error && (
                                        <p className="text-sm text-red-400 whitespace-pre-line">
                                            {error}
                                        </p>
                                    )}
                                    {success && (
                                        <p className="text-sm text-emerald-400 whitespace-pre-line">
                                            {success}
                                        </p>
                                    )}

                                    <button
                                        type="submit"
                                        disabled={saving}
                                        className="w-full px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-sm font-semibold disabled:opacity-60"
                                    >
                                        {saving ? '저장 중...' : '목표 혈압 저장'}
                                    </button>
                                </form>

                                <p className="text-[11px] text-slate-500">
                                    ※ 이 값은 AI 코치가 참고하는 목표 범위일 뿐, 실제 진단 기준은 아니에요.
                                    정확한 목표 혈압은 의료 전문가와 상의해 주세요.
                                </p>
                            </>
                        )}
                    </section>
                )}
            </div>
        </main>
    );
}
