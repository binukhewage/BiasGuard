from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading
import main

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Start Simulation in Background
@app.on_event("startup")
def start_background_sim():
    t = threading.Thread(target=main.run_simulation, daemon=True)
    t.start()

@app.get("/metrics")
def get_metrics():
    return main.DASHBOARD_STATE