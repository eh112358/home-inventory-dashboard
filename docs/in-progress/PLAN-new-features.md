# New Features Implementation Plan

## Features Overview

| # | Feature | Scope | Complexity | Status |
|---|---------|-------|------------|--------|
| 1 | Voice input for purchases | Frontend only | Medium | To do |
| 2 | Inventory table/grid view toggle | Frontend only | Low | ✅ Done |
| 3 | Multi-edit mode (quantity + usage rates) | Full stack | Medium | ✅ Done |
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

## Feature 3: ✅ Multi-Edit Mode — COMPLETED

**Implemented:** Added `PUT /api/inventory/batch` endpoint that accepts up to 100 item updates in a single request with per-item validation and partial success support. Frontend adds a pencil toggle button in inventory filter bar (mobile + desktop). Entering multi-edit replaces static quantity/usage text with inline number inputs within existing list items. Changed items highlight yellow, a sticky save/cancel bar shows count. "Save All" sends a single batch API call. Works on both mobile (stacked card layout) and desktop (horizontal row layout). New functions: `enterMultiEdit()`, `exitMultiEdit()`, `renderMultiEditList()`, `saveMultiEdit()`. Tests added for batch endpoint. (Commit: pending)

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
3. ~~**Feature 3 (Multi-Edit)** - More complex, builds on grid patterns~~ ✅ Done
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
- [x] Multi-Edit: Changes highlighted, Save All updates all modified items
- [x] Multi-Edit: Cancel discards changes
- [x] Categories: Create new category, appears in all dropdowns
- [x] Categories: Edit name/icon, changes reflected everywhere
- [x] Categories: Delete empty category succeeds
- [x] Categories: Delete category with items shows error message
- [ ] Mobile: Voice button works, grid toggle hidden, multi-edit works on mobile

---

## Files Summary

| File | Changes |
|------|---------|
| `backend/app.py` | ✅ +3 category endpoints, ✅ +batch inventory endpoint, remaining: none for planned features |
| `backend/tests/test_api.py` | ✅ +category CRUD tests, ✅ +batch inventory tests, remaining: none for planned features |
| `frontend/index.html` | ✅ +category section/modals, ✅ +toggle buttons, ✅ +multi-edit controls, remaining: +voice button |
| `frontend/js/app.js` | ✅ +category CRUD/emoji picker, ✅ +view toggle, ✅ +multi-edit mode, remaining: +VoiceInput |
| `frontend/css/styles.css` | ✅ +category/emoji styles, ✅ +grid toggle, ✅ +multi-edit styles, remaining: +voice styles |

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
| PUT | `/api/inventory/batch` | Batch update quantities and usage rates | ✅ Done |
