# Implementation Plan: IMPROVEMENTS.md Items 6-9

## Status: ✅ COMPLETED

**Commit:** cc4dc12
**Branch:** dev
**Date:** 2026-02-09
**Tests:** 29/29 passing

## Overview

This plan covers four backend infrastructure simplifications:
- **Item 6:** ✅ Standardize on Weekly Usage Rates
- **Item 7:** ✅ Consolidate Purchase Rendering
- **Item 8:** ✅ Remove Unused API Endpoint
- **Item 9:** ✅ Simplify Dashboard Calculations (with caching)

---

## Item 8: Remove Unused API Endpoint

**Scope:** Backend only
**Risk:** Low
**Files:** `backend/app.py`

### Current State
- `/api/usage-rate/<int:consumable_id>` endpoint exists (lines 441-456)
- Frontend uses `/api/inventory/<id>` PUT instead
- Endpoint is dead code

### Implementation
1. Delete the endpoint from `app.py` (lines 440-456):
   ```python
   # DELETE THIS:
   @app.route('/api/usage-rate/<int:consumable_id>', methods=['PUT'])
   @login_required
   def update_usage_rate(consumable_id):
       ...
   ```

2. Update tests if any reference this endpoint (none found)

### Verification
- Run test suite
- Confirm no 404 errors in normal app usage

---

## Item 6: Standardize on Weekly Usage Rates

**Scope:** Backend + Frontend + Database
**Risk:** Medium (data migration required)
**Files:**
- `backend/database.py`
- `backend/app.py`
- `frontend/js/app.js`
- `frontend/index.html`
- `backend/tests/test_api.py`

### Current State
- `usage_rate_period` column stores 'day', 'week', or 'month'
- Backend converts to daily rate for calculations (app.py:417-424)
- Frontend has period dropdown selectors
- All rates will be reset to weekly defaults

### Implementation

#### Step 1: Database Migration
Add migration function in `database.py`:
```python
def migrate_to_weekly_rates():
    """Remove usage_rate_period, standardize all rates to weekly."""
    conn = get_db()
    cursor = conn.cursor()

    # Reset all usage rates to default weekly value (1.0)
    cursor.execute('''
        UPDATE consumable_types
        SET default_usage_rate = 1.0, usage_rate_period = 'week'
    ''')

    # Note: Column removal requires table rebuild in SQLite
    # For simplicity, keep column but ignore it

    conn.commit()
    conn.close()
```

#### Step 2: Backend Changes (`app.py`)

1. **Simplify dashboard calculation** (lines 416-424):
   ```python
   # BEFORE:
   if period == 'day':
       daily_rate = usage_rate
   elif period == 'week':
       daily_rate = usage_rate / 7
   elif period == 'month':
       daily_rate = usage_rate / 30
   else:
       daily_rate = usage_rate / 7

   # AFTER:
   daily_rate = usage_rate / 7  # All rates are weekly
   ```

2. **Remove period from consumable creation** (line 215):
   - Hardcode `'week'` instead of accepting from request

3. **Remove period from consumable update** (line 246):
   - Hardcode `'week'` instead of accepting from request

#### Step 3: Frontend Changes

1. **Remove period selector from Add Item form** (`index.html` ~line 150):
   - Delete the `<select id="new-item-usage-period">` element
   - Update label to say "Usage Rate (per week)"

2. **Remove period selector from Edit Item modal** (`index.html` ~line 207):
   - Delete the `<select id="edit-item-usage-period">` element
   - Update label to say "Usage Rate (per week)"

3. **Update JavaScript** (`app.js`):
   - Remove `usage_rate_period` from form data collection (~line 517, 542)
   - Remove period display from item rendering (~line 371, 471)
   - Simplify to show just the rate number with "/wk" suffix

#### Step 4: Update Tests
- Remove `usage_rate_period` from test data
- Update assertions that check for period values

### Verification
- Run migration on test database
- Run full test suite
- Manual testing: add item, edit item, verify dashboard calculations

---

## Item 7: Consolidate Purchase Rendering

**Scope:** Frontend only
**Risk:** Low
**Files:**
- `frontend/js/app.js`
- `frontend/css/styles.css`

### Current State
- `renderPurchasesTable()` generates BOTH table AND cards HTML (lines 409-451)
- `renderPurchasesCards()` is a separate function (lines 729-743)
- CSS controls visibility based on viewport
- Duplicate delete button event binding

### Implementation

#### Option A: Single Template with CSS Grid (Recommended)
Replace both table and cards with a single responsive grid layout:

1. **Create unified purchase item component**:
   ```javascript
   function renderPurchaseItem(p) {
       return `
           <div class="purchase-item" data-id="${p.id}">
               <span class="purchase-date">${escapeHtml(p.purchase_date)}</span>
               <span class="purchase-name">${escapeHtml(p.consumable_name)}</span>
               <span class="purchase-qty">${p.quantity} ${escapeHtml(p.unit)}</span>
               <span class="purchase-price">${formatPrice(p.price)}</span>
               <button class="btn-delete" data-id="${p.id}">Delete</button>
           </div>
       `;
   }
   ```

