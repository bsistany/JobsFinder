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

function CareerAdvisorTab() {
  const [resumeText, setResumeText] = useState('');
  const [fileName, setFileName] = useState('');
  const [inputMode, setInputMode] = useState('paste');
  const [resumeReady, setResumeReady] = useState(false);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      alert('Please upload a PDF file.');
      return;
    }

    setFileName(file.name);
    setResumeReady(false);
    alert(`"${file.name}" selected. PDF parsing will be available in the next update!`);
  };

  const handlePasteSubmit = () => {
    if (resumeText.trim().length < 100) {
      alert('Please paste more of your resume — it looks too short.');
      return;
    }
    setResumeReady(true);
  };

  const handleReset = () => {
    setResumeText('');
    setFileName('');
    setResumeReady(false);
  };

  return (
    <div className="tab-content advisor-content">
      {!resumeReady ? (
        <div className="advisor-input">
          <div className="advisor-intro">
            <h2>🎯 Career Advisor</h2>
            <p>
              Upload or paste your resume and I'll analyze your background,
              ask a few clarifying questions, and search for the best-fit
              roles across multiple job categories — all at once.
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
                onClick={handlePasteSubmit}
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
                {fileName ? (
                  <span>📄 {fileName}</span>
                ) : (
                  <span>Click to select a PDF file</span>
                )}
              </label>
              <p className="upload-note">PDF parsing coming in the next update.</p>
            </div>
          )}
        </div>
      ) : (
        <div className="advisor-ready">
          <div className="resume-confirmed">
            <span>✅ Resume received</span>
            <button className="reset-btn" onClick={handleReset}>Start Over</button>
          </div>
          <div className="advisor-placeholder">
            <p>🚧 Analysis coming in Phase B!</p>
            <p>Your resume has been received. In the next update, I'll analyze
            your background and ask a few questions before searching for the
            best-fit roles for you.</p>
          </div>
        </div>
      )}
    </div>
  );
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
