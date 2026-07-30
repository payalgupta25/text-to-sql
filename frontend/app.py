import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# 1. MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="AI SQL Assistant", page_icon="⚡", layout="wide")

# 2. Sidebar Configuration
API_BASE_URL = st.sidebar.text_input("Backend API Base URL", value="http://localhost:8000")

st.title("⚡ Dynamic Text-to-SQL Enterprise Assistant")

# --- STEP 1: Database & Table Selection ---
st.sidebar.header("1. Database Selection")

# Initialize selected_tables to avoid NameError if DB isn't selected or fails to load
selected_tables = None
selected_db = None

try:
    db_response = requests.get(f"{API_BASE_URL}/databases").json()
    available_dbs = db_response.get("databases", [])
except Exception:
    st.error("Failed to connect to the backend server. Make sure FastAPI is running at " + API_BASE_URL)
    st.stop()

if available_dbs:
    selected_db = st.sidebar.selectbox("Select Target Database", options=available_dbs)

if selected_db:
    try:
        tbl_response = requests.get(f"{API_BASE_URL}/databases/{selected_db}/tables").json()
        available_tables = tbl_response.get("tables", [])
        
        selected_tables = st.sidebar.multiselect(
            "Focus Tables (Optional)", 
            options=available_tables,
            default=available_tables,
            help="Limit schema context to specific tables to speed up generation."
        )
    except Exception as e:
        st.sidebar.warning(f"Could not load tables for {selected_db}: {e}")

# --- STEP 2: Natural Language Query ---
if selected_db:
    st.subheader(f"Connected to Database: `{selected_db}`")
    user_prompt = st.text_input(
        "Ask a question about your database:", 
        placeholder="e.g., Show top 5 states with highest median income in 2022"
    )

    if st.button("Run Query", type="primary") and user_prompt:
        with st.spinner("Analyzing schema and generating SQL query..."):
            payload = {
                "db_name": selected_db,
                "question": user_prompt,
                "selected_tables": selected_tables
            }
            
            try:
                res = requests.post(f"{API_BASE_URL}/query", json=payload)
                
                if res.status_code == 200:
                    data = res.json()
                    sql_query = data["sql"]
                    records = data["data"]
                    
                    # Render Code Output
                    st.markdown("### Generated SQL Query")
                    st.code(sql_query, language="sql")
                    
                    df = pd.DataFrame(records)
                    
                    # Render Output Table
                    st.markdown(f"### Results ({len(df)} rows)")
                    st.dataframe(df, use_container_width=True)
                    
                    # Automatic Visualization
                    num_cols = df.select_dtypes(include=['number']).columns.tolist()
                    cat_cols = df.select_dtypes(include=['object']).columns.tolist()
                    
                    if len(num_cols) >= 1 and len(cat_cols) >= 1:
                        st.markdown("### Data Visualization")
                        fig = px.bar(df, x=cat_cols[0], y=num_cols[0], title=f"{num_cols[0]} by {cat_cols[0]}")
                        st.plotly_chart(fig, use_container_width=True)
                        
                else:
                    st.error(f"Error from API: {res.json().get('detail')}")
            except Exception as e:
                st.error(f"Failed to communicate with API backend: {e}")
else:
    st.info("Please select a target database from the sidebar to start asking questions.")