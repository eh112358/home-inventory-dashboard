"""
Test Plan for Home Inventory Application
=========================================

1. Authentication Tests
   - Test login with correct password
   - Test login with incorrect password
   - Test logout functionality
   - Test auth check endpoint
   - Test protected endpoints without auth

2. Categories Tests
   - Test get all categories
   - Test categories require auth

3. Consumables Tests
   - Test get all consumables
   - Test get consumables by category
   - Test create consumable
   - Test update consumable
   - Test delete consumable
   - Test consumables require auth

4. Inventory Tests
   - Test update inventory quantity
   - Test update custom usage rate
   - Test inventory requires auth

5. Purchases Tests
   - Test get all purchases
   - Test create purchase (updates inventory)
   - Test delete purchase (reverts inventory)
   - Test purchases require auth

6. Dashboard Tests
   - Test dashboard returns items sorted by priority
   - Test days_until_empty calculation
   - Test needs_purchase flag
   - Test low_stock flag

7. Stats Tests
   - Test stats endpoint returns correct counts
"""

import pytest
import json
import os
import sys
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set required environment variables BEFORE importing app/config
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing'
os.environ['APP_PASSWORD'] = 'testpassword123'

from app import app
from database import init_db, get_db
from config import Config

# Test password constant
TEST_PASSWORD = 'testpassword123'


@pytest.fixture
def client():
    """Create a test client with a temporary database."""
    # Use a temporary database for testing
    db_fd, db_path = tempfile.mkstemp()
    Config.DATABASE_PATH = db_path

    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'

    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

    # Clean up
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def authenticated_client(client):
    """Create an authenticated test client."""
    client.post('/api/auth/login',
                data=json.dumps({'password': TEST_PASSWORD}),
                content_type='application/json')
    return client


# =============================================================================
# Authentication Tests
# =============================================================================

