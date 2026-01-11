from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from functools import wraps
from datetime import datetime, timedelta
import os

from config import Config
from database import get_db, init_db

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config.from_object(Config)
CORS(app, supports_credentials=True)

# Initialize database on startup
init_db()

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
    if not data.get('category_id') or not data.get('name'):
        return jsonify({'error': 'category_id and name are required'}), 400
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO consumable_types
        (category_id, name, unit, default_usage_rate, usage_rate_period, min_stock_level, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['category_id'],
        data['name'],
        data.get('unit', 'units'),
        data.get('default_usage_rate', 1.0),
        data.get('usage_rate_period', 'week'),
        data.get('min_stock_level', 1.0),
        data.get('notes')
    ))

    consumable_id = cursor.lastrowid

    # Create inventory entry
    cursor.execute('''
        INSERT INTO inventory (consumable_type_id, current_quantity)
        VALUES (?, 0)
    ''', (consumable_id,))

    conn.commit()
    conn.close()
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
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM inventory WHERE consumable_type_id = ?', (id,))
    cursor.execute('DELETE FROM purchases WHERE consumable_type_id = ?', (id,))
    cursor.execute('DELETE FROM usage_log WHERE consumable_type_id = ?', (id,))
    cursor.execute('DELETE FROM consumable_types WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# Inventory endpoints
@app.route('/api/inventory/<int:consumable_id>', methods=['PUT'])
@login_required
def update_inventory(consumable_id):
    data = request.get_json() or {}
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE inventory
        SET current_quantity = ?, custom_usage_rate = ?, last_updated = CURRENT_TIMESTAMP
        WHERE consumable_type_id = ?
    ''', (
        data.get('current_quantity', 0),
        data.get('custom_usage_rate'),
        consumable_id
    ))

    conn.commit()
    conn.close()
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
    if not data.get('consumable_type_id') or data.get('quantity') is None:
        return jsonify({'error': 'consumable_type_id and quantity are required'}), 400
    conn = get_db()
    cursor = conn.cursor()

    # Add purchase record
    cursor.execute('''
        INSERT INTO purchases
        (consumable_type_id, quantity, purchase_date, price, notes)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        data['consumable_type_id'],
        data['quantity'],
        data.get('purchase_date', datetime.now().strftime('%Y-%m-%d')),
        data.get('price'),
        data.get('notes')
    ))

    # Update inventory
    cursor.execute('''
        UPDATE inventory
        SET current_quantity = current_quantity + ?, last_updated = CURRENT_TIMESTAMP
        WHERE consumable_type_id = ?
    ''', (data['quantity'], data['consumable_type_id']))

    conn.commit()
    conn.close()
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
