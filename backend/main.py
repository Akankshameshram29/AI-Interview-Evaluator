
from fastapi import FastAPI
from database.connection import Base, engine
from backend.routes import auth
from backend.routes import topics
from backend.routes import practice
from backend.routes import auth, topics, practice, attempts, progress
from backend.limiter import limiter

Base.metadata.create_all(bind=engine)  # creates tables from models if not present

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


app.include_router(auth.router)
app.include_router(topics.router)
app.include_router(practice.router)
app.include_router(attempts.router)
app.include_router(progress.router)

@app.get("/hello")
def hello():
    return {"message": "Hello from FastAPI"}


@app.get("/")
def read_root():
    return {"status": "Backend running on Vercel!"}

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for this project's scope; tighten to your exact frontend URL later if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)