# Family Fitness Tracker

A full-stack fitness tracking app for families — log workouts, share screenshots, and compete on the leaderboard.

Built with **FastAPI** (backend) + **Streamlit** (frontend) + **SQLite** + **ImageKit** (media storage).

---

## Features

- **Register / Login** — JWT-based authentication via fastapi-users
- **Log Activity** — Upload a screenshot or video of your workout along with steps, distance, and duration
- **Activity Feed** — See all family members' latest workouts in chronological order
- **Leaderboard** — Ranked by total steps; shows every family member even if they have 0 steps logged

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + fastapi-users |
| Frontend | Streamlit |
| Database | SQLite (aiosqlite) |
| ORM | SQLAlchemy (async) |
| Media Storage | ImageKit |
| Auth | JWT (Bearer token) |

---

## Project Structure

```
fast-api-fullstack-project/
├── app/
│   ├── app.py          # FastAPI routes (upload, feed, leaderboard)
│   ├── db.py           # SQLAlchemy models and database setup
│   ├── frontend.py     # Streamlit UI
│   ├── images.py       # ImageKit client setup
│   ├── schemas.py      # Pydantic schemas
│   └── users.py        # fastapi-users config (auth, JWT)
├── main.py             # Uvicorn entry point
├── .env                # Environment variables (not committed)
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- An [ImageKit](https://imagekit.io/) account (for media uploads)

### Setup

1. **Clone the repo**
   ```bash
   git clone <repo-url>
   cd fast-api-fullstack-project
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv fastenv
   # Windows
   fastenv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install fastapi uvicorn[standard] sqlalchemy aiosqlite fastapi-users fastapi-users-db-sqlalchemy python-multipart imagekitio streamlit requests python-dotenv
   ```

4. **Create a `.env` file**
   ```env
   IMAGEKIT_PRIVATE_KEY=your_imagekit_private_key_here
   ```

5. **Run the backend**
   ```bash
   python main.py
   ```
   API available at `http://localhost:8000`
   Interactive docs at `http://localhost:8000/docs`

6. **Run the frontend** (in a separate terminal)
   ```bash
   fastenv\Scripts\streamlit.exe run app/frontend.py
   ```
   UI available at `http://localhost:8501`

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/jwt/login` | Login and receive JWT token |
| POST | `/upload` | Upload a workout (photo/video + stats) |
| GET | `/feed` | Get all activity posts (newest first) |
| GET | `/leaderboard` | Get all users ranked by total steps |

---

## Environment Variables

| Variable | Description |
|---|---|
| `IMAGEKIT_PRIVATE_KEY` | Private key from your ImageKit dashboard |
