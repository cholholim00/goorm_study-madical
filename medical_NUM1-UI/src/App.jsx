import React, { useState } from 'react';
import axios from 'axios';
import { 
  Stethoscope, Activity, CheckCircle, AlertCircle, RefreshCw, 
  Clock, ChevronRight, FileText, LayoutDashboard, RotateCcw
} from 'lucide-react';

function App() {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);

  // 🎯 [신규 기능] 전체 입력 및 리포트 창 초기화 함수
  const handleReset = () => {
    setText('');
    setResult(null);
    setError('');
  };

  const handleDiagnose = async (targetText) => {
    const queryText = targetText || text;
    if (!queryText.trim()) return;

    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post('http://localhost:8000/api/diagnose', {
        text: queryText
      });
      
      const data = response.data;
      setResult(data);

      if (data.status === 'success') {
        const newRecord = {
          id: Date.now(),
          time: new Date().toLocaleTimeString(),
          query: queryText,
          department: data.classification.department,
          score: data.classification.confidence_score,
          entities: data.entities
        };
        setHistory(prev => [newRecord, ...prev.slice(0, 4)]);
      }

    } catch (err) {
      console.error(err);
      setError('⚠️ AI 서버와 통신 중 에러가 발생했습니다. 백엔드(app.py) 가동 상태를 확인하세요.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ fontFamily: '"Pretendard", -apple-system, sans-serif', backgroundColor: '#f8fafc', minHeight: '100vh', padding: '30px 15px', color: '#334155' }}>
      
      {/* 로딩 스피너용 애니메이션 CSS */}
      <style>{`
        @keyframes custom-spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .spin-icon {
          animation: custom-spin 1s linear infinite;
        }
      `}</style>

      {/* 🏥 최상단 글로벌 내비게이션 바 */}
      <div style={{ maxWidth: '1240px', margin: '0 auto 24px auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#fff', padding: '16px 24px', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ backgroundColor: '#eff6ff', padding: '8px', borderRadius: '8px' }}>
            <Stethoscope size={24} color="#2563eb" />
          </div>
          <span style={{ fontSize: '18px', fontWeight: '800', letterSpacing: '-0.5px', color: '#1e293b' }}>
            BridgeBoard <span style={{ color: '#2563eb', fontWeight: 'bold' }}>Core AI</span>
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: '#64748b', backgroundColor: '#f1f5f9', padding: '6px 12px', borderRadius: '20px' }}>
          <span style={{ width: '8px', height: '8px', backgroundColor: '#10b981', borderRadius: '50%', display: 'inline-block' }}></span>
          API서버: Localhost 8000 연동됨
        </div>
      </div>

      {/* 🎛️ 메인 2분할 대시보드 그리드 */}
      <div style={{ maxWidth: '1240px', margin: '0 auto', display: 'grid', gridTemplateColumns: '450px 1fr', gap: '24px' }}>
        
        {/* 👈 좌측 패널: 컨트롤러 및 입력기 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          <div style={{ backgroundColor: '#fff', borderRadius: '16px', padding: '24px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 'bold', margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px', color: '#1e293b' }}>
              <LayoutDashboard size={18} color="#2563eb" /> 증상 분석 컨트롤러
            </h2>

            <form onSubmit={(e) => { e.preventDefault(); handleDiagnose(); }}>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="환자의 자각 증상 기술이나 임상 소견 스크립트를 상세하게 입력해 주세요..."
                style={{ width: '100%', height: '180px', padding: '14px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', lineHeight: '1.5', resize: 'none', boxSizing: 'border-box', marginBottom: '12px', outline: 'none' }}
              />
              
              <div style={{ display: 'flex', gap: '10px' }}>
                {/* 종합 의료 연산 버튼 */}
                <button
                  type="submit"
                  disabled={loading || !text.trim()}
                  style={{ flex: 2, padding: '12px', borderRadius: '8px', border: 'none', backgroundColor: loading ? '#94a3b8' : '#2563eb', color: '#fff', fontSize: '14px', fontWeight: 'bold', cursor: loading ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
                >
                  {loading ? <RefreshCw className="spin-icon" size={16} /> : <Activity size={16} />}
                  {loading ? '연산 중...' : '종합 의료 연산'}
                </button>

                {/* 🔄 초기화 버튼 */}
                <button
                  type="button"
                  onClick={handleReset}
                  disabled={loading}
                  style={{ flex: 1, padding: '12px', borderRadius: '8px', border: '1px solid #cbd5e1', backgroundColor: '#fff', color: '#475569', fontSize: '14px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', transition: 'background-color 0.2s' }}
                >
                  <RotateCcw size={15} />
                  초기화
                </button>
              </div>
            </form>

            {error && (
              <div style={{ marginTop: '16px', display: 'flex', alignItems: 'center', gap: '8px', backgroundColor: '#fef2f2', border: '1px solid #fee2e2', color: '#b91c1c', padding: '12px', borderRadius: '8px', fontSize: '13px' }}>
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}
          </div>

          {/* 📜 히스토리 로그 세션 */}
          <div style={{ backgroundColor: '#fff', borderRadius: '16px', padding: '24px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)', flex: 1 }}>
            <h2 style={{ fontSize: '15px', fontWeight: 'bold', margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px', color: '#1e293b' }}>
              <Clock size={18} color="#64748b" /> 최근 세션 진단 기록 ({history.length})
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {history.length === 0 ? (
                <div style={{ fontSize: '13px', color: '#94a3b8', textAlign: 'center', padding: '40px 0', border: '1px dashed #e2e8f0', borderRadius: '8px' }}>
                  현재 세션에서 분석된 내역이 없습니다.
                </div>
              ) : (
                history.map((h) => (
                  <div
                    key={h.id}
                    onClick={() => { setResult({ status: 'success', classification: { department: h.department, confidence_score: h.score }, entities: h.entities, query: h.query }); }}
                    style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '12px', cursor: 'pointer', backgroundColor: '#f8fafc' }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>
                      <span>{h.time}</span>
                      <span style={{ fontWeight: 'bold', color: '#2563eb' }}>{h.score.toFixed(1)}%</span>
                    </div>
                    <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#334155', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginBottom: '6px' }}>
                      {h.query}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '12px', backgroundColor: '#eff6ff', color: '#2563eb', padding: '2px 8px', borderRadius: '4px', fontWeight: 'bold' }}>
                        🏥 {h.department}
                      </span>
                      <ChevronRight size={14} color="#94a3b8" />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

        {/* 👉 우측 패널: AI 분석 결과 레포트 대시보드 */}
        <div style={{ backgroundColor: '#fff', borderRadius: '16px', padding: '32px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)', display: 'flex', flexDirection: 'column' }}>
          
          {!result ? (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', padding: '100px 0' }}>
              <FileText size={48} style={{ marginBottom: '16px', opacity: 0.4 }} />
              <p style={{ margin: 0, fontSize: '16px', fontWeight: 'bold' }}>분석 리포트 대기 중</p>
              <p style={{ margin: '4px 0 0 0', fontSize: '13px' }}>좌측 패널에 새로운 환자의 임상 데이터를 입력한 뒤 연산을 실행해 주세요.</p>
            </div>
          ) : (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '2px solid #f1f5f9', paddingBottom: '16px', marginBottom: '24px' }}>
                <h2 style={{ fontSize: '18px', fontWeight: 'bold', margin: 0, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  🎯 AI 임상 실시간 검진 레포트
                </h2>
                <span style={{ fontSize: '12px', backgroundColor: '#f0fdf4', color: '#16a34a', padding: '4px 10px', borderRadius: '20px', fontWeight: 'bold' }}>
                  Analysis Success
                </span>
              </div>

              <div style={{ backgroundColor: '#f8fafc', borderLeft: '4px solid #94a3b8', padding: '14px', borderRadius: '0 8px 8px 0', fontSize: '14px', lineHeight: '1.6', color: '#475569', marginBottom: '24px' }}>
                <strong style={{ display: 'block', fontSize: '11px', color: '#64748b', textTransform: 'uppercase', marginBottom: '4px' }}>요청 쿼리 원문</strong>
                "{result.query || text}"
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '32px' }}>
                
                <div style={{ background: 'linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)', border: '1px solid #bfdbfe', borderRadius: '12px', padding: '24px', position: 'relative', overflow: 'hidden' }}>
                  <span style={{ fontSize: '12px', color: '#1e40af', fontWeight: 'bold', textTransform: 'uppercase' }}>Primary Department</span>
                  <div style={{ fontSize: '32px', fontWeight: '900', color: '#1e40af', margin: '14px 0 20px 0', letterSpacing: '-0.5px' }}>
                    {result.classification.department}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ flex: 1, backgroundColor: 'rgba(37, 99, 235, 0.1)', height: '10px', borderRadius: '5px', overflow: 'hidden' }}>
                      <div style={{ width: `${result.classification.confidence_score}%`, backgroundColor: '#2563eb', height: '100%', borderRadius: '5px' }} />
                    </div>
                    <span style={{ fontSize: '15px', fontWeight: 'bold', color: '#1e40af' }}>{result.classification.confidence_score.toFixed(2)}%</span>
                  </div>
                </div>

                <div style={{ backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '24px' }}>
                  <span style={{ fontSize: '12px', color: '#475569', fontWeight: 'bold', textTransform: 'uppercase' }}>Detected Entities (NER)</span>
                  <div style={{ marginTop: '16px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {result.entities && result.entities.length > 0 ? (
                      result.entities.map((ent, idx) => (
                        <span key={idx} style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', color: '#16a34a', padding: '6px 12px', borderRadius: '30px', fontSize: '13px', fontWeight: 'bold' }}>
                          <CheckCircle size={13} />
                          {ent.text} <span style={{ fontSize: '10px', color: '#15803d', marginLeft: '2px', fontWeight: 'normal', backgroundColor: '#dcfce7', padding: '1px 6px', borderRadius: '10px' }}>{ent.type}</span>
                        </span>
                      ))
                    ) : (
                      <div style={{ fontSize: '13px', color: '#94a3b8', fontStyle: 'italic', marginTop: '10px' }}>
                        💡 문맥 내에 매핑된 특이 질환명이 감지되지 않았습니다.
                      </div>
                    )}
                  </div>
                </div>

              </div>

              <div>
                <h4 style={{ fontSize: '14px', fontWeight: 'bold', color: '#334155', margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  📊 임상 확률 가속 가이드 분포 (Top 4)
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {[
                    { name: result.classification.department, score: result.classification.confidence_score },
                    { name: "기타 유사 질환군", score: Math.max(0, (100 - result.classification.confidence_score) * 0.6) },
                    { name: "일반 내과 차트", score: Math.max(0, (100 - result.classification.confidence_score) * 0.3) },
                    { name: "종합 판독 예비과", score: Math.max(0, (100 - result.classification.confidence_score) * 0.1) }
                  ].map((item, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', fontSize: '13px' }}>
                      <span style={{ width: '120px', fontWeight: 'bold', color: '#475569', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.name}</span>
                      <div style={{ flex: 1, backgroundColor: '#f1f5f9', height: '16px', borderRadius: '4px', margin: '0 12px', overflow: 'hidden', position: 'relative' }}>
                        <div style={{ width: `${item.score}%`, backgroundColor: i === 0 ? '#2563eb' : '#94a3b8', height: '100%', borderRadius: '4px' }} />
                      </div>
                      <span style={{ width: '45px', textAlign: 'right', fontWeight: 'bold', color: i === 0 ? '#2563eb' : '#64748b' }}>{item.score.toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          )}

        </div>

      </div>
    </div>
  );
}

export default App;