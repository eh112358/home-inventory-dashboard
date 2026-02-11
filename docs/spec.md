# Home Inventory Manager - Specification

## Overview

**Project Name:** Home Inventory Manager
**Version:** Post-MVP / Active Development
**Status:** Active Development
**Primary Use:** Personal household inventory tracking

A self-hosted web application for tracking household consumables and determining when items need to be restocked based on usage rates. Mobile-first design optimized for phone use.

---

## Goals

### Primary Goal
Provide a simple, reliable way to track household consumable inventory and know when to purchase more before running out, via a mobile device web browser.

### Success Criteria
- Never run out of essential household items unexpectedly
- Reduce waste from over-purchasing
- Quick and easy logging of purchases
- At-a-glance visibility into what needs restocking

---

## Target User

- **Single person** managing personal household supplies
- Self-hosting on personal infrastructure (Docker)
- Comfortable with basic technical setup (Docker, environment variables)

---

## Current Features

### Dashboard
- Items that need to be purchased (below minimum stock level)
- Low-stock warnings (less than 7 days supply remaining)
- "Days until empty" calculations based on weekly usage rates
- Quick statistics: items needing purchase, total tracked items, recent purchases (7 days)
- Category filter dropdown
- Items grouped by category with collapsible sections on mobile
- Quick-purchase and edit buttons on each item card

### Inventory Management
- View current stock levels for all items
- Per-item customizable usage rates (weekly)
- List view (mobile + desktop) and grid/table view toggle (desktop only)
- Category filter dropdown
- View preference persists in localStorage

### Purchase Logging
- Log purchases with quantity, date, and optional price
- Automatic inventory quantity updates
- Purchase history with deletion capability
- Responsive layout: card-style on mobile, table on desktop

### Category Management
- Create custom categories with emoji icons (24 emoji choices)
- Edit category name and icon via modal
- Delete categories (blocked with error if items still assigned)
- Compact category list with 3-dot overflow menu for Edit/Delete
- Add categories via FAB on mobile or "+ Add" button on desktop

### Item Management
- Add/edit/delete consumable types
- Configure: name, category, unit, weekly usage rate, minimum stock level, notes
- Per-item custom usage rate override
- Edit modal with all fields + delete option

### Backup & Restore
- Download SQLite database for backup via Settings modal
- Upload and restore from backup files
- Confirmation dialog before restore (destructive action)

### Authentication
- Simple password-based authentication
- Session-based with httpOnly cookies

### Mobile-First UI
- CSS is mobile-first; desktop styles in `@media (min-width: 769px)`
- Fixed top navigation bar (mobile) with 4 view tabs
- Desktop header with sticky nav bar
- Bottom-sheet modals on mobile, centered overlays on desktop
- Floating Action Button (FAB): context-aware
  - Manage view: opens Add Category modal
  - Other views: navigates to Purchases view
  - Hidden on desktop (769px+)
- Toast notifications (success, error, info) replace browser alerts
- Custom confirmation dialogs replace browser confirm()
- 44px minimum touch targets on all interactive elements
- Collapsible category groups on dashboard (mobile)

### Other
- Environment indicator badge in header (dev/beta/staging)
- Dashboard data caching with invalidation on data changes
- XSS prevention via HTML escaping helper
- Easter egg (hearts animation)

---

## Technical Architecture

### Stack
| Component | Technology |
|-----------|------------|
| Backend | Flask 3.0.0 (Python 3.11) |
| Database | SQLite3 |
| Frontend | Vanilla HTML/CSS/JavaScript (SPA) |
| Server | Gunicorn (production) |
| Containerization | Docker + Docker Compose |
| CI/CD | GitHub Actions |

### Project Structure
```
homeinventory-backup/
├── backend/
│   ├── app.py              # Flask API (~500 lines, 14 route groups)
│   ├── database.py         # SQLite schema & initialization
│   ├── config.py           # Configuration management
│   └── tests/              # Pytest test suite
│       └── test_api.py     # 29+ tests
├── frontend/
│   ├── index.html          # Single-page application (4 views + 5 modals)
│   ├── js/app.js           # Application logic (~1225 lines)
│   └── css/styles.css      # Mobile-first responsive styling (~1660 lines)
├── data/                   # Persistent data (mounted volume, gitignored)
│   └── inventory.db        # SQLite database
├── docs/
│   ├── spec.md             # This file — project specification
│   ├── HANDOFF.md          # Session handoff for continuity
│   ├── in-progress/        # Active planning docs
│   │   ├── IMPROVEMENTS.md # Refactoring tracker (6 of 9 done)
│   │   └── PLAN-new-features.md  # Feature tracker (3 of 5 done)
│   └── completed/          # Finished plans from previous sessions
│       ├── HANDOFF.md      # Archived handoff from first session
│       └── PLAN-improvements-6-9.md  # Completed improvement plan
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── .github/workflows/      # CI/CD pipeline
└── README.md
```

