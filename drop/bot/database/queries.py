import sqlite3
from typing import List, Optional, Tuple
from bot.config import DB_NAME
from bot.database.models import User, Verification, Order

def get_connection():
    return sqlite3.connect(DB_NAME)

# User queries
def add_or_update_user(user_id: int, username: Optional[str]) -> None:
    """Add a new user or update existing if username changed."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, status) VALUES (?, ?, ?)', (user_id, username, 'guest'))
    cursor.execute('UPDATE users SET username = ? WHERE user_id = ? AND username != ?', (username, user_id, username))
    conn.commit()
    conn.close()

def get_user(user_id: int) -> Optional[User]:
    """Get user by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, status, name, age, document_photo FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return User(*row)
    return None

def update_user_status(user_id: int, status: str) -> None:
    """Update user status."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET status = ? WHERE user_id = ?', (status, user_id))
    conn.commit()
    conn.close()

# Verification queries
def add_verification(user_id: int, name: str, age: int, document_photo: str, activity: str) -> None:
    """Add a verification request."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO verifications (user_id, name, age, document_photo, activity, status)
        VALUES (?, ?, ?, ?, ?, 'pending')
    ''', (user_id, name, age, document_photo, activity))
    # Also update user status
    cursor.execute('UPDATE users SET status = ?, name = ?, age = ?, document_photo = ? WHERE user_id = ?',
                   ('pending', name, age, document_photo, user_id))
    conn.commit()
    conn.close()

def get_pending_verifications(limit: int = 10) -> List[Verification]:
    """Get pending verification requests."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, name, age, document_photo, activity, status
        FROM verifications
        WHERE status = 'pending'
        ORDER BY user_id DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [Verification(*row) for row in rows]

def update_verification_status(user_id: int, status: str) -> None:
    """Update verification status."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE verifications SET status = ? WHERE user_id = ?', (status, user_id))
    cursor.execute('UPDATE users SET status = ? WHERE user_id = ?', (status, user_id))
    conn.commit()
    conn.close()

# Order queries
def add_order(user_id: int, item: str, price: float, address: str) -> int:
    """Add a new order and return order_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (user_id, item, price, address)
        VALUES (?, ?, ?, ?)
    ''', (user_id, item, price, address))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_pending_orders(limit: int = 20) -> List[Tuple[int, str, float, str, int]]:
    """Get pending orders for drops."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT order_id, item, price, address, user_id
        FROM orders
        WHERE status = 'pending'
        ORDER BY order_id DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_completed_orders(limit: int = 20) -> List[Tuple[int, str, float, str, int]]:
    """Get completed orders for admin."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT order_id, item, price, address, user_id
        FROM orders
        WHERE status = 'completed'
        ORDER BY order_id DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_order(order_id: int) -> Optional[Order]:
    """Get order by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT order_id, user_id, item, price, address, status, drop_id FROM orders WHERE order_id = ?', (order_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return Order(*row)
    return None

def take_order(order_id: int, drop_id: int) -> None:
    """Assign order to a drop."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = 'taken', drop_id = ? WHERE order_id = ?", (drop_id, order_id))
    conn.commit()
    conn.close()

def complete_order(order_id: int) -> None:
    """Mark order as completed."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = 'completed' WHERE order_id = ?", (order_id,))
    conn.commit()
    conn.close()

def restore_order(order_id: int) -> None:
    """Restore order to pending."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = 'pending', drop_id = NULL WHERE order_id = ?", (order_id,))
    conn.commit()
    conn.close()

def get_user_orders(user_id: int) -> List[Order]:
    """Get user's orders."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT order_id, user_id, item, price, address, status, drop_id FROM orders WHERE user_id = ?', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [Order(*row) for row in rows]

def get_active_orders_for_drop(drop_id: int) -> List[Order]:
    """Get active orders for a drop (taken but not completed)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT order_id, user_id, item, price, address, status, drop_id
        FROM orders
        WHERE drop_id = ? AND status = 'taken'
    ''', (drop_id,))
    rows = cursor.fetchall()
    conn.close()
    return [Order(*row) for row in rows]



def get_active_order_for_drop(drop_id: int) -> Optional[Order]:
    """Get active order for a drop (taken but not completed)."""
    orders = get_active_orders_for_drop(drop_id)
    return orders[0] if orders else None

def get_verified_users() -> List[User]:
    """Get all verified users (drops)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, status, name, age, document_photo FROM users WHERE status = "verified"')
    rows = cursor.fetchall()
    conn.close()
    return [User(*row) for row in rows]

def get_user_verification(user_id: int) -> Optional[Verification]:
    """Get verification for user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, name, age, document_photo, activity, status FROM verifications WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return Verification(*row)
    return None