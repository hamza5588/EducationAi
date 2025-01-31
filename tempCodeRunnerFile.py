import sqlite3
import os
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseInitializer:
    def __init__(self, db_name='chat.db'):
        self.db_name = db_name
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            logger.info("Database connection established")
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def create_tables(self):
        """Create all required tables"""
        try:
            # Create users table
            self.cursor.execute('''
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
            self.cursor.execute('''
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

            # Create chat history table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'bot')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
            ''')

            # Create indexes for better performance
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_history_conversation_id ON chat_history(conversation_id)')
            
            logger.info("Tables created successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}")
            raise

    def validate_database(self):
        """Validate database structure"""
        try:
            # Check if all tables exist
            tables = ['users', 'conversations', 'chat_history']
            for table in tables:
                self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                if not self.cursor.fetchone():
                    raise Exception(f"Table {table} was not created properly")

            # Verify table structures
            self.cursor.execute("PRAGMA foreign_key_check")
            if self.cursor.fetchall():
                raise Exception("Foreign key constraints are not valid")

            logger.info("Database validation completed successfully")
            
        except (sqlite3.Error, Exception) as e:
            logger.error(f"Database validation failed: {e}")
            raise

    def initialize_database(self):
        """Main initialization method"""
        try:
            # Remove existing database if it exists
            if os.path.exists(self.db_name):
                os.remove(self.db_name)
                logger.info(f"Removed existing database: {self.db_name}")

            # Connect to database
            self.connect()

            # Enable foreign key support
            self.cursor.execute("PRAGMA foreign_keys = ON")

            # Create tables
            self.create_tables()

            # Validate database
            self.validate_database()

            # Commit changes
            self.conn.commit()
            logger.info("Database initialized successfully")

        except (sqlite3.Error, Exception) as e:
            if self.conn:
                self.conn.rollback()
            logger.error(f"Database initialization failed: {e}")
            raise

        finally:
            if self.conn:
                self.conn.close()
                logger.info("Database connection closed")

def main():
    try:
        initializer = DatabaseInitializer()
        initializer.initialize_database()
        print("Database setup completed successfully!")
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        exit(1)

if __name__ == "__main__":
    main()