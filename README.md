\# 🤖 GanAI — Full-Stack AI Agent Platform



> A production-oriented full-stack AI assistant built with \*\*Next.js, React, TypeScript, FastAPI, Python, LLMs, and AI tools\*\*.



GanAI is a full-stack AI agent platform designed to interact with Large Language Models, route requests to specialized agents, and execute tools such as calculations, date/time operations, weather information, and web search.



The project is being developed toward a production-ready AI engineering architecture with persistent memory, RAG, agentic workflows, observability, Docker, CI/CD, and cloud deployment.



\---



\## 🚀 Features



\* 🤖 LLM-powered AI conversations

\* 🧠 Multiple specialized AI agents

\* 🔀 Intelligent agent routing

\* 🧮 Calculator tool

\* 🕐 Date \& time tool

\* 🌤️ Weather tool

\* 🔎 Web search tool

\* ⚡ Streaming AI responses

\* 💬 Conversation management

\* 🔌 Multiple LLM provider support

\* 🐍 FastAPI backend

\* ⚛️ Next.js + React frontend

\* 📘 TypeScript frontend

\* 🔐 Environment-based API configuration

\* 🧩 Modular agent and tool architecture



\---



\## 🏗️ Architecture



```text

&#x20;                        ┌─────────────────────────┐

&#x20;                        │       Next.js UI        │

&#x20;                        │   React + TypeScript    │

&#x20;                        └────────────┬────────────┘

&#x20;                                     │

&#x20;                                     │ HTTP / Streaming

&#x20;                                     ▼

&#x20;                        ┌─────────────────────────┐

&#x20;                        │      FastAPI API        │

&#x20;                        │       Python            │

&#x20;                        └────────────┬────────────┘

&#x20;                                     │

&#x20;                                     ▼

&#x20;                        ┌─────────────────────────┐

&#x20;                        │      Agent Service      │

&#x20;                        │                         │

&#x20;                        │  ┌───────────────────┐  │

&#x20;                        │  │ Assistant Agent   │  │

&#x20;                        │  ├───────────────────┤  │

&#x20;                        │  │ Code Expert       │  │

&#x20;                        │  ├───────────────────┤  │

&#x20;                        │  │ Data Scientist    │  │

&#x20;                        │  └───────────────────┘  │

&#x20;                        └────────────┬────────────┘

&#x20;                                     │

&#x20;                        ┌────────────┴────────────┐

&#x20;                        ▼                         ▼

&#x20;               ┌──────────────────┐     ┌──────────────────┐

&#x20;               │   LLM Providers  │     │      Tools       │

&#x20;               │                  │     │                  │

&#x20;               │ OpenAI           │     │ Calculator       │

&#x20;               │ Gemini           │     │ DateTime         │

&#x20;               │ Anthropic        │     │ Weather          │

&#x20;               │                  │     │ Web Search       │

&#x20;               └──────────────────┘     └──────────────────┘

```



\---



\## 🧠 AI Agent Architecture



The backend uses a modular agent architecture.



\### Available Agents



| Agent          | Purpose                                      |

| -------------- | -------------------------------------------- |

| Assistant      | General-purpose AI assistant                 |

| Code Expert    | Programming and software-development tasks   |

| Data Scientist | Data analysis and data-science related tasks |



The application can route requests to the appropriate agent based on the user's query.



\---



\## 🛠️ Technology Stack



\### Frontend



\* Next.js

\* React

\* TypeScript

\* CSS

\* ESLint



\### Backend



\* Python

\* FastAPI

\* Uvicorn

\* Pydantic

\* REST APIs



\### AI / GenAI



\* Large Language Models

\* OpenAI API

\* Google Gemini API

\* Anthropic API

\* Prompt Engineering

\* AI Agents

\* Tool Calling Architecture



\### Tools



\* Calculator

\* Date \& Time

\* Weather API

\* Web Search API



\### Development



\* Git

\* GitHub

\* VS Code

\* Python Virtual Environment

\* npm



\---



\## 📁 Project Structure



