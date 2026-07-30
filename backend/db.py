import os
import pymysql

def get_db_connection(db_name: str = None):
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=db_name,
        connect_timeout=5,
        cursorclass=pymysql.cursors.DictCursor
    )

def fetch_all_databases():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SHOW DATABASES;")
        rows = cursor.fetchall()
    conn.close()
    
    # Exclude system schemas
    system_dbs = {'information_schema', 'mysql', 'performance_schema', 'sys'}
    return [row['Database'] for row in rows if row['Database'] not in system_dbs]

def fetch_tables_in_db(db_name: str):
    conn = get_db_connection(db_name)
    with conn.cursor() as cursor:
        cursor.execute("SHOW TABLES;")
        rows = cursor.fetchall()
    conn.close()
    return [list(row.values())[0] for row in rows]

def extract_schema_context(db_name: str, selected_tables: list = None):
    conn = get_db_connection(db_name)
    with conn.cursor() as cursor:
        if not selected_tables:
            cursor.execute("SHOW TABLES;")
            selected_tables = [list(r.values())[0] for r in cursor.fetchall()]
        
        schema_lines = [f"Database Engine: MySQL\nDatabase Target: {db_name}"]
        for table in selected_tables:
            schema_lines.append(f"\nTable: `{table}`")
            cursor.execute(f"""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s;
            """, (db_name, table))
            
            for col in cursor.fetchall():
                key_info = f", Primary Key" if col['COLUMN_KEY'] == 'PRI' else ""
                schema_lines.append(f"  - `{col['COLUMN_NAME']}` ({col['DATA_TYPE']}{key_info})")
                
    conn.close()
    return "\n".join(schema_lines)