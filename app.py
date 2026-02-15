import json
from pathlib import Path
from datetime import datetime
import uuid
import streamlit as st

LEDGER_FILE = Path("wbam_ledger.json")

# ============================
# Helpers
# ============================

def now_iso() -> str:
    return datetime.utcnow().isoformat()

def clamp(x, lo=0, hi=10):
    try:
        x = float(x)
    except Exception:
        return lo
    return max(lo, min(hi, x))

def pct(score):
    return int((clamp(score) / 10) * 100)

def new_id() -> str:
    return str(uuid.uuid4())

def empty_ledger():
    return {
        "meta": {
            "app": "WBAM Training App",
            "version": "1.0",
            "created_at": now_iso()
        },
        "sessions": [],      # [{session_id, started_at, topic, module, level}]
        "tasks": [],         # [{task_id, session_id, title, status, difficulty, created_at, completed_at}]
        "scores": [],        # [{score_id, session_id, created_at, python, sql, bi, banking, analytical, business, portfolio}]
        "notes": []          # [{note_id, session_id, created_at, action_answer, technical_notes}]
    }

def load_ledger():
    if LEDGER_FILE.exists():
        return json.loads(LEDGER_FILE.read_text(encoding="utf-8"))
    return empty_ledger()

def save_ledger(ledger):
    LEDGER_FILE.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")

def get_sessions(ledger):
    return sorted(ledger["sessions"], key=lambda s: s["started_at"], reverse=True)

def get_session_by_id(ledger, session_id):
    for s in ledger["sessions"]:
        if s["session_id"] == session_id:
            return s
    return None

def get_tasks_for_session(ledger, session_id):
    tasks = [t for t in ledger["tasks"] if t["session_id"] == session_id]
    return sorted(tasks, key=lambda t: t["created_at"], reverse=True)

def latest_scores_for_session(ledger, session_id):
    rows = [r for r in ledger["scores"] if r["session_id"] == session_id]
    if not rows:
        return None
    return sorted(rows, key=lambda r: r["created_at"], reverse=True)[0]

def next_objective_from_tasks(tasks):
    # priority: doing > todo > none
    doing = [t for t in tasks if t["status"] == "doing"]
    todo = [t for t in tasks if t["status"] == "todo"]
    if doing:
        return f"Continue: {doing[0]['title']}"
    if todo:
        return f"Start: {todo[0]['title']}"
    return "No pending tasks. Create the next technical task."

def upsert_latest_note(ledger, session_id, action_answer, technical_notes):
    # keep history (append), but also easy to find latest
    ledger["notes"].append({
        "note_id": new_id(),
        "session_id": session_id,
        "created_at": now_iso(),
        "action_answer": action_answer,
        "technical_notes": technical_notes
    })

# ============================
# UI
# ============================

st.set_page_config(page_title="WBAM Training App", layout="wide")
st.title("Wealth Banking Analytics Mentor — Training App (Ledger)")

ledger = load_ledger()

tabs = st.tabs(["Session", "Tasks", "Scores", "Week 1", "Export / Import"])

# ============================
# Session Tab
# ============================
with tabs[0]:
    st.header("Session Control Center")

    sessions = get_sessions(ledger)
    if sessions:
        session_options = [f"{s['started_at'][:19]} | {s.get('module','M0')} L{s.get('level',1)} | {s.get('topic','')}" for s in sessions]
        selected_idx = st.selectbox("Select session", list(range(len(sessions))), format_func=lambda i: session_options[i])
        session_id = sessions[selected_idx]["session_id"]
    else:
        session_id = None
        st.info("No sessions yet. Create your first session.")

    st.divider()
    st.subheader("Create new session")

    c1, c2, c3 = st.columns([2, 1, 1])
    topic = c1.text_input("Topic", placeholder="e.g., Data grain discipline, cohort analysis, SQL joins")
    module = c2.text_input("Module", value="M0")
    level = c3.selectbox("Level", [1, 2, 3], index=0)

    if st.button("Create Session"):
        sid = new_id()
        ledger["sessions"].append({
            "session_id": sid,
            "started_at": now_iso(),
            "topic": topic.strip(),
            "module": module.strip(),
            "level": int(level)
        })
        save_ledger(ledger)
        st.success(f"Session created: {sid}")
        st.rerun()

    st.divider()

    if session_id:
        s = get_session_by_id(ledger, session_id)
        tasks = get_tasks_for_session(ledger, session_id)
        next_obj = next_objective_from_tasks(tasks)

        st.subheader("Snapshot")
        st.write(f"**Session:** `{session_id}`")
        st.write(f"**Topic:** {s.get('topic','')}")
        st.write(f"**Module/Level:** {s.get('module','')} / L{s.get('level',1)}")
        st.write(f"**Next objective:** {next_obj}")

        # show a quick readiness bar from latest score snapshot if exists
        latest = latest_scores_for_session(ledger, session_id)
        if latest:
            st.progress(pct(latest["python"]) / 100)
            st.caption("Python readiness (latest snapshot)")
        else:
            st.caption("No score snapshot yet for this session.")