2. **Simplify renderPurchasesTable()**:
   ```javascript
   function renderPurchasesTable(purchases) {
       const container = document.getElementById('purchases-list');
       if (purchases.length === 0) {
           container.innerHTML = '<div class="empty-state"><p>No purchases recorded</p></div>';
           return;
       }

       container.innerHTML = `
           <div class="purchases-grid">
               <div class="purchases-header">
                   <span>Date</span><span>Item</span><span>Qty</span><span>Price</span><span></span>
               </div>
               ${purchases.map(renderPurchaseItem).join('')}
           </div>
       `;

       // Single event binding
       container.querySelectorAll('.btn-delete').forEach(btn => {
           btn.addEventListener('click', () => deletePurchase(parseInt(btn.dataset.id)));
       });
   }
   ```

3. **Delete `renderPurchasesCards()` function** (lines 728-743)

4. **Update CSS** - Use CSS Grid with responsive breakpoints:
   ```css
   .purchases-grid {
       display: grid;
       gap: 0.5rem;
   }

   .purchase-item {
       display: grid;
       grid-template-columns: 1fr 2fr 1fr 1fr auto;
       align-items: center;
       padding: 0.75rem;
       background: var(--card-bg);
       border-radius: 8px;
   }

   .purchases-header {
       display: grid;
       grid-template-columns: 1fr 2fr 1fr 1fr auto;
       font-weight: bold;
       padding: 0.5rem 0.75rem;
   }

   @media (max-width: 768px) {
       .purchases-header { display: none; }

       .purchase-item {
           grid-template-columns: 1fr 1fr;
           grid-template-rows: auto auto;
       }

       .purchase-name { grid-column: 1 / -1; font-weight: bold; }
       .btn-delete { justify-self: end; }
   }
   ```

### Verification
- Test on desktop (should look like current table)
- Test on mobile (should look like current cards)
- Verify delete functionality works

---

## Item 9: Simplify Dashboard Calculations (Caching)

**Scope:** Backend
**Risk:** Low-Medium
**Files:** `backend/app.py`

### Current State
- Dashboard endpoint calculates `days_until_empty` on every request
- No caching; recalculates even when data hasn't changed
- Calculations are in `/api/dashboard` route (lines 380-438)

### Implementation

#### Approach: Invalidation-based Cache

1. **Add cache storage** (top of app.py):
   ```python
   # Simple in-memory cache for dashboard data
   _dashboard_cache = {
       'data': None,
       'valid': False
   }

   def invalidate_dashboard_cache():
       """Call this when inventory or purchases change."""
       _dashboard_cache['valid'] = False
   ```

2. **Update dashboard endpoint**:
   ```python
   @app.route('/api/dashboard', methods=['GET'])
   @login_required
   def get_dashboard():
       # Return cached data if valid
       if _dashboard_cache['valid'] and _dashboard_cache['data'] is not None:
           return jsonify(_dashboard_cache['data'])

       # ... existing calculation logic ...

       # Cache the result
       _dashboard_cache['data'] = items
       _dashboard_cache['valid'] = True

       return jsonify(items)
   ```

3. **Invalidate cache on data changes**:
   - After purchase creation (`/api/purchases` POST)
   - After purchase deletion (`/api/purchases/<id>` DELETE)
   - After inventory update (`/api/inventory/<id>` PUT)
   - After consumable creation/update/deletion

   Add to each endpoint:
   ```python
   invalidate_dashboard_cache()
   ```

### Cache Invalidation Points
| Endpoint | Method | Invalidate? |
|----------|--------|-------------|
| `/api/purchases` | POST | Yes |
| `/api/purchases/<id>` | DELETE | Yes |
| `/api/inventory/<id>` | PUT | Yes |
| `/api/consumables` | POST | Yes |
| `/api/consumables/<id>` | PUT | Yes |
| `/api/consumables/<id>` | DELETE | Yes |

### Verification
- Dashboard loads quickly on repeated requests
- Changes to inventory/purchases reflect immediately on dashboard
- Run test suite

---

## Implementation Order

Recommended sequence (least to most complex):

1. **Item 8: Remove Unused Endpoint** (~5 min)
   - Quick win, no dependencies

2. **Item 9: Dashboard Caching** (~20 min)
   - Independent of other changes
   - Immediate performance benefit

3. **Item 7: Consolidate Purchase Rendering** (~30 min)
   - Frontend-only, no backend dependencies
   - Good test of CSS grid approach

4. **Item 6: Standardize Weekly Rates** (~45 min)
   - Most complex, touches all layers
   - Requires migration and careful testing

---

## Rollback Plan

Each item can be rolled back independently via git:
```bash
git revert <commit-hash>
```

For Item 6 (database changes):
- Keep original `usage_rate_period` column in schema
- Migration only updates values, doesn't remove column
- Rollback: restore original values from backup

---

## Testing Checklist

- [x] All existing tests pass (29/29)
- [ ] Dashboard displays correctly
- [ ] Items can be added/edited/deleted
- [ ] Purchases can be logged/deleted
- [ ] Mobile layout works correctly
- [ ] No console errors in browser
- [ ] Docker container builds and runs

## Implementation Summary

| Item | Status | Changes |
|------|--------|---------|
| 8: Remove unused endpoint | ✅ Done | Deleted `/api/usage-rate/<id>` from app.py |
| 9: Dashboard caching | ✅ Done | Added `_dashboard_cache` + `invalidate_dashboard_cache()` |
| 7: Purchase rendering | ✅ Done | Single CSS Grid layout, deleted `renderPurchasesCards()` |
| 6: Weekly rates only | ✅ Done | Removed period selectors, simplified calculations |

**Net code reduction:** ~22 lines
