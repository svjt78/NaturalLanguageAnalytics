import os
import time
import sys
import requests
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

# Load environment (for API_BASE)
load_dotenv()
API_BASE = os.getenv("API_BASE", "http://backend:8000")

st.set_page_config(page_title="Autonomous Analytics MVP", layout="wide")
st.title("Autonomous Analytics")

tabs = st.tabs(["Ingest Data", "Metrics Catalogue", "Natural-Language Query"])
tab1, tab2, tab3 = tabs

# --------------------
# Tab 1: Ingest Data
# --------------------
with tab1:
    st.header("1. Ingest CSV / Excel")

    # Ingestion mode selector
    mode = st.radio("Ingestion Mode:", ["create", "replace", "append"])

    # If replace/append, ask for existing table name
    target_table = ""
    if mode in ("replace", "append"):
        target_table = st.text_input("Existing Table Name:")

    # File uploader always run, so uploaded_file is defined
    uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xls", "xlsx"])

    # Kick off ingestion when button pressed
    if st.button("Start Ingestion"):
        if not uploaded_file:
            st.error("Please select a file first.")
        else:
            with st.spinner("Uploading & starting agents..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                data = {"mode": mode, "table_name": target_table or ""}
                try:
                    resp = requests.post(f"{API_BASE}/ingest/", data=data, files=files)
                    resp.raise_for_status()
                except Exception as e:
                    st.error(f"Ingestion start failed: {e}")
                    st.stop()

                info = resp.json()
                run_id = info["run_id"]
                tables = info["tables"]

            st.success(f"Ingestion started (run {run_id[:8]}).")
            placeholder = st.empty()

            # Polling stepper
            all_done = False
            while not all_done:
                try:
                    status_resp = requests.get(f"{API_BASE}/ingest/{run_id}/status")
                    status_resp.raise_for_status()
                except Exception as e:
                    st.error(f"Could not fetch status: {e}")
                    break

                status = status_resp.json()["status"][tables[0]]

                # Render horizontal stepper
                with placeholder.container():
                    cols = st.columns(3)
                    for idx, agent in enumerate(["extractor", "dictionary", "analyst"]):
                        col = cols[idx]
                        col.markdown(f"**{agent.capitalize()}**")
                        s = status[agent]["status"]
                        if s == "pending":
                            col.markdown("⏳ pending")
                        elif s == "running":
                            col.markdown("🔄 running")
                        elif s == "done":
                            col.markdown("✅ done")
                        elif s == "failed":
                            col.markdown("❌ failed")
                            with col.expander("Error details"):
                                col.code(status[agent]["error"])

                states = [status[a]["status"] for a in status]
                if all(s == "done" for s in states) or any(s == "failed" for s in states):
                    all_done = True
                else:
                    time.sleep(1)

            placeholder.empty()
            if any(s == "failed" for s in states):
                st.error("One or more agents failed during ingestion.")
            else:
                st.success("All agents completed successfully!")
                st.experimental_rerun()

# --------------------
# Tab 2: Metrics Catalogue
# --------------------
with tab2:
    st.header("2. Metrics Catalogue")
    try:
        resp = requests.get(f"{API_BASE}/metrics/")
        resp.raise_for_status()
        metrics = resp.json()
        df_metrics = pd.DataFrame(metrics)
        st.dataframe(df_metrics, use_container_width=True)

        if not df_metrics.empty:
            selected = st.selectbox("Select a metric to run:", df_metrics["name"])
            if st.button("Run Metric"):
                metric_id = int(df_metrics[df_metrics["name"] == selected]["id"].iloc[0])
                resp2 = requests.get(f"{API_BASE}/metric/{metric_id}")
                resp2.raise_for_status()
                payload = resp2.json()
                data = pd.DataFrame(payload["data"])
                viz = payload["viz"]

                st.subheader(f"Results for `{selected}`")
                st.dataframe(data, use_container_width=True)

                if viz and viz.get("type"):
                    x = viz.get("x")
                    y = viz.get("y")
                    kind = viz.get("type")
                    if kind == "bar":
                        fig = px.bar(data, x=x, y=y)
                    elif kind == "line":
                        fig = px.line(data, x=x, y=y)
                    else:
                        fig = px.scatter(data, x=x, y=y)
                    st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Failed to fetch metrics: {e}")

# --------------------
# Tab 3: Natural-Language Query
# --------------------
with tab3:
    st.header("3. Natural-Language Query")
    nl_query = st.text_area("Enter your question in plain English", height=120)
    if st.button("Ask"):
        if not nl_query.strip():
            st.error("Please type a question.")
        else:
            with st.spinner("Running NL→SQL…"):
                try:
                    resp = requests.post(
                        f"{API_BASE}/query/",
                        data={"nl_query": nl_query, "user": "streamlit_user"}
                    )
                    resp.raise_for_status()
                    payload = resp.json()
                    sql_used = payload.get("sql")
                    data = pd.DataFrame(payload.get("data", []))

                    st.markdown("**Generated SQL:**")
                    st.code(sql_used, language="sql")
                    st.subheader("Query Results")
                    st.dataframe(data, use_container_width=True)
                except Exception as e:
                    st.error(f"Error: {e}")
