import streamlit as st
import requests
import pandas as pd
import time

# ---------------- CONFIG ----------------
API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Industrial AI Dashboard", layout="wide")


# ---------------- HEADER ----------------
st.title("🏭 Industrial AI Vision System")
st.subheader("Real-Time Factory Monitoring Dashboard")


# ---------------- API SAFE CALL ----------------
def safe_get(endpoint):
    try:
        res = requests.get(f"{API_URL}{endpoint}")
        return res.json()
    except:
        return None


def safe_post(endpoint, payload):
    try:
        res = requests.post(f"{API_URL}{endpoint}", json=payload)
        return res.json()
    except:
        return None


# ---------------- SIDEBAR CONTROL ----------------
st.sidebar.title("⚙ Controls")

run_simulation = st.sidebar.button("Run AI Simulation")

if run_simulation:
    sample_data = {
        "defects": ["crack", "scratch"] if time.time() % 2 == 0 else [],
        "machine_load": int(time.time() % 100)
    }

    result = safe_post("/live-ai", sample_data)

    if result:
        st.success("AI Updated Successfully")


# ---------------- LIVE AI STATUS ----------------
st.header("🧠 AI Decision Engine")

ai_data = safe_post("/live-ai", {"defects": [], "machine_load": 50})

if ai_data:
    col1, col2, col3 = st.columns(3)

    col1.metric("Decision", ai_data["decision"])
    col2.metric("Risk Level", ai_data["risk_level"])
    col3.metric("Alert", ai_data["alert"])

else:
    st.error("AI API not responding")


# ---------------- LIVE CAMERA SECTION ----------------
st.header("🎥 Live Camera Feed")

st.info("Camera stream handled by FastAPI /live-camera endpoint")

st.code(f"{API_URL}/live-camera")


# ---------------- ANALYTICS ----------------
st.header("📊 Factory Analytics")

analytics = safe_get("/analytics")

if analytics and "logs" in analytics:

    df = pd.DataFrame(
        analytics["logs"],
        columns=["ID", "Timestamp", "Defects", "Load", "Decision"]
    )

    # ---------------- GRAPHS ----------------
    st.subheader("Defects Over Time")
    st.line_chart(df["Defects"])

    st.subheader("Machine Load Trend")
    st.line_chart(df["Load"])

    # ---------------- TABLE ----------------
    st.subheader("Recent Logs")
    st.dataframe(df.tail(10))

else:
    st.warning("No analytics data available")


# ---------------- AUTO REFRESH ----------------
st.markdown("🔄 Auto-refreshing every 5 seconds...")

time.sleep(5)
st.rerun()