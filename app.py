"""
Streamlit AI Demonstration Module
----------------------------------
Entry point for the AI demo interface.
Algorithm visualizations will be added in later steps.
"""

import streamlit as st
import requests

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Factory Maintenance - Demo",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 100%);
        padding: 2rem;
        border-radius: 12px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }
    .status-card {
        background: #f0f7ff;
        border-left: 4px solid #2d6a9f;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .module-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🏭 AI Factory Maintenance Planner</h1>
    <p>AI Demonstration Interface — Algorithms will be visualized here</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/factory.png", width=80)
    st.title("AI Demo Modules")
    st.divider()

    demo_module = st.selectbox("Select Module", [
        "🏠 Overview",
        "🤖 Intelligent Agents (Coming Soon)",
        "🔍 Heuristic Search (Coming Soon)",
        "⚙️ CSP Solver (Coming Soon)",
        "📋 Rule Engine (Coming Soon)",
        "🔄 Dynamic Replanner (Coming Soon)",
    ])

    st.divider()
    st.caption("Step 1: Initial Setup")
    st.caption("AI algorithms — future steps")

# ── Main Content ──────────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📡 Backend Connection Status")

    try:
        response = requests.get("http://localhost:8000/api/health", timeout=3)
        if response.status_code == 200:
            data = response.json()
            st.success(f"✅ Backend is **online** — {data['app']} v{data['version']}")
            st.json(data)
        else:
            st.error(f"⚠️ Backend responded with status {response.status_code}")
    except Exception as e:
        st.warning("⚠️ Backend is not reachable. Start the FastAPI server first.")
        st.code("cd backend\nuvicorn app.main:app --reload", language="bash")

with col2:
    st.subheader("🧠 AI Engine Modules")
    modules = {
        "Intelligent Agents": "pending",
        "Heuristic Search (A*)": "pending",
        "CSP Solver": "pending",
        "Rule Engine": "pending",
        "Scheduler": "pending",
        "Dynamic Replanner": "pending",
    }
    for module, status in modules.items():
        icon = "⏳"
        color = "#fff3cd"
        st.markdown(
            f'<div class="status-card" style="background:{color}">'
            f'{icon} <b>{module}</b> — <i>{status}</i></div>',
            unsafe_allow_html=True
        )

st.divider()
st.info("🚀 **Step 1 Complete** — Project structure and initial architecture set up. AI algorithm modules will be implemented in upcoming steps.")
