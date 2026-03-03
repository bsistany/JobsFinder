# System Architecture: JobsFinder

JobsFinder is an AI-augmented job search platform that utilizes **Natural Language Processing (NLP)** to bridge the gap between user intent and structured job data. 

## High-Level Component Overview

The system is built on a decoupled, containerized architecture using **Docker Compose**.

### 1. Frontend (React)
- **Role:** The Presentation Layer.
- **Key Responsibilities:** Managing conversational state, rendering interactive job cards, and providing search shortcuts.

### 2. Backend API (FastAPI)
- **Role:** The Orchestration Hub (Middleware).
- **Key Responsibilities:** Managing the "Intelligence Loop," API routing, and data sanitization.
- **Key Modules:** - `claude_service.py`: Orchestrates prompts for the **Groq AI API**.
    - `adzuna_service.py`: Interfaces with the **Adzuna API** for job listings.

### 3. External Services
- **Groq AI (LLaMA 3.1):** Handles intent parsing and natural language summarization.
- **Adzuna API:** The source of truth for global job market data.

---

## The "Intelligence Loop" Data Flow

The Backend acts as the strict intermediary. Data never flows directly between Adzuna and Groq.

1. **User Query:** User enters a prompt in the React UI (e.g., *"Find Python jobs in London"*).
2. **Intent Parsing:** Backend sends the prompt to **Groq** to extract structured parameters (`title`, `location`).
3. **Data Retrieval:** Backend queries **Adzuna** using the parameters returned by Groq.
4. **Raw Data:** Adzuna returns a list of job objects to the Backend.
5. **Summarization:** Backend sends those results to **Groq** to generate a conversational summary.
6. **Formatting:** Groq returns a human-friendly response string to the Backend.
7. **Final Payload:** Backend packages the **Groq Summary** + **Adzuna Job Objects** into one JSON response.
8. **UI Render:** React displays the AI’s message and the interactive Job Cards.

---

## Infrastructure & Security
- **Docker Network:** Services reside in a private bridge network. Only the necessary ports are exposed.
- **Environment Management:** API keys for Adzuna and Groq are managed via `.env` files and never hardcoded.

## Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Language** | Python 3.11, JavaScript (ES6+) |
| **Backend** | FastAPI (Asynchronous) |
| **Frontend** | React |
| **AI Model** | LLaMA 3.1 (via Groq) |
| **Orchestration** | Docker Compose |
