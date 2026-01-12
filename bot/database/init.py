import sqlite3
from bot.config import DB_NAME

def init_db() -> None:
    """Initialize the database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            status TEXT DEFAULT 'guest' NOT NULL,
            name TEXT,
            age INTEGER,
            document_photo TEXT
        )
    ''')

    # Verifications table (for pending verifications)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verifications (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            document_photo TEXT,
            activity TEXT NOT NULL,
            status TEXT DEFAULT 'pending' NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    # Check if activity column exists, if not add it
    cursor.execute("PRAGMA table_info(verifications)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    if 'activity' not in column_names:
        cursor.execute('ALTER TABLE verifications ADD COLUMN activity TEXT NOT NULL DEFAULT ""')

    # Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item TEXT NOT NULL,
            price REAL NOT NULL,
            address TEXT NOT NULL,
            status TEXT DEFAULT 'pending' NOT NULL,
            drop_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (drop_id) REFERENCES users (user_id)
        )
    ''')

    # Indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_status ON users (status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_verifications_status ON verifications (status)')

    conn.commit()
    conn.close()