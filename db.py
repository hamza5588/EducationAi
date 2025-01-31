# db.py
import sqlite3
from flask import g

def get_db_connection():
    """Create a database connection if it doesn't exist and return it."""
    if 'db' not in g:
        g.db = sqlite3.connect('chat.db')
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Close the database connection."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def get_user_groq_api_key(user_id):
    """Get the Groq API key for a specific user.
    
    Args:
        user_id: The ID of the user
        
    Returns:
        str: The user's Groq API key or None if not found
    """
    try:
        conn = sqlite3.connect('chat.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT groq_api_key FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        
        return result['groq_api_key'] if result else None
    
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()

def initialize_database():
    """Initialize the database with required tables."""
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            useremail TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            class_standard TEXT NOT NULL,
            medium TEXT NOT NULL,
            groq_api_key TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
    ''')
    
    # Create conversations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # Create chat_history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'bot')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

def insert_user(username, useremail, password, class_standard, medium, groq_api_key):
    """Insert a new user into the database."""
    try:
        conn = sqlite3.connect('chat.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (username, useremail, password, class_standard, medium, groq_api_key)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, useremail, password, class_standard, medium, groq_api_key))
        
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error inserting user: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_user_by_email(useremail):
    """Get user details by email."""
    try:
        conn = sqlite3.connect('chat.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE useremail = ?', (useremail,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Error getting user: {e}")
        return None
    finally:
        if conn:
            conn.close()

def update_user_api_key(user_id, new_api_key):
    """Update a user's Groq API key."""
    try:
        conn = sqlite3.connect('chat.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET groq_api_key = ?
            WHERE id = ?
        ''', (new_api_key, user_id))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating API key: {e}")
        return False
    finally:
        if conn:
            conn.close()