class TestAuthentication:
    def test_login_correct_password(self, client):
        """Test login with correct password returns success."""
        response = client.post('/api/auth/login',
                               data=json.dumps({'password': TEST_PASSWORD}),
                               content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_login_incorrect_password(self, client):
        """Test login with incorrect password returns 401."""
        response = client.post('/api/auth/login',
                               data=json.dumps({'password': 'wrongpassword'}),
                               content_type='application/json')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data

    def test_logout(self, authenticated_client):
        """Test logout clears session."""
        response = authenticated_client.post('/api/auth/logout')
        assert response.status_code == 200

        # Verify we're logged out
        response = authenticated_client.get('/api/auth/check')
        data = json.loads(response.data)
        assert data['authenticated'] is False

    def test_auth_check_unauthenticated(self, client):
        """Test auth check returns false when not logged in."""
        response = client.get('/api/auth/check')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['authenticated'] is False

    def test_auth_check_authenticated(self, authenticated_client):
        """Test auth check returns true when logged in."""
        response = authenticated_client.get('/api/auth/check')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['authenticated'] is True

    def test_protected_endpoint_without_auth(self, client):
        """Test protected endpoints return 401 without auth."""
        response = client.get('/api/categories')
        assert response.status_code == 401


# =============================================================================
# Categories Tests
# =============================================================================

class TestCategories:
    def test_get_categories(self, authenticated_client):
        """Test getting all categories."""
        response = authenticated_client.get('/api/categories')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 3  # Default categories
        category_names = [c['name'] for c in data]
        assert 'Household' in category_names
        assert 'Food & Pantry' in category_names
        assert 'Personal Care' in category_names

    def test_categories_require_auth(self, client):
        """Test categories endpoint requires authentication."""
        response = client.get('/api/categories')
        assert response.status_code == 401


# =============================================================================
# Consumables Tests
# =============================================================================

class TestConsumables:
    def test_get_all_consumables(self, authenticated_client):
        """Test getting all consumables."""
        response = authenticated_client.get('/api/consumables')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) > 0  # Should have default consumables

    def test_get_consumables_by_category(self, authenticated_client):
        """Test filtering consumables by category."""
        response = authenticated_client.get('/api/consumables?category_id=1')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert all(c['category_id'] == 1 for c in data)

    def test_create_consumable(self, authenticated_client):
        """Test creating a new consumable."""
        new_item = {
            'category_id': 1,
            'name': 'Test Item',
            'unit': 'pieces',
            'default_usage_rate': 5.0,
            'usage_rate_period': 'week',
            'min_stock_level': 3.0
        }
        response = authenticated_client.post('/api/consumables',
                                             data=json.dumps(new_item),
                                             content_type='application/json')
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'id' in data
        assert data['success'] is True

        # Verify item was created
        response = authenticated_client.get('/api/consumables')
        items = json.loads(response.data)
        item_names = [i['name'] for i in items]
        assert 'Test Item' in item_names

    def test_update_consumable(self, authenticated_client):
        """Test updating a consumable."""
        # First create an item
        new_item = {
            'category_id': 1,
            'name': 'Update Test Item',
            'unit': 'pieces',
            'default_usage_rate': 5.0,
            'usage_rate_period': 'week',
            'min_stock_level': 3.0
        }
        response = authenticated_client.post('/api/consumables',
                                             data=json.dumps(new_item),
                                             content_type='application/json')
        item_id = json.loads(response.data)['id']

        # Update the item
        updated_item = {
            'category_id': 1,
            'name': 'Updated Name',
            'unit': 'boxes',
            'default_usage_rate': 10.0,
            'usage_rate_period': 'month',
            'min_stock_level': 5.0
        }
        response = authenticated_client.put(f'/api/consumables/{item_id}',
                                            data=json.dumps(updated_item),
                                            content_type='application/json')
        assert response.status_code == 200

        # Verify update
        response = authenticated_client.get('/api/consumables')
        items = json.loads(response.data)
        updated = next((i for i in items if i['id'] == item_id), None)
        assert updated is not None
        assert updated['name'] == 'Updated Name'
        assert updated['unit'] == 'boxes'

    def test_delete_consumable(self, authenticated_client):
        """Test deleting a consumable."""
        # First create an item
        new_item = {
            'category_id': 1,
            'name': 'Delete Test Item',
            'unit': 'pieces',
            'default_usage_rate': 5.0,
            'usage_rate_period': 'week',
            'min_stock_level': 3.0
        }
        response = authenticated_client.post('/api/consumables',
                                             data=json.dumps(new_item),
                                             content_type='application/json')
        item_id = json.loads(response.data)['id']

        # Delete the item
        response = authenticated_client.delete(f'/api/consumables/{item_id}')
        assert response.status_code == 200

        # Verify deletion
        response = authenticated_client.get('/api/consumables')
        items = json.loads(response.data)
        assert not any(i['id'] == item_id for i in items)


# =============================================================================
# Inventory Tests
# =============================================================================

class TestInventory:
    def test_update_inventory_quantity(self, authenticated_client):
        """Test updating inventory quantity."""
        # Get first consumable
        response = authenticated_client.get('/api/consumables')
        items = json.loads(response.data)
        item_id = items[0]['id']

        # Update quantity
        update_data = {'current_quantity': 25.0}
        response = authenticated_client.put(f'/api/inventory/{item_id}',
                                            data=json.dumps(update_data),
                                            content_type='application/json')
        assert response.status_code == 200

        # Verify update
        response = authenticated_client.get('/api/consumables')
        items = json.loads(response.data)
        updated = next((i for i in items if i['id'] == item_id), None)
        assert updated['current_quantity'] == 25.0

    def test_update_custom_usage_rate(self, authenticated_client):
        """Test updating custom usage rate."""
        # Get first consumable
        response = authenticated_client.get('/api/consumables')
        items = json.loads(response.data)
        item_id = items[0]['id']

        # Update custom rate
        update_data = {'current_quantity': 10.0, 'custom_usage_rate': 3.5}
        response = authenticated_client.put(f'/api/inventory/{item_id}',
                                            data=json.dumps(update_data),
                                            content_type='application/json')
        assert response.status_code == 200

        # Verify update
        response = authenticated_client.get('/api/consumables')
        items = json.loads(response.data)
        updated = next((i for i in items if i['id'] == item_id), None)
        assert updated['custom_usage_rate'] == 3.5


