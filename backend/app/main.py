from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.routers import auth, chat, logs, memory, projects, status, users

settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="OBITO AI",
    description="Personal AI operating system backend — FAKHIR AI",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(users.router)
app.include_router(status.router)
app.include_router(logs.router)
app.include_router(projects.router)
app.include_router(memory.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"ok": "obito-backend", "phase": "1"}
