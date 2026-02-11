# Session Handoff

## Project
Home Inventory Manager — a self-hosted web app for tracking household consumables and knowing when to buy more. Python/Flask backend with SQLite, vanilla HTML/CSS/JS frontend. Runs in Docker.

## Current Branch
`dev` — all active work happens here. `main` has the initial MVP only.

## Repository Layout
```
backend/           Python Flask API + SQLite database
  app.py           Main application (~500 lines)
  database.py      Schema & initialization
  config.py        Configuration management
  tests/           pytest test suite (29+ tests)
frontend/
  index.html       Single-page app (4 views + 5 modals, ~330 lines)
  css/styles.css   Mobile-first responsive styles (~1660 lines)
  js/app.js        All client logic (~1225 lines)
docs/
  spec.md          Product specification (v2.0)
  HANDOFF.md       This file — session continuity
  in-progress/     Active planning docs
    IMPROVEMENTS.md    Refactoring tracker (6 of 9 done)
    PLAN-new-features.md  Feature tracker (3 of 5 done)
  completed/       Finished plans from previous sessions
    HANDOFF.md         Archived handoff from first session
    PLAN-improvements-6-9.md  Completed improvement plan
```

## Commit History (dev branch)
```
bba6e22 Refactor categories UI with 3-dot menu, add-category modal, and context-aware FAB
134c3fd Improve category card layout on mobile with two-row grid
c92b485 Redesign frontend for mobile-first with bottom-sheet modals and toast notifications
2d2f63a Add inventory list/grid view toggle, consolidate navigation, and update docs
f1aea75 Add ability to create, edit, and delete categories
53bea13 docs: Add new features plan and session handoff
2881f30 docs: Mark items 6-9 as completed in improvement docs
cc4dc12 Implement IMPROVEMENTS.md items 6-9
9ac516f Initial commit: Home Inventory Manager MVP
```

## What Has Been Built (cumulative)

### MVP (commit 9ac516f)
- Flask API with auth, consumable CRUD, purchases, dashboard, backup/restore
- Desktop-first responsive SPA with 4 views
- 27 pre-configured items across 3 categories
- Docker deployment with CI/CD

### Improvements batch (commit cc4dc12)
- Standardized all usage rates to weekly-only (removed day/month)
- Consolidated purchase rendering into single CSS Grid layout
- Removed unused `/api/usage-rate` endpoint
- Added dashboard caching with invalidation

### Categories (commit f1aea75)
- Full CRUD for categories: POST/PUT/DELETE endpoints with validation
- Emoji icon picker (24 emojis)
- Delete blocked if items exist in category (409 error)
- Edit modal, inline add form

### Grid view + nav consolidation (commit 2d2f63a)
- Inventory list/grid view toggle (desktop only, persists in localStorage)
- Unified nav button event handling (shared `view-nav-btn` class)
- Merged duplicate `renderInventoryList()`/`renderManageList()` into `renderItemList()`

### Mobile-first redesign (commit c92b485)
- Full CSS rewrite: mobile-first base, desktop in `@media (min-width: 769px)`
- Bottom-sheet modals on mobile, centered overlays on desktop
- Toast notifications replacing all `alert()` calls
- Custom confirmation dialogs replacing `confirm()`
- 44px minimum touch targets on all interactive elements
- Floating Action Button (FAB) for quick purchases
- Fixed top nav bar on mobile, collapsible category groups on dashboard
- `inputmode="decimal"` on numeric inputs

### Category card layout fix (commit 134c3fd)
- Category cards use two-row grid on mobile (info row + actions row)
- Single-row flex on desktop

### Category UI refactor (commit bba6e22)
- Replaced Edit/Delete buttons with 3-dot overflow menu on category rows
- Moved add-category form from inline to a modal (bottom sheet on mobile)
- FAB is now context-aware: opens Add Category modal on Manage view, navigates to Purchases on other views
- Desktop gets "+ Add" button in section header (FAB hidden on desktop)
- Toast notification on successful category add

## Remaining Work

### From IMPROVEMENTS.md (3 items left)
| # | Item | Notes |
|---|------|-------|
| 1 | Remove unused usage_log table | DB table exists but is never read; drop table + remove backend code |
| 3 | Eliminate custom usage rate feature | Adds complexity; most items use defaults |
| 9 | Add show/hide toggle to login password field | Frontend-only, small task |

### From PLAN-new-features.md (2 features left)
| # | Feature | Scope |
|---|---------|-------|
| 1 | Voice input for purchases | Frontend only, medium complexity |
| 3 | Multi-edit mode (quantity + usage rates) | Full stack, medium complexity |

### Longer-term Roadmap (from spec.md)
- Notifications & alerts (email when items low)
- Shopping list export
- Usage analytics / charts
- Barcode scanning

## Key Patterns to Know

- **State management:** Global variables (`categories`, `consumables`, `currentView`, `activeCategoryDropdown`) + localStorage for preferences (`collapsedCategories`, `inventoryViewMode`)
- **API helper:** `api(endpoint, options)` handles auth, JSON, 401 redirects
- **XSS prevention:** `escapeHtml()` used in all template rendering
- **Mobile detection:** `isMobileView()` checks `window.innerWidth <= 768`
- **Render pattern:** Functions generate HTML strings with template literals, inject via `innerHTML`, then attach event listeners with `querySelectorAll`
- **Category grouping:** Dashboard items group by category on mobile with collapsible headers (`renderItemsGridGrouped`)
- **Modal system:** `.modal.hidden` toggled; `.close-modal` buttons and overlay clicks wired in `setupEventListeners()` via `querySelectorAll`
- **Toast system:** `showToast(message, type)` creates auto-removing toast elements
- **Confirm system:** `showConfirm(message)` returns a Promise, used with `await`
- **Category dropdown:** 3-dot button creates dropdown dynamically, `document.addEventListener('click', closeCategoryDropdown)` closes on outside click
- **FAB:** `handleFabClick()` checks `currentView` — opens add-category modal on manage, purchase flow on others

## Modals (5 in HTML + dynamic confirms)
1. `edit-modal` — Edit item (full form + delete button)
2. `quick-purchase-modal` — Quick add purchase for a specific item
3. `settings-modal` — Backup/restore + easter egg
4. `edit-category-modal` — Edit category name/icon + delete button
5. `add-category-modal` — Add new category with emoji picker
6. Confirm dialogs — Created dynamically via `showConfirm()`, not in HTML

## CLAUDE.md Notes

The user's global CLAUDE.md specifies a TypeScript/Next.js/Prisma/pnpm stack, but this project predates those rules and uses Python/Flask + vanilla JS. Follow the existing patterns for this project.
