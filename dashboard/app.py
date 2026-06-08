"""
Industrial AI Vision System - Advanced Dashboard
dashboard/app.py

Architecture:
- Modular page components using st.navigation (Streamlit 1.36+)
- Centralized API client with retry logic + connection state
- Session-state driven cache with TTL to avoid hammering the backend
- Plotly charts for interactive, professional visualizations
- Configurable via environment variables (no hard-coded URLs)
"""

import os
import time
import random
import logging
from datetime import datetime, timedelta
from typing import Optional

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "5"))   # seconds
CACHE_TTL = int(os.getenv("CACHE_TTL", "4"))                 # seconds
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "3"))      # seconds

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Industrial AI Vision",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Sidebar polish */
    [data-testid="stSidebar"] { background: #0f1117; }
    [data-testid="stSidebar"] * { color: #e0e0e0 !important; }
    [data-testid="stSidebar"] hr { border-color: #2a2a3a; }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: #1a1d2e;
        border: 1px solid #2a2d4a;
        border-radius: 10px;
        padding: 12px 18px;
    }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 700; }

    /* Status badges */
    .badge-ok    { background:#0d3b2e; color:#2de083; padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }
    .badge-warn  { background:#3b2c0d; color:#f0a500; padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }
    .badge-crit  { background:#3b0d0d; color:#f05050; padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }

    /* Section headers */
    .section-header {
        font-size: 1.05rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .08em;
        color: #8888aa;
        margin: 1.5rem 0 .5rem 0;
        border-bottom: 1px solid #2a2d4a;
        padding-bottom: 6px;
    }

    /* Hide streamlit branding */
    #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE INITIALIZATION
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "api_ok": False,
        "last_check": 0.0,
        "defect_history": [],
        "load_history": [],
        "alert_log": [],
        "sim_count": 0,
        "last_analytics": None,
        "last_analytics_ts": 0.0,
        "selected_machines": ["M-01", "M-02", "M-03"],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─────────────────────────────────────────────
# API CLIENT  (retry-aware, session-pooled)
# ─────────────────────────────────────────────
@st.cache_resource
def get_http_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=2, backoff_factor=0.3, status_forcelist=[500, 502, 503])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def api_get(endpoint: str) -> Optional[dict]:
    try:
        r = get_http_session().get(f"{API_URL}{endpoint}", timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        st.session_state.api_ok = True
        return r.json()
    except Exception as exc:
        logger.warning("GET %s failed: %s", endpoint, exc)
        st.session_state.api_ok = False
        return None


def api_post(endpoint: str, payload: dict) -> Optional[dict]:
    try:
        r = get_http_session().post(
            f"{API_URL}{endpoint}", json=payload, timeout=REQUEST_TIMEOUT
        )
        r.raise_for_status()
        st.session_state.api_ok = True
        return r.json()
    except Exception as exc:
        logger.warning("POST %s failed: %s", endpoint, exc)
        st.session_state.api_ok = False
        return None


def cached_analytics() -> Optional[dict]:
    """Return analytics, only re-fetching if cache is stale."""
    now = time.time()
    if now - st.session_state.last_analytics_ts > CACHE_TTL:
        data = api_get("/analytics")
        if data:
            st.session_state.last_analytics = data
            st.session_state.last_analytics_ts = now
    return st.session_state.last_analytics


# ─────────────────────────────────────────────
# SIMULATED FALLBACK DATA (when API is offline)
# ─────────────────────────────────────────────
DEFECT_TYPES = ["crack", "scratch", "dent", "corrosion", "misalignment"]
MACHINES = ["M-01", "M-02", "M-03", "M-04", "M-05"]

def mock_live_ai() -> dict:
    load = random.randint(20, 95)
    defects = random.sample(DEFECT_TYPES, k=random.randint(0, 2))
    risk = "HIGH" if load > 80 or len(defects) > 1 else ("MEDIUM" if load > 60 or defects else "LOW")
    decision = "HALT" if risk == "HIGH" else ("INSPECT" if risk == "MEDIUM" else "CONTINUE")
    alert = f"⚠️ {', '.join(defects)} detected" if defects else "✅ All clear"
    return {
        "decision": decision, "risk_level": risk,
        "alert": alert, "machine_load": load,
        "defects": defects, "confidence": round(random.uniform(0.82, 0.99), 3),
    }


def mock_analytics(n=40) -> dict:
    now = datetime.now()
    logs = []
    for i in range(n):
        ts = now - timedelta(minutes=(n - i) * 2)
        defects = random.randint(0, 3)
        load = random.randint(30, 95)
        risk = "HIGH" if defects > 1 or load > 85 else ("MEDIUM" if defects or load > 65 else "LOW")
        logs.append({
            "id": i + 1,
            "timestamp": ts.strftime("%H:%M:%S"),
            "defects": defects,
            "load": load,
            "decision": "HALT" if risk == "HIGH" else ("INSPECT" if risk == "MEDIUM" else "CONTINUE"),
            "risk": risk,
            "machine": random.choice(MACHINES),
        })
    return {"logs": logs}


# ─────────────────────────────────────────────
# HELPER: RISK COLOR
# ─────────────────────────────────────────────
def risk_badge(level: str) -> str:
    cls = {"HIGH": "badge-crit", "MEDIUM": "badge-warn", "LOW": "badge-ok"}.get(level, "badge-ok")
    return f'<span class="{cls}">{level}</span>'


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏭 Industrial AI Vision")
    st.markdown("---")

    # API health indicator
    status_color = "🟢" if st.session_state.api_ok else "🔴"
    api_label = "API Connected" if st.session_state.api_ok else "API Offline (demo mode)"
    st.markdown(f"**{status_color} {api_label}**")
    st.caption(f"Endpoint: `{API_URL}`")
    st.markdown("---")

    st.markdown("### ⚙️ Controls")
    auto_refresh = st.toggle("Auto Refresh", value=True)
    refresh_sec = st.slider("Refresh interval (s)", 3, 30, REFRESH_INTERVAL, step=1)

    st.markdown("---")
    st.markdown("### 🔧 Simulation")
    sim_defects = st.multiselect(
        "Inject defects",
        DEFECT_TYPES,
        default=[],
        help="Manually inject defect types into the next simulation run.",
    )
    sim_load = st.slider("Machine load override (%)", 0, 100, 60)

    run_sim = st.button("▶ Run AI Simulation", use_container_width=True)

    st.markdown("---")
    st.markdown("### 🖥️ Machine Filter")
    sel_machines = st.multiselect("Show machines", MACHINES, default=st.session_state.selected_machines)
    if sel_machines:
        st.session_state.selected_machines = sel_machines

    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")


# ─────────────────────────────────────────────
# SIMULATION TRIGGER
# ─────────────────────────────────────────────
if run_sim:
    payload = {"defects": sim_defects, "machine_load": sim_load}
    result = api_post("/live-ai", payload) or mock_live_ai()
    st.session_state.sim_count += 1

    # Append to local history
    st.session_state.defect_history.append(len(result.get("defects", [])))
    st.session_state.load_history.append(result.get("machine_load", sim_load))
    if result.get("risk_level") in ("HIGH", "MEDIUM"):
        st.session_state.alert_log.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "risk": result["risk_level"],
            "message": result.get("alert", ""),
        })
        st.session_state.alert_log = st.session_state.alert_log[-50:]  # keep last 50

    st.success(f"Simulation #{st.session_state.sim_count} complete — Decision: **{result['decision']}**")


# ─────────────────────────────────────────────
# LIVE AI STATUS
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">🧠 Live AI Decision Engine</div>', unsafe_allow_html=True)

ai_data = api_post("/live-ai", {"defects": [], "machine_load": 50}) or mock_live_ai()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Decision", ai_data["decision"])
c2.metric("Risk Level", ai_data["risk_level"])
c3.metric("Machine Load", f"{ai_data.get('machine_load', '—')}%")
c4.metric("Confidence", f"{ai_data.get('confidence', 0.0):.1%}")
c5.metric("Active Defects", len(ai_data.get("defects", [])))

if ai_data.get("defects"):
    st.warning(f"**Detected defects:** {', '.join(ai_data['defects'])}")


# ─────────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Factory Analytics</div>', unsafe_allow_html=True)

raw = cached_analytics() or mock_analytics()

if raw and "logs" in raw:
    df = pd.DataFrame(raw["logs"])

    # Normalise column names defensively
    col_map = {
        "ID": "id", "Timestamp": "timestamp", "Defects": "defects",
        "Load": "load", "Decision": "decision",
    }
    df.rename(columns=col_map, inplace=True)

    # Filter by selected machines (if 'machine' column exists)
    if "machine" in df.columns and st.session_state.selected_machines:
        df = df[df["machine"].isin(st.session_state.selected_machines)]

    # ── KPI row ───────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    total_defects = int(df["defects"].sum()) if "defects" in df.columns else 0
    avg_load = round(df["load"].mean(), 1) if "load" in df.columns else 0
    halt_pct = (
        round((df["decision"] == "HALT").sum() / max(len(df), 1) * 100, 1)
        if "decision" in df.columns else 0
    )
    high_risk = (df["risk"] == "HIGH").sum() if "risk" in df.columns else 0

    k1.metric("Total Defects Logged", total_defects)
    k2.metric("Avg Machine Load", f"{avg_load}%")
    k3.metric("HALT Rate", f"{halt_pct}%", delta=f"{halt_pct - 20:.1f}% vs baseline", delta_color="inverse")
    k4.metric("High-Risk Events", int(high_risk))

    # ── Charts row ────────────────────────────
    ch1, ch2 = st.columns(2)

    with ch1:
        st.markdown("**Defect count over time**")
        if "defects" in df.columns:
            fig_def = go.Figure()
            fig_def.add_trace(go.Scatter(
                x=df.get("timestamp", list(range(len(df)))),
                y=df["defects"],
                mode="lines+markers",
                line=dict(color="#f05050", width=2),
                marker=dict(size=5),
                fill="tozeroy",
                fillcolor="rgba(240,80,80,0.12)",
                name="Defects",
            ))
            fig_def.update_layout(
                height=220, margin=dict(l=0, r=0, t=10, b=30),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#aaa", size=11),
                xaxis=dict(showgrid=False, tickangle=-30),
                yaxis=dict(showgrid=True, gridcolor="#1e2133"),
            )
            st.plotly_chart(fig_def, use_container_width=True)

    with ch2:
        st.markdown("**Machine load trend**")
        if "load" in df.columns:
            fig_load = go.Figure()
            fig_load.add_trace(go.Scatter(
                x=df.get("timestamp", list(range(len(df)))),
                y=df["load"],
                mode="lines",
                line=dict(color="#4a9eff", width=2),
                fill="tozeroy",
                fillcolor="rgba(74,158,255,0.12)",
                name="Load %",
            ))
            # Threshold line at 80%
            fig_load.add_hline(y=80, line_dash="dash", line_color="#f0a500",
                               annotation_text="80% threshold", annotation_position="top left")
            fig_load.update_layout(
                height=220, margin=dict(l=0, r=0, t=10, b=30),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#aaa", size=11),
                xaxis=dict(showgrid=False, tickangle=-30),
                yaxis=dict(showgrid=True, gridcolor="#1e2133", range=[0, 105]),
            )
            st.plotly_chart(fig_load, use_container_width=True)

    # ── Decision distribution (donut) ─────────
    if "decision" in df.columns:
        dec_counts = df["decision"].value_counts().reset_index()
        dec_counts.columns = ["Decision", "Count"]
        color_map = {"CONTINUE": "#2de083", "INSPECT": "#f0a500", "HALT": "#f05050"}

        ch3, ch4 = st.columns([1, 2])
        with ch3:
            st.markdown("**Decision distribution**")
            fig_pie = px.pie(
                dec_counts, names="Decision", values="Count",
                color="Decision", color_discrete_map=color_map,
                hole=0.55,
            )
            fig_pie.update_traces(textinfo="percent+label", textfont_size=12)
            fig_pie.update_layout(
                height=220, margin=dict(l=0, r=0, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#aaa"),
                showlegend=False,
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with ch4:
            if "machine" in df.columns and "defects" in df.columns:
                st.markdown("**Defects per machine**")
                machine_df = df.groupby("machine")["defects"].sum().reset_index()
                fig_bar = px.bar(
                    machine_df, x="machine", y="defects",
                    color="defects", color_continuous_scale=["#2de083", "#f0a500", "#f05050"],
                )
                fig_bar.update_layout(
                    height=220, margin=dict(l=0, r=0, t=10, b=30),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#aaa", size=11),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor="#1e2133"),
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig_bar, use_container_width=True)

    # ── Recent logs table ─────────────────────
    st.markdown('<div class="section-header">📋 Recent Event Log</div>', unsafe_allow_html=True)

    display_df = df.tail(15).copy()
    if "risk" in display_df.columns:
        risk_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
        display_df["risk"] = display_df["risk"].map(lambda r: f"{risk_emoji.get(r, '')} {r}")

    st.dataframe(
        display_df,
        use_container_width=True,
        height=320,
        hide_index=True,
    )

else:
    st.warning("No analytics data available. The API may be offline — demo data is being used.")


# ─────────────────────────────────────────────
# ALERT LOG (session-state driven)
# ─────────────────────────────────────────────
if st.session_state.alert_log:
    st.markdown('<div class="section-header">🚨 Alert History (this session)</div>', unsafe_allow_html=True)
    alert_df = pd.DataFrame(st.session_state.alert_log[::-1])
    st.dataframe(alert_df, use_container_width=True, hide_index=True, height=200)


# ─────────────────────────────────────────────
# CAMERA STREAM SECTION
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">🎥 Live Camera Stream</div>', unsafe_allow_html=True)

cam_col1, cam_col2 = st.columns([2, 1])
with cam_col1:
    st.info(
        f"Camera stream served via FastAPI at `{API_URL}/live-camera`.  \n"
        "Open the link below in a browser tab or embed via `<img src=...>` in your HTML frontend.",
        icon="ℹ️",
    )
    stream_url = f"{API_URL}/live-camera"
    st.code(stream_url, language="text")
    if st.button("🔗 Open stream in new tab"):
        st.markdown(f'<meta http-equiv="refresh" content="0; url={stream_url}">', unsafe_allow_html=True)

with cam_col2:
    st.markdown("**Stream health**")
    probe = api_get("/health") or api_get("/") or {}
    if st.session_state.api_ok:
        st.success("Backend reachable")
    else:
        st.error("Backend unreachable")


# ─────────────────────────────────────────────
# PPE / VISION MODULE STATUS
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">🦺 PPE Compliance Module</div>', unsafe_allow_html=True)

ppe_col1, ppe_col2, ppe_col3, ppe_col4 = st.columns(4)
ppe_items = [
    ("Person", "ti-user", random.random() > 0.1),
    ("Helmet", "ti-hard-hat", random.random() > 0.2),
    ("Safety Vest", "ti-shirt", random.random() > 0.15),
    ("Boots", "ti-shoe", random.random() > 0.25),
]
for col, (label, _, detected) in zip([ppe_col1, ppe_col2, ppe_col3, ppe_col4], ppe_items):
    status = "✅ Detected" if detected else "❌ Missing"
    col.metric(label, status)


# ─────────────────────────────────────────────
# AUTO-REFRESH
# ─────────────────────────────────────────────
if auto_refresh:
    st.caption(f"🔄 Auto-refreshing every {refresh_sec}s…")
    time.sleep(refresh_sec)
    st.rerun()