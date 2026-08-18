from fastapi import FastAPI
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()
engine = create_engine(os.getenv("DATABASE_URL"))

@app.get("/hello")
def hello():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT NOW()"))
        db_time = result.scalar()
    return {"message": "Hello from FastAPI", "db_time": str(db_time)}