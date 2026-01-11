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

1. **Build and run with Docker Compose:**

```bash
docker-compose up -d
```

2. **Access the application:**

Open http://localhost:828 in your browser.

3. **Default password:** `home123`

## Configuration

Create a `.env` file to customize:

```env
SECRET_KEY=your-secret-key-here
APP_PASSWORD=your-password-here
```

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
python app.py
```
