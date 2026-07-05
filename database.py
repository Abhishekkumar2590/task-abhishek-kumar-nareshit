"""
Database setup and models
"""
import sqlite3
from datetime import datetime
from contextlib import contextmanager
import os
from config import DATABASE_FILE


class DatabaseManager:
    """Manages SQLite database operations"""
    
    def __init__(self, db_file=DATABASE_FILE):
        self.db_file = db_file
        self._init_db()
    
    def _init_db(self):
        """Initialize the database with the items table"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def insert_item(self, item):
        """Insert a new item with status=pending"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO items (item, status)
                VALUES (?, ?)
            ''', (item, 'pending'))
            conn.commit()
            return cursor.lastrowid
    
    def update_item_status(self, item, new_status):
        """
        Update the status of an item.
        Only updates a single row to handle duplicate items carefully.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Get the first pending item with this name
            cursor.execute('''
                SELECT id FROM items 
                WHERE item = ? AND status = 'pending'
                ORDER BY created_at ASC
                LIMIT 1
            ''', (item,))
            result = cursor.fetchone()
            
            if result:
                item_id = result[0]
                cursor.execute('''
                    UPDATE items 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (new_status, item_id))
                conn.commit()
                return True
            return False
    
    def get_all_items(self):
        """Get all items from the database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, item, status FROM items ORDER BY id DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_item_by_id(self, item_id):
        """Get a specific item by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, item, status FROM items WHERE id = ?', (item_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def reset_database(self):
        """Reset the database - useful for testing"""
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
        self._init_db()


# Global database manager instance
db = DatabaseManager()
