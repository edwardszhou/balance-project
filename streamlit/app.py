import streamlit as st

trial_page = st.Page("views/aggregate_view.py", title="Aggregate View", default=True)
session_page = st.Page("views/session_view.py", title="Session View")

pg = st.navigation([trial_page, session_page])
pg.run()
