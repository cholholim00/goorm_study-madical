// app/records/[id]/edit/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getToken } from '@/lib/authStorage';


const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:5001';

type HealthRecord = {
    id: number;
    datetime: string;
    type: 'blood_pressure' | 'blood_sugar';
    value1: number;
    value2?: number | null;
    pulse?: number | null;
    state?: string | null;
    memo?: string | null;
    sleepHours?: number | null;
    exercise?: boolean | null;
    stressLevel?: number | null;
};

export default function EditRecordPage() {
    const params = useParams();
    const router = useRouter();
    const id = Number(params?.id);

    const [initialLoading, setInitialLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);

    const [datetime, setDatetime] = useState('');
    const [sys, setSys] = useState('');
    const [dia, setDia] = useState('');
    const [pulse, setPulse] = useState('');
    const [stateText, setStateText] = useState('');
    const [memo, setMemo] = useState('');

    const [sleepHours, setSleepHours] = useState('');
    const [exercise, setExercise] = useState<'yes' | 'no' | ''>('');
    const [stressLevel, setStressLevel] = useState('3');

    const [submitting, setSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState<string | null>(null);
    const [needLogin, setNeedLogin] = useState(false);


    useEffect(() => {
        if (!id || Number.isNaN(id)) {
            setLoadError('잘못된 id입니다.');
            setInitialLoading(false);
            return;
        }

        const fetchRecord = async () => {
            try {
                setInitialLoading(true);
                setLoadError(null);

                const res = await fetch(`${API_BASE}/api/records/${id}`);
                if (!res.ok) {
                    throw new Error(`API error: ${res.status}`);
                }

                const r = (await res.json()) as HealthRecord;

                const d = new Date(r.datetime);
                setDatetime(d.toISOString().slice(0, 16)); // yyyy-MM-ddTHH:mm
                setSys(String(r.value1 ?? ''));
                setDia(String(r.value2 ?? ''));
                setPulse(r.pulse != null ? String(r.pulse) : '');
                setStateText(r.state ?? '');
                setMemo(r.memo ?? '');

                setSleepHours(
                    r.sleepHours != null ? String(r.sleepHours) : '',
                );
                setExercise(
                    r.exercise == null ? '' : r.exercise ? 'yes' : 'no',
                );
                setStressLevel(
                    r.stressLevel != null ? String(r.stressLevel) : '3',
                );
            } catch (err: any) {
                setLoadError(err.message ?? '기록을 불러오는 중 오류가 발생했습니다.');
            } finally {
                setInitialLoading(false);
            }
        };

        fetchRecord();
    }, [id]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!id || Number.isNaN(id)) return;

        try {
            setSubmitting(true);
            setSubmitError(null);

            const sysNum = Number(sys);
            const diaNum = Number(dia);

            if (Number.isNaN(sysNum) || Number.isNaN(diaNum)) {
                setSubmitError('수축기/이완기 혈압을 숫자로 입력해 주세요.');
                setSubmitting(false);
                return;
            }

            const body: any = {
                type: 'blood_pressure',
                datetime: new Date(datetime).toISOString(),
                value1: sysNum,
                value2: diaNum,
            };

            if (pulse.trim() !== '') {
                const p = Number(pulse);
                if (!Number.isNaN(p)) {
                    body.pulse = p;
                }
            }

            if (stateText.trim() !== '') {
                body.state = stateText.trim();
            }

            if (memo.trim() !== '') {
                body.memo = memo.trim();
            }

            if (sleepHours.trim() !== '') {
                const s = Number(sleepHours);
                if (!Number.isNaN(s) && s > 0) {
                    body.sleepHours = s;
                }
            }

            if (exercise === 'yes') {
                body.exercise = true;
            } else if (exercise === 'no') {
                body.exercise = false;
            }

            if (stressLevel.trim() !== '') {
                const s = Number(stressLevel);
                if (!Number.isNaN(s) && s > 0) {
                    body.stressLevel = s;
                }
            }

            const res = await fetch(`${API_BASE}/api/records/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(body),
            });

            if (!res.ok) {
                const errJson = await res.json().catch(() => ({}));
                throw new Error(errJson.error || `API error: ${res.status}`);
            }

            // 수정 완료 후 전체 기록 페이지로
            router.push('/records');
        } catch (err: any) {
            setSubmitError(err.message ?? '기록 수정 중 오류가 발생했습니다.');
        } finally {
            setSubmitting(false);
        }
    };

    if (initialLoading) {
        return (
            <main className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
                <p>기록을 불러오는 중...</p>
            </main>
        );
    }

    if (loadError) {
        return (
            <main className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
                <div className="space-y-3 text-center">
                    <p className="text-sm text-red-400">에러: {loadError}</p>
                    <button
                        onClick={() => router.push('/records')}
                        className="text-sm text-slate-300 underline"
                    >
                        ← 기록 목록으로 돌아가기
                    </button>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-slate-950 text-slate-100 flex justify-center">
            <div className="w-full max-w-2xl p-6 space-y-6">
                <header className="flex items-center justify-between">
                    <h1 className="text-2xl font-bold">✏️ 혈압 기록 수정</h1>
                    <button
                        type="button"
                        onClick={() => router.push('/records')}
                        className="text-sm text-slate-300 hover:text-slate-100 underline"
                    >
                        ← 기록 목록으로
                    </button>
                </header>

                <section className="p-4 rounded-xl bg-slate-900 border border-slate-800">
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {/* 기본 측정값 */}
                        <div className="grid gap-4 md:grid-cols-2">
                            <div className="space-y-2">
                                <label className="block text-sm text-slate-300">
                                    측정 일시
                                </label>
                                <input
                                    type="datetime-local"
                                    value={datetime}
                                    onChange={(e) => setDatetime(e.target.value)}
                                    className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
                                />
                            </div>

                            <div className="space-y-2">
                                <label className="block text-sm text-slate-300">
                                    혈압 (수축기 / 이완기)
                                </label>
                                <div className="flex items-center gap-2">
                                    <input
                                        type="number"
                                        placeholder="수축기 (위)"
                                        value={sys}
                                        onChange={(e) => setSys(e.target.value)}
                                        className="w-1/2 rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
                                    />
                                    <span>/</span>
                                    <input
                                        type="number"
                                        placeholder="이완기 (아래)"
                                        value={dia}
                                        onChange={(e) => setDia(e.target.value)}
                                        className="w-1/2 rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* 선택 필드: 맥박, 상태, 메모 */}
                        <div className="grid gap-4 md:grid-cols-3">
                            <div className="space-y-2">
                                <label className="block text-sm text-slate-300">
                                    맥박 (선택)
                                </label>
                                <input
                                    type="number"
                                    placeholder="예: 70"
                                    value={pulse}
                                    onChange={(e) => setPulse(e.target.value)}
                                    className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
                                />
                            </div>

                            <div className="space-y-2 md:col-span-2">
                                <label className="block text-sm text-slate-300">
                                    상태 라벨 (예: 아침 / 저녁 / 두통 / 안정 시)
                                </label>
                                <input
                                    type="text"
                                    placeholder="간단한 상태 설명"
                                    value={stateText}
                                    onChange={(e) => setStateText(e.target.value)}
                                    className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="block text-sm text-slate-300">메모 (선택)</label>
                            <textarea
                                rows={3}
                                placeholder="오늘 컨디션, 먹은 약/음식, 특별한 일 등을 기록해 두면 좋아요."
                                value={memo}
                                onChange={(e) => setMemo(e.target.value)}
                                className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
                            />
                        </div>

                        {/* 라이프스타일 섹션 */}
                        <div className="mt-4 border-t border-slate-800 pt-4 space-y-4">
                            <h2 className="text-sm font-semibold text-slate-200">
                                라이프스타일
                            </h2>

                            <div className="grid gap-4 md:grid-cols-3">
                                {/* 수면 시간 */}
                                <div className="space-y-2">
                                    <label className="block text-sm text-slate-300">
                                        수면 시간 (시간)
                                    </label>
                                    <input
                                        type="number"
                                        min={0}
                                        step={0.5}
                                        placeholder="예: 6.5"
                                        value={sleepHours}
                                        onChange={(e) => setSleepHours(e.target.value)}
                                        className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
                                    />
                                </div>

                                {/* 운동 여부 */}
                                <div className="space-y-2">
                                    <label className="block text-sm text-slate-300">
                                        오늘 운동했나요?
                                    </label>
                                    <div className="flex gap-2">
                                        <button
                                            type="button"
                                            onClick={() => setExercise('yes')}
                                            className={`flex-1 px-3 py-2 rounded-lg border text-sm ${
                                                exercise === 'yes'
                                                    ? 'bg-emerald-500/20 border-emerald-500 text-emerald-300'
                                                    : 'bg-slate-950 border-slate-700 text-slate-300'
                                            }`}
                                        >
                                            했다
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => setExercise('no')}
                                            className={`flex-1 px-3 py-2 rounded-lg border text-sm ${
                                                exercise === 'no'
                                                    ? 'bg-slate-500/20 border-slate-500 text-slate-200'
                                                    : 'bg-slate-950 border-slate-700 text-slate-300'
                                            }`}
                                        >
                                            안 했다
                                        </button>
                                    </div>
                                </div>

                                {/* 스트레스 정도 */}
                                <div className="space-y-2">
                                    <label className="block text-sm text-slate-300">
                                        오늘 스트레스 정도 (1~5)
                                    </label>
                                    <select
                                        value={stressLevel}
                                        onChange={(e) => setStressLevel(e.target.value)}
                                        className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
                                    >
                                        <option value="1">1 - 거의 없음</option>
                                        <option value="2">2 - 조금 있음</option>
                                        <option value="3">3 - 보통</option>
                                        <option value="4">4 - 다소 높음</option>
                                        <option value="5">5 - 매우 높음</option>
                                    </select>
                                </div>
                            </div>
                        </div>

                        {/* 에러 & 버튼 */}
                        {submitError && (
                            <p className="text-sm text-red-400">
                                에러: {submitError}
                            </p>
                        )}

                        <div className="flex justify-end gap-2 pt-2">
                            <button
                                type="button"
                                onClick={() => router.push('/records')}
                                className="px-4 py-2 rounded-xl bg-slate-700 hover:bg-slate-600 text-sm font-semibold"
                            >
                                취소
                            </button>
                            <button
                                type="submit"
                                disabled={submitting}
                                className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-sm font-semibold disabled:opacity-60"
                            >
                                {submitting ? '수정 중...' : '변경 사항 저장'}
                            </button>
                        </div>
                    </form>
                </section>
            </div>
        </main>
    );
}
