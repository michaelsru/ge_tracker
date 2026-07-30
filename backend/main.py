from fastapi import FastAPI
from fastapi.responses import FileResponse
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from typing import List
from .engine import engine
from .models import Recipe, PricePoint
from .db import db
import os, json

TIMERS_PATH = os.path.join(os.path.dirname(__file__), "timers.json")

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
    return engine.get_processed_recipes()

@app.get("/api/timers")
def get_timers():
    with open(TIMERS_PATH) as f:
        return json.load(f)

@app.patch("/api/timers/{tag}")
def update_timer(tag: str, body: dict):
    with open(TIMERS_PATH) as f:
        timers = json.load(f)
    entry = next((t for t in timers if t["tag"] == tag), None)
    if not entry:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Tag '{tag}' not found")
    entry["rateConfig"].update({
        k: v for k, v in body.items() if k in ("loopSecs", "conversionsPerLoop")
    })
    with open(TIMERS_PATH, "w") as f:
        json.dump(timers, f, indent=2)
    return entry

@app.patch("/api/recipes/{recipe_id}")
def update_recipe(recipe_id: str, body: dict):
    if "hidden" in body:
        success = engine.set_recipe_hidden(recipe_id, bool(body["hidden"]))
        if not success:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"Recipe '{recipe_id}' not found")
    return {"status": "ok"}

@app.get("/api/history/{item_id}")
def get_history(item_id: int):
    return db.get_history(item_id)

@app.post("/api/refresh")
def refresh_prices():
    success = engine.fetch_prices()
    return {"status": "success" if success else "error"}
