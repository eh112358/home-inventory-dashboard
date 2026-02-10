from contextlib import contextmanager
import sqlite3
from config import Config

def get_db():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db_connection():
    """Context manager for database connections with automatic commit/rollback."""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def migrate_remove_duplicates(cursor):
    """Remove duplicate consumable_types and rebuild table with UNIQUE constraint."""
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='consumable_types'")
    if not cursor.fetchone():
        return  # Table doesn't exist yet, no migration needed

    # Check if duplicates exist
    cursor.execute('''
        SELECT category_id, name, COUNT(*) as cnt
        FROM consumable_types
        GROUP BY category_id, name
        HAVING cnt > 1
    ''')
    if not cursor.fetchone():
        return  # No duplicates, no migration needed

    print("Migrating: Removing duplicate consumable_types...")

    # Create new table with unique constraint
    cursor.execute('DROP TABLE IF EXISTS consumable_types_new')
    cursor.execute('''
        CREATE TABLE consumable_types_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            unit TEXT NOT NULL DEFAULT 'units',
            default_usage_rate REAL NOT NULL DEFAULT 1.0,
            usage_rate_period TEXT NOT NULL DEFAULT 'week',
            min_stock_level REAL NOT NULL DEFAULT 1.0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id),
            UNIQUE(category_id, name)
        )
    ''')

    # Copy unique records (keeping the first occurrence by using MIN(id))
    cursor.execute('''
        INSERT INTO consumable_types_new
            (category_id, name, unit, default_usage_rate, usage_rate_period, min_stock_level, notes, created_at)
        SELECT category_id, name, unit, default_usage_rate, usage_rate_period, min_stock_level, notes, created_at
        FROM consumable_types
        WHERE id IN (
            SELECT MIN(id) FROM consumable_types GROUP BY category_id, name
        )
    ''')

    # Get IDs to keep (first occurrence of each item)
    cursor.execute('''
        SELECT MIN(id) as keep_id, category_id, name
        FROM consumable_types
        GROUP BY category_id, name
    ''')
    items_to_keep = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

    # Delete duplicate entries using parameterized queries (safe from SQL injection)
    ids = list(items_to_keep.keys())
    if ids:
        placeholders = ','.join('?' * len(ids))
        cursor.execute(f'''
            DELETE FROM inventory
            WHERE consumable_type_id NOT IN ({placeholders})
        ''', ids)

        cursor.execute(f'''
            DELETE FROM purchases
            WHERE consumable_type_id NOT IN ({placeholders})
        ''', ids)

        cursor.execute(f'''
            DELETE FROM usage_log
            WHERE consumable_type_id NOT IN ({placeholders})
        ''', ids)

    # Now build ID mapping from old kept IDs to new IDs
    cursor.execute('SELECT id, category_id, name FROM consumable_types_new')
    new_items = {(row[1], row[2]): row[0] for row in cursor.fetchall()}

    # Update references for kept items to new IDs
    for old_id, (cat_id, name) in items_to_keep.items():
        new_id = new_items.get((cat_id, name))
        if new_id and old_id != new_id:
            cursor.execute('UPDATE inventory SET consumable_type_id = ? WHERE consumable_type_id = ?', (new_id, old_id))
            cursor.execute('UPDATE purchases SET consumable_type_id = ? WHERE consumable_type_id = ?', (new_id, old_id))
            cursor.execute('UPDATE usage_log SET consumable_type_id = ? WHERE consumable_type_id = ?', (new_id, old_id))

    # Drop old table and rename new one
    cursor.execute('DROP TABLE consumable_types')
    cursor.execute('ALTER TABLE consumable_types_new RENAME TO consumable_types')

    print("Migration complete: Duplicates removed.")

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Run migration to fix duplicates if needed
    migrate_remove_duplicates(cursor)
    conn.commit()

    # Categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            icon TEXT DEFAULT '📦'
        )
    ''')

    # Consumable types table (with UNIQUE constraint to prevent duplicates)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consumable_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            unit TEXT NOT NULL DEFAULT 'units',
            default_usage_rate REAL NOT NULL DEFAULT 1.0,
            usage_rate_period TEXT NOT NULL DEFAULT 'week',
            min_stock_level REAL NOT NULL DEFAULT 1.0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id),
            UNIQUE(category_id, name)
        )
    ''')

    # Inventory table (current stock of each consumable)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consumable_type_id INTEGER NOT NULL UNIQUE,
            current_quantity REAL NOT NULL DEFAULT 0,
            custom_usage_rate REAL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (consumable_type_id) REFERENCES consumable_types(id)
        )
    ''')

    # Purchases table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consumable_type_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            purchase_date DATE NOT NULL,
            price REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (consumable_type_id) REFERENCES consumable_types(id)
        )
    ''')

    # Usage log table (for tracking actual usage and improving estimates)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consumable_type_id INTEGER NOT NULL,
            quantity_used REAL NOT NULL,
            usage_date DATE NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (consumable_type_id) REFERENCES consumable_types(id)
        )
    ''')

    # Insert default categories
    default_categories = [
        ('Household', '🏠'),
        ('Food & Pantry', '🍎'),
        ('Personal Care', '🧴')
    ]

    for name, icon in default_categories:
        cursor.execute('''
            INSERT OR IGNORE INTO categories (name, icon) VALUES (?, ?)
        ''', (name, icon))

    # Insert some common consumable types with family-of-5 usage rates
    # (2 adults + 3 young children)
    default_consumables = [
        # Household (category_id=1)
        (1, 'Toilet Paper', 'rolls', 7.0, 'week', 4),
        (1, 'Paper Towels', 'rolls', 2.0, 'week', 2),
        (1, 'Dish Soap', 'bottles', 1.0, 'month', 1),
        (1, 'Laundry Detergent', 'loads', 10.0, 'week', 20),
        (1, 'Trash Bags', 'bags', 7.0, 'week', 10),
        (1, 'Diapers', 'diapers', 35.0, 'week', 50),
        (1, 'Baby Wipes', 'packs', 2.0, 'week', 2),
        (1, 'Cleaning Spray', 'bottles', 1.0, 'month', 1),
        (1, 'Sponges', 'sponges', 2.0, 'month', 2),

        # Food & Pantry (category_id=2)
        (2, 'Milk', 'gallons', 3.0, 'week', 2),
        (2, 'Bread', 'loaves', 2.0, 'week', 1),
        (2, 'Eggs', 'dozens', 2.0, 'week', 1),
        (2, 'Butter', 'sticks', 2.0, 'week', 2),
        (2, 'Cereal', 'boxes', 2.0, 'week', 2),
        (2, 'Juice Boxes', 'boxes', 15.0, 'week', 10),
        (2, 'Snack Crackers', 'boxes', 2.0, 'week', 2),
        (2, 'Fruit Snacks', 'boxes', 1.0, 'week', 1),
        (2, 'Pasta', 'boxes', 2.0, 'week', 3),
        (2, 'Rice', 'pounds', 1.0, 'week', 2),

        # Personal Care (category_id=3)
        (3, 'Toothpaste', 'tubes', 1.0, 'month', 1),
        (3, 'Shampoo', 'bottles', 1.0, 'month', 1),
        (3, 'Conditioner', 'bottles', 1.0, 'month', 1),
        (3, 'Body Wash', 'bottles', 2.0, 'month', 1),
        (3, 'Hand Soap', 'bottles', 2.0, 'month', 2),
        (3, 'Lotion', 'bottles', 1.0, 'month', 1),
        (3, 'Sunscreen', 'bottles', 1.0, 'month', 1),
        (3, 'Band-Aids', 'boxes', 1.0, 'month', 1),
        (3, 'Children\'s Tylenol', 'bottles', 1.0, 'month', 1),
    ]

    for cat_id, name, unit, rate, period, min_stock in default_consumables:
        cursor.execute('''
            INSERT OR IGNORE INTO consumable_types
            (category_id, name, unit, default_usage_rate, usage_rate_period, min_stock_level)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (cat_id, name, unit, rate, period, min_stock))

    # Initialize inventory for all consumable types
    cursor.execute('''
        INSERT OR IGNORE INTO inventory (consumable_type_id, current_quantity)
        SELECT id, 0 FROM consumable_types
        WHERE id NOT IN (SELECT consumable_type_id FROM inventory)
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
