# Home Inventory Manager

A simple, self-hosted web application for tracking household consumables and knowing when to restock. Mobile-first design optimized for quick use on your phone.

## Features

### Dashboard
- Items that need to be purchased (below minimum stock level)
- Low-stock warnings (less than 7 days supply remaining)
- "Days until empty" calculations based on weekly usage rates
- Quick stats: items needing purchase, total tracked, recent purchases (7 days)
- Items grouped by category with collapsible sections on mobile

### Inventory
- View current stock levels for all items
- List view (default) and grid/table view toggle (desktop)
- Filter by category

### Purchases
- Log purchases with quantity, date, and optional price
- Automatic inventory quantity updates on purchase
- Purchase history with deletion

### Category Management
- Create custom categories with emoji icons (24 emoji choices)
- Edit category name and icon
- Delete categories (blocked if items still assigned)
- Compact list with 3-dot overflow menu for Edit/Delete actions
- Add categories via FAB (mobile) or "+ Add" button (desktop)

### Item Management
- Add/edit/delete consumable items
- Configure: name, unit, weekly usage rate, minimum stock level, notes
- Per-item custom usage rate override

### Mobile-First UI
- Bottom-sheet modals on mobile, centered overlays on desktop
- Fixed top navigation bar with 4 views
- Floating Action Button (FAB): context-aware (add category on Manage view, quick purchase on others)
- Toast notifications instead of browser alerts
- Custom confirmation dialogs
- 44px minimum touch targets throughout

### Other
- Simple password-based authentication
- Database backup download and restore via Settings
- Environment indicator badge (dev/beta/staging)
- Easter egg

## Quick Start

1. **Create a `.env` file (required):**

```bash
cp .env.example .env
```

Edit `.env` and set your values:
```env
SECRET_KEY=your-long-random-secret-key
APP_PASSWORD=your-secure-password-min-8-chars
```

Generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

2. **Build and run with Docker Compose:**

```bash
docker-compose up -d
```

3. **Access the application:**

Open http://localhost:828 in your browser and log in with your `APP_PASSWORD`.

## Configuration

Environment variables (set in `.env` file):

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Secret key for session encryption |
| `APP_PASSWORD` | Yes | Application password (min 8 characters) |
| `DATABASE_PATH` | No | Database file path (default: /app/data/inventory.db) |
| `APP_ENVIRONMENT` | No | Environment indicator: `dev`, `beta`, `staging`, or `production` (default) |

## Usage

1. **Dashboard** - See what needs to be purchased and items running low. Tap an item to quick-purchase or edit.
2. **Inventory** - View current stock levels. Toggle between list and grid views on desktop.
3. **Purchases** - Log new purchases to update inventory. View and delete purchase history.
4. **Manage Items** - Create/edit/delete categories and items. Adjust usage rates and stock levels.

On mobile, use the floating **+** button at the bottom-right for quick actions (add purchase or add category depending on which view you're on).

## Data Storage

All data is stored in a SQLite database at `./data/inventory.db`. This directory is mounted directly into the container, so your data persists on your local filesystem.

**Backup:** Use the Settings modal in the app to download a backup, or copy the file directly:
```bash
cp ./data/inventory.db ./backup.db
```

**Restore:** Use the Settings modal to upload a backup file, or replace the database file and restart:
```bash
cp ./backup.db ./data/inventory.db
docker-compose restart
```

### Migrating from Named Volume

If you previously used the named volume (`inventory-data`), export your data before updating:
```bash
docker cp home-inventory:/app/data/inventory.db ./data/inventory.db
```

## Development

Run locally without Docker:

```bash
cd backend
pip install -r requirements.txt

# Set required environment variables
export SECRET_KEY="dev-secret-key-change-in-prod"
export APP_PASSWORD="devpassword"

python app.py
```

Run tests:
```bash
cd backend
pytest tests/ -v
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Flask 3.0.0 (Python 3.11) |
| Database | SQLite3 |
| Frontend | Vanilla HTML/CSS/JavaScript (SPA) |
| Server | Gunicorn (production) |
| Containerization | Docker + Docker Compose |
| CI/CD | GitHub Actions |
