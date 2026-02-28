import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [jobs, setJobs] = useState([]);
  const [showJobs, setShowJobs] = useState(false);
  const [version, setVersion] = useState('');

  useEffect(() => {
    axios.get(`${API_URL}/`).then(res => setVersion(res.data.version));
  }, []);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { text: input, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    const userInput = input;
    setInput('');
    setLoading(true);

    try {
      // All messages go through /api/chat — Claude decides what to do
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
      const errorMessage = {
        text: 'Sorry, I encountered an error. Please try again!',
        sender: 'ai'
      };
      setMessages(prev => [...prev, errorMessage]);
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
    <div className="App">
      <header className="App-header">
        <h1>🤖 Job Search AI Assistant</h1>
        <p>Your AI-powered career companion {version && `· v${version}`}</p>
      </header>

      <div className="chat-container">
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
              <div className="message-content">
                {msg.text}
              </div>
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
              <div className="message-content typing">
                Thinking...
              </div>
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
    </div>
  );
}

export default App;
