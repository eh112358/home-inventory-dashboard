from flask import Flask, request, jsonify, session, send_from_directory, send_file
from flask_cors import CORS
from functools import wraps
from datetime import datetime, timedelta
import os
import shutil

from config import Config
from database import get_db, get_db_connection, init_db

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config.from_object(Config)
CORS(app, supports_credentials=True)

# Validate configuration before starting
Config.validate()

# Initialize database on startup
init_db()

# Validation helpers
def validate_positive_number(value, field_name, required=True, allow_zero=False):
    if value is None:
        if required:
            return None, f"{field_name} is required"
        return None, None
    try:
        num = float(value)
        if allow_zero and num < 0:
            return None, f"{field_name} must be non-negative"
        if not allow_zero and num <= 0:
            return None, f"{field_name} must be positive"
        return num, None
    except (TypeError, ValueError):
        return None, f"{field_name} must be a valid number"

def validate_string(value, field_name, required=True, max_length=255):
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            return None, f"{field_name} is required"
        return None, None
    if not isinstance(value, str):
        return None, f"{field_name} must be a string"
    value = value.strip()
    if len(value) > max_length:
        return None, f"{field_name} must be at most {max_length} characters"
    return value, None

# Auth decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Serve frontend
@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# Auth endpoints
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    if data.get('password') == Config.APP_PASSWORD:
        session['authenticated'] = True
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid password'}), 401

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.pop('authenticated', None)
    return jsonify({'success': True})

@app.route('/api/auth/check', methods=['GET'])
def check_auth():
    return jsonify({'authenticated': session.get('authenticated', False)})

# Environment endpoint (public - used for UI indicators)
@app.route('/api/environment', methods=['GET'])
def get_environment():
    return jsonify({'environment': Config.APP_ENVIRONMENT})

# Backup endpoints
@app.route('/api/backup/download', methods=['GET'])
@login_required
def download_backup():
    """Download the SQLite database file for backup"""
    db_path = Config.DATABASE_PATH
    if not os.path.exists(db_path):
        return jsonify({'error': 'Database not found'}), 404

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return send_file(
        db_path,
        mimetype='application/x-sqlite3',
        as_attachment=True,
        download_name=f'inventory_backup_{timestamp}.db'
    )

