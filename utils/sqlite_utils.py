"""
SQLite utilities for P.U.L.S.E. (Prime Uminda's Learning System Engine)
Provides optimized SQLite database configuration and management
"""

import os
import sqlite3
import structlog
from typing import List, Optional, Dict, Any, Union

# Configure logger
logger = structlog.get_logger("sqlite_utils")

def optimize_sqlite_db(db_path: str, cache_size_kb: int = 5000) -> bool:
    """
    Optimize a SQLite database with WAL mode and other performance settings
    
    Args:
        db_path: Path to the SQLite database file
        cache_size_kb: Cache size in KB (default: 5000)
        
    Returns:
        True if optimization was successful, False otherwise
    """
    try:
        # Check if the database file exists or create it
        if not os.path.exists(db_path):
            logger.info(f"Creating new SQLite database: {db_path}")
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable WAL mode
        cursor.execute("PRAGMA journal_mode=WAL")
        wal_result = cursor.fetchone()[0]
        
        # Set synchronous mode to NORMAL (1) for better performance
        cursor.execute("PRAGMA synchronous=NORMAL")
        
        # Store temp tables in memory
        cursor.execute("PRAGMA temp_store=MEMORY")
        
        # Set cache size
        cursor.execute(f"PRAGMA cache_size={cache_size_kb}")
        
        # Enable memory-mapped I/O
        cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
        
        # Commit changes
        conn.commit()
        
        # Close connection
        conn.close()
        
        logger.info(f"SQLite database optimized: {db_path} (WAL mode: {wal_result})")
        return True
    except Exception as e:
        logger.error(f"Failed to optimize SQLite database {db_path}: {str(e)}")
        return False

def create_table(db_path: str, table_name: str, columns: Dict[str, str], 
                 primary_key: Optional[str] = None, 
                 indexes: Optional[List[Union[str, List[str]]]] = None) -> bool:
    """
    Create a table in a SQLite database if it doesn't exist
    
    Args:
        db_path: Path to the SQLite database file
        table_name: Name of the table to create
        columns: Dictionary of column names and their types
        primary_key: Optional primary key column name
        indexes: Optional list of column names to create indexes on
        
    Returns:
        True if table creation was successful, False otherwise
    """
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Build the CREATE TABLE statement
        column_defs = []
        for col_name, col_type in columns.items():
            if primary_key and col_name == primary_key:
                column_defs.append(f"{col_name} {col_type} PRIMARY KEY")
            else:
                column_defs.append(f"{col_name} {col_type}")
        
        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
        
        # Execute the CREATE TABLE statement
        cursor.execute(create_table_sql)
        
        # Create indexes if specified
        if indexes:
            for idx in indexes:
                if isinstance(idx, list):
                    # Multi-column index
                    idx_name = f"idx_{table_name}_{'_'.join(idx)}"
                    idx_cols = ', '.join(idx)
                    cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name} ({idx_cols})")
                else:
                    # Single-column index
                    idx_name = f"idx_{table_name}_{idx}"
                    cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name} ({idx})")
        
        # Commit changes
        conn.commit()
        
        # Close connection
        conn.close()
        
        logger.info(f"Table {table_name} created or verified in {db_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create table {table_name} in {db_path}: {str(e)}")
        return False

def execute_query(db_path: str, query: str, params: Optional[tuple] = None) -> Dict[str, Any]:
    """
    Execute a query on a SQLite database
    
    Args:
        db_path: Path to the SQLite database file
        query: SQL query to execute
        params: Optional parameters for the query
        
    Returns:
        Dictionary with query results
    """
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        
        # Enable row factory to get results as dictionaries
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Execute the query
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Check if this is a SELECT query
        if query.strip().upper().startswith("SELECT"):
            # Fetch results
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            
            # Close connection
            conn.close()
            
            return {"success": True, "data": results, "count": len(results)}
        else:
            # For non-SELECT queries, commit changes
            conn.commit()
            
            # Get row count for INSERT/UPDATE/DELETE
            row_count = cursor.rowcount
            
            # Get last inserted row ID for INSERT
            last_id = cursor.lastrowid if query.strip().upper().startswith("INSERT") else None
            
            # Close connection
            conn.close()
            
            return {"success": True, "rowcount": row_count, "lastrowid": last_id}
    except Exception as e:
        logger.error(f"Error executing query on {db_path}: {str(e)}")
        return {"success": False, "error": str(e)}

def initialize_chat_history_db(db_path: str = "data/pulse_memory.db") -> bool:
    """
    Initialize the chat history database with necessary tables
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        True if initialization was successful, False otherwise
    """
    try:
        # Optimize the database
        optimize_sqlite_db(db_path)
        
        # Create chat_history table
        create_table(
            db_path=db_path,
            table_name="chat_history",
            columns={
                "id": "INTEGER",
                "user_id": "TEXT",
                "timestamp": "TIMESTAMP",
                "user_input": "TEXT",
                "assistant_response": "TEXT",
                "model": "TEXT",
                "metadata": "TEXT"  # JSON string
            },
            primary_key="id",
            indexes=["user_id", "timestamp", ["user_id", "timestamp"]]
        )
        
        # Create chat_memories table
        create_table(
            db_path=db_path,
            table_name="chat_memories",
            columns={
                "id": "INTEGER",
                "user_id": "TEXT",
                "category": "TEXT",
                "content": "TEXT",
                "timestamp": "TIMESTAMP",
                "metadata": "TEXT"  # JSON string
            },
            primary_key="id",
            indexes=["user_id", "category", "timestamp", ["user_id", "category"]]
        )
        
        # Create chat_vectors table
        create_table(
            db_path=db_path,
            table_name="chat_vectors",
            columns={
                "id": "INTEGER",
                "user_id": "TEXT",
                "chat_id": "INTEGER",
                "text": "TEXT",
                "vector_blob": "BLOB",  # Binary vector data
                "timestamp": "TIMESTAMP"
            },
            primary_key="id",
            indexes=["user_id", "chat_id"]
        )
        
        logger.info(f"Chat history database initialized: {db_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize chat history database: {str(e)}")
        return False
