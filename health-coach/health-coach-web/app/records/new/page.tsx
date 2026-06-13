// app/records/new/page.tsx
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { getToken } from '@/lib/authStorage';

const API_BASE =
    process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:5001';

type RecordType = 'blood_pressure' | 'blood_sugar';

export default function NewRecordPage() {
    const router = useRouter();

    const [type, setType] = useState<RecordType>('blood_pressure');
    const [datetime, setDatetime] = useState<string>(() => {
        // YYYY-MM-DDTHH:MM 형태 (datetime-local input용)
        const d = new Date();
        const yyyy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, '0');
        const dd = String(d.getDate()).padStart(2, '0');
        const hh = String(d.getHours()).padStart(2, '0');
        const mi = String(d.getMinutes()).padStart(2, '0');
        return `${yyyy}-${mm}-${dd}T${hh}:${mi}`;
    });

    const [value1, setValue1] = useState(''); // 수축기 또는 혈당
    const [value2, setValue2] = useState(''); // 이완기 (혈압일 때만)
    const [pulse, setPulse] = useState('');
    const [state, setState] = useState('');
    const [memo, setMemo] = useState('');

    // 라이프스타일 필드
    const [sleepHours, setSleepHours] = useState('');
    const [exercise, setExercise] = useState<'yes' | 'no' | ''>('');
    const [stressLevel, setStressLevel] = useState('');

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [needLogin, setNeedLogin] = useState(false);

    // 처음에 토큰 있는지 확인
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

        // 간단 유효성 체크
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
            if (pulse) body.pulse = Number(pulse);
            if (state.trim()) body.state = state.trim();
            if (memo.trim()) body.memo = memo.trim();
            if (sleepHours) body.sleepHours = Number(sleepHours);
            if (exercise !== '') body.exercise = exercise === 'yes';
            if (stressLevel) body.stressLevel = Number(stressLevel);

            const res = await fetch(`${API_BASE}/api/records`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`, // 🔹 토큰 꼭 붙이기
                },
                body: JSON.stringify(body),
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.error || `기록 저장 실패: ${res.status}`);
            }

            await res.json();

            // 저장 성공 → 대시보드로
            router.push('/');
        } catch (err: any) {
            setError(err.message ?? '기록 저장 중 오류가 발생했습니다.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="min-h-screen bg-slate-950 text-slate-100 flex justify-center">
            <div className="w-full max-w-2xl p-6 space-y-6">
                <header className="flex items-center justify-between gap-3">
                    <div>
                        <h1 className="text-2xl font-bold">📝 새 건강 기록 추가</h1>
                        <p className="text-sm text-slate-300">
                            혈압/혈당과 함께 수면, 운동, 스트레스 정보까지 같이 남겨두면
                            나중에 인사이트에서 패턴을 볼 수 있어요.
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
                    // 🔐 로그인 안 되어 있을 때
                    <section className="p-4 rounded-xl bg-slate-900 border border-slate-800">
                        <p className="text-sm text-slate-300">
                            기록을 추가하려면 먼저 로그인이 필요합니다.
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
                    // ✅ 로그인 된 상태: 폼 보여주기
                    <section className="p-4 rounded-xl bg-slate-900 border border-slate-800">
                        <form onSubmit={handleSubmit} className="space-y-4">
                            {/* 타입 선택 */}
                            <div className="space-y-1">
                                <label className="text-sm text-slate-300">기록 종류</label>
                                <div className="flex gap-3 text-sm">
                                    <button
                                        type="button"
                                        onClick={() => setType('blood_pressure')}
                                        className={`px-3 py-1 rounded-lg border ${
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
                                        className={`px-3 py-1 rounded-lg border ${
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
                                <label className="text-sm text-slate-300">측정 시각</label>
                                <input
                                    type="datetime-local"
                                    className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
                                    value={datetime}
                                    onChange={(e) => setDatetime(e.target.value)}
                                    required
                                />
                            </div>

                            {/* 값 입력 */}
                            {type === 'blood_pressure' ? (
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                                    <div className="space-y-1">
                                        <label className="text-sm text-slate-300">
                                            수축기 혈압 (위)
                                        </label>
                                        <input
                                            type="number"
                                            className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
                                            value={value1}
                                            onChange={(e) => setValue1(e.target.value)}
                                            required
                                        />
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-sm text-slate-300">
                                            이완기 혈압 (아래)
                                        </label>
                                        <input
                                            type="number"
                                            className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
                                            value={value2}
                                            onChange={(e) => setValue2(e.target.value)}
                                        />
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-sm text-slate-300">맥박 (선택)</label>
                                        <input
                                            type="number"
                                            className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
                                            value={pulse}
                                            onChange={(e) => setPulse(e.target.value)}
                                        />
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-1">
                                    <label className="text-sm text-slate-300">
                                        혈당 (mg/dL)
                                    </label>
                                    <input
                                        type="number"
                                        className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
                                        value={value1}
                                        onChange={(e) => setValue1(e.target.value)}
                                        required
                                    />
                                </div>
                            )}

                            {/* 상태 & 메모 */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                <div className="space-y-1">
                                    <label className="text-sm text-slate-300">상태 (선택)</label>
                                    <input
                                        type="text"
                                        placeholder="아침 공복, 운동 후, 야근 후 같은 메모"
                                        className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
                                        value={state}
                                        onChange={(e) => setState(e.target.value)}
                                    />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-sm text-slate-300">메모 (선택)</label>
                                    <input
                                        type="text"
                                        className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
                                        value={memo}
                                        onChange={(e) => setMemo(e.target.value)}
                                    />
                                </div>
                            </div>

                            {/* 라이프스타일 섹션 */}
                            <div className="mt-4 border-t border-slate-800 pt-4 space-y-3">
                                <h2 className="text-sm font-semibold text-slate-200">
                                    🌙 라이프스타일 정보 (선택 입력)
                                </h2>

                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                                    {/* 수면 시간 */}
                                    <div className="space-y-1">
                                        <label className="text-sm text-slate-300">
                                            수면 시간 (시간)
                                        </label>
                                        <input
                                            type="number"
                                            step="0.5"
                                            placeholder="예: 6.5"
                                            className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
                                            value={sleepHours}
                                            onChange={(e) => setSleepHours(e.target.value)}
                                        />
                                    </div>

                                    {/* 운동 여부 */}
                                    <div className="space-y-1">
                                        <label className="text-sm text-slate-300">
                                            오늘 운동 했나요?
                                        </label>
                                        <select
                                            className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
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

                                    {/* 스트레스 지수 */}
                                    <div className="space-y-1">
                                        <label className="text-sm text-slate-300">
                                            스트레스 지수 (1~5)
                                        </label>
                                        <select
                                            className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
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

                                <p className="text-[11px] text-slate-500">
                                    * 이 정보들은 나중에 라이프스타일 인사이트에서
                                    &quot;수면/운동/스트레스에 따라 혈압이 어떻게 달라졌는지&quot;
                                    확인하는 데 사용돼요.
                                </p>
                            </div>

                            {error && (
                                <p className="text-sm text-red-400 whitespace-pre-line">
                                    {error}
                                </p>
                            )}

                            <div className="flex justify-end gap-2 mt-4">
                                <button
                                    type="button"
                                    onClick={() => router.push('/')}
                                    className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-sm font-semibold"
                                >
                                    취소
                                </button>
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-sm font-semibold disabled:opacity-60"
                                >
                                    {loading ? '저장 중...' : '기록 저장하기'}
                                </button>
                            </div>
                        </form>
                    </section>
                )}
            </div>
        </main>
    );
}
