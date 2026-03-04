import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// ─── Job Search Tab ───────────────────────────────────────────────────────────

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
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/api/chat`, {
        message: userInput
      });

      const aiMessage = { text: response.data.response, sender: 'ai' };
      setMessages(prev => [...prev, aiMessage]);

      if (response.data.jobs && response.data.jobs.length > 0) {
        setJobs(response.data.jobs);
        setShowJobs(true);
      } else {
        setShowJobs(false);
      }

    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        text: 'Sorry, I encountered an error. Please try again!',
        sender: 'ai'
      }]);
      setShowJobs(false);
    } finally {
      setLoading(false);
    }
  };

  const quickSearch = (what, where) => {
    setInput(`Find ${what} jobs in ${where}`);
    setTimeout(() => {
      document.querySelector('.input-form button').click();
    }, 100);
  };

  return (
    <div className="tab-content">
      <div className="messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <h2>Welcome! 👋</h2>
            <p>I can help you find jobs using real-time data from Adzuna!</p>
            <div className="quick-searches">
              <h3>Try these quick searches:</h3>
              <button onClick={() => quickSearch('Python developer', 'Toronto')}>
                Python Developer in Toronto
              </button>
              <button onClick={() => quickSearch('Software Engineer', 'Vancouver')}>
                Software Engineer in Vancouver
              </button>
              <button onClick={() => quickSearch('Data Scientist', 'Ontario')}>
                Data Scientist in Ontario
              </button>
            </div>
            <p className="hint">Or just describe what you're looking for in plain English!</p>
          </div>
        )}

        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            <div className="message-content">{msg.text}</div>
          </div>
        ))}

        {showJobs && jobs.length > 0 && (
          <div className="jobs-list">
            {jobs.map((job, index) => (
              <div key={job.id || index} className="job-card">
                <h3>{job.title}</h3>
                <p className="company">🏢 {job.company}</p>
                <p className="location">📍 {job.location}</p>
                {job.salary_min && job.salary_max && (
                  <p className="salary">
                    💰 ${job.salary_min?.toLocaleString()} - ${job.salary_max?.toLocaleString()}
                  </p>
                )}
                <p className="category">📂 {job.category}</p>
                <p className="description">{job.description}</p>
                {job.redirect_url && (
                  <a
                    href={job.redirect_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="apply-button"
                  >
                    View Job →
                  </a>
                )}
              </div>
            ))}
          </div>
        )}

        {loading && (
          <div className="message ai">
            <div className="message-content typing">Thinking...</div>
          </div>
        )}
      </div>

      <form onSubmit={sendMessage} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Try: Find senior cybersecurity jobs in remote"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}

// ─── Career Advisor Tab ───────────────────────────────────────────────────────

const ADVISOR_STAGE = {
  INPUT: 'input',
  ANALYZING: 'analyzing',
  QUESTIONS: 'questions',
  SUGGESTING: 'suggesting',
  READY: 'ready',
};

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
    if (file.type !== 'application/pdf') {
      alert('Please upload a PDF file.');
      return;
    }
    setFileName(file.name);
    alert(`"${file.name}" selected. PDF parsing coming in the next update!`);
  };

  const handleAnalyze = async () => {
    setError('');
    setStage(ADVISOR_STAGE.ANALYZING);
    try {
      const response = await axios.post(`${API_URL}/api/advisor/analyze`, {
        resume_text: resumeText
      });
      setProfile(response.data.profile);
      setQuestions(response.data.questions);
      setStage(ADVISOR_STAGE.QUESTIONS);
    } catch (err) {
      setError('Sorry, I had trouble analyzing your resume. Please try again.');
      setStage(ADVISOR_STAGE.INPUT);
    }
  };

  const handleAnswerChange = (questionId, value) => {
    setAnswers(prev => ({ ...prev, [questionId]: value }));
  };

  const allAnswered = questions.length > 0 &&
    questions.every(q => answers[q.id] && answers[q.id].trim().length > 0);

  const handleSuggest = async () => {
    setError('');
    setStage(ADVISOR_STAGE.SUGGESTING);
    try {
      const formattedAnswers = questions.map(q => ({
        question_id: q.id,
        question: q.text,
        answer: answers[q.id] || ''
      }));
      const response = await axios.post(`${API_URL}/api/advisor/suggest`, {
        profile,
        answers: formattedAnswers
      });
      setSuggestions(response.data);
      setStage(ADVISOR_STAGE.READY);
    } catch (err) {
      setError('Sorry, I had trouble generating suggestions. Please try again.');
      setStage(ADVISOR_STAGE.QUESTIONS);
    }
  };

  const handleReset = () => {
    setStage(ADVISOR_STAGE.INPUT);
    setResumeText('');
    setFileName('');
    setProfile(null);
    setQuestions([]);
    setAnswers({});
    setSuggestions(null);
    setError('');
  };

  // ── Stage: Resume Input ──
  if (stage === ADVISOR_STAGE.INPUT) {
    return (
      <div className="tab-content advisor-content">
        <div className="advisor-intro">
          <h2>🎯 Career Advisor</h2>
          <p>
            Paste your resume and I'll analyze your background, ask a few
            clarifying questions, and find the best-fit roles for you across
            multiple job categories.
          </p>
        </div>

        <div className="input-mode-toggle">
          <button
            className={inputMode === 'paste' ? 'mode-btn active' : 'mode-btn'}
            onClick={() => setInputMode('paste')}
          >
            📋 Paste Resume
          </button>
          <button
            className={inputMode === 'upload' ? 'mode-btn active' : 'mode-btn'}
            onClick={() => setInputMode('upload')}
          >
            📄 Upload PDF
          </button>
        </div>

        {inputMode === 'paste' && (
          <div className="paste-input">
            <textarea
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              placeholder="Paste the text of your resume here..."
              rows={14}
            />
            <button
              className="advisor-submit-btn"
              onClick={handleAnalyze}
              disabled={resumeText.trim().length < 100}
            >
              Analyze My Resume →
            </button>
          </div>
        )}

        {inputMode === 'upload' && (
          <div className="upload-input">
            <label className="upload-label">
              <input
                type="file"
                accept="application/pdf"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
              />
              {fileName ? <span>📄 {fileName}</span> : <span>Click to select a PDF file</span>}
            </label>
            <p className="upload-note">PDF parsing coming in the next update.</p>
          </div>
        )}

        {error && <p className="advisor-error">{error}</p>}
      </div>
    );
  }

  // ── Stage: Analyzing ──
  if (stage === ADVISOR_STAGE.ANALYZING) {
    return (
      <div className="tab-content advisor-content advisor-centered">
        <div className="advisor-spinner">🔍</div>
        <p>Analyzing your resume...</p>
      </div>
    );
  }

  // ── Stage: Clarifying Questions ──
  if (stage === ADVISOR_STAGE.QUESTIONS) {
    return (
      <div className="tab-content advisor-content">
        <div className="advisor-profile">
          <h2>🎯 Great — I've read your resume!</h2>
          <div className="profile-summary">
            <p><strong>Background:</strong> {profile?.summary}</p>
            <p><strong>Experience level:</strong> {profile?.experience_level}</p>
            <p><strong>Key skills:</strong> {profile?.key_skills?.join(', ')}</p>
            <p><strong>Possible directions:</strong> {profile?.possible_directions?.join(', ')}</p>
          </div>
        </div>

        <div className="advisor-questions">
          <h3>Just a few questions to narrow things down:</h3>
          {questions.map((q) => (
            <div key={q.id} className="question-block">
              <label>{q.text}</label>
              <input
                type="text"
                value={answers[q.id] || ''}
                onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                placeholder="Your answer..."
              />
            </div>
          ))}

          <button
            className="advisor-submit-btn"
            onClick={handleSuggest}
            disabled={!allAnswered}
          >
            Find My Jobs →
          </button>
        </div>

        {error && <p className="advisor-error">{error}</p>}
        <button className="reset-link" onClick={handleReset}>← Start over</button>
      </div>
    );
  }

  // ── Stage: Suggesting ──
  if (stage === ADVISOR_STAGE.SUGGESTING) {
    return (
      <div className="tab-content advisor-content advisor-centered">
        <div className="advisor-spinner">🤔</div>
        <p>Finding the best job titles for you...</p>
      </div>
    );
  }

  // ── Stage: Ready ──
  if (stage === ADVISOR_STAGE.READY) {
    return (
      <div className="tab-content advisor-content">
        <div className="suggestions-intro">
          <p>{suggestions?.intro}</p>
        </div>

        <div className="suggestions-list">
          {suggestions?.searches?.map((s, i) => (
            <div key={i} className="suggestion-card">
              <h3>🔎 {s.title}</h3>
              <p>{s.rationale}</p>
            </div>
          ))}
        </div>

        <p className="advisor-note">
          🚧 <strong>Phase C coming next:</strong> I'll run all these searches
          automatically and show you the combined results!
        </p>

        <button className="reset-link" onClick={handleReset}>← Start over</button>
      </div>
    );
  }

  return null;
}

// ─── Main App ─────────────────────────────────────────────────────────────────

function App() {
  const [activeTab, setActiveTab] = useState('search');
  const [version, setVersion] = useState('');

  useEffect(() => {
    axios.get(`${API_URL}/`).then(res => setVersion(res.data.version));
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>🤖 Job Search AI Assistant</h1>
        <p>Your AI-powered career companion {version && `· v${version}`}</p>
      </header>

      <div className="chat-container">
        <div className="tab-bar">
          <button
            className={activeTab === 'search' ? 'tab active' : 'tab'}
            onClick={() => setActiveTab('search')}
          >
            🔍 Job Search
          </button>
          <button
            className={activeTab === 'advisor' ? 'tab active' : 'tab'}
            onClick={() => setActiveTab('advisor')}
          >
            🎯 Career Advisor
          </button>
        </div>

        {activeTab === 'search' ? <JobSearchTab /> : <CareerAdvisorTab />}
      </div>
    </div>
  );
}

export default App;
