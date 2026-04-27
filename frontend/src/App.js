import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import axios from 'axios';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function ScoreBadge({ score }) {
  const cls = score >= 85 ? 'score-badge score-high' : 'score-badge score-med';
  return <span className={cls}>{score}%</span>;
}

function StatusBadge({ status }) {
  return <span className={`status-badge status-${status}`}>{status.replace('_', ' ')}</span>;
}

function CopyBtn({ text }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };
  return <button className="copy-btn" onClick={copy}>{copied ? '✓ copied' : 'copy'}</button>;
}

// ─── Profile Page ─────────────────────────────────────────────────────────────

function ProfilePage() {
  const [intro, setIntro] = useState('');
  const [resume, setResume] = useState('');
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    axios.get(`${API}/api/pipeline/profile`).then(r => {
      if (r.data.profile) {
        setIntro(r.data.profile.intro_text || '');
        setResume(r.data.profile.resume_text || '');
      }
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const save = async () => {
    setError(''); setSaving(true);
    try {
      await axios.post(`${API}/api/pipeline/profile`, { intro_text: intro, resume_text: resume });
      setSaved(true);
      window.scrollTo({ top: 0, behavior: 'smooth' });
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      setError(e.response?.data?.detail || 'Save failed.');
    } finally { setSaving(false); }
  };

  if (loading) return <div className="empty-state"><div className="spinner" /></div>;

  return (
    <div>
      <div className="page-header">
        <div className="page-title">profile</div>
        <div className="page-subtitle">Your intro document and resume — stored once, used by every pipeline run.</div>
      </div>

      {saved && <div className="alert alert-ok">✓ Profile saved.</div>}
      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        <div className="card-title" style={{marginBottom:12}}>intro document</div>
        <label>Who you are and what you're looking for</label>
        <textarea
          value={intro}
          onChange={e => setIntro(e.target.value)}
          rows={10}
          placeholder="Paste your intro document here..."
        />
      </div>

      <div className="card">
        <div className="card-title" style={{marginBottom:12}}>resume</div>
        <label>Your current resume (text)</label>
        <textarea
          value={resume}
          onChange={e => setResume(e.target.value)}
          rows={14}
          placeholder="Paste your resume text here..."
        />
      </div>

      <button
        className="btn btn-primary"
        onClick={save}
        disabled={saving || saved || intro.trim().length < 50 || resume.trim().length < 100}
      >
        {saving ? <><span className="spinner" /> saving…</> : saved ? '✓ profile saved' : '↳ save profile'}
      </button>
    </div>
  );
}

// ─── Setup Page ───────────────────────────────────────────────────────────────

const SETUP_STAGE = { IDLE:'idle', ANALYZING:'analyzing', QUESTIONS:'questions', CONFIRMING:'confirming', DONE:'done' };

function SetupPage() {
  const [stage, setStage] = useState(SETUP_STAGE.IDLE);
  const [profileData, setProfileData] = useState(null);
  const [suggestedTitles, setSuggestedTitles] = useState([]);
  const [selectedSuggested, setSelectedSuggested] = useState(new Set());
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [finalTitles, setFinalTitles] = useState([]);
  const [selectedFinal, setSelectedFinal] = useState(new Set());
  const [summary, setSummary] = useState('');
  const [storedTitles, setStoredTitles] = useState([]);
  const [newTitle, setNewTitle] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const loadTitles = useCallback(() => {
    axios.get(`${API}/api/pipeline/titles`).then(r => setStoredTitles(r.data.titles || []));
  }, []);

  // Load persisted advisor session on mount
  useEffect(() => {
    loadTitles();
    axios.get(`${API}/api/pipeline/setup/session`).then(r => {
      const { stage: s, data: d } = r.data;
      if (s && s !== 'idle') {
        setStage(s);
        if (d.profileData) setProfileData(d.profileData);
        if (d.suggestedTitles) {
          setSuggestedTitles(d.suggestedTitles);
          setSelectedSuggested(new Set(d.selectedSuggested || d.suggestedTitles.map((_,i) => i)));
        }
        if (d.questions) setQuestions(d.questions);
        if (d.answers) setAnswers(d.answers);
        if (d.finalTitles) {
          setFinalTitles(d.finalTitles);
          setSelectedFinal(new Set(d.selectedFinal || d.finalTitles.map((_,i) => i)));
        }
      }
    }).catch(() => {});
  }, [loadTitles]);

  // Persist session whenever key state changes
  const persistSession = useCallback((overrides = {}) => {
    const state = {
      stage: overrides.stage ?? stage,
      data: {
        profileData: overrides.profileData ?? profileData,
        suggestedTitles: overrides.suggestedTitles ?? suggestedTitles,
        selectedSuggested: [...(overrides.selectedSuggested ?? selectedSuggested)],
        questions: overrides.questions ?? questions,
        answers: overrides.answers ?? answers,
        finalTitles: overrides.finalTitles ?? finalTitles,
        selectedFinal: [...(overrides.selectedFinal ?? selectedFinal)],
      }
    };
    axios.post(`${API}/api/pipeline/setup/session`, state).catch(() => {});
  }, [stage, profileData, suggestedTitles, selectedSuggested, questions, answers, finalTitles, selectedFinal]);

  const runAnalysis = async () => {
    setError('');
    const profile = await axios.get(`${API}/api/pipeline/profile`);
    if (!profile.data.profile) {
      setError('No profile saved. Go to Profile and save your intro + resume first.');
      return;
    }
    setStage(SETUP_STAGE.ANALYZING);
    try {
      const r = await axios.post(`${API}/api/pipeline/setup/analyze`, {
        intro_text: profile.data.profile.intro_text,
        resume_text: profile.data.profile.resume_text
      });
      const pd = r.data.profile;
      const st = r.data.suggested_titles || [];
      const qs = r.data.questions || [];
      const sel = new Set(st.map((_,i) => i));
      setProfileData(pd);
      setSuggestedTitles(st);
      setSelectedSuggested(sel);
      setQuestions(qs);
      setStage(SETUP_STAGE.QUESTIONS);
      persistSession({ stage: SETUP_STAGE.QUESTIONS, profileData: pd, suggestedTitles: st, selectedSuggested: sel, questions: qs, answers: {} });
    } catch(e) {
      setError(e.response?.data?.detail || 'Analysis failed.');
      setStage(SETUP_STAGE.IDLE);
    }
  };

  const refine = async () => {
    setError('');
    setStage(SETUP_STAGE.CONFIRMING);
    try {
      const profile = await axios.get(`${API}/api/pipeline/profile`);
      const r = await axios.post(`${API}/api/pipeline/setup/refine`, {
        profile: profileData,
        suggested_titles: suggestedTitles.filter((_,i) => selectedSuggested.has(i)),
        answers: questions.map(q => ({ question_id: q.id, question: q.text, answer: answers[q.id] || '' }))
      });
      const ft = r.data.titles || [];
      const sf = new Set(ft.map((_,i) => i));
      setFinalTitles(ft);
      setSelectedFinal(sf);
      setStage(SETUP_STAGE.DONE);
      persistSession({ stage: SETUP_STAGE.DONE, finalTitles: ft, selectedFinal: sf });
    } catch(e) {
      setError(e.response?.data?.detail || 'Refinement failed.');
      setStage(SETUP_STAGE.QUESTIONS);
    }
  };

  const confirmTitles = async () => {
    setSaving(true);
    try {
      const advisorTitles = finalTitles.filter((_,i) => selectedFinal.has(i));
      // Merge with any manually added stored titles (already in DB)
      const storedTitleStrings = storedTitles.map(t => t.title);
      const merged = [...new Set([...storedTitleStrings, ...advisorTitles])];
      if (merged.length === 0) { setError('Select at least one title.'); setSaving(false); return; }
      await axios.post(`${API}/api/pipeline/titles`, { titles: merged });
      await axios.delete(`${API}/api/pipeline/setup/session`);
      loadTitles();
      setStage(SETUP_STAGE.IDLE);
      setProfileData(null); setSuggestedTitles([]); setSelectedSuggested(new Set());
      setQuestions([]); setAnswers({}); setFinalTitles([]); setSelectedFinal(new Set()); setSummary('');
    } catch(e) {
      setError('Failed to save titles.');
    } finally { setSaving(false); }
  };

  const deleteTitle = async (id) => {
    await axios.delete(`${API}/api/pipeline/titles/${id}`);
    loadTitles();
  };

  const addTitle = async () => {
    if (!newTitle.trim()) return;
    await axios.post(`${API}/api/pipeline/titles/add`, { title: newTitle.trim() });
    setNewTitle(''); loadTitles();
  };

  const allAnswered = questions.length > 0 && questions.every(q => answers[q.id]?.trim());

  return (
    <div>
      <div className="page-header">
        <div className="page-title">search setup</div>
        <div className="page-subtitle">Configure the job titles the pipeline will search for. Run the advisor once — then manage titles manually anytime.</div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Current stored titles */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">active search titles</div>
          <button className="btn btn-outline btn-sm" onClick={runAnalysis} disabled={stage !== SETUP_STAGE.IDLE}>
            ↻ re-run advisor
          </button>
        </div>

        {storedTitles.length === 0
          ? <div className="alert alert-info">No titles yet. Run the advisor below or add one manually.</div>
          : <div>{storedTitles.map(t => (
              <span key={t.id} className="title-pill">
                {t.title}
                <button className="title-pill-del" onClick={() => deleteTitle(t.id)}>×</button>
              </span>
            ))}</div>
        }

        <div style={{display:'flex',gap:8,marginTop:16}}>
          <input
            type="text"
            value={newTitle}
            onChange={e => setNewTitle(e.target.value)}
            placeholder="Add a title manually…"
            onKeyDown={e => e.key === 'Enter' && addTitle()}
            style={{flex:1}}
          />
          <button className="btn btn-outline" onClick={addTitle} disabled={!newTitle.trim()}>+ add</button>
        </div>
      </div>

      {/* Advisor flow */}
      {stage === SETUP_STAGE.IDLE && (
        <div className="card">
          <div className="card-title" style={{marginBottom:8}}>advisor-driven setup</div>
          <p style={{color:'var(--text2)',fontSize:13,marginBottom:16}}>
            The advisor analyzes your intro + resume, suggests the best job titles, and asks a couple of clarifying questions before locking them in.
          </p>
          <button className="btn btn-primary" onClick={runAnalysis}>run advisor →</button>
        </div>
      )}

      {stage === SETUP_STAGE.ANALYZING && (
        <div className="card" style={{textAlign:'center',padding:'32px'}}>
          <div className="spinner" style={{width:24,height:24,marginBottom:12}} />
          <p style={{color:'var(--text2)',fontFamily:'var(--mono)',fontSize:12}}>Analyzing your profile…</p>
        </div>
      )}

      {stage === SETUP_STAGE.QUESTIONS && (
        <div className="card">
          <div className="card-title" style={{marginBottom:12}}>profile summary</div>
          <div style={{background:'var(--bg)',border:'1px solid var(--border)',borderRadius:'var(--radius)',padding:14,marginBottom:20,fontSize:13}}>
            <p style={{marginBottom:6}}><strong>Background:</strong> {profileData?.summary}</p>
            <p style={{marginBottom:6}}><strong>Level:</strong> {profileData?.experience_level}</p>
            <p><strong>Key skills:</strong> {profileData?.key_skills?.join(', ')}</p>
          </div>

          <div className="card-title" style={{marginBottom:8}}>suggested titles</div>
          <p style={{fontSize:12,color:'var(--text2)',margin:'0 0 12px'}}>Deselect any titles that don't fit before continuing.</p>
          {suggestedTitles.map((s,i) => {
            const on = selectedSuggested.has(i);
            return (
              <div key={i} onClick={() => setSelectedSuggested(prev => {
                const n = new Set(prev); on ? n.delete(i) : n.add(i);
                persistSession({ selectedSuggested: n }); return n;
              })}
                style={{background: on ? 'var(--bg)' : 'var(--bg3)', border: `1px solid ${on ? 'var(--border2)' : 'var(--border)'}`,
                  borderRadius:'var(--radius)', padding:12, marginBottom:8, cursor:'pointer',
                  opacity: on ? 1 : 0.45, transition:'all .15s', display:'flex', alignItems:'flex-start', gap:10}}>
                <span style={{fontFamily:'var(--mono)',fontSize:14,color: on ? 'var(--green)' : 'var(--text3)',marginTop:1,flexShrink:0}}>
                  {on ? '✓' : '○'}
                </span>
                <div>
                  <div style={{fontFamily:'var(--mono)',fontSize:13,color:'var(--text)',marginBottom:3}}>{s.title}</div>
                  <div style={{fontSize:12,color:'var(--text2)'}}>{s.rationale}</div>
                </div>
              </div>
            );
          })}

          <div style={{marginTop:20}} className="card-title">clarifying questions</div>
          <p style={{fontSize:12,color:'var(--text2)',margin:'8px 0 16px'}}>Answer these to refine the final title list:</p>
          {questions.map(q => (
            <div key={q.id} className="question-block">
              <span className="qlabel">{q.text}</span>
              <input
                type="text"
                value={answers[q.id] || ''}
                onChange={e => {
                  const updated = {...answers, [q.id]: e.target.value};
                  setAnswers(updated);
                  persistSession({ answers: updated });
                }}
                placeholder="Your answer…"
              />
            </div>
          ))}
          <div className="btn-row">
            <button className="btn btn-primary" onClick={refine} disabled={!allAnswered}>confirm & finalize →</button>
            <button className="btn btn-outline" onClick={() => setStage(SETUP_STAGE.IDLE)}>cancel</button>
          </div>
        </div>
      )}

      {stage === SETUP_STAGE.CONFIRMING && (
        <div className="card" style={{textAlign:'center',padding:'32px'}}>
          <div className="spinner" style={{width:24,height:24,marginBottom:12}} />
          <p style={{color:'var(--text2)',fontFamily:'var(--mono)',fontSize:12}}>Finalizing title list…</p>
        </div>
      )}

      {stage === SETUP_STAGE.DONE && (
        <div className="card">
          <div className="card-title" style={{marginBottom:8}}>final titles</div>
          <p style={{fontSize:13,color:'var(--text2)',marginBottom:16}}>Deselect any you don't want before saving.</p>
          {finalTitles.map((t,i) => {
            const on = selectedFinal.has(i);
            return (
              <div key={i} onClick={() => setSelectedFinal(prev => {
                const n = new Set(prev); on ? n.delete(i) : n.add(i);
                persistSession({ selectedFinal: n }); return n;
              })}
                style={{display:'inline-flex', alignItems:'center', gap:6,
                  background: on ? 'var(--bg3)' : 'var(--bg)', border: `1px solid ${on ? 'var(--border2)' : 'var(--border)'}`,
                  borderRadius:4, padding:'5px 10px 5px 10px', fontFamily:'var(--mono)', fontSize:12,
                  color: on ? 'var(--text2)' : 'var(--text3)', margin:4, cursor:'pointer',
                  opacity: on ? 1 : 0.4, transition:'all .15s'}}>
                <span style={{color: on ? 'var(--green)' : 'var(--text3)'}}>{on ? '✓' : '○'}</span>
                {t}
              </div>
            );
          })}
          <div className="btn-row">
            <button className="btn btn-success" onClick={confirmTitles} disabled={saving}>
              {saving ? <><span className="spinner"/> saving…</> : `✓ save ${[...selectedFinal].length + storedTitles.length} title${([...selectedFinal].length + storedTitles.length) !== 1 ? 's' : ''}`}
            </button>
            <button className="btn btn-outline" onClick={() => setStage(SETUP_STAGE.QUESTIONS)}>← go back</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Pipeline Page ────────────────────────────────────────────────────────────

function PipelinePage() {
  const [running, setRunning] = useState(false);
  const [runResult, setRunResult] = useState(null);
  const [log, setLog] = useState([]);
  const [queue, setQueue] = useState([]);
  const [loadingQueue, setLoadingQueue] = useState(true);
  const [deciding, setDeciding] = useState({});
  const [generating, setGenerating] = useState({});
  const [selectedJob, setSelectedJob] = useState(null);
  const [error, setError] = useState('');

  const loadQueue = useCallback(() => {
    setLoadingQueue(true);
    axios.get(`${API}/api/pipeline/queue`)
      .then(r => setQueue(r.data.jobs || []))
      .catch(() => setQueue([]))
      .finally(() => setLoadingQueue(false));
  }, []);

  useEffect(() => { loadQueue(); }, [loadQueue]);

  const runPipeline = async () => {
    setError(''); setRunning(true); setRunResult(null);
    setLog([{text:'Fetching jobs from Adzuna…', type:'active'}]);
    try {
      const r = await axios.post(`${API}/api/pipeline/run`, { results_per_page: 10 });
      const d = r.data;
      setLog([
        {text:`✓ Fetched ${d.fetched} jobs across all titles`, type:'done'},
        {text:`✓ Scored ${d.scored} jobs`, type:'done'},
        {text:`✓ ${d.queued} passed the 70% threshold`, type:'done'},
        {text:`  ${d.dropped} dropped (below threshold)`, type:'active'},
        ...(d.errors.length ? [{text:`⚠ ${d.errors.length} error(s) — check console`, type:'err'}] : [])
      ]);
      setRunResult(d);
      loadQueue();
    } catch(e) {
      setError(e.response?.data?.detail || 'Pipeline run failed.');
      setLog([]);
    } finally { setRunning(false); }
  };

  const decide = async (jobId, action) => {
    setDeciding(d => ({...d, [jobId]: action}));
    try {
      await axios.post(`${API}/api/pipeline/queue/${jobId}/decide`, { action });
      setQueue(q => q.filter(j => j.id !== jobId));
    } catch(e) {
      setError('Decision failed.');
    } finally { setDeciding(d => ({...d, [jobId]: null})); }
  };

  const generate = async (job) => {
    setGenerating(g => ({...g, [job.id]: true}));
    try {
      const r = await axios.post(`${API}/api/pipeline/generate/${job.id}`);
      setSelectedJob(r.data.job);
    } catch(e) {
      setError(e.response?.data?.detail || 'Generation failed.');
    } finally { setGenerating(g => ({...g, [job.id]: false})); }
  };

  const saveEdited = async (jobId, resumeNotes, coverLetter) => {
    await axios.post(`${API}/api/pipeline/tracker/${jobId}/docs`, {
      resume_notes: resumeNotes,
      cover_letter: coverLetter
    });
  };

  // Document view
  if (selectedJob) {
    return <DocsView job={selectedJob} onBack={() => setSelectedJob(null)} onSave={saveEdited} />;
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-title">pipeline</div>
        <div className="page-subtitle">Run to fetch and score jobs. Only matches ≥ 70% appear here.</div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        <div className="card-header">
          <div className="card-title">run pipeline</div>
          <button className="btn btn-primary" onClick={runPipeline} disabled={running}>
            {running ? <><span className="spinner"/> running…</> : '▶ run now'}
          </button>
        </div>
        <p style={{fontSize:12,color:'var(--text2)'}}>
          Searches Adzuna for all your configured titles, scores every JD against your profile, and adds anything ≥ 70% to the queue below.
        </p>

        {log.length > 0 && (
          <div className="run-progress" style={{marginTop:16}}>
            {log.map((l,i) => <div key={i} className={`run-log-line ${l.type}`}>{l.text}</div>)}
          </div>
        )}

        {runResult && (
          <div className="stats-row" style={{marginTop:16,marginBottom:0}}>
            <div className="stat-box"><div className="stat-value">{runResult.fetched}</div><div className="stat-label">fetched</div></div>
            <div className="stat-box"><div className="stat-value">{runResult.scored}</div><div className="stat-label">scored</div></div>
            <div className="stat-box"><div className="stat-value" style={{color:'var(--green)'}}>{runResult.queued}</div><div className="stat-label">queued</div></div>
            <div className="stat-box"><div className="stat-value" style={{color:'var(--text3)'}}>{runResult.dropped}</div><div className="stat-label">dropped</div></div>
          </div>
        )}
      </div>

      {/* Queue */}
      <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:12}}>
        <div className="card-title">approval queue <span style={{color:'var(--text3)',fontWeight:400}}>({queue.length})</span></div>
        <button className="btn btn-outline btn-sm" onClick={loadQueue}>↻ refresh</button>
      </div>

      {loadingQueue && <div className="empty-state"><div className="spinner"/></div>}

      {!loadingQueue && queue.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">📭</div>
          <div>Queue is empty. Run the pipeline to fetch new matches.</div>
        </div>
      )}

      {queue.map(job => (
        <div key={job.id} className="job-card">
          <div className="job-card-header">
            <div>
              <div className="job-title">{job.title}</div>
              <div className="job-company">{job.company}</div>
            </div>
            <div className="job-card-meta">
              <ScoreBadge score={job.score} />
              {job.redirect_url && (
                <a href={job.redirect_url} target="_blank" rel="noopener noreferrer"
                   style={{fontSize:11,color:'var(--text3)',fontFamily:'var(--mono)'}}>
                  view ↗
                </a>
              )}
            </div>
          </div>
          <div className="job-location">{job.location}</div>
          {job.salary_min && job.salary_max && (
            <div className="job-salary" style={{marginTop:4}}>
              ${Math.round(job.salary_min).toLocaleString()} – ${Math.round(job.salary_max).toLocaleString()}
            </div>
          )}
          {job.score_reason && <div className="job-reason">{job.score_reason}</div>}
          <div className="job-actions">
            <button
              className="btn btn-success btn-sm"
              onClick={() => decide(job.id, 'approve')}
              disabled={deciding[job.id]}
            >
              {deciding[job.id] === 'approve' ? <span className="spinner"/> : '✓'} approve
            </button>
            <button
              className="btn btn-danger btn-sm"
              onClick={() => decide(job.id, 'reject')}
              disabled={deciding[job.id]}
            >
              {deciding[job.id] === 'reject' ? <span className="spinner"/> : '✗'} reject
            </button>
            <button
              className="btn btn-outline btn-sm"
              onClick={() => generate(job)}
              disabled={generating[job.id]}
            >
              {generating[job.id] ? <><span className="spinner"/> generating…</> : '✦ generate docs'}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Docs View (inline, within Pipeline page) ─────────────────────────────────

function DocsView({ job, onBack, onSave }) {
  const [notes, setNotes] = useState(job.resume_notes || '');
  const [letter, setLetter] = useState(job.cover_letter || '');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const save = async () => {
    setSaving(true);
    try {
      await onSave(job.id, notes, letter);
      setSaved(true); setTimeout(() => setSaved(false), 2000);
    } finally { setSaving(false); }
  };

  return (
    <div>
      <div className="page-header">
        <button className="btn btn-outline btn-sm" onClick={onBack} style={{marginBottom:12}}>← back to queue</button>
        <div className="page-title">{job.title}</div>
        <div className="page-subtitle">{job.company} · {job.location} · <ScoreBadge score={job.score} /></div>
      </div>

      {saved && <div className="alert alert-ok">✓ Documents saved.</div>}

      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:16}}>
        <div className="card">
          <div className="doc-header">
            <div className="doc-label">resume notes</div>
            <CopyBtn text={notes} />
          </div>
          <textarea className="doc-area" value={notes} onChange={e => setNotes(e.target.value)} rows={14} />
        </div>
        <div className="card">
          <div className="doc-header">
            <div className="doc-label">cover letter</div>
            <CopyBtn text={letter} />
          </div>
          <textarea className="doc-area" value={letter} onChange={e => setLetter(e.target.value)} rows={14} />
        </div>
      </div>

      <div className="btn-row">
        <button className="btn btn-primary" onClick={save} disabled={saving}>
          {saving ? <><span className="spinner"/> saving…</> : '↳ save edits'}
        </button>
        {job.redirect_url && (
          <a href={job.redirect_url} target="_blank" rel="noopener noreferrer" className="btn btn-outline">
            view job posting ↗
          </a>
        )}
      </div>
    </div>
  );
}

// ─── Tracker Page ─────────────────────────────────────────────────────────────

const STATUSES = ['queued','approved','rejected','drafted','applied','no_response'];

function TrackerPage() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [selectedJob, setSelectedJob] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    axios.get(`${API}/api/pipeline/tracker`)
      .then(r => setJobs(r.data.jobs || []))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const updateStatus = async (jobId, status) => {
    await axios.patch(`${API}/api/pipeline/tracker/${jobId}/status`, { status });
    setJobs(j => j.map(x => x.id === jobId ? {...x, status} : x));
  };

  const filtered = filter === 'all' ? jobs : jobs.filter(j => j.status === filter);

  if (selectedJob) {
    return <DocsView job={selectedJob} onBack={() => setSelectedJob(null)} onSave={async (id, rn, cl) => {
      await axios.post(`${API}/api/pipeline/tracker/${id}/docs`, { resume_notes: rn, cover_letter: cl });
    }} />;
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-title">tracker</div>
        <div className="page-subtitle">All applications — update status as you progress.</div>
      </div>

      <div style={{display:'flex',gap:8,marginBottom:20,flexWrap:'wrap'}}>
        {['all',...STATUSES].map(s => (
          <button
            key={s}
            className={`tab-btn${filter===s?' active':''}`}
            onClick={() => setFilter(s)}
          >
            {s.replace('_',' ')}
            {s === 'all'
              ? ` (${jobs.length})`
              : ` (${jobs.filter(j=>j.status===s).length})`
            }
          </button>
        ))}
      </div>

      {loading && <div className="empty-state"><div className="spinner"/></div>}
      {!loading && filtered.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">📋</div>
          <div>No applications yet.</div>
        </div>
      )}

      {!loading && filtered.length > 0 && (
        <div style={{overflowX:'auto'}}>
          <table className="tracker-table">
            <thead>
              <tr>
                <th>role</th>
                <th>company</th>
                <th>score</th>
                <th>status</th>
                <th>docs</th>
                <th>link</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(job => (
                <tr key={job.id}>
                  <td style={{fontWeight:500,color:'var(--text)'}}>{job.title}</td>
                  <td style={{color:'var(--text2)'}}>{job.company}</td>
                  <td><ScoreBadge score={job.score} /></td>
                  <td>
                    <select value={job.status} onChange={e => updateStatus(job.id, e.target.value)}>
                      {STATUSES.map(s => <option key={s} value={s}>{s.replace('_',' ')}</option>)}
                    </select>
                  </td>
                  <td>
                    {job.resume_notes || job.cover_letter
                      ? <button className="btn btn-outline btn-sm" onClick={() => setSelectedJob(job)}>view docs</button>
                      : <span style={{color:'var(--text3)',fontSize:11,fontFamily:'var(--mono)'}}>—</span>
                    }
                  </td>
                  <td>
                    {job.redirect_url
                      ? <a href={job.redirect_url} target="_blank" rel="noopener noreferrer"
                           style={{fontSize:11,color:'var(--text3)',fontFamily:'var(--mono)'}}>↗</a>
                      : '—'
                    }
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Existing: Job Search Tab (unchanged) ─────────────────────────────────────

function JobSearchTab() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [jobs, setJobs] = useState([]);
  const [showJobs, setShowJobs] = useState(false);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    const userMessage = { text: input, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    const userInput = input;
    setInput(''); setLoading(true);
    try {
      const response = await axios.post(`${API}/api/chat`, { message: userInput });
      setMessages(prev => [...prev, { text: response.data.response, sender: 'ai' }]);
      if (response.data.jobs?.length > 0) { setJobs(response.data.jobs); setShowJobs(true); }
      else setShowJobs(false);
    } catch {
      setMessages(prev => [...prev, { text: 'Sorry, I encountered an error.', sender: 'ai' }]);
      setShowJobs(false);
    } finally { setLoading(false); }
  };

  const quickSearch = (what, where) => {
    setInput(`Find ${what} jobs in ${where}`);
    setTimeout(() => document.querySelector('.input-form button')?.click(), 100);
  };

  return (
    <div className="tab-content">
      <div className="messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <h2>Job Search</h2>
            <p style={{color:'var(--text2)',marginBottom:16}}>Search Adzuna with natural language.</p>
            <div className="quick-searches">
              <button onClick={() => quickSearch('Python developer','Toronto')}>Python Developer · Toronto</button>
              <button onClick={() => quickSearch('Software Engineer','Vancouver')}>Software Engineer · Vancouver</button>
              <button onClick={() => quickSearch('Data Scientist','Ontario')}>Data Scientist · Ontario</button>
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.sender}`}>
            <div className="message-content">{msg.text}</div>
          </div>
        ))}
        {showJobs && jobs.map((job, i) => (
          <div key={job.id||i} className="job-card">
            <div className="job-title">{job.title}</div>
            <div className="job-company">{job.company} · {job.location}</div>
            {job.salary_min && <div className="job-salary">${job.salary_min?.toLocaleString()} – ${job.salary_max?.toLocaleString()}</div>}
            <p style={{fontSize:12,color:'var(--text2)',marginTop:6}}>{job.description}</p>
            {job.redirect_url && <a href={job.redirect_url} target="_blank" rel="noopener noreferrer" className="apply-button">View Job →</a>}
          </div>
        ))}
        {loading && <div className="message ai"><div className="message-content typing">Thinking…</div></div>}
      </div>
      <form onSubmit={sendMessage} className="input-form">
        <input type="text" value={input} onChange={e => setInput(e.target.value)} placeholder="Find senior cybersecurity jobs in remote" disabled={loading}/>
        <button type="submit" disabled={loading || !input.trim()}>Send</button>
      </form>
    </div>
  );
}

// ─── Existing: Career Advisor Tab (unchanged) ─────────────────────────────────

const ADVISOR_STAGE = { INPUT:'input', ANALYZING:'analyzing', QUESTIONS:'questions', SUGGESTING:'suggesting', READY:'ready' };

function CareerAdvisorTab() {
  const [stage, setStage] = useState(ADVISOR_STAGE.INPUT);
  const [resumeText, setResumeText] = useState('');
  const [inputMode, setInputMode] = useState('paste');
  const [fileName, setFileName] = useState('');
  const [profile, setProfile] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [suggestions, setSuggestions] = useState(null);
  const [error, setError] = useState('');

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.type !== 'application/pdf') { alert('Please upload a PDF file.'); return; }
    setFileName(file.name);
    alert(`"${file.name}" selected. PDF parsing coming in the next update!`);
  };

  const handleAnalyze = async () => {
    setError(''); setStage(ADVISOR_STAGE.ANALYZING);
    try {
      const r = await axios.post(`${API}/api/advisor/analyze`, { resume_text: resumeText });
      setProfile(r.data.profile); setQuestions(r.data.questions); setStage(ADVISOR_STAGE.QUESTIONS);
    } catch { setError('Sorry, I had trouble analyzing your resume.'); setStage(ADVISOR_STAGE.INPUT); }
  };

  const handleSuggest = async () => {
    setError(''); setStage(ADVISOR_STAGE.SUGGESTING);
    try {
      const formattedAnswers = questions.map(q => ({ question_id: q.id, question: q.text, answer: answers[q.id] || '' }));
      const r = await axios.post(`${API}/api/advisor/suggest`, { profile, answers: formattedAnswers });
      setSuggestions(r.data); setStage(ADVISOR_STAGE.READY);
    } catch { setError('Sorry, I had trouble generating suggestions.'); setStage(ADVISOR_STAGE.QUESTIONS); }
  };

  const handleReset = () => { setStage(ADVISOR_STAGE.INPUT); setResumeText(''); setFileName(''); setProfile(null); setQuestions([]); setAnswers({}); setSuggestions(null); setError(''); };
  const allAnswered = questions.length > 0 && questions.every(q => answers[q.id]?.trim());

  if (stage === ADVISOR_STAGE.INPUT) return (
    <div className="advisor-content">
      <div className="advisor-intro"><h2>🎯 Career Advisor</h2><p>Paste your resume and I'll analyze your background, ask a few clarifying questions, and find the best-fit roles for you.</p></div>
      <div className="input-mode-toggle">
        <button className={inputMode==='paste'?'mode-btn active':'mode-btn'} onClick={()=>setInputMode('paste')}>📋 Paste Resume</button>
        <button className={inputMode==='upload'?'mode-btn active':'mode-btn'} onClick={()=>setInputMode('upload')}>📄 Upload PDF</button>
      </div>
      {inputMode==='paste' && <div><textarea value={resumeText} onChange={e=>setResumeText(e.target.value)} placeholder="Paste your resume text here..." rows={14}/><button className="advisor-submit-btn" onClick={handleAnalyze} disabled={resumeText.trim().length<100}>Analyze My Resume →</button></div>}
      {inputMode==='upload' && <div><label className="upload-label"><input type="file" accept="application/pdf" onChange={handleFileUpload} style={{display:'none'}}/>{fileName?<span>📄 {fileName}</span>:<span>Click to select a PDF file</span>}</label><p className="upload-note">PDF parsing coming in the next update.</p></div>}
      {error && <p className="advisor-error">{error}</p>}
    </div>
  );

  if (stage === ADVISOR_STAGE.ANALYZING) return <div className="advisor-centered"><div className="advisor-spinner">🔍</div><p>Analyzing your resume…</p></div>;

  if (stage === ADVISOR_STAGE.QUESTIONS) return (
    <div className="advisor-content">
      <div className="advisor-profile"><h2>🎯 Got it!</h2>
        <div className="profile-summary">
          <p><strong>Background:</strong> {profile?.summary}</p>
          <p><strong>Level:</strong> {profile?.experience_level}</p>
          <p><strong>Skills:</strong> {profile?.key_skills?.join(', ')}</p>
          <p><strong>Directions:</strong> {profile?.possible_directions?.join(', ')}</p>
        </div>
      </div>
      <div><h3 style={{marginBottom:12}}>A few questions:</h3>
        {questions.map(q=>(
          <div key={q.id} className="question-block">
            <label>{q.text}</label>
            <input type="text" value={answers[q.id]||''} onChange={e=>setAnswers(a=>({...a,[q.id]:e.target.value}))} placeholder="Your answer…"/>
          </div>
        ))}
        <button className="advisor-submit-btn" onClick={handleSuggest} disabled={!allAnswered}>Find My Jobs →</button>
      </div>
      {error && <p className="advisor-error">{error}</p>}
      <button className="reset-link" onClick={handleReset}>← Start over</button>
    </div>
  );

  if (stage === ADVISOR_STAGE.SUGGESTING) return <div className="advisor-centered"><div className="advisor-spinner">🤔</div><p>Finding the best job titles for you…</p></div>;

  if (stage === ADVISOR_STAGE.READY) return (
    <div className="advisor-content">
      <div className="suggestions-intro"><p>{suggestions?.intro}</p></div>
      {suggestions?.searches?.map((s,i)=>(
        <div key={i} className="suggestion-card"><h3>🔎 {s.title}</h3><p>{s.rationale}</p></div>
      ))}
      <button className="reset-link" onClick={handleReset}>← Start over</button>
    </div>
  );

  return null;
}

// ─── Main App ─────────────────────────────────────────────────────────────────

const VIEWS = {
  pipeline: { label: 'pipeline', icon: '▶', component: PipelinePage },
  setup:    { label: 'search setup', icon: '⚙', component: SetupPage },
  profile:  { label: 'profile', icon: '◈', component: ProfilePage },
  tracker:  { label: 'tracker', icon: '◻', component: TrackerPage },
};

export default function App() {
  const [view, setView] = useState('pipeline');
  const [activeTab, setActiveTab] = useState('pipeline');
  const [version, setVersion] = useState('');

  useEffect(() => {
    axios.get(`${API}/`).then(r => setVersion(r.data.version)).catch(() => {});
  }, []);

  const ViewComponent = VIEWS[view]?.component;

  return (
    <div className="app-shell">
      {/* Top bar */}
      <div className="topbar">
        <span className="topbar-logo">JobsFinder</span>
        {version && <span className="topbar-version">v{version}</span>}
        <div className="topbar-spacer" />
        <span className="topbar-status">api connected</span>
      </div>

      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-label">pipeline</div>
        {Object.entries(VIEWS).map(([key, v]) => (
          <button
            key={key}
            className={`nav-btn${view===key&&activeTab==='pipeline'?' active':''}`}
            onClick={() => { setView(key); setActiveTab('pipeline'); }}
          >
            <span className="nav-icon">{v.icon}</span>
            {v.label}
          </button>
        ))}

        <hr className="sidebar-divider" />
        <div className="sidebar-label">general</div>
        <button
          className={`nav-btn${activeTab==='search'?' active':''}`}
          onClick={() => setActiveTab('search')}
        >
          <span className="nav-icon">🔍</span> job search
        </button>
        <button
          className={`nav-btn${activeTab==='advisor'?' active':''}`}
          onClick={() => setActiveTab('advisor')}
        >
          <span className="nav-icon">🎯</span> career advisor
        </button>
      </div>

      {/* Main */}
      <div className="main-content">
        {activeTab === 'pipeline' && ViewComponent && <ViewComponent />}
        {activeTab === 'search' && <JobSearchTab />}
        {activeTab === 'advisor' && <CareerAdvisorTab />}
      </div>
    </div>
  );
}
