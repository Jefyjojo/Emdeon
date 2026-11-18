# Login / Registration (React + FastAPI + SQLite)

Passwords are hashed with bcrypt, users are stored in SQLite, login returns a JWT.

## Backend
```
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Frontend
```
cd frontend
npm install
npm run dev
```
Open http://localhost:5173, register, then log in.