@app.route('/api/backup/upload', methods=['POST'])
@login_required
def upload_backup():
    """Upload and replace the SQLite database file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Basic validation - check it's a SQLite file
    header = file.read(16)
    file.seek(0)
    if header[:16] != b'SQLite format 3\x00':
        return jsonify({'error': 'Invalid SQLite database file'}), 400

    db_path = Config.DATABASE_PATH

    # Backup current database before replacing
    if os.path.exists(db_path):
        backup_path = db_path + '.bak'
        shutil.copy2(db_path, backup_path)

    # Save uploaded file
    file.save(db_path)

    return jsonify({'success': True, 'message': 'Database restored successfully'})

# Categories endpoints
@app.route('/api/categories', methods=['GET'])
@login_required
def get_categories():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM categories ORDER BY name')
    categories = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(categories)

# Consumable types endpoints
@app.route('/api/consumables', methods=['GET'])
@login_required
def get_consumables():
    conn = get_db()
    cursor = conn.cursor()

    category_id = request.args.get('category_id')
    if category_id:
        cursor.execute('''
            SELECT ct.*, c.name as category_name, c.icon as category_icon,
                   i.current_quantity, i.custom_usage_rate
            FROM consumable_types ct
            JOIN categories c ON ct.category_id = c.id
            LEFT JOIN inventory i ON ct.id = i.consumable_type_id
            WHERE ct.category_id = ?
            ORDER BY ct.name
        ''', (category_id,))
    else:
        cursor.execute('''
            SELECT ct.*, c.name as category_name, c.icon as category_icon,
                   i.current_quantity, i.custom_usage_rate
            FROM consumable_types ct
            JOIN categories c ON ct.category_id = c.id
            LEFT JOIN inventory i ON ct.id = i.consumable_type_id
            ORDER BY c.name, ct.name
        ''')

    consumables = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(consumables)

@app.route('/api/consumables', methods=['POST'])
@login_required
def create_consumable():
    data = request.get_json() or {}
    
    name, err = validate_string(data.get('name'), 'name')
    if err:
        return jsonify({'error': err}), 400
    
    category_id, err = validate_positive_number(data.get('category_id'), 'category_id')
    if err:
        return jsonify({'error': err}), 400
    
    usage_rate = data.get('default_usage_rate', 1.0)
    if usage_rate is not None:
        usage_rate, err = validate_positive_number(usage_rate, 'default_usage_rate')
        if err:
            return jsonify({'error': err}), 400
    
    min_stock = data.get('min_stock_level', 1.0)
    if min_stock is not None:
        min_stock, err = validate_positive_number(min_stock, 'min_stock_level', allow_zero=True)
        if err:
            return jsonify({'error': err}), 400

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO consumable_types
            (category_id, name, unit, default_usage_rate, usage_rate_period, min_stock_level, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            int(category_id),
            name,
            data.get('unit', 'units'),
            usage_rate or 1.0,
            data.get('usage_rate_period', 'week'),
            min_stock or 1.0,
            data.get('notes')
        ))
        consumable_id = cursor.lastrowid
        cursor.execute('''
            INSERT INTO inventory (consumable_type_id, current_quantity)
            VALUES (?, 0)
        ''', (consumable_id,))
    
    return jsonify({'id': consumable_id, 'success': True}), 201

@app.route('/api/consumables/<int:id>', methods=['PUT'])
@login_required
def update_consumable(id):
    data = request.get_json() or {}
    if not data.get('category_id') or not data.get('name'):
        return jsonify({'error': 'category_id and name are required'}), 400
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE consumable_types
        SET category_id = ?, name = ?, unit = ?, default_usage_rate = ?,
            usage_rate_period = ?, min_stock_level = ?, notes = ?
        WHERE id = ?
    ''', (
        data['category_id'],
        data['name'],
        data.get('unit', 'units'),
        data.get('default_usage_rate', 1.0),
        data.get('usage_rate_period', 'week'),
        data.get('min_stock_level', 1.0),
        data.get('notes'),
        id
    ))

    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/consumables/<int:id>', methods=['DELETE'])
@login_required
def delete_consumable(id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM inventory WHERE consumable_type_id = ?', (id,))
        cursor.execute('DELETE FROM purchases WHERE consumable_type_id = ?', (id,))
        cursor.execute('DELETE FROM usage_log WHERE consumable_type_id = ?', (id,))
        cursor.execute('DELETE FROM consumable_types WHERE id = ?', (id,))
    return jsonify({'success': True})

# Inventory endpoints
@app.route('/api/inventory/<int:consumable_id>', methods=['PUT'])
@login_required
def update_inventory(consumable_id):
    data = request.get_json() or {}
    
    current_quantity = data.get('current_quantity', 0)
    current_quantity, err = validate_positive_number(current_quantity, 'current_quantity', allow_zero=True)
    if err:
        return jsonify({'error': err}), 400
    
    custom_usage_rate = data.get('custom_usage_rate')
    if custom_usage_rate is not None:
        custom_usage_rate, err = validate_positive_number(custom_usage_rate, 'custom_usage_rate', required=False)
        if err:
            return jsonify({'error': err}), 400

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE inventory
            SET current_quantity = ?, custom_usage_rate = ?, last_updated = CURRENT_TIMESTAMP
            WHERE consumable_type_id = ?
        ''', (current_quantity, custom_usage_rate, consumable_id))
    
    return jsonify({'success': True})

# Purchases endpoints
@app.route('/api/purchases', methods=['GET'])
@login_required
def get_purchases():
    conn = get_db()
    cursor = conn.cursor()

    consumable_id = request.args.get('consumable_id')
    limit = request.args.get('limit', 50)

    if consumable_id:
        cursor.execute('''
            SELECT p.*, ct.name as consumable_name, ct.unit
            FROM purchases p
            JOIN consumable_types ct ON p.consumable_type_id = ct.id
            WHERE p.consumable_type_id = ?
            ORDER BY p.purchase_date DESC
            LIMIT ?
        ''', (consumable_id, limit))
    else:
        cursor.execute('''
            SELECT p.*, ct.name as consumable_name, ct.unit
            FROM purchases p
            JOIN consumable_types ct ON p.consumable_type_id = ct.id
            ORDER BY p.purchase_date DESC
            LIMIT ?
        ''', (limit,))

    purchases = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(purchases)

@app.route('/api/purchases', methods=['POST'])
@login_required
def create_purchase():
    data = request.get_json() or {}
    
    consumable_type_id, err = validate_positive_number(data.get('consumable_type_id'), 'consumable_type_id')
    if err:
        return jsonify({'error': err}), 400
    
    quantity, err = validate_positive_number(data.get('quantity'), 'quantity')
    if err:
        return jsonify({'error': err}), 400
    
    price = data.get('price')
    if price is not None:
        price, err = validate_positive_number(price, 'price', required=False, allow_zero=True)
        if err:
            return jsonify({'error': err}), 400

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO purchases
            (consumable_type_id, quantity, purchase_date, price, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            int(consumable_type_id),
            quantity,
            data.get('purchase_date', datetime.now().strftime('%Y-%m-%d')),
            price,
            data.get('notes')
        ))
        cursor.execute('''
            UPDATE inventory
            SET current_quantity = current_quantity + ?, last_updated = CURRENT_TIMESTAMP
            WHERE consumable_type_id = ?
        ''', (quantity, int(consumable_type_id)))
    
    return jsonify({'success': True}), 201

@app.route('/api/purchases/<int:id>', methods=['DELETE'])
@login_required
def delete_purchase(id):
    conn = get_db()
    cursor = conn.cursor()

    # Get purchase details to reverse inventory
    cursor.execute('SELECT consumable_type_id, quantity FROM purchases WHERE id = ?', (id,))
    purchase = cursor.fetchone()

    if purchase:
        cursor.execute('''
            UPDATE inventory
            SET current_quantity = current_quantity - ?, last_updated = CURRENT_TIMESTAMP
            WHERE consumable_type_id = ?
        ''', (purchase['quantity'], purchase['consumable_type_id']))

    cursor.execute('DELETE FROM purchases WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# Dashboard endpoint - items that need to be purchased
@app.route('/api/dashboard', methods=['GET'])
@login_required
def get_dashboard():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT ct.*, c.name as category_name, c.icon as category_icon,
               i.current_quantity, i.custom_usage_rate,
               COALESCE(i.custom_usage_rate, ct.default_usage_rate) as effective_usage_rate
        FROM consumable_types ct
        JOIN categories c ON ct.category_id = c.id
        LEFT JOIN inventory i ON ct.id = i.consumable_type_id
        ORDER BY
            CASE WHEN i.current_quantity <= ct.min_stock_level THEN 0 ELSE 1 END,
            (i.current_quantity / COALESCE(i.custom_usage_rate, ct.default_usage_rate)) ASC
    ''')

    items = []
    for row in cursor.fetchall():
        item = dict(row)

        # Calculate days until empty
        usage_rate = item['effective_usage_rate'] or item['default_usage_rate']
        current_qty = item['current_quantity'] or 0
        period = item['usage_rate_period']

        # Convert usage rate to daily rate
        if period == 'day':
            daily_rate = usage_rate
        elif period == 'week':
            daily_rate = usage_rate / 7
        elif period == 'month':
            daily_rate = usage_rate / 30
        else:
            daily_rate = usage_rate / 7  # default to week

        if daily_rate > 0:
            days_until_empty = current_qty / daily_rate
        else:
            days_until_empty = 9999  # Use large number instead of infinity (JSON compatible)

        item['days_until_empty'] = round(days_until_empty, 1) if days_until_empty < 9999 else None
        item['needs_purchase'] = current_qty <= item['min_stock_level']
        item['low_stock'] = days_until_empty <= 7 and not item['needs_purchase']

        items.append(item)

    conn.close()
    return jsonify(items)

# Usage rate update endpoint
@app.route('/api/usage-rate/<int:consumable_id>', methods=['PUT'])
@login_required
def update_usage_rate(consumable_id):
    data = request.get_json() or {}
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE inventory
        SET custom_usage_rate = ?, last_updated = CURRENT_TIMESTAMP
        WHERE consumable_type_id = ?
    ''', (data.get('usage_rate'), consumable_id))

    conn.commit()
    conn.close()
    return jsonify({'success': True})

# Stats endpoint
@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    conn = get_db()
    cursor = conn.cursor()

    # Count items needing purchase
    cursor.execute('''
        SELECT COUNT(*) as count
        FROM inventory i
        JOIN consumable_types ct ON i.consumable_type_id = ct.id
        WHERE i.current_quantity <= ct.min_stock_level
    ''')
    needs_purchase = cursor.fetchone()['count']

    # Total items tracked
    cursor.execute('SELECT COUNT(*) as count FROM consumable_types')
    total_items = cursor.fetchone()['count']

    # Recent purchases (last 7 days)
    cursor.execute('''
        SELECT COUNT(*) as count FROM purchases
        WHERE purchase_date >= date('now', '-7 days')
    ''')
    recent_purchases = cursor.fetchone()['count']

    conn.close()
    return jsonify({
        'needs_purchase': needs_purchase,
        'total_items': total_items,
        'recent_purchases': recent_purchases
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
