// app/mobile/checkin/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { getToken } from '@/lib/authStorage';

const API_BASE =
    process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:5001';

type RecordType = 'blood_pressure' | 'blood_sugar';

export default function MobileCheckinPage() {
    const router = useRouter();

    const [type, setType] = useState<RecordType>('blood_pressure');
    const [datetime, setDatetime] = useState<string>(() => {
        const d = new Date();
        const yyyy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, '0');
        const dd = String(d.getDate()).padStart(2, '0');
        const hh = String(d.getHours()).padStart(2, '0');
        const mi = String(d.getMinutes()).padStart(2, '0');
        return `${yyyy}-${mm}-${dd}T${hh}:${mi}`;
    });

    const [value1, setValue1] = useState('');
    const [value2, setValue2] = useState('');
    const [state, setState] = useState('');
    const [memo, setMemo] = useState('');

    // 라이프스타일 필드
    const [sleepHours, setSleepHours] = useState('');
    const [exercise, setExercise] = useState<'yes' | 'no' | ''>('');
    const [stressLevel, setStressLevel] = useState('');

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [needLogin, setNeedLogin] = useState(false);

    // 최초 마운트 시 로그인 체크
    useEffect(() => {
        const token = getToken();
        if (!token) {
            setNeedLogin(true);
        }
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        const token = getToken();
        if (!token) {
            setNeedLogin(true);
            setError('기록을 추가하려면 먼저 로그인해야 합니다.');
            return;
        }

        if (!value1) {
            setError(
                type === 'blood_pressure'
                    ? '수축기 혈압을 입력해주세요.'
                    : '혈당 값을 입력해주세요.',
            );
            return;
        }

        try {
            setLoading(true);

            const body: any = {
                type,
                datetime: new Date(datetime).toISOString(),
                value1: Number(value1),
            };

            if (type === 'blood_pressure' && value2) {
                body.value2 = Number(value2);
            }
            if (state.trim()) body.state = state.trim();
            if (memo.trim()) body.memo = memo.trim();
            if (sleepHours) body.sleepHours = Number(sleepHours);
            if (exercise !== '') body.exercise = exercise === 'yes';
            if (stressLevel) body.stressLevel = Number(stressLevel);

            const res = await fetch(`${API_BASE}/api/records`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`, // 🔹 로그인 토큰 필수
                },
                body: JSON.stringify(body),
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.error || `기록 저장 실패: ${res.status}`);
            }

            await res.json();

            // 저장 성공 → 대시보드로 이동
            router.push('/');
        } catch (err: any) {
            setError(err.message ?? '기록 저장 중 오류가 발생했습니다.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="min-h-screen bg-slate-950 text-slate-100 flex justify-center">
            <div className="w-full max-w-md p-4 space-y-4">
                {/* 헤더 */}
                <header className="flex items-center justify-between gap-2">
                    <button
                        type="button"
                        onClick={() => router.push('/')}
                        className="px-2 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs"
                    >
                        ⬅ 대시보드
                    </button>
                    <h1 className="text-lg font-bold text-right">
                        📱 모바일 빠른 기록 (Check-in)
                    </h1>
                </header>

                {needLogin ? (
                    // 🔐 로그인 안 되어 있을 때
                    <section className="p-4 rounded-xl bg-slate-900 border border-slate-800">
                        <p className="text-sm text-slate-300">
                            이 모바일 입력 화면을 사용하려면 로그인이 필요합니다.
                        </p>
                        <div className="mt-3 flex gap-2 justify-end">
                            <Link
                                href="/auth/login"
                                className="px-3 py-1.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-xs font-semibold"
                            >
                                로그인
                            </Link>
                            <Link
                                href="/auth/register"
                                className="px-3 py-1.5 rounded-xl bg-slate-700 hover:bg-slate-600 text-xs font-semibold"
                            >
                                회원가입
                            </Link>
                        </div>
                    </section>
                ) : (
                    // ✅ 로그인 된 상태: 입력 폼
                    <section className="p-4 rounded-xl bg-slate-900 border border-slate-800">
                        <form onSubmit={handleSubmit} className="space-y-3">
                            {/* 타입 선택 */}
                            <div className="space-y-1">
                                <label className="text-xs text-slate-300">기록 종류</label>
                                <div className="flex gap-2 text-xs">
                                    <button
                                        type="button"
                                        onClick={() => setType('blood_pressure')}
                                        className={`flex-1 px-2 py-1 rounded-lg border ${
                                            type === 'blood_pressure'
                                                ? 'bg-emerald-500/20 border-emerald-500 text-emerald-200'
                                                : 'bg-slate-950 border-slate-700 text-slate-300'
                                        }`}
                                    >
                                        혈압
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setType('blood_sugar')}
                                        className={`flex-1 px-2 py-1 rounded-lg border ${
                                            type === 'blood_sugar'
                                                ? 'bg-sky-500/20 border-sky-500 text-sky-200'
                                                : 'bg-slate-950 border-slate-700 text-slate-300'
                                        }`}
                                    >
                                        혈당
                                    </button>
                                </div>
                            </div>

                            {/* 날짜/시간 */}
                            <div className="space-y-1">
                                <label className="text-xs text-slate-300">측정 시각</label>
                                <input
                                    type="datetime-local"
                                    className="w-full rounded-lg bg-slate-950 border border-slate-700 px-2 py-2 text-xs"
                                    value={datetime}
                                    onChange={(e) => setDatetime(e.target.value)}
                                    required
                                />
                            </div>

                            {/* 값 입력 */}
                            {type === 'blood_pressure' ? (
                                <div className="grid grid-cols-2 gap-2">
                                    <div className="space-y-1">
                                        <label className="text-xs text-slate-300">수축기</label>
                                        <input
                                            type="number"
                                            className="w-full rounded-lg bg-slate-950 border border-slate-700 px-2 py-2 text-xs"
                                            value={value1}
                                            onChange={(e) => setValue1(e.target.value)}
                                            required
                                        />
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-xs text-slate-300">이완기</label>
                                        <input
                                            type="number"
                                            className="w-full rounded-lg bg-slate-950 border border-slate-700 px-2 py-2 text-xs"
                                            value={value2}
                                            onChange={(e) => setValue2(e.target.value)}
                                        />
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-1">
                                    <label className="text-xs text-slate-300">혈당 (mg/dL)</label>
                                    <input
                                        type="number"
                                        className="w-full rounded-lg bg-slate-950 border border-slate-700 px-2 py-2 text-xs"
                                        value={value1}
                                        onChange={(e) => setValue1(e.target.value)}
                                        required
                                    />
                                </div>
                            )}

                            {/* 상태/메모 */}
                            <div className="space-y-1">
                                <label className="text-xs text-slate-300">상태 (선택)</label>
                                <input
                                    type="text"
                                    placeholder="아침 공복, 운동 후 등"
                                    className="w-full rounded-lg bg-slate-950 border border-slate-700 px-2 py-2 text-xs"
                                    value={state}
                                    onChange={(e) => setState(e.target.value)}
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-xs text-slate-300">메모 (선택)</label>
                                <textarea
                                    className="w-full rounded-lg bg-slate-950 border border-slate-700 px-2 py-2 text-xs min-h-[60px]"
                                    value={memo}
                                    onChange={(e) => setMemo(e.target.value)}
                                />
                            </div>

                            {/* 라이프스타일 */}
                            <div className="mt-2 space-y-2 border-t border-slate-800 pt-2">
                                <p className="text-[11px] text-slate-400">
                                    🌙 라이프스타일 정보는 나중에 인사이트 분석에 사용돼요.
                                </p>

                                <div className="space-y-1">
                                    <label className="text-xs text-slate-300">
                                        수면 시간 (시간)
                                    </label>
                                    <input
                                        type="number"
                                        step="0.5"
                                        placeholder="예: 6.5"
                                        className="w-full rounded-lg bg-slate-950 border border-slate-700 px-2 py-2 text-xs"
                                        value={sleepHours}
                                        onChange={(e) => setSleepHours(e.target.value)}
                                    />
                                </div>

                                <div className="space-y-1">
                                    <label className="text-xs text-slate-300">
                                        오늘 운동 했나요?
                                    </label>
                                    <select
                                        className="w-full rounded-lg bg-slate-950 border border-slate-700 px-2 py-2 text-xs"
                                        value={exercise}
                                        onChange={(e) =>
                                            setExercise(e.target.value as 'yes' | 'no' | '')
                                        }
                                    >
                                        <option value="">선택 안 함</option>
                                        <option value="yes">네</option>
                                        <option value="no">아니요</option>
                                    </select>
                                </div>

                                <div className="space-y-1">
                                    <label className="text-xs text-slate-300">
                                        스트레스 지수 (1~5)
                                    </label>
                                    <select
                                        className="w-full rounded-lg bg-slate-950 border border-slate-700 px-2 py-2 text-xs"
                                        value={stressLevel}
                                        onChange={(e) => setStressLevel(e.target.value)}
                                    >
                                        <option value="">선택 안 함</option>
                                        <option value="1">1 - 매우 낮음</option>
                                        <option value="2">2 - 낮음</option>
                                        <option value="3">3 - 보통</option>
                                        <option value="4">4 - 높음</option>
                                        <option value="5">5 - 매우 높음</option>
                                    </select>
                                </div>
                            </div>

                            {error && (
                                <p className="text-xs text-red-400 whitespace-pre-line">
                                    {error}
                                </p>
                            )}

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full mt-2 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-sm font-semibold disabled:opacity-60"
                            >
                                {loading ? '저장 중...' : '빠르게 기록 저장하기'}
                            </button>
                        </form>
                    </section>
                )}
            </div>
        </main>
    );
}
