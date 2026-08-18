
from fastapi import FastAPI
from database.connection import Base, engine
from backend.routes import auth
from backend.routes import topics

Base.metadata.create_all(bind=engine)  # creates tables from models if not present

app = FastAPI()
app.include_router(auth.router)
app.include_router(topics.router)

@app.get("/hello")
def hello():
    return {"message": "Hello from FastAPI"}