Based on my comprehensive exploration, here are my recommendations for simplifying your home inventory dashboard:

## High-Priority Simplifications (Quick Wins)

### 1. Remove Unused usage_log Table
- This table exists in the schema but is never populated or used
- Saves database complexity and maintenance overhead
- No user impact since it's completely unused

### 2. ✅ Consolidate Duplicate Navigation — COMPLETED
- ~~You have both desktop nav (top) and mobile nav (bottom) with identical functionality~~
- ~~Use a single nav component with CSS media queries for positioning~~
- ~~Saves ~50+ lines of duplicate HTML/JS~~

**Implemented:** Added shared `view-nav-btn` class to all 8 nav buttons. Consolidated two separate event listener blocks and two separate active-state update blocks into single blocks using `.view-nav-btn` in both `setupEventListeners()` and `switchView()`. (Commit: f1aea75+)

### 3. Eliminate Custom Usage Rate Feature
- Adds calculation complexity throughout codebase
- Allows per-item rate overrides that may not be needed for typical use
- If most items use defaults, this is just extra complexity

## UI Improvements

### 9. Add Show/Hide Toggle to Login Password Field
- Password field has no visibility toggle, making it hard to verify input on mobile
- Add an eye icon button next to the password input that toggles between `type="password"` and `type="text"`
- Frontend-only change: `index.html` (button markup) + `app.js` (toggle handler) + `styles.css` (button positioning)

## Medium-Priority Refactoring

### 4. ✅ Unify Item Rendering Functions — COMPLETED
- ~~renderItemsGrid() — dead code, never called~~
- ~~renderManageList() and renderInventoryList() — 100% identical HTML~~

**Implemented:** Deleted dead `renderItemsGrid()` function (~47 lines). Merged `renderInventoryList()` and `renderManageList()` into a single `renderItemList(containerId, emptyMessage)` function. Net reduction of ~75 lines. (Commit: f1aea75+)

### 5. ✅ Standardize on Weekly Usage Rates — COMPLETED
- ~~Currently supports 3 periods (day/week/month) with conversion logic~~
- ~~Simplification: Pick weekly as standard, remove period flexibility~~
- ~~Reduces calculation complexity in backend (app.py:417-424)~~

**Implemented:** All usage rates are now weekly-only. Removed period selectors from UI, simplified backend calculations, updated tests. (Commit: cc4dc12)

### 6. ✅ Consolidate Purchase Rendering — COMPLETED
- ~~Separate functions for desktop table vs mobile cards~~
- ~~Both render same data with different markup~~
- ~~Could use single data structure with CSS-only layout switching~~

**Implemented:** Replaced dual table/cards rendering with single CSS Grid layout. Deleted `renderPurchasesCards()` function. Responsive design via media queries. (Commit: cc4dc12)

## Backend Infrastructure Simplifications

### 7. ✅ Remove Unused API Endpoint — COMPLETED
- ~~/api/usage-rate/<id> exists but isn't called by frontend~~
- ~~Frontend uses /api/inventory/<id> PUT instead~~
- ~~Clean up unused routes~~

**Implemented:** Deleted the unused `/api/usage-rate/<id>` endpoint from app.py. (Commit: cc4dc12)

### 8. ✅ Simplify Dashboard Calculations — COMPLETED
- ~~The "days until empty" calculation runs on every dashboard request with no caching.~~

**Implemented:** Added invalidation-based caching. Dashboard data is cached and only recalculated when inventory, purchases, or consumables change. Cache invalidation added to all 6 data-modifying endpoints. (Commit: cc4dc12)

---

## What to Keep (Working Well)
✅ Mobile UI enhancements (FAB, collapsible categories, responsive cards)
✅ Backup/restore functionality
✅ Authentication system
✅ Test coverage
✅ Database migrations
✅ Easter egg (it's fun!)

## Progress Summary

| # | Item | Status |
|---|------|--------|
| 1 | Remove unused usage_log table | To do |
| 2 | Consolidate duplicate navigation | ✅ Done |
| 3 | Eliminate custom usage rate feature | To do |
| 4 | Unify item rendering functions | ✅ Done |
| 5 | Standardize on weekly usage rates | ✅ Done |
| 6 | Consolidate purchase rendering | ✅ Done |
| 7 | Remove unused API endpoint | ✅ Done |
| 8 | Simplify dashboard calculations | ✅ Done |
| 9 | Add show/hide toggle to login password field | To do |
