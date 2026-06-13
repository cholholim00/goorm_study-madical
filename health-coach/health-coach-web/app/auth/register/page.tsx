// app/auth/register/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

const API_BASE =
    process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:5001';

export default function RegisterPage() {
    const router = useRouter();

    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // 이미 로그인 되어 있으면 / 로 보내기
    useEffect(() => {
        if (typeof window === 'undefined') return;

        const token = localStorage.getItem('hc_token');
        if (token) {
            router.replace('/');
        }
    }, [router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (loading) return; // 중복 클릭 방지
        setError(null);
        setLoading(true);

        try {
            console.log('📝 [REGISTER] request start', { email, name });

            const res = await fetch(`${API_BASE}/api/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email,
                    password,
                    name: name || null,
                }),
            });

            let body: any = null;
            try {
                body = await res.json();
            } catch (parseErr) {
                console.warn('⚠️ [REGISTER] response JSON 파싱 실패', parseErr);
            }

            console.log('📝 [REGISTER] raw response', res.status, body);

            if (!res.ok) {
                const msg =
                    body?.error || `회원가입 실패 (status: ${res.status})`;
                throw new Error(msg);
            }

            if (!body?.token || !body?.user) {
                throw new Error('서버 응답 형식이 올바르지 않습니다.');
            }

            if (typeof window !== 'undefined') {
                localStorage.setItem('hc_token', body.token);
                localStorage.setItem('hc_user', JSON.stringify(body.user));
            }

            console.log('✅ [REGISTER] success, redirect to /');
            router.push('/');
        } catch (err: any) {
            console.error('❌ [REGISTER] error in handleSubmit:', err);
            setError(
                err?.message ?? '회원가입 중 알 수 없는 오류가 발생했습니다.',
            );
        } finally {
            // ✅ 성공/실패 상관없이 무조건 로딩 OFF
            setLoading(false);
        }
    };

    return (
        <main className="min-h-screen bg-slate-950 text-slate-100 flex justify-center">
            <div className="w-full max-w-md p-6 space-y-6">
                <header className="space-y-1">
                    <h1 className="text-2xl font-bold">회원가입</h1>
                    <p className="text-sm text-slate-300">
                        AI 혈압 코치 대시보드를 사용하기 위한 계정을 만들어 주세요.
                    </p>
                </header>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-1">
                        <label className="text-sm text-slate-300">이름 (선택)</label>
                        <input
                            type="text"
                            className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-sm"
                            value={name}
                            onChange={e => setName(e.target.value)}
                            placeholder="예: 닉네임"
                        />
                    </div>

                    <div className="space-y-1">
                        <label className="text-sm text-slate-300">이메일</label>
                        <input
                            type="email"
                            className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-sm"
                            value={email}
                            onChange={e => setEmail(e.target.value)}
                            required
                        />
                    </div>

                    <div className="space-y-1">
                        <label className="text-sm text-slate-300">비밀번호</label>
                        <input
                            type="password"
                            className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-sm"
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                            required
                            minLength={6}
                        />
                    </div>

                    {error && (
                        <p className="text-sm text-red-400 whitespace-pre-line">
                            {error}
                        </p>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-sm font-semibold disabled:opacity-60"
                    >
                        {loading ? '회원가입 중...' : '회원가입'}
                    </button>
                </form>

                <p className="text-xs text-slate-400">
                    이미 계정이 있으신가요?{' '}
                    <a
                        href="/auth/login"
                        className="text-emerald-400 hover:underline"
                    >
                        로그인 하기
                    </a>
                </p>
            </div>
        </main>
    );
}