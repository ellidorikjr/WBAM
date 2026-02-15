import json
from pathlib import Path
import streamlit as st

STATE_FILE = Path("wbam_state.json")

# ---------------------------
# Utility functions
# ---------------------------

def clamp(x, lo=0, hi=10):
    try:
        x = float(x)
    except:
        return lo
    return max(lo, min(hi, x))

def pct(score):
    return int((clamp(score) / 10) * 100)

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {
        "scores": {
            "python": 5,
            "bi": 4,
            "banking": 4,
            "analytical": 5,
            "portfolio": 0
        },
        "notes": "",
        "action_answer": ""
    }

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

# ---------------------------
# App Start
# ---------------------------

st.set_page_config(page_title="WBAM Training App", layout="wide")
st.title("Wealth Banking Analytics Mentor")

state = load_state()

# ---------------------------
# Progress Snapshot
# ---------------------------

st.header("Progress Snapshot")

col1, col2 = st.columns(2)

with col1:
    state["scores"]["python"] = clamp(st.number_input("Python (0-10)", 0.0, 10.0, float(state["scores"]["python"])))
    state["scores"]["bi"] = clamp(st.number_input("BI (0-10)", 0.0, 10.0, float(state["scores"]["bi"])))
    state["scores"]["banking"] = clamp(st.number_input("Banking Knowledge (0-10)", 0.0, 10.0, float(state["scores"]["banking"])))

with col2:
    state["scores"]["analytical"] = clamp(st.number_input("Analytical Thinking (0-10)", 0.0, 10.0, float(state["scores"]["analytical"])))
    state["scores"]["portfolio"] = clamp(st.number_input("Portfolio Strength (0-10)", 0.0, 10.0, float(state["scores"]["portfolio"])))

st.progress(pct(state["scores"]["python"]) / 100)
st.caption("Python readiness level")

st.divider()

# ---------------------------
# Week 1 - Grain Discipline
# ---------------------------

st.header("Week 1 – Data Grain Discipline")

st.subheader("Action Block")

state["action_answer"] = st.text_area(
    "Τι συμβαίνει αν κάνεις merge snapshot με transaction table χωρίς aggregation; Ποια είναι η σωστή διαδικασία;",
    value=state.get("action_answer", ""),
    height=200
)

st.subheader("Technical Notes")
state["notes"] = st.text_area(
    "Write validation logic, grain alignment logic, reconciliation ideas.",
    value=state.get("notes", ""),
    height=200
)

st.divider()

# ---------------------------
# Save Section
# ---------------------------

if st.button("Save Progress"):
    save_state(state)
    st.success("Saved to wbam_state.json")

st.caption("Local storage file: wbam_state.json")
