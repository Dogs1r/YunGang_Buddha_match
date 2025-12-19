import sqlite3
import os

def connect_db(db_path):
    """
    Connect to SQLite database and create table if not exists.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        tuple: (connection, cursor)
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS buddha_face_features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buddha_name TEXT,
            cave_number TEXT,
            image_path TEXT,
            face_feature TEXT,
            style TEXT,
            year TEXT,
            description TEXT,
            history TEXT
        )
    """)
    
    # 检查是否需要添加新列（针对已有数据库的迁移）
    cursor.execute("PRAGMA table_info(buddha_face_features)")
    columns = [info[1] for info in cursor.fetchall()]
    if "description" not in columns:
        cursor.execute("ALTER TABLE buddha_face_features ADD COLUMN description TEXT")
    if "history" not in columns:
        cursor.execute("ALTER TABLE buddha_face_features ADD COLUMN history TEXT")
        
    conn.commit()
    return conn, cursor
    conn.commit()
    return conn, cursor
