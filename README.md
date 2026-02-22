# Recruiter AI 🤖

An AI-powered recruitment pipeline that parses job descriptions, evaluates resumes, and ranks candidates — all through a clean, minimalist web UI.

![Stack](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi) ![Stack](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB?logo=react) ![Stack](https://img.shields.io/badge/AI-Google%20Gemini-4285F4?logo=google)

---

## What it does

1. **Upload** a Job Description (PDF or TXT) and multiple resumes
2. **AI evaluates** each candidate against the JD using Google Gemini
3. **Results screen** shows ranked candidates with scores — Interview / Hold / Reject
4. **Confirm actions** with a human-in-the-loop review step
5. **Email preview** shows draft interview invitations (simulated — no emails actually sent)

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React 18, Vite, CSS Modules |
| Backend | FastAPI, Python 3.11+ |
| AI | Google Gemini 2.0 Flash |
| State | In-memory (no database) |
| Auth | None (MVP) |

---

## Project Structure

```
Recruiter.AI/
├── app/
│   ├── main.py              # FastAPI app — all routes
│   ├── config.py            # Settings (reads .env)
│   └── services/
│       ├── llm_service.py   # Gemini integration + demo fallback
│       └── pdf_service.py   # PDF/TXT text extraction
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Screen state machine
│   │   ├── api.js           # Axios API client
│   │   └── components/
│   │       ├── Screen1.jsx  # Upload JD + resumes
│   │       ├── Screen2.jsx  # Processing spinner
│   │       ├── Screen3.jsx  # Results table
│   │       ├── Screen4.jsx  # Action confirmation
│   │       └── Screen5.jsx  # Email preview
│   └── vite.config.js       # Dev proxy → backend
├── requirements.txt
├── .env.example
└── README.md
```

---

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| `POST` | `/analyze` | Upload JD + resumes, returns ranked candidates |
| `POST` | `/override` | Update a candidate's decision |
| `POST` | `/finalize/{session_id}` | Simulate sending interview emails |
| `GET`  | `/health` | Health check |

---

## Quick Start (Local)

### 1. Clone & configure

```bash
git clone https://github.com/khanfawwaz/Recruiter.AI.git
cd Recruiter.AI
cp .env.example .env
```

Edit `.env` and set your Gemini API key:
```env
GEMINI_API_KEY=your-key-here   # https://aistudio.google.com/apikey
DEMO_MODE=false                 # set true to skip Gemini (for testing)
```

### 2. Backend

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 5000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**

---

## Production Deployment (Oracle VPS / Any Linux Server)

See [Server Setup Commands](#server-setup) below.

### Prerequisites on server
- Ubuntu 22.04+
- Python 3.11+
- Node.js 20+
- Nginx
- Supervisor (or systemd)

### Server Setup

```bash
# 1. Clone the repo
git clone https://github.com/khanfawwaz/Recruiter.AI.git
cd Recruiter.AI

# 2. Backend setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Create .env
cp .env.example .env
nano .env   # add your GEMINI_API_KEY

# 4. Build frontend
cd frontend
npm install
npm run build
cd ..

# 5. Serve frontend via Nginx (static files from frontend/dist/)
# 6. Run backend with Gunicorn/uvicorn (see below)
```

### Run backend with systemd

Create `/etc/systemd/system/recruiter.service`:
```ini
[Unit]
Description=Recruiter AI Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/Recruiter.AI
EnvironmentFile=/home/ubuntu/Recruiter.AI/.env
ExecStart=/home/ubuntu/Recruiter.AI/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 5000 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable recruiter
sudo systemctl start recruiter
```

### Nginx config

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend (built static files)
    root /home/ubuntu/Recruiter.AI/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API proxy
    location ~ ^/(analyze|override|finalize|session|health) {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 50M;
    }
}
```

```bash
sudo nginx -t && sudo nginx -s reload
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | — | From [aistudio.google.com](https://aistudio.google.com/apikey) |
| `GEMINI_MODEL` | No | `gemini-2.0-flash` | Model to use |
| `DEMO_MODE` | No | `false` | Skip Gemini, return realistic mock results |
| `MAX_UPLOAD_SIZE_MB` | No | `10` | Max file size per upload |

---

## Demo Mode

Set `DEMO_MODE=true` to run without making any Gemini API calls. The backend will:
- Auto-extract candidate names from filenames (`Resume_Ahmed_Khan.pdf` → "Ahmed Khan")
- Generate deterministic, realistic scores per file
- Add realistic delays so the UI feels like real processing

Useful for demos or when free-tier quota is exhausted.

---

## License

MIT
