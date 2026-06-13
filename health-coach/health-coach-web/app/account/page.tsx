// app/account/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
    getToken,
    getUser,
    clearAuth,
    type StoredUser,
} from '@/lib/authStorage';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:5001';

export default function AccountPage() {
    const router = useRouter();

    const [user, setUser] = useState<StoredUser | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [deleting, setDeleting] = useState(false);

    // 최초 진입 시 로그인 여부 체크
    useEffect(() => {
        if (typeof window === 'undefined') return;

        const token = getToken();
        if (!token) {
            router.replace('/auth/login');
            return;
        }

        const u = getUser();
        if (!u) {
            router.replace('/auth/login');
            return;
        }

        setUser(u);
        setLoading(false);
    }, [router]);

    const handleLogout = () => {
        clearAuth();
        router.replace('/auth/login');
    };

    const handleDeleteAccount = async () => {
        const token = getToken();
        if (!token) {
            router.replace('/auth/login');
            return;
        }

        const confirm1 = window.confirm(
            '정말 회원 탈퇴를 진행할까요?\n모든 혈압/혈당 기록과 AI 코칭 히스토리가 삭제됩니다.',
        );
        if (!confirm1) return;

        const confirm2 = window.confirm(
            '정말 정말 삭제할까요?\n이 작업은 되돌릴 수 없어요.',
        );
        if (!confirm2) return;

        try {
            setDeleting(true);
            setError(null);

            const res = await fetch(`${API_BASE}/api/auth/me`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                },
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.error || `회원 탈퇴 실패: ${res.status}`);
            }

            // 토큰/유저 정보 삭제
            clearAuth();

            alert('회원 탈퇴가 완료되었습니다.\n그동안 서비스를 이용해 주셔서 감사합니다.');

            // 탈퇴 후에는 회원가입 페이지로 이동
            router.replace('/auth/register');
        } catch (err: any) {
            setError(err.message ?? '회원 탈퇴 중 오류가 발생했습니다.');
        } finally {
            setDeleting(false);
        }
    };

    if (loading) {
        return (
            <main className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
                <p className="text-sm text-slate-300">계정 정보를 불러오는 중...</p>
            </main>
        );
    }

    if (!user) {
        return (
            <main className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
                <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-3 text-center">
                    <p className="text-sm text-slate-300">
                        로그인 정보가 없습니다. 다시 로그인해 주세요.
                    </p>
                    <Link
                        href="/auth/login"
                        className="inline-flex px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-sm font-semibold"
                    >
                        로그인 하러가기
                    </Link>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-slate-950 text-slate-100 flex justify-center">
            <div className="w-full max-w-3xl p-6 space-y-6">
                {/* 상단 헤더 */}
                <header className="flex items-center justify-between gap-3">
                    <div>
                        <h1 className="text-2xl font-bold">👤 계정 관리</h1>
                        <p className="text-xs text-slate-300">
                            로그인 정보 확인과 회원 탈퇴를 할 수 있는 페이지입니다.
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Link
                            href="/"
                            className="px-3 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold"
                        >
                            ⬅ 대시보드로
                        </Link>
                        <button
                            onClick={handleLogout}
                            className="px-3 py-1 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-600 text-xs font-semibold"
                        >
                            로그아웃
                        </button>
                    </div>
                </header>

                {/* 계정 정보 카드 */}
                <section className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <p className="text-xs text-slate-400">로그인 계정</p>
                            <p className="text-sm font-semibold text-slate-100">
                                {user.name ? `${user.name} (${user.email})` : user.email}
                            </p>
                        </div>
                    </div>

                    <div className="grid sm:grid-cols-2 gap-3 text-xs text-slate-300">
                        <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                            <p className="text-[11px] text-slate-400 mb-1">이메일</p>
                            <p className="font-medium">{user.email}</p>
                        </div>
                        <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                            <p className="text-[11px] text-slate-400 mb-1">표시 이름</p>
                            <p className="font-medium">
                                {user.name ?? '설정된 이름이 없습니다.'}
                            </p>
                        </div>
                    </div>

                    <p className="text-[11px] text-slate-500">
                        ※ 현재 버전에서는 비밀번호 변경, 닉네임 변경 등은 지원하지 않고,
                        혈압/혈당 기록 관리와 AI 코칭 기능에 집중하고 있습니다.
                    </p>
                </section>

                {/* 위험 구역: 회원 탈퇴 */}
                <section className="p-4 rounded-xl bg-slate-950 border border-rose-700/60 space-y-3">
                    <h2 className="text-sm font-semibold text-rose-300 flex items-center gap-2">
                        <span>위험 구역</span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/20 border border-rose-500/60 text-rose-200">
              되돌릴 수 없음
            </span>
                    </h2>
                    <p className="text-xs text-slate-300">
                        회원 탈퇴를 진행하면 아래 데이터가 모두 즉시 삭제됩니다.
                    </p>

                    <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
                        <li>혈압 / 혈당 모든 기록</li>
                        <li>라이프스타일 인사이트 계산에 사용된 기록</li>
                        <li>AI 코치 / 라이프스타일 인사이트 코멘트 히스토리</li>
                        <li>목표 혈압 설정 값</li>
                    </ul>

                    {error && (
                        <p className="text-xs text-red-400 whitespace-pre-line">
                            {error}
                        </p>
                    )}

                    <div className="flex justify-end">
                        <button
                            onClick={handleDeleteAccount}
                            disabled={deleting}
                            className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-xs font-semibold disabled:opacity-60"
                        >
                            {deleting ? '탈퇴 처리 중...' : '정말 회원 탈퇴하기'}
                        </button>
                    </div>

                    <p className="text-[10px] text-slate-500">
                        ※ 이 서비스는 학습/포트폴리오용 데모 프로젝트입니다. 실제 진료 기록이나
                        민감한 의료 정보는 저장하지 않습니다.
                    </p>
                </section>
            </div>
        </main>
    );
}
