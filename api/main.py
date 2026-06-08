from fastapi import FastAPI
from pydantic import BaseModel

from core.database import init_db, insert_log
from core.alerts import generate_alert
from core.predictor import predict_risk
from vision.camera import stop_camera

app = FastAPI()


# ---------------- INIT DATABASE ----------------
init_db()


# ---------------- INPUT MODEL ----------------
class FactoryInput(BaseModel):
    defects: list = []
    machine_load: int = 50


# ---------------- HEALTH CHECK ----------------
@app.get("/health")
def health():
    return {"status": "Smart Factory API running"}


# ---------------- LIVE AI ENGINE ----------------
@app.post("/live-ai")
def live_ai(data: FactoryInput):

    defects = data.defects
    machine_load = data.machine_load

    # ---------------- DECISION ENGINE ----------------
    if len(defects) > 3:
        decision = "🔧 SLOW PRODUCTION"
    elif machine_load > 80:
        decision = "⚡ OVERLOAD WARNING"
    else:
        decision = "NORMAL_OPERATION"

    # ---------------- ALERT ENGINE ----------------
    alert = generate_alert(defects, machine_load, decision)

    # ---------------- PREDICTION ENGINE ----------------
    risk_level = predict_risk(defects, machine_load)

    # ---------------- DATABASE LOGGING ----------------
    insert_log(defects, machine_load, decision)

    return {
        "status": "LIVE AI SYSTEM",
        "decision": decision,
        "defects": len(defects),
        "machine_load": machine_load,
        "alert": alert,
        "risk_level": risk_level
    }


# ---------------- LIVE CAMERA ENDPOINT ----------------
@app.get("/live-camera")
def live_camera():
    return {
        "status": "LIVE CAMERA ENDPOINT ACTIVE"
    }


# ---------------- ANALYTICS ENDPOINT ----------------
@app.get("/analytics")
def analytics():
    import sqlite3
    from core.database import DB_NAME

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 50")
    rows = c.fetchall()

    conn.close()

    return {
        "logs": rows
    }


# ---------------- CLEAN SHUTDOWN ----------------
@app.on_event("shutdown")
def shutdown_event():
    stop_camera()