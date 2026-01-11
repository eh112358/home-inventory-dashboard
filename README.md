# Home Inventory Manager

A simple Docker-based application for tracking household consumables and knowing when to restock.

## Features

- Dashboard showing items that need to be purchased
- Track consumables across categories: Household, Food & Pantry, Personal Care
- Log purchases and automatically update inventory
- Usage rate estimation based on a family of 5 (2 adults, 3 young children)
- Editable usage rates per item
- Simple password protection

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

## Pre-configured Items

The app comes with common household items pre-configured with estimated usage rates for a family of 5:

**Household:** Toilet Paper, Paper Towels, Dish Soap, Laundry Detergent, Trash Bags, Diapers, Baby Wipes, etc.

**Food & Pantry:** Milk, Bread, Eggs, Butter, Cereal, Juice Boxes, Snacks, etc.

**Personal Care:** Toothpaste, Shampoo, Body Wash, Hand Soap, Lotion, Sunscreen, Band-Aids, etc.

## Usage

1. **Dashboard** - See what needs to be purchased and items running low
2. **Inventory** - View current stock levels for all items
3. **Purchases** - Log new purchases to update inventory
4. **Manage Items** - Add/edit/delete consumable types and adjust usage rates

## Data Persistence

All data is stored in a SQLite database mounted as a Docker volume (`inventory-data`).

To backup your data:

```bash
docker cp home-inventory:/app/data/inventory.db ./backup.db
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
