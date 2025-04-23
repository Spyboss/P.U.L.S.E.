import sqlite3
import os

# Print current directory
print(f"Current directory: {os.getcwd()}")
print(f"Directory contents: {os.listdir('.')}")

# Check if memory directory exists
if os.path.exists('memory'):
    print(f"Memory directory contents: {os.listdir('memory')}")
else:
    print("Memory directory not found")

# Try to connect to the database
try:
    conn = sqlite3.connect('memory/tasks.db')
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables in database: {tables}")
    
    # For each table, get schema and sample data
    for table in tables:
        table_name = table[0]
        print(f"\nTable: {table_name}")
        
        # Get schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"Columns: {columns}")
        
        # Get sample data (first 5 rows)
        try:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            print(f"Sample data: {rows}")
            
            # Count rows
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"Total rows: {count}")
        except sqlite3.Error as e:
            print(f"Error getting data from {table_name}: {e}")
    
    conn.close()
except Exception as e:
    print(f"Error connecting to database: {e}")