# ============================
# Tasks Tab
# ============================
with tabs[1]:
    st.header("Tasks Ledger")

    sessions = get_sessions(ledger)
    if not sessions:
        st.info("Create a session first.")
    else:
        session_options = [f"{s['started_at'][:19]} | {s.get('module','M0')} L{s.get('level',1)} | {s.get('topic','')}" for s in sessions]
        sel = st.selectbox("Session", list(range(len(sessions))), format_func=lambda i: session_options[i], key="tasks_session")
        session_id = sessions[sel]["session_id"]

        st.subheader("Add task")
        t1, t2, t3 = st.columns([3, 1, 1])
        title = t1.text_input("Task title", placeholder="e.g., Implement grain check + aggregation before merge")
        difficulty = t2.selectbox("Difficulty", [1, 2, 3], index=0)
        status = t3.selectbox("Status", ["todo", "doing", "done"], index=0)

        if st.button("Add Task"):
            if not title.strip():
                st.error("Task title is required.")
            else:
                ledger["tasks"].append({
                    "task_id": new_id(),
                    "session_id": session_id,
                    "title": title.strip(),
                    "status": status,
                    "difficulty": int(difficulty),
                    "created_at": now_iso(),
                    "completed_at": now_iso() if status == "done" else None
                })
                save_ledger(ledger)
                st.success("Task added.")
                st.rerun()

        st.divider()
        st.subheader("Update task status")

        tasks = get_tasks_for_session(ledger, session_id)
        if not tasks:
            st.caption("No tasks yet.")
        else:
            # pick task
            task_labels = [f"{t['created_at'][:19]} | {t['status'].upper()} | D{t['difficulty']} | {t['title']}" for t in tasks]
            tidx = st.selectbox("Select task", list(range(len(tasks))), format_func=lambda i: task_labels[i])
            task = tasks[tidx]

            new_status = st.selectbox("New status", ["todo", "doing", "done"], index=["todo","doing","done"].index(task["status"]))
            if st.button("Apply Status"):
                for t in ledger["tasks"]:
                    if t["task_id"] == task["task_id"]:
                        t["status"] = new_status
                        t["completed_at"] = now_iso() if new_status == "done" else None
                        break
                save_ledger(ledger)
                st.success("Status updated.")
                st.rerun()

            st.divider()
            st.subheader("Tasks table")
            st.dataframe(tasks, use_container_width=True)

# ============================
# Scores Tab
# ============================
with tabs[2]:
    st.header("Skill Score Snapshots")

    sessions = get_sessions(ledger)
    if not sessions:
        st.info("Create a session first.")
    else:
        session_options = [f"{s['started_at'][:19]} | {s.get('module','M0')} L{s.get('level',1)} | {s.get('topic','')}" for s in sessions]
        sel = st.selectbox("Session", list(range(len(sessions))), format_func=lambda i: session_options[i], key="scores_session")
        session_id = sessions[sel]["session_id"]

        st.subheader("Add snapshot (0–10)")
        # defaults: last snapshot if exists, else baseline
        last = latest_scores_for_session(ledger, session_id) or {
            "python": 5, "sql": 3, "bi": 4, "banking": 3, "analytical": 5, "business": 4, "portfolio": 0
        }

        c1, c2, c3, c4 = st.columns(4)
        python_score = clamp(c1.number_input("Python", 0.0, 10.0, float(last["python"])))
        sql_score = clamp(c2.number_input("SQL", 0.0, 10.0, float(last["sql"])))
        bi_score = clamp(c3.number_input("BI", 0.0, 10.0, float(last["bi"])))
        banking_score = clamp(c4.number_input("Banking", 0.0, 10.0, float(last["banking"])))

        c5, c6, c7 = st.columns(3)
        analytical_score = clamp(c5.number_input("Analytical", 0.0, 10.0, float(last["analytical"])))
        business_score = clamp(c6.number_input("Business", 0.0, 10.0, float(last["business"])))
        portfolio_score = clamp(c7.number_input("Portfolio", 0.0, 10.0, float(last["portfolio"])))

        if st.button("Save snapshot"):
            ledger["scores"].append({
                "score_id": new_id(),
                "session_id": session_id,
                "created_at": now_iso(),
                "python": python_score,
                "sql": sql_score,
                "bi": bi_score,
                "banking": banking_score,
                "analytical": analytical_score,
                "business": business_score,
                "portfolio": portfolio_score
            })
            save_ledger(ledger)
            st.success("Snapshot saved.")
            st.rerun()

        st.divider()
        st.subheader("History (latest first)")
        rows = sorted([r for r in ledger["scores"] if r["session_id"] == session_id], key=lambda r: r["created_at"], reverse=True)
        st.dataframe(rows, use_container_width=True)

# ============================
# Week 1 Tab (Your original prompt, but ledgered)
# ============================
with tabs[3]:
    st.header("Week 1 — Data Grain Discipline (Ledgered)")

    sessions = get_sessions(ledger)
    if not sessions:
        st.info("Create a session first (topic: Week 1 – Data Grain Discipline).")
    else:
        session_options = [f"{s['started_at'][:19]} | {s.get('module','M0')} L{s.get('level',1)} | {s.get('topic','')}" for s in sessions]
        sel = st.selectbox("Session", list(range(len(sessions))), format_func=lambda i: session_options[i], key="week1_session")
        session_id = sessions[sel]["session_id"]

        st.subheader("Action Block")
        action_answer = st.text_area(
            "Τι συμβαίνει αν κάνεις merge snapshot με transaction table χωρίς aggregation; Ποια είναι η σωστή διαδικασία;",
            value="",
            height=180
        )

        st.subheader("Technical Notes")
        technical_notes = st.text_area(
            "Write validation logic, grain alignment logic, reconciliation ideas.",
            value="",
            height=180
        )

        if st.button("Save Week 1 Notes to Ledger"):
            upsert_latest_note(ledger, session_id, action_answer, technical_notes)
            # also ensure there is at least one task representing this exercise
            if not any(t for t in ledger["tasks"] if t["session_id"] == session_id and t["title"].startswith("Week 1: Data Grain Discipline")):
                ledger["tasks"].append({
                    "task_id": new_id(),
                    "session_id": session_id,
                    "title": "Week 1: Data Grain Discipline — write correct merge/aggregation procedure",
                    "status": "doing",
                    "difficulty": 1,
                    "created_at": now_iso(),
                    "completed_at": None
                })
            save_ledger(ledger)
            st.success("Saved notes + ensured Week 1 task exists.")
            st.rerun()

        st.divider()
        st.subheader("Notes history (latest first)")
        notes = sorted([n for n in ledger["notes"] if n["session_id"] == session_id], key=lambda n: n["created_at"], reverse=True)
        st.dataframe(notes, use_container_width=True)

# ============================
# Export / Import Tab
# ============================
with tabs[4]:
    st.header("Export / Import — Absolute Record")

    st.warning(
        "Για 100% αξιοπιστία στο Streamlit Cloud: κάνε Export στο τέλος κάθε session και κράτα το JSON."
    )

    export_str = json.dumps(ledger, ensure_ascii=False, indent=2)
    st.download_button(
        label="Download wbam_ledger.json",
        data=export_str.encode("utf-8"),
        file_name="wbam_ledger.json",
        mime="application/json"
    )

    st.divider()
    uploaded = st.file_uploader("Upload wbam_ledger.json to restore", type=["json"])
    if uploaded is not None:
        try:
            incoming = json.loads(uploaded.read().decode("utf-8"))
            # minimal schema check
            required = {"sessions", "tasks", "scores", "notes", "meta"}
            if not required.issubset(set(incoming.keys())):
                st.error("Invalid ledger format (missing keys).")
            else:
                ledger = incoming
                save_ledger(ledger)
                st.success("Ledger imported and saved.")
                st.rerun()
        except Exception as e:
            st.error(f"Failed to import: {e}")

    st.divider()
    if st.button("Reset ledger (danger)"):
        ledger = empty_ledger()
        save_ledger(ledger)
        st.success("Ledger reset.")
        st.rerun()

st.caption(f"Ledger file: {LEDGER_FILE.name}")
