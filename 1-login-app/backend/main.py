import os
import re
import sqlite3
import datetime

import bcrypt
import jwt
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

SECRET = os.getenv("JWT_SECRET", "change-this-secret")
DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

app = FastAPI(title="Login API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


with db() as conn:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash BLOB NOT NULL
        )"""
    )


class RegisterIn(BaseModel):
    name: str
    email: str
    password: str


class LoginIn(BaseModel):
    email: str
    password: str


def make_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


@app.post("/register", status_code=201)
def register(data: RegisterIn):
    name, email = data.name.strip(), data.email.strip().lower()
    if not name:
        raise HTTPException(400, "Name is required")
    if not EMAIL_RE.match(email):
        raise HTTPException(400, "Invalid email")
    if len(data.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt())
    try:
        with db() as conn:
            conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, hashed),
            )
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Email already registered")
    return {"message": "Registered successfully"}


@app.post("/login")
def login(data: LoginIn):
    email = data.email.strip().lower()
    with db() as conn:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user or not bcrypt.checkpw(data.password.encode(), user["password_hash"]):
        raise HTTPException(401, "Invalid email or password")
    return {"token": make_token(user["id"]), "name": user["name"]}


@app.get("/me")
def me(authorization: str = Header(default="")):
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")
    with db() as conn:
        user = conn.execute(
            "SELECT name, email FROM users WHERE id = ?", (int(payload["sub"]),)
        ).fetchone()
    if not user:
        raise HTTPException(404, "User not found")
    return dict(user)
