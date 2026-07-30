import os
import re
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# 1. Resolve path to root .env dynamically regardless of working directory
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SYSTEM_PROMPT = """
You are a senior database engineer specializing in MySQL.
Generate a syntactically correct MySQL query to answer the user's question based strictly on the provided schema.

Rules:
1. Output ONLY the raw SQL code wrapped in a ```sql ... ``` block.
2. Use standard MySQL syntax (e.g., `LIMIT` for pagination, backticks for column/table identifiers).
3. Do not modify or drop data; only write SELECT queries.
4. If joining tables, use explicit foreign key matches or standard column mappings.
"""

def generate_sql(question: str, schema_context: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing from environment variables. Check your .env file.")

    # Initialize client inside the function to ensure env vars are fully loaded
    client = Groq(api_key=api_key)

    # Query Groq API
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"SCHEMA DEFINITION:\n{schema_context}\n\nUSER QUESTION: {question}"}
        ],
        temperature=0
    )
    
    raw_response = response.choices[0].message.content.strip()
    
    # Extract SQL from markdown blocks
    match = re.search(r"```sql\s*(.*?)\s*```", raw_response, re.DOTALL)
    
    return match.group(1).strip() if match else raw_response