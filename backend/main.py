import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

from db import fetch_all_databases, fetch_tables_in_db, extract_schema_context, get_db_connection
from llm import generate_sql

load_dotenv("../.env")
app = FastAPI(title="Text-to-SQL API Gateway (Groq Powered)")

class QueryRequest(BaseModel):
    db_name: str
    question: str
    selected_tables: Optional[List[str]] = None

@app.get("/databases")
def get_databases():
    try:
        return {"databases": fetch_all_databases()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/databases/{db_name}/tables")
def get_tables(db_name: str):
    try:
        return {"tables": fetch_tables_in_db(db_name)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
def execute_query(payload: QueryRequest):
    try:
        # Step 1: Schema Context
        schema = extract_schema_context(payload.db_name, payload.selected_tables)
        
        # Step 2: Generate SQL
        sql_query = generate_sql(payload.question, schema)
        
        # Step 3: Direct Execution with PyMySQL
        conn = get_db_connection(payload.db_name)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        
        # Fetch rows and column names explicitly
        rows = cursor.fetchall()
        
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
        else:
            columns = []
            
        cursor.close()
        conn.close()

        # Build DataFrame safely
        # If cursor returned dicts (DictCursor):
        if rows and isinstance(rows[0], dict):
            df = pd.DataFrame(rows)
        else:
            df = pd.DataFrame(rows, columns=columns)
            
        df = df.fillna("")

        return {
            "sql": sql_query,
            "columns": list(df.columns),
            "data": df.to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Execution error: {str(e)}")