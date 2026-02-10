# New Features Implementation Plan

## Features Overview

| # | Feature | Scope | Complexity |
|---|---------|-------|------------|
| 1 | Voice input for purchases | Frontend only | Medium |
| 2 | Inventory table/grid view toggle | Frontend only | Low |
| 3 | Multi-edit mode (quantity + usage rates) | Full stack | Medium |
| 4 | Add custom categories | Full stack | Low |
| 5 | Edit/delete existing categories | Full stack | Low |

## Design Decisions

- **Voice Input**: Auto-fill form fields, user confirms before submit
- **Grid View**: Toggle option (user switches between list and grid views)
- **Multi-Edit**: Edit stock quantities AND usage rates together
- **Category Deletion**: Block if items exist in category

---

## Feature 1: Voice Input for Purchases

### Implementation
- Use Web Speech API (`SpeechRecognition`)
- Add microphone button to purchase form
- Parse speech like "5 rolls of paper towels" → extract quantity + fuzzy match item
- Show confirmation modal before auto-filling form

### Files to Modify
- `frontend/index.html` - Add mic button, voice status indicator, confirmation modal
- `frontend/js/app.js` - Add `VoiceInput` module with speech recognition handlers
- `frontend/css/styles.css` - Voice button styles, listening animation, modal styles

### Key Code
```javascript
// Parse patterns: "5 rolls of paper towels", "10 boxes cereal", "3 milk"
const patterns = [
    /(\d+(?:\.\d+)?)\s+(?:rolls?|boxes?|bottles?|packs?|units?|cans?|bags?|gallons?|dozens?)\s+(?:of\s+)?(.+)/i,
    /(\d+(?:\.\d+)?)\s+(.+)/i
];
```

### Edge Cases
- Browser doesn't support Web Speech API: Hide microphone button
- Microphone permission denied: Show clear error message
- Item not found: Display parsed name, allow manual selection
- Quantity not detected: Allow manual entry

---

## Feature 2: Inventory Table/Grid View Toggle

### Implementation
- Add toggle buttons (list/grid icons) to Inventory view header
- Grid view: table-like layout with columns (Name, Category, Qty, Usage, Min, Actions)
- Store preference in `localStorage`
- Hide toggle on mobile (always list view)

### Files to Modify
- `frontend/index.html` - Add toggle buttons in Inventory section header
- `frontend/js/app.js` - Add `inventoryViewMode` state, `renderInventoryGrid()` function
- `frontend/css/styles.css` - Grid view styles, toggle button styles

### Grid Layout
```css
.grid-header, .grid-row {
    display: grid;
    grid-template-columns: 2fr 1.5fr 1fr 0.8fr 0.8fr 80px;
    gap: 1rem;
}
```

---

## Feature 3: Multi-Edit Mode

### Backend
Add batch update endpoint:
```
PUT /api/inventory/batch
Body: { "updates": [{ "consumable_type_id": 1, "current_quantity": 10, "custom_usage_rate": 3 }, ...] }
Response: { "success": true, "updated": 2 }
```

Validation:
- Max 100 updates per request
- Validate each quantity and usage rate
- Return partial success (HTTP 207) if some updates fail

### Frontend
- Add "Edit Multiple" button to Inventory view
- Transform to editable grid with input fields for quantity + usage rate
- Track modified items with `Map`, highlight changes
- Save All / Cancel buttons
- Single batch API call

### Files to Modify
- `backend/app.py` - Add `batch_update_inventory()` endpoint
- `frontend/index.html` - Add multi-edit controls
- `frontend/js/app.js` - Add `editedItems` Map, render/save functions
- `frontend/css/styles.css` - Multi-edit grid styles, modified row highlighting

---

## Feature 4: Add Custom Categories

### Backend
Add create endpoint:
```
POST /api/categories
Body: { "name": "Electronics", "icon": "🔌" }
Response: { "id": 4, "name": "Electronics", "icon": "🔌", "success": true }
```

Validation:
- Name required, max 50 characters
- Unique name (case-insensitive)
- Default icon: 📦

### Frontend
- Add "Categories" section to Manage Items view
- Inline form: emoji picker + name input
- Render categories list with edit/delete buttons

### Files to Modify
- `backend/app.py` - Add `create_category()` endpoint
- `frontend/index.html` - Add category form, emoji picker modal
- `frontend/js/app.js` - Add category form handlers, emoji picker
- `frontend/css/styles.css` - Category list styles, emoji picker grid

### Emoji Picker
```javascript
const CATEGORY_EMOJIS = [
    '📦', '🏠', '🍎', '🧴', '🧹', '🧺', '🧽', '🧻',
    '💊', '🩹', '🧸', '🎮', '📚', '✏️', '🔧', '🔌',
    '🚗', '🌱', '🐕', '🐈', '👶', '👕', '🧴', '🧼'
];
```

---

## Feature 5: Edit/Delete Existing Categories

### Backend
Add update and delete endpoints:
```
PUT /api/categories/{id}
Body: { "name": "New Name", "icon": "🏠" }
Response: { "id": 1, "name": "New Name", "icon": "🏠", "success": true }

DELETE /api/categories/{id}
Response: { "success": true }
Error: { "error": "Cannot delete category \"Household\": 9 item(s) are using this category." }
```

Validation:
- Check category exists (404 if not)
- Check unique name on update (409 if duplicate)
- Block deletion if items exist (409 with item count)

### Frontend
- Edit button opens modal with name/icon fields
- Delete button shows confirmation, displays error if blocked
- Refresh all category dropdowns after changes

### Files to Modify
- `backend/app.py` - Add `update_category()`, `delete_category()` endpoints
- `frontend/index.html` - Add edit category modal
- `frontend/js/app.js` - Add edit/delete handlers
- `backend/tests/test_api.py` - Add category CRUD tests

---

## Implementation Order

1. **Features 4 & 5 (Categories)** - Foundation, no dependencies
2. **Feature 2 (Grid Toggle)** - Simple, frontend only
3. **Feature 3 (Multi-Edit)** - More complex, builds on grid patterns
4. **Feature 1 (Voice Input)** - Independent, can parallel others

---

## Verification Plan

### Backend Tests
```bash
cd backend && pytest tests/ -v
```
- Test category CRUD (create, update, delete, block deletion with items)
- Test batch inventory update (valid, partial failure, validation errors)

### Manual Testing Checklist
- [ ] Voice: Mic button appears, speech recognized, item matched, form filled
- [ ] Voice: Graceful handling when browser doesn't support Web Speech API
- [ ] Grid: Toggle persists across page reloads
- [ ] Grid: Both views render correctly, edit works in both
- [ ] Multi-Edit: Changes highlighted, Save All updates all modified items
- [ ] Multi-Edit: Cancel discards changes
- [ ] Categories: Create new category, appears in all dropdowns
- [ ] Categories: Edit name/icon, changes reflected everywhere
- [ ] Categories: Delete empty category succeeds
- [ ] Categories: Delete category with items shows error message
- [ ] Mobile: Voice button works, grid toggle hidden, multi-edit hidden

---

## Files Summary

| File | Changes |
|------|---------|
| `backend/app.py` | +4 endpoints (POST/PUT/DELETE categories, PUT batch inventory) |
| `backend/tests/test_api.py` | +tests for new endpoints |
| `frontend/index.html` | +voice button, +modals, +category section, +toggle buttons |
| `frontend/js/app.js` | +VoiceInput module, +view toggle, +multi-edit, +category CRUD |
| `frontend/css/styles.css` | +all new component styles |

---

## API Contracts Summary

### Categories
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/categories` | List all categories (existing) |
| POST | `/api/categories` | Create new category |
| PUT | `/api/categories/{id}` | Update category name/icon |
| DELETE | `/api/categories/{id}` | Delete category (blocked if has items) |

### Inventory
| Method | Endpoint | Description |
|--------|----------|-------------|
| PUT | `/api/inventory/batch` | Batch update quantities and usage rates |
