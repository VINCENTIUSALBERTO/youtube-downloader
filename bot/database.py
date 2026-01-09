"""
Database module for YouTube Downloader Bot.

Handles SQLite database operations for users, tokens, and download history.
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)


class Database:
    """SQLite database handler for the bot."""
    
    def __init__(self, db_path: str):
        """Initialize database connection."""
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self) -> None:
        """Initialize database tables."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                tokens INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Download history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                download_type TEXT NOT NULL,
                delivery_method TEXT NOT NULL,
                drive_link TEXT,
                file_size INTEGER,
                duration TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Token transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                description TEXT,
                admin_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    # User operations
    def get_user(self, user_id: int) -> Optional[dict]:
        """Get user by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def create_or_update_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> dict:
        """Create or update user."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        existing = self.get_user(user_id)
        if existing:
            cursor.execute("""
                UPDATE users 
                SET username = COALESCE(?, username),
                    first_name = COALESCE(?, first_name),
                    last_name = COALESCE(?, last_name),
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (username, first_name, last_name, user_id))
        else:
            cursor.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, tokens)
                VALUES (?, ?, ?, ?, 0)
            """, (user_id, username, first_name, last_name))
        
        conn.commit()
        conn.close()
        return self.get_user(user_id)  # type: ignore
    
    def get_user_tokens(self, user_id: int) -> int:
        """Get user token balance."""
        user = self.get_user(user_id)
        return user["tokens"] if user else 0
    
    def add_tokens(
        self,
        user_id: int,
        amount: int,
        admin_id: int,
        description: str = "Token added by admin",
    ) -> int:
        """Add tokens to user account."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Ensure user exists
        self.create_or_update_user(user_id)
        
        # Update token balance
        cursor.execute("""
            UPDATE users 
            SET tokens = tokens + ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (amount, user_id))
        
        # Record transaction
        cursor.execute("""
            INSERT INTO token_transactions 
            (user_id, amount, transaction_type, description, admin_id)
            VALUES (?, ?, 'credit', ?, ?)
        """, (user_id, amount, description, admin_id))
        
        conn.commit()
        conn.close()
        return self.get_user_tokens(user_id)
    
    def use_token(self, user_id: int, description: str = "Token used for download") -> bool:
        """Use one token for download."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        current_tokens = self.get_user_tokens(user_id)
        if current_tokens < 1:
            conn.close()
            return False
        
        # Deduct token
        cursor.execute("""
            UPDATE users 
            SET tokens = tokens - 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (user_id,))
        
        # Record transaction
        cursor.execute("""
            INSERT INTO token_transactions 
            (user_id, amount, transaction_type, description)
            VALUES (?, -1, 'debit', ?)
        """, (user_id, description))
        
        conn.commit()
        conn.close()
        return True
    
    def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned."""
        user = self.get_user(user_id)
        return bool(user and user["is_banned"])
    
    def ban_user(self, user_id: int, banned: bool = True) -> None:
        """Ban or unban a user."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET is_banned = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (1 if banned else 0, user_id))
        conn.commit()
        conn.close()
    
    def get_all_users(self) -> List[dict]:
        """Get all users."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_user_stats(self) -> dict:
        """Get user statistics."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM users")
        total_users = cursor.fetchone()["total"]
        
        cursor.execute("SELECT SUM(tokens) as total FROM users")
        total_tokens = cursor.fetchone()["total"] or 0
        
        cursor.execute("SELECT COUNT(*) as total FROM downloads WHERE status = 'completed'")
        total_downloads = cursor.fetchone()["total"]
        
        conn.close()
        return {
            "total_users": total_users,
            "total_tokens": total_tokens,
            "total_downloads": total_downloads,
        }
    
    # Download history operations
    def create_download(
        self,
        user_id: int,
        url: str,
        download_type: str,
        delivery_method: str,
        title: Optional[str] = None,
    ) -> int:
        """Create download record."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO downloads 
            (user_id, url, title, download_type, delivery_method, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (user_id, url, title, download_type, delivery_method))
        download_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return download_id  # type: ignore
    
    def update_download(
        self,
        download_id: int,
        status: Optional[str] = None,
        drive_link: Optional[str] = None,
        file_size: Optional[int] = None,
        duration: Optional[str] = None,
        title: Optional[str] = None,
    ) -> None:
        """Update download record."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        updates = []
        values = []
        
        if status:
            updates.append("status = ?")
            values.append(status)
            if status == "completed":
                updates.append("completed_at = CURRENT_TIMESTAMP")
        if drive_link:
            updates.append("drive_link = ?")
            values.append(drive_link)
        if file_size:
            updates.append("file_size = ?")
            values.append(file_size)
        if duration:
            updates.append("duration = ?")
            values.append(duration)
        if title:
            updates.append("title = ?")
            values.append(title)
        
        if updates:
            values.append(download_id)
            cursor.execute(
                f"UPDATE downloads SET {', '.join(updates)} WHERE id = ?",
                values,
            )
            conn.commit()
        conn.close()
    
    def get_user_downloads(self, user_id: int, limit: int = 10) -> List[dict]:
        """Get user download history."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM downloads 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (user_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_user_token_history(self, user_id: int, limit: int = 10) -> List[dict]:
        """Get user token transaction history."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM token_transactions 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (user_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