### Database Schema
| Table | Purpose |
|-------|---------|
| categories | Item categories with name and emoji icon |
| consumable_types | Product definitions with usage rates, units, min stock |
| inventory | Current stock levels per item, optional custom usage rate |
| purchases | Purchase history with quantity, date, price |
| usage_log | *Unused - candidate for removal* |

### API Endpoints

#### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Log in with password |
| POST | `/api/auth/logout` | Log out |
| GET | `/api/auth/check` | Check authentication status |

#### Categories
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/categories` | List all categories |
| POST | `/api/categories` | Create new category (name + icon) |
| PUT | `/api/categories/{id}` | Update category name/icon |
| DELETE | `/api/categories/{id}` | Delete category (blocked if has items) |

#### Consumables (Items)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/consumables` | List all items (optional `?category_id=` filter) |
| POST | `/api/consumables` | Create new item |
| PUT | `/api/consumables/{id}` | Update item details |
| DELETE | `/api/consumables/{id}` | Delete item and its purchase history |

#### Inventory
| Method | Endpoint | Description |
|--------|----------|-------------|
| PUT | `/api/inventory/{id}` | Update stock level and custom usage rate |

#### Purchases
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/purchases` | List all purchases |
| POST | `/api/purchases` | Log a new purchase (updates inventory) |
| DELETE | `/api/purchases/{id}` | Delete purchase (updates inventory) |

#### Dashboard & Stats
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard` | Dashboard data with days-until-empty (cached) |
| GET | `/api/stats` | Summary statistics |

#### Backup
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/backup/download` | Download SQLite database file |
| POST | `/api/backup/upload` | Upload and restore database file |

#### Other
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/environment` | Get environment name for UI badge |
| GET | `/api/health` | Health check endpoint |

---

## Deployment

### Requirements
- Docker and Docker Compose
- Persistent volume for SQLite database

### Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| SECRET_KEY | Yes | Flask session secret |
| APP_PASSWORD | Yes | Login password (min 8 characters) |
| APP_ENVIRONMENT | No | Environment name for UI badge |
| DATABASE_PATH | No | Database file path (default: /app/data/inventory.db) |

### Port
- Container exposes port 5000
- Default host mapping: 828:5000

---

## Roadmap

### Planned Features

#### Phase 1: Notifications & Alerts
- Email notifications when items reach low stock
- Configurable alert thresholds
- Daily/weekly digest option

#### Phase 2: Shopping List Export
- Generate shopping list from items needing purchase
- Export formats: plain text, markdown, printable
- Optional: integration with shopping list apps

#### Phase 3: Usage Analytics
- Charts showing consumption patterns over time
- Per-item usage trends
- Monthly/quarterly consumption reports
- Identify seasonal patterns

#### Phase 4: Barcode Scanning
- Scan product barcodes to quickly add purchases
- Barcode lookup for product information
- Mobile camera integration

### Remaining Improvements (from IMPROVEMENTS.md)

| # | Item | Status |
|---|------|--------|
| 1 | Remove unused usage_log table | To do |
| 3 | Eliminate custom usage rate feature | To do |
| 9 | Add show/hide toggle to login password field | To do |

### Remaining Features (from PLAN-new-features.md)

| # | Feature | Status |
|---|---------|--------|
| 1 | Voice input for purchases | To do |
| 3 | Multi-edit mode (quantity + usage rates) | To do |

---

## Out of Scope

The following are explicitly **not** goals for this project:

- Multi-user/multi-household support
- Commercial/SaaS deployment
- Real-time sync across devices
- Integration with external inventory systems
- Automated purchasing/ordering
- Recipe or meal planning features
- Price comparison or deal finding

---

## Security Considerations

- Password-based authentication with secure session cookies
- Input validation on all endpoints
- XSS prevention via HTML escaping (`escapeHtml()` helper)
- SQL injection prevention via parameterized queries
- SQLite file validation on backup upload
- CORS enabled with credentials support

---

## Testing

- Framework: Pytest with coverage reporting
- CI/CD: GitHub Actions runs tests on every push
- Test categories: Authentication, CRUD operations, Dashboard calculations, Category management

---

## Constraints

| Constraint | Details |
|------------|---------|
| Hosting | Self-hosted Docker on personal infrastructure |
| Database | SQLite (single-file, no external database server) |
| Users | Single user, single household |
| Budget | Personal project, no recurring costs |
| Availability | Home network only (not publicly accessible) |
| Mobile Experience | Mobile browser is the primary access method; desktop is secondary |

---

## Document History

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-09 | 1.0 | Initial specification |
| 2026-02-11 | 2.0 | Updated with all post-MVP features: custom categories, mobile-first UI redesign, 3-dot menus, context-aware FAB, toast notifications, bottom-sheet modals, inventory view toggle. Expanded API endpoint documentation. Updated project structure and file sizes. |
