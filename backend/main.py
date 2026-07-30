from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from typing import List
from .engine import engine
from .models import Recipe, PricePoint
from .db import db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler = BackgroundScheduler()
    scheduler.add_job(engine.fetch_prices, 'interval', minutes=5)
    scheduler.start()
    
    # Initial Fetch
    engine.fetch_prices()
    
    yield
    
    # Shutdown
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/api/prices")
def get_prices():
    # Return all prices dump or formatted?
    # Maybe just return the recipes with their calculated profits
    return engine.get_processed_recipes()

@app.get("/api/history/{item_id}")
def get_history(item_id: int):
    return db.get_history(item_id)

@app.post("/api/refresh")
def refresh_prices():
    success = engine.fetch_prices()
    return {"status": "success" if success else "error"}
