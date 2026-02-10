# Home Inventory Manager - Specification

## Overview

**Project Name:** Home Inventory Manager
**Version:** MVP / Early Stage
**Status:** Active Development
**Primary Use:** Personal household inventory tracking

A self-hosted web application for tracking household consumables and determining when items need to be restocked based on usage rates.

---

## Goals

### Primary Goal
Provide a simple, reliable way to track household consumable inventory and know when to purchase more before running out.

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

## Current Features (MVP)

### Dashboard
- Items that need to be purchased (below minimum stock level)
- Low-stock warnings (less than 7 days supply remaining)
- "Days until empty" calculations based on usage rates
- Quick statistics: items needing purchase, total tracked items, recent purchases

### Inventory Management
- Track current stock levels for each item
- Per-item customizable usage rates
- 27 pre-configured consumable items across 3 categories
- Categories: Household, Food & Pantry, Personal Care

### Purchase Logging
- Log purchases with quantity, date, and optional price
- Automatic inventory quantity updates
- Purchase history with deletion capability

### Item Management
- Add/edit/delete consumable types
- Configure: name, unit, usage rate, minimum stock level, notes

### Backup & Restore
- Download SQLite database for backup
- Upload and restore from backup files

### Authentication
- Simple password-based authentication
- Session-based with httpOnly cookies

### Mobile Support
- Responsive design
- Bottom navigation bar
- Floating action button for quick purchases

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
│   ├── app.py              # Flask API (13 route groups)
│   ├── database.py         # SQLite schema & initialization
│   ├── config.py           # Configuration management
│   └── tests/              # Pytest test suite
├── frontend/
│   ├── index.html          # Single-page application
│   ├── js/app.js           # Application logic
│   └── css/styles.css      # Responsive styling
├── data/                   # Persistent data (mounted volume)
│   └── inventory.db        # SQLite database
├── docker-compose.yml
├── Dockerfile
└── .github/workflows/      # CI/CD pipeline
```

### Database Schema
| Table | Purpose |
|-------|---------|
| categories | Item categories (Household, Food, Personal Care) |
| consumable_types | Product definitions with usage rates |
| inventory | Current stock levels per item |
| purchases | Purchase history |
| usage_log | *Unused - candidate for removal* |

### API Endpoints
- `POST /api/auth/login` - Authentication
- `GET /api/categories` - List categories
- `GET/POST/PUT/DELETE /api/consumables` - Item management
- `PUT /api/inventory/<id>` - Update stock levels
- `GET/POST/DELETE /api/purchases` - Purchase logging
- `GET /api/dashboard` - Dashboard data with calculations
- `GET /api/stats` - Summary statistics
- `GET/POST /api/backup/*` - Backup and restore

---

## Deployment

### Requirements
- Docker and Docker Compose
- Persistent volume for SQLite database

### Environment Variables
| Variable | Description |
|----------|-------------|
| SECRET_KEY | Flask session secret (required) |
| APP_PASSWORD | Login password (required) |
| ENVIRONMENT | Environment name for UI badge |

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

### Technical Improvements

#### Standardize Usage Rates
- Simplify to weekly-only usage rate calculations
- Remove daily/monthly period options
- Clearer, more consistent UI

#### Code Consolidation
- Refactor duplicate item rendering functions (~4-5 similar functions)
- Consolidate purchase rendering logic
- Reduce frontend code duplication

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
- XSS prevention via HTML escaping
- SQL injection prevention via parameterized queries
- SQLite file validation on backup upload
- CORS enabled with credentials support

---

## Testing

- Framework: Pytest with coverage reporting
- CI/CD: GitHub Actions runs tests on every push
- Test categories: Authentication, CRUD operations, Dashboard calculations

---

## Constraints

| Constraint | Details |
|------------|---------|
| Hosting | Self-hosted Docker on personal infrastructure |
| Database | SQLite (single-file, no external database server) |
| Users | Single user, single household |
| Budget | Personal project, no recurring costs |
| Availability | Home network only (not publicly accessible) |

---

## Document History

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-09 | 1.0 | Initial specification |
