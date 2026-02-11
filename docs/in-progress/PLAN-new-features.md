# New Features Implementation Plan

## Features Overview

| # | Feature | Scope | Complexity | Status |
|---|---------|-------|------------|--------|
| 1 | Voice input for purchases | Frontend only | Medium | To do |
| 2 | Inventory table/grid view toggle | Frontend only | Low | ✅ Done |
| 3 | Multi-edit mode (quantity + usage rates) | Full stack | Medium | To do |
| 4 | Add custom categories | Full stack | Low | ✅ Done |
| 5 | Edit/delete existing categories | Full stack | Low | ✅ Done |

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

## Feature 2: ✅ Inventory Table/Grid View Toggle — COMPLETED

**Implemented:** Toggle buttons (list/grid icons) in inventory filter bar, visible on desktop only (hidden on mobile where list view is always used). Grid view renders items in a CSS Grid table with aligned columns (Name, Category, Qty, Usage, Min, Edit). Preference persists in localStorage via `inventoryViewMode`. New functions: `renderInventoryGrid()`, `renderInventoryView()`, `setInventoryViewMode()`. (Commit: 2d2f63a)

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

## Feature 4: ✅ Add Custom Categories — COMPLETED

**Implemented:** Added `POST /api/categories` endpoint with name validation (required, max 50 chars, case-insensitive uniqueness) and default icon (📦). Frontend includes inline form with emoji picker in Manage Items view. Categories list renders with edit/delete buttons. Tests added. (Commit: f1aea75)

---

## Feature 5: ✅ Edit/Delete Existing Categories — COMPLETED

**Implemented:** Added `PUT /api/categories/{id}` and `DELETE /api/categories/{id}` endpoints. Update validates unique name, delete blocks if items exist in category (409 with item count). Frontend edit opens modal with name/icon fields, delete shows confirmation. All category dropdowns refresh after changes. Tests added. (Commit: f1aea75)

---

## Implementation Order

1. ~~**Features 4 & 5 (Categories)** - Foundation, no dependencies~~ ✅ Done
2. ~~**Feature 2 (Grid Toggle)** - Simple, frontend only~~ ✅ Done
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
- [x] Grid: Toggle persists across page reloads
- [x] Grid: Both views render correctly, edit works in both
- [ ] Multi-Edit: Changes highlighted, Save All updates all modified items
- [ ] Multi-Edit: Cancel discards changes
- [x] Categories: Create new category, appears in all dropdowns
- [x] Categories: Edit name/icon, changes reflected everywhere
- [x] Categories: Delete empty category succeeds
- [x] Categories: Delete category with items shows error message
- [ ] Mobile: Voice button works, grid toggle hidden, multi-edit hidden

---

## Files Summary

| File | Changes |
|------|---------|
| `backend/app.py` | ✅ +3 category endpoints (POST/PUT/DELETE), remaining: +1 batch inventory |
| `backend/tests/test_api.py` | ✅ +category CRUD tests, remaining: +batch inventory tests |
| `frontend/index.html` | ✅ +category section/modals, ✅ +toggle buttons, remaining: +voice button |
| `frontend/js/app.js` | ✅ +category CRUD/emoji picker, ✅ +view toggle, remaining: +VoiceInput, +multi-edit |
| `frontend/css/styles.css` | ✅ +category/emoji styles, ✅ +grid toggle, remaining: +voice, +multi-edit styles |

---

## API Contracts Summary

### Categories (✅ All implemented)
| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/api/categories` | List all categories | ✅ Done |
| POST | `/api/categories` | Create new category | ✅ Done |
| PUT | `/api/categories/{id}` | Update category name/icon | ✅ Done |
| DELETE | `/api/categories/{id}` | Delete category (blocked if has items) | ✅ Done |

### Inventory
| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| PUT | `/api/inventory/batch` | Batch update quantities and usage rates | To do |