```text

ganai-ai-agent-platform/

│

├── ai-agent-frontend/

│   ├── app/

│   │   ├── globals.css

│   │   ├── layout.tsx

│   │   └── page.tsx

│   ├── public/

│   ├── package.json

│   ├── package-lock.json

│   ├── next.config.ts

│   └── tsconfig.json

│

├── backend/

│   ├── agents/

│   │   ├── assistant\_agent.py

│   │   ├── base\_agent.py

│   │   └── specialist\_agent.py

│   │

│   ├── models/

│   │   ├── llm\_provider.py

│   │   └── model\_config.py

│   │

│   ├── services/

│   │   ├── agent\_service.py

│   │   └── conversation\_service.py

│   │

│   ├── tools/

│   │   ├── calculator.py

│   │   ├── datetime\_tool.py

│   │   ├── tool\_registry.py

│   │   ├── weather.py

│   │   └── web\_search.py

│   │

│   ├── main.py

│   └── .env.example

│

├── .gitignore

└── requirements.txt

```



\---



\# ⚙️ Local Setup



\## 1. Clone the repository



```bash

git clone https://github.com/punnamganesh/ganai-ai-agent-platform.git

cd ganai-ai-agent-platform

```



\---



\## 2. Backend Setup



Create a Python virtual environment:



\### Windows



```powershell

python -m venv venv

```



Activate it:



```powershell

.\\venv\\Scripts\\Activate.ps1

```



Install dependencies:



```powershell

pip install -r requirements.txt

```



\---



\## 3. Configure Environment Variables



Create:



```text

backend/.env

```



Use the example file as a reference:



```text

backend/.env.example

```



Example:



```env

OPENAI\_API\_KEY=

GEMINI\_API\_KEY=

ANTHROPIC\_API\_KEY=



TAVILY\_API\_KEY=

WEATHER\_API\_KEY=

```



Never commit your actual `.env` file.



\---



\## 4. Start the Backend



From the project root:



```powershell

uvicorn backend.main:app --reload --port 8000

```



Backend:



```text

http://localhost:8000

```



API documentation:



```text

http://localhost:8000/docs

```



\---



\# 💻 Frontend Setup



Open another terminal.



```powershell

cd ai-agent-frontend

```



Install dependencies:



```powershell

npm install

```



Start the development server:



```powershell

npm run dev

```



Frontend:



```text

http://localhost:3000

```



\---



\# 🔌 API Endpoints



\### Health Check



```http

GET /

```



```http

GET /health

```



\### Agents



```http

GET /api/agents

```



\### Chat



```http

POST /api/chat

```



\### Streaming Chat



```http

POST /api/chat/stream

```



\### Conversations



```http

GET /api/conversations

```



```http

GET /api/conversations/{id}

```



\### Delete Conversation



```http

DELETE /api/conversations/{id}

```



\---



\# 🧪 Example API Request



```json

{

&#x20; "message": "Explain Python decorators with an example"

}

```



The backend processes the request through the agent architecture and returns the AI response.



\---



\# 🔄 Current AI Request Flow



```text

User

&#x20; │

&#x20; ▼

Next.js Frontend

&#x20; │

&#x20; ▼

FastAPI API

&#x20; │

&#x20; ▼

Agent Service

&#x20; │

&#x20; ▼

Agent Selection

&#x20; │

&#x20; ├── Assistant

&#x20; ├── Code Expert

&#x20; └── Data Scientist

&#x20; │

&#x20; ▼

LLM Provider

&#x20; │

&#x20; ├── OpenAI

&#x20; ├── Gemini

&#x20; └── Anthropic

&#x20; │

&#x20; ▼

Tool Execution (when required)

&#x20; │

&#x20; ▼

AI Response

&#x20; │

&#x20; ▼

Frontend

```



\---



\# 🗺️ Development Roadmap



The project is being enhanced incrementally toward a production-oriented AI engineering platform.



\### Phase 1 — Foundation



\* \[x] FastAPI backend

\* \[x] Ne



