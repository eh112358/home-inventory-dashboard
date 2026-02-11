# Session Handoff - Home Inventory Manager

## Project Overview

A self-hosted web application for tracking household consumables and determining when items need restocking.

**Tech Stack:**
- Backend: Flask 3.0.0 (Python 3.11) + SQLite
- Frontend: Vanilla HTML/CSS/JavaScript (SPA)
- Deployment: Docker + GitHub Actions CI/CD

**Repository:** Local git repo, not yet pushed to remote
**Branch:** `dev` (active development)

---

## Project Structure

```
homeinventory-backup/
├── backend/
│   ├── app.py              # Flask API (~500 lines, 13 route groups)
│   ├── database.py         # SQLite schema & initialization
│   ├── config.py           # Configuration management
│   └── tests/test_api.py   # Pytest test suite (29 tests)
├── frontend/
│   ├── index.html          # Single-page application
│   ├── js/app.js           # Application logic (~750 lines)
│   └── css/styles.css      # Responsive styling (~1000 lines)
├── data/                   # Persistent data (gitignored)
│   └── inventory.db        # SQLite database
├── docker-compose.yml
├── Dockerfile
├── spec.md                 # Project specification
├── IMPROVEMENTS.md         # Simplification recommendations (items 6-9 completed)
├── PLAN-improvements-6-9.md # Completed implementation plan
├── PLAN-new-features.md    # NEW: Pending features plan
└── README.md
```

---

## Current State

### Git Status
```
Branch: dev
Latest commits:
  2881f30 docs: Mark items 6-9 as completed in improvement docs
  cc4dc12 Implement IMPROVEMENTS.md items 6-9
  9ac516f Initial commit: Home Inventory Manager MVP

master branch: 9ac516f (unchanged)
```

### Recent Changes (dev branch)
Implemented IMPROVEMENTS.md items 6-9:
1. **Removed unused `/api/usage-rate` endpoint** - dead code cleanup
2. **Added dashboard caching** - invalidation-based cache for performance
3. **Consolidated purchase rendering** - single CSS Grid layout (was dual table+cards)
4. **Standardized weekly usage rates** - removed day/month options, simplified calculations

All 29 tests passing.

---

## Pending Work

### New Features Plan (`PLAN-new-features.md`)

5 features planned but NOT yet implemented:

| # | Feature | Scope | Status |
|---|---------|-------|--------|
| 1 | Voice input for purchases | Frontend | Planned |
| 2 | Inventory grid view toggle | Frontend | Planned |
| 3 | Multi-edit mode (qty + rates) | Full stack | Planned |
| 4 | Add custom categories | Full stack | Planned |
| 5 | Edit/delete categories | Full stack | Planned |

**Recommended implementation order:**
1. Features 4 & 5 (Categories) - foundation
2. Feature 2 (Grid Toggle) - simple
3. Feature 3 (Multi-Edit) - complex
4. Feature 1 (Voice Input) - independent

See `PLAN-new-features.md` for full implementation details.

---

## Key Files Reference

### Backend (`backend/app.py`)
- Authentication: `/api/auth/login`, `/api/auth/logout`, `/api/auth/check`
- Categories: `GET /api/categories`
- Consumables: `GET/POST/PUT/DELETE /api/consumables`
- Inventory: `PUT /api/inventory/<id>`
- Purchases: `GET/POST/DELETE /api/purchases`
- Dashboard: `GET /api/dashboard` (cached)
- Stats: `GET /api/stats`
- Backup: `GET /api/backup/download`, `POST /api/backup/upload`

### Frontend (`frontend/js/app.js`)
- View switching: `switchView()`
- Dashboard: `loadDashboard()`, `renderItemsGridGrouped()`
- Inventory: `loadInventory()`, `renderInventoryList()`
- Purchases: `loadPurchases()`, `renderPurchasesTable()`
- Item management: `handleAddItem()`, `handleEditItem()`, `openEditModal()`
- Categories: `loadCategories()`, `populateCategorySelects()`

### Database Schema (`backend/database.py`)
- `categories`: id, name (unique), icon
- `consumable_types`: id, category_id (FK), name, unit, default_usage_rate, min_stock_level, notes
- `inventory`: id, consumable_type_id (FK), current_quantity, custom_usage_rate
- `purchases`: id, consumable_type_id (FK), quantity, purchase_date, price, notes
- `usage_log`: unused (candidate for removal)

---

## How to Run

### Tests
```bash
cd backend
pytest tests/ -v
```

### Development (Docker)
```bash
docker-compose up --build
# App runs on http://localhost:828
```

### Environment Variables
- `SECRET_KEY` - Flask session secret (required)
- `APP_PASSWORD` - Login password (required)
- `ENVIRONMENT` - Environment name for UI badge (optional)

---

## Design Decisions to Remember

- **Single user, self-hosted** - no multi-tenant support needed
- **SQLite only** - no external database server
- **Usage rates are weekly** - standardized, no day/month options
- **Dashboard is cached** - invalidated on data changes
- **Mobile-first responsive** - FAB for quick purchases, collapsible categories
- **Categories have items protection** - block deletion if items exist (planned)

---

## Notes for Next Session

1. The new features plan is complete and ready for implementation
2. Start with Features 4 & 5 (category CRUD) as they're foundational
3. All backend endpoints follow existing patterns (validation helpers, `get_db_connection()` context manager, `invalidate_dashboard_cache()`)
4. Frontend follows existing patterns (modal system, form handlers, `api()` helper)
5. Tests should be added for new endpoints in `backend/tests/test_api.py`
