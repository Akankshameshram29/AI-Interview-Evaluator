
from fastapi import FastAPI
from database.connection import Base, engine
from backend.routes import auth
from backend.routes import topics
from backend.routes import practice
from backend.routes import auth, topics, practice, attempts, progress

Base.metadata.create_all(bind=engine)  # creates tables from models if not present

app = FastAPI()
app.include_router(auth.router)
app.include_router(topics.router)
app.include_router(practice.router)


app.include_router(attempts.router)
app.include_router(progress.router)
@app.get("/hello")
def hello():
    return {"message": "Hello from FastAPI"}