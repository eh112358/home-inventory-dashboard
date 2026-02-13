# Code Cleanup: Orphaned & Obsolete Code

A full audit of the application found dead functions, unused styles, vestigial parameters, and other orphaned code left behind from previous refactors. None of this code causes bugs, but removing it reduces maintenance burden and makes the codebase easier to understand.

---

## HIGH PRIORITY — Dead Functions & Their Styles

### 1. ✅ Remove `renderItemsGridGrouped()` function — COMPLETED
- ~~**File:** `frontend/js/app.js` lines 1070-1125~~
- ~~**What it is:** The old dashboard render function that drew large item cards in a grid. It was replaced by `renderDashboardItems()` during the compact row redesign.~~

**Removed:** Deleted the entire function (~56 lines). Updated stale comment on `renderDashboardItems()`.

### 2. ✅ Remove `renderItemCards()` function — COMPLETED
- ~~**File:** `frontend/js/app.js` lines 1128-1160~~
- ~~**What it is:** Helper that generated the HTML for individual item cards (`.item-card` elements). Only ever called by `renderItemsGridGrouped()`.~~

**Removed:** Deleted the entire function (~33 lines).

### 3. ✅ Remove `.item-card` and all related CSS — COMPLETED
- ~~**File:** `frontend/css/styles.css` lines 507-595~~
- ~~**What it is:** 15 selectors for the old dashboard cards: `.item-card`, `.item-header`, `.item-name`, `.item-category`, `.item-stats`, `.item-quantity`, `.item-unit`, `.item-days`, `.item-actions`, and their variants.~~

**Removed:** Deleted all 15 selectors (~89 lines). Preserved `.btn-purchase` and `.btn-edit` which are still used by compact row actions.

### 4. ✅ Remove `.items-grid` CSS — COMPLETED
- ~~**File:** `frontend/css/styles.css` — 3 locations: base styles, `.category-content` override, desktop media query override~~
- ~~**What it is:** The grid layout container that held the old item cards on the dashboard. Replaced by `.items-compact-list`.~~

**Removed:** Deleted all 3 rules (~12 lines). Verified no `items-grid` references remain anywhere in the frontend.

---

## MEDIUM PRIORITY — Unused Backend Code

### 5. Remove unused `timedelta` import
- **File:** `backend/app.py` line 4
- **What it is:** `from datetime import datetime, timedelta` — `timedelta` is imported but never used anywhere in the file.
- **Fix:** Change to `from datetime import datetime`

---

## LOW PRIORITY — Code Quality Improvements

### 6. ✅ Remove `showUrgent` parameter from dead functions — RESOLVED
- ~~Vestigial parameter in `renderItemsGridGrouped()` and `renderItemCards()`.~~

**Resolved:** Automatically fixed when items #1 and #2 were completed — the entire functions containing this parameter were deleted.

### 7. Replace inline styles with CSS classes
- **File:** `frontend/js/app.js`
  - Line 621: `style="font-size:0.8rem;color:var(--gray-500)"` on a `<span>` for unit display in the inventory list
  - Lines 1098, 1217: `style="${!isCollapsed ? 'max-height: 2000px;' : ''}"` on category content divs
- **What it is:** Inline styles that should be CSS classes for consistency with the rest of the codebase.
- **Fix for line 621:** Create a `.list-item-unit` CSS class with those properties
- **Fix for lines 1098/1217:** Create a CSS rule like `.category-content:not(.collapsed) { max-height: 2000px; }` and remove the inline style entirely. The collapse/expand already toggles the `.collapsed` class.

---

## Summary

| # | Item | File(s) | Lines Removed | Status |
|---|------|---------|---------------|--------|
| 1 | Remove `renderItemsGridGrouped()` | app.js | ~56 | ✅ Done |
| 2 | Remove `renderItemCards()` | app.js | ~33 | ✅ Done |
| 3 | Remove `.item-card` CSS | styles.css | ~89 | ✅ Done |
| 4 | Remove `.items-grid` CSS | styles.css | ~12 | ✅ Done |
| 5 | Remove unused `timedelta` import | app.py | 1 | To do |
| 6 | Remove `showUrgent` parameter | app.js | (covered by #1-2) | ✅ Resolved |
| 7 | Replace inline styles with CSS classes | app.js, styles.css | net 0 (refactor) | To do |

**Completed:** ~190 lines of dead code removed from `app.js` and `styles.css`. All 46 backend tests pass. Frontend JS parses cleanly. No stale class references remain.

**Remaining:** 2 items (medium + low priority)