# =============================================================================
# Purchases Tests
# =============================================================================

class TestPurchases:
    def test_get_purchases_empty(self, authenticated_client):
        """Test getting purchases when empty."""
        response = authenticated_client.get('/api/purchases')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_create_purchase_updates_inventory(self, authenticated_client):
        """Test creating a purchase updates inventory."""
        # Get first consumable
        response = authenticated_client.get('/api/consumables')
        items = json.loads(response.data)
        item = items[0]
        item_id = item['id']
        initial_qty = item['current_quantity'] or 0

        # Create purchase
        purchase_data = {
            'consumable_type_id': item_id,
            'quantity': 10.0,
            'purchase_date': '2024-01-15'
        }
        response = authenticated_client.post('/api/purchases',
                                             data=json.dumps(purchase_data),
                                             content_type='application/json')
        assert response.status_code == 201

        # Verify inventory updated
        response = authenticated_client.get('/api/consumables')
        items = json.loads(response.data)
        updated = next((i for i in items if i['id'] == item_id), None)
        assert updated['current_quantity'] == initial_qty + 10.0

    def test_delete_purchase_reverts_inventory(self, authenticated_client):
        """Test deleting a purchase reverts inventory."""
        # Get first consumable
        response = authenticated_client.get('/api/consumables')
        items = json.loads(response.data)
        item = items[0]
        item_id = item['id']

        # Set initial quantity
        authenticated_client.put(f'/api/inventory/{item_id}',
                                 data=json.dumps({'current_quantity': 20.0}),
                                 content_type='application/json')

        # Create purchase
        purchase_data = {
            'consumable_type_id': item_id,
            'quantity': 15.0,
            'purchase_date': '2024-01-15'
        }
        authenticated_client.post('/api/purchases',
                                  data=json.dumps(purchase_data),
                                  content_type='application/json')

        # Get purchase ID
        response = authenticated_client.get('/api/purchases')
        purchases = json.loads(response.data)
        purchase_id = purchases[0]['id']

        # Delete purchase
        response = authenticated_client.delete(f'/api/purchases/{purchase_id}')
        assert response.status_code == 200

        # Verify inventory reverted
        response = authenticated_client.get('/api/consumables')
        items = json.loads(response.data)
        updated = next((i for i in items if i['id'] == item_id), None)
        assert updated['current_quantity'] == 20.0


# =============================================================================
# Dashboard Tests
# =============================================================================

class TestDashboard:
    def test_dashboard_returns_items(self, authenticated_client):
        """Test dashboard returns items."""
        response = authenticated_client.get('/api/dashboard')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_dashboard_calculates_days_until_empty(self, authenticated_client):
        """Test dashboard calculates days_until_empty correctly."""
        # Get first consumable and set quantity
        response = authenticated_client.get('/api/consumables')
        items = json.loads(response.data)
        item = items[0]
        item_id = item['id']

        # Set quantity to 14 (2 weeks worth at 7/week rate for toilet paper)
        authenticated_client.put(f'/api/inventory/{item_id}',
                                 data=json.dumps({'current_quantity': 14.0}),
                                 content_type='application/json')

        # Check dashboard
        response = authenticated_client.get('/api/dashboard')
        data = json.loads(response.data)
        dashboard_item = next((i for i in data if i['id'] == item_id), None)
        assert dashboard_item is not None
        assert 'days_until_empty' in dashboard_item

    def test_dashboard_needs_purchase_flag(self, authenticated_client):
        """Test dashboard sets needs_purchase flag correctly."""
        # Get a consumable
        response = authenticated_client.get('/api/consumables')
        items = json.loads(response.data)
        item = items[0]
        item_id = item['id']
        min_stock = item['min_stock_level']

        # Set quantity below min stock
        authenticated_client.put(f'/api/inventory/{item_id}',
                                 data=json.dumps({'current_quantity': min_stock - 1}),
                                 content_type='application/json')

        # Check dashboard
        response = authenticated_client.get('/api/dashboard')
        data = json.loads(response.data)
        dashboard_item = next((i for i in data if i['id'] == item_id), None)
        assert dashboard_item['needs_purchase'] is True


# =============================================================================
# Stats Tests
# =============================================================================

class TestStats:
    def test_stats_returns_counts(self, authenticated_client):
        """Test stats endpoint returns correct structure."""
        response = authenticated_client.get('/api/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'needs_purchase' in data
        assert 'total_items' in data
        assert 'recent_purchases' in data

    def test_stats_total_items_count(self, authenticated_client):
        """Test stats counts total items correctly."""
        response = authenticated_client.get('/api/consumables')
        items = json.loads(response.data)

        response = authenticated_client.get('/api/stats')
        stats = json.loads(response.data)
        assert stats['total_items'] == len(items)



# =============================================================================
# Input Validation Tests
# =============================================================================

class TestInputValidation:
    def test_create_consumable_negative_usage_rate(self, authenticated_client):
        """Test creating consumable with negative usage rate fails."""
        new_item = {
            'category_id': 1,
            'name': 'Test Negative Rate',
            'unit': 'pieces',
            'default_usage_rate': -5.0,
        }
        response = authenticated_client.post('/api/consumables',
                                             data=json.dumps(new_item),
                                             content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_create_consumable_invalid_usage_rate(self, authenticated_client):
        """Test creating consumable with non-numeric usage rate fails."""
        new_item = {
            'category_id': 1,
            'name': 'Test Invalid Rate',
            'unit': 'pieces',
            'default_usage_rate': 'not-a-number',
        }
        response = authenticated_client.post('/api/consumables',
                                             data=json.dumps(new_item),
                                             content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_create_purchase_negative_quantity(self, authenticated_client):
        """Test creating purchase with negative quantity fails."""
        response = authenticated_client.get('/api/consumables')
        items = json.loads(response.data)
        item_id = items[0]['id']

        purchase_data = {
            'consumable_type_id': item_id,
            'quantity': -10.0,
            'purchase_date': '2024-01-15'
        }
        response = authenticated_client.post('/api/purchases',
                                             data=json.dumps(purchase_data),
                                             content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_create_purchase_zero_quantity(self, authenticated_client):
        """Test creating purchase with zero quantity fails."""
        response = authenticated_client.get('/api/consumables')
        items = json.loads(response.data)
        item_id = items[0]['id']

        purchase_data = {
            'consumable_type_id': item_id,
            'quantity': 0,
            'purchase_date': '2024-01-15'
        }
        response = authenticated_client.post('/api/purchases',
                                             data=json.dumps(purchase_data),
                                             content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_update_inventory_negative_quantity(self, authenticated_client):
        """Test updating inventory with negative quantity fails."""
        response = authenticated_client.get('/api/consumables')
        items = json.loads(response.data)
        item_id = items[0]['id']

        update_data = {'current_quantity': -5.0}
        response = authenticated_client.put(f'/api/inventory/{item_id}',
                                            data=json.dumps(update_data),
                                            content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_create_consumable_empty_name(self, authenticated_client):
        """Test creating consumable with empty name fails."""
        new_item = {
            'category_id': 1,
            'name': '   ',
            'unit': 'pieces',
        }
        response = authenticated_client.post('/api/consumables',
                                             data=json.dumps(new_item),
                                             content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
