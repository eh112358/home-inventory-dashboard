// HTML escape helper to prevent XSS
function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

// API helper
async function api(endpoint, options = {}) {
    const response = await fetch(`/api${endpoint}`, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        credentials: 'include'
    });

    if (response.status === 401) {
        showLogin();
        throw new Error('Unauthorized');
    }

    return response.json();
}

// State
let categories = [];
let consumables = [];
let currentView = 'dashboard';
let collapsedCategories = JSON.parse(localStorage.getItem('collapsedCategories') || '{}');
let selectedCategoryIcon = '📦';
let editCategoryIcon = '📦';
let inventoryViewMode = localStorage.getItem('inventoryViewMode') || 'list';
let activeCategoryDropdown = null;

// Emoji choices for category icons
const CATEGORY_EMOJIS = [
    '📦', '🏠', '🍎', '🧴', '🧹', '🧺', '🧽', '🧻',
    '💊', '🩹', '🧸', '🎮', '📚', '✏️', '🔧', '🔌',
    '🚗', '🌱', '🐕', '🐈', '👶', '👕', '🧼', '🛒'
];

// Toast notification system
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    const duration = type === 'error' ? 5000 : 3000;

    setTimeout(() => {
        toast.classList.add('toast-removing');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Custom confirm dialog (replaces native confirm())
function showConfirm(message) {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'confirm-overlay';
        overlay.innerHTML = `
            <div class="confirm-dialog">
                <p>${escapeHtml(message)}</p>
                <div class="confirm-dialog-actions">
                    <button class="confirm-cancel">Cancel</button>
                    <button class="confirm-ok">Confirm</button>
                </div>
            </div>
        `;

        overlay.querySelector('.confirm-cancel').addEventListener('click', () => {
            overlay.remove();
            resolve(false);
        });

        overlay.querySelector('.confirm-ok').addEventListener('click', () => {
            overlay.remove();
            resolve(true);
        });

        // Close on overlay background click
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.remove();
                resolve(false);
            }
        });

        document.body.appendChild(overlay);
    });
}

// Modal close helper
function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

// Environment indicator
async function loadEnvironment() {
    try {
        const response = await fetch('/api/environment');
        const data = await response.json();
        const env = data.environment?.toLowerCase();

        if (env && env !== 'production') {
            // Update page title
            const envLabel = env.toUpperCase();
            document.title = `[${envLabel}] Home Inventory Manager`;

            // Update header badge
            const badge = document.getElementById('env-badge');
            if (badge) {
                badge.textContent = envLabel;
                badge.classList.remove('hidden');
                badge.classList.add(`env-${env}`);
            }
        }
    } catch {
        // Silently ignore - environment indicator is non-critical
    }
}

// DOM Elements
const loginScreen = document.getElementById('login-screen');
const appScreen = document.getElementById('app-screen');
const loginForm = document.getElementById('login-form');
const loginError = document.getElementById('login-error');
const logoutBtn = document.getElementById('logout-btn');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // Load environment indicator (runs regardless of auth)
    loadEnvironment();

    try {
        const auth = await api('/auth/check');
        if (auth.authenticated) {
            showApp();
        } else {
            showLogin();
        }
    } catch {
        showLogin();
    }

    setupEventListeners();
});

function setupEventListeners() {
    // Login form
    loginForm.addEventListener('submit', handleLogin);
    logoutBtn.addEventListener('click', handleLogout);

    // Settings modal
    document.getElementById('settings-btn').addEventListener('click', openSettingsModal);
    document.getElementById('download-backup-btn').addEventListener('click', downloadBackup);
    document.getElementById('restore-backup-btn').addEventListener('click', triggerRestoreUpload);
    document.getElementById('restore-file-input').addEventListener('change', handleRestoreUpload);

    // Easter egg
    document.getElementById('easter-egg-trigger').addEventListener('click', triggerHeartsAnimation);

    // Navigation (desktop + mobile)
    document.querySelectorAll('.view-nav-btn').forEach(btn => {
        btn.addEventListener('click', () => switchView(btn.dataset.view));
    });

    // Compact header on scroll (desktop only)
    window.addEventListener('scroll', () => {
        const header = document.querySelector('header');
        if (window.scrollY > 50) {
            header.classList.add('compact');
        } else {
            header.classList.remove('compact');
        }
    });

    // Category filters
    document.getElementById('dashboard-category-filter').addEventListener('change', loadDashboard);
    document.getElementById('inventory-category-filter').addEventListener('change', loadInventory);
    document.getElementById('manage-category-filter').addEventListener('change', loadManageItems);

    // Inventory view toggle
    document.getElementById('view-list-btn').addEventListener('click', () => setInventoryViewMode('list'));
    document.getElementById('view-grid-btn').addEventListener('click', () => setInventoryViewMode('grid'));

    // Forms
    document.getElementById('purchase-form').addEventListener('submit', handleNewPurchase);
    document.getElementById('add-item-form').addEventListener('submit', handleAddItem);
    document.getElementById('edit-item-form').addEventListener('submit', handleEditItem);
    document.getElementById('quick-purchase-form').addEventListener('submit', handleQuickPurchase);
    document.getElementById('delete-item-btn').addEventListener('click', handleDeleteItem);

    // Modals
    document.querySelectorAll('.close-modal').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.modal').forEach(m => m.classList.add('hidden'));
        });
    });

    // Close modal on outside click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.classList.add('hidden');
        });
    });

    // Set default purchase date to today
    document.getElementById('purchase-date').valueAsDate = new Date();

    // FAB (Floating Action Button) — context-aware
    document.getElementById('fab-add').addEventListener('click', handleFabClick);

    // Category management
    document.getElementById('add-category-btn').addEventListener('click', handleAddCategory);
    document.getElementById('category-icon-btn').addEventListener('click', () => toggleEmojiPicker('emoji-picker', 'category-icon-btn', 'add'));
    document.getElementById('edit-category-form').addEventListener('submit', handleEditCategory);
    document.getElementById('edit-category-icon-btn').addEventListener('click', () => toggleEmojiPicker('edit-emoji-picker', 'edit-category-icon-btn', 'edit'));
    document.getElementById('delete-category-btn').addEventListener('click', handleDeleteCategory);
    document.getElementById('add-category-desktop-btn').addEventListener('click', openAddCategoryModal);

    // Allow pressing Enter in category name input to add
    document.getElementById('new-category-name').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleAddCategory();
        }
    });

    // Close category dropdown on any outside click
    document.addEventListener('click', closeCategoryDropdown);

    // Initialize emoji pickers
    initEmojiPicker('emoji-picker', 'add');
    initEmojiPicker('edit-emoji-picker', 'edit');
}

// Auth functions
async function handleLogin(e) {
    e.preventDefault();
    const password = document.getElementById('password-input').value;

    try {
        const result = await api('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ password })
        });

        if (result.success) {
            showApp();
        }
    } catch (err) {
        loginError.textContent = 'Invalid password';
    }
}

async function handleLogout() {
    await api('/auth/logout', { method: 'POST' });
    showLogin();
}

function showLogin() {
    loginScreen.classList.remove('hidden');
    appScreen.classList.add('hidden');
    document.getElementById('password-input').value = '';
    loginError.textContent = '';
}

async function showApp() {
    loginScreen.classList.add('hidden');
    appScreen.classList.remove('hidden');

    await loadCategories();
    switchView('dashboard');
}

// View switching
async function switchView(view) {
    currentView = view;

    document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
    document.getElementById(`${view}-view`).classList.remove('hidden');

    // Update nav active state (desktop + mobile)
    document.querySelectorAll('.view-nav-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });

    // Update FAB label based on current view
    const fab = document.getElementById('fab-add');
    fab.setAttribute('aria-label', view === 'manage' ? 'Add new category' : 'Quick add purchase');

    switch (view) {
        case 'dashboard':
            await loadDashboard();
            break;
        case 'inventory':
            // Sync toggle button active states with stored preference
            document.getElementById('view-list-btn').classList.toggle('active', inventoryViewMode === 'list');
            document.getElementById('view-grid-btn').classList.toggle('active', inventoryViewMode === 'grid');
            await loadInventory();
            break;
        case 'purchases':
            await loadPurchases();
            break;
        case 'manage':
            await loadManageItems();
            break;
    }
}

// Data loading functions
async function loadCategories() {
    categories = await api('/categories');
    populateCategorySelects();
}

function populateCategorySelects() {
    const selects = [
        'dashboard-category-filter',
        'inventory-category-filter',
        'manage-category-filter',
        'new-item-category',
        'edit-item-category'
    ];

    selects.forEach(id => {
        const select = document.getElementById(id);
        const isFilter = id.includes('filter');

        select.innerHTML = '';

        if (isFilter) {
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = 'All Categories';
            select.appendChild(defaultOption);
        }

        categories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat.id;
            option.textContent = `${cat.icon} ${cat.name}`;
            select.appendChild(option);
        });
    });
}

async function loadDashboard() {
    const stats = await api('/stats');
    document.getElementById('stat-needs-purchase').textContent = stats.needs_purchase;
    document.getElementById('stat-total').textContent = stats.total_items;
    document.getElementById('stat-recent').textContent = stats.recent_purchases;

    const items = await api('/dashboard');
    const categoryFilter = document.getElementById('dashboard-category-filter').value;

    const filteredItems = categoryFilter
        ? items.filter(i => i.category_id == categoryFilter)
        : items;

    const needsPurchase = filteredItems.filter(i => i.needs_purchase);
    const lowStock = filteredItems.filter(i => i.low_stock);

    renderItemsGridGrouped('needs-purchase-list', needsPurchase, true);
    renderItemsGridGrouped('low-stock-list', lowStock, false);
}

async function loadInventory() {
    const categoryFilter = document.getElementById('inventory-category-filter').value;
    const endpoint = categoryFilter ? `/consumables?category_id=${categoryFilter}` : '/consumables';
    consumables = await api(endpoint);
    renderInventoryView();
}

async function loadPurchases() {
    consumables = await api('/consumables');
    populatePurchaseSelect();

    const purchases = await api('/purchases');
    renderPurchasesTable(purchases);
}

async function loadManageItems() {
    const categoryFilter = document.getElementById('manage-category-filter').value;
    const endpoint = categoryFilter ? `/consumables?category_id=${categoryFilter}` : '/consumables';
    consumables = await api(endpoint);
    renderItemList('manage-items-list', 'No items to manage');
    renderCategoryList();
}

// Render functions
function renderItemList(containerId, emptyMessage) {
    const container = document.getElementById(containerId);

    if (consumables.length === 0) {
        container.innerHTML = `<div class="empty-state"><p>${escapeHtml(emptyMessage)}</p></div>`;
        return;
    }

    container.innerHTML = consumables.map(item => {
        const usageRate = item.custom_usage_rate || item.default_usage_rate;
        return `
            <div class="list-item">
                <div class="list-item-row">
                    <div class="list-item-name">${escapeHtml(item.name)}</div>
                    <div class="list-item-quantity">${item.current_quantity || 0} ${escapeHtml(item.unit)}</div>
                </div>
                <div class="list-item-meta">
                    <span class="list-item-category">${escapeHtml(item.category_icon)} ${escapeHtml(item.category_name)}</span>
                    <span class="list-item-usage">${usageRate}/wk</span>
                    <span class="list-item-min">Min: ${item.min_stock_level}</span>
                    <button class="btn-edit" data-id="${item.id}">Edit</button>
                </div>
            </div>
        `;
    }).join('');

    container.querySelectorAll('.btn-edit').forEach(btn => {
        btn.addEventListener('click', () => openEditModal(parseInt(btn.dataset.id)));
    });
}

function renderInventoryGrid() {
    const container = document.getElementById('inventory-list');

    if (consumables.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No items in inventory</p></div>';
        return;
    }

    container.innerHTML = `
        <div class="inventory-grid">
            <div class="inventory-grid-header">
                <span>Name</span>
                <span>Category</span>
                <span>Qty</span>
                <span>Usage</span>
                <span>Min</span>
                <span></span>
            </div>
            ${consumables.map(item => {
                const usageRate = item.custom_usage_rate || item.default_usage_rate;
                return `
                    <div class="inventory-grid-row">
                        <span>${escapeHtml(item.name)}</span>
                        <span>${escapeHtml(item.category_icon)} ${escapeHtml(item.category_name)}</span>
                        <span>${item.current_quantity || 0} ${escapeHtml(item.unit)}</span>
                        <span>${usageRate}/wk</span>
                        <span>${item.min_stock_level}</span>
                        <button class="btn-edit" data-id="${item.id}">Edit</button>
                    </div>
                `;
            }).join('')}
        </div>
    `;

    container.querySelectorAll('.btn-edit').forEach(btn => {
        btn.addEventListener('click', () => openEditModal(parseInt(btn.dataset.id)));
    });
}

function renderInventoryView() {
    if (isMobileView() || inventoryViewMode === 'list') {
        renderItemList('inventory-list', 'No items in inventory');
    } else {
        renderInventoryGrid();
    }
}

function setInventoryViewMode(mode) {
    inventoryViewMode = mode;
    localStorage.setItem('inventoryViewMode', mode);
    document.getElementById('view-list-btn').classList.toggle('active', mode === 'list');
    document.getElementById('view-grid-btn').classList.toggle('active', mode === 'grid');
    renderInventoryView();
}

function populatePurchaseSelect() {
    const select = document.getElementById('purchase-item');
    select.innerHTML = '<option value="">Select Item</option>';

    const grouped = {};
    consumables.forEach(item => {
        if (!grouped[item.category_name]) {
            grouped[item.category_name] = [];
        }
        grouped[item.category_name].push(item);
    });

    Object.entries(grouped).forEach(([category, items]) => {
        const optgroup = document.createElement('optgroup');
        optgroup.label = category;
        items.forEach(item => {
            const option = document.createElement('option');
            option.value = item.id;
            option.textContent = `${item.name} (${item.unit})`;
            optgroup.appendChild(option);
        });
        select.appendChild(optgroup);
    });
}

function formatPrice(price) {
    return (price !== null && price !== undefined) ? '$' + Number(price).toFixed(2) : '-';
}

function renderPurchasesTable(purchases) {
    const container = document.getElementById('purchases-list');

    if (purchases.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No purchases recorded</p></div>';
        return;
    }

    // Single responsive grid layout - CSS handles desktop vs mobile display
    container.innerHTML = `
        <div class="purchases-grid">
            <div class="purchases-header">
                <span>Date</span>
                <span>Item</span>
                <span>Qty</span>
                <span>Price</span>
                <span></span>
            </div>
            ${purchases.map(p => `
                <div class="purchase-item">
                    <span class="purchase-date">${escapeHtml(p.purchase_date)}</span>
                    <span class="purchase-name">${escapeHtml(p.consumable_name)}</span>
                    <span class="purchase-qty">${p.quantity} ${escapeHtml(p.unit)}</span>
                    <span class="purchase-price">${formatPrice(p.price)}</span>
                    <button class="btn-delete" data-id="${p.id}">Delete</button>
                </div>
            `).join('')}
        </div>
    `;

    container.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', () => deletePurchase(parseInt(btn.dataset.id)));
    });
}

// Form handlers
async function handleNewPurchase(e) {
    e.preventDefault();

    const data = {
        consumable_type_id: parseInt(document.getElementById('purchase-item').value),
        quantity: parseFloat(document.getElementById('purchase-quantity').value),
        purchase_date: document.getElementById('purchase-date').value,
        price: document.getElementById('purchase-price').value
            ? parseFloat(document.getElementById('purchase-price').value)
            : null
    };

    await api('/purchases', {
        method: 'POST',
        body: JSON.stringify(data)
    });

    // Reset form
    document.getElementById('purchase-form').reset();
    document.getElementById('purchase-date').valueAsDate = new Date();

    await loadPurchases();
}

async function handleAddItem(e) {
    e.preventDefault();

    const data = {
        category_id: parseInt(document.getElementById('new-item-category').value),
        name: document.getElementById('new-item-name').value,
        unit: document.getElementById('new-item-unit').value,
        default_usage_rate: parseFloat(document.getElementById('new-item-usage-rate').value),
        min_stock_level: parseFloat(document.getElementById('new-item-min-stock').value),
        notes: document.getElementById('new-item-notes').value
    };

    await api('/consumables', {
        method: 'POST',
        body: JSON.stringify(data)
    });

    document.getElementById('add-item-form').reset();
    await loadManageItems();
}

async function handleEditItem(e) {
    e.preventDefault();

    const id = document.getElementById('edit-item-id').value;

    // Update consumable type
    const typeData = {
        category_id: parseInt(document.getElementById('edit-item-category').value),
        name: document.getElementById('edit-item-name').value,
        unit: document.getElementById('edit-item-unit').value,
        default_usage_rate: parseFloat(document.getElementById('edit-item-usage-rate').value),
        min_stock_level: parseFloat(document.getElementById('edit-item-min-stock').value),
        notes: document.getElementById('edit-item-notes').value
    };

    await api(`/consumables/${id}`, {
        method: 'PUT',
        body: JSON.stringify(typeData)
    });

    // Update inventory
    const customRate = document.getElementById('edit-item-custom-rate').value;
    const inventoryData = {
        current_quantity: parseFloat(document.getElementById('edit-item-quantity').value),
        custom_usage_rate: customRate ? parseFloat(customRate) : null
    };

    await api(`/inventory/${id}`, {
        method: 'PUT',
        body: JSON.stringify(inventoryData)
    });

    document.getElementById('edit-modal').classList.add('hidden');
    await switchView(currentView);
}

async function handleDeleteItem() {
    const id = document.getElementById('edit-item-id').value;
    const name = document.getElementById('edit-item-name').value;

    if (!(await showConfirm(`Are you sure you want to delete "${name}"? This will also delete all purchase history for this item.`))) return;

    await api(`/consumables/${id}`, { method: 'DELETE' });
    closeModal('edit-modal');
    await switchView(currentView);
}

async function handleQuickPurchase(e) {
    e.preventDefault();

    const data = {
        consumable_type_id: parseInt(document.getElementById('quick-purchase-item-id').value),
        quantity: parseFloat(document.getElementById('quick-purchase-quantity').value),
        purchase_date: new Date().toISOString().split('T')[0]
    };

    await api('/purchases', {
        method: 'POST',
        body: JSON.stringify(data)
    });

    document.getElementById('quick-purchase-modal').classList.add('hidden');
    await switchView(currentView);
}

// Modal functions
async function openEditModal(id) {
    const items = await api('/consumables');
    const item = items.find(i => i.id === id);

    if (!item) return;

    document.getElementById('edit-item-id').value = item.id;
    document.getElementById('edit-item-category').value = item.category_id;
    document.getElementById('edit-item-name').value = item.name;
    document.getElementById('edit-item-unit').value = item.unit;
    document.getElementById('edit-item-usage-rate').value = item.default_usage_rate;
    document.getElementById('edit-item-custom-rate').value = item.custom_usage_rate || '';
    document.getElementById('edit-item-quantity').value = item.current_quantity || 0;
    document.getElementById('edit-item-min-stock').value = item.min_stock_level;
    document.getElementById('edit-item-notes').value = item.notes || '';

    document.getElementById('edit-modal').classList.remove('hidden');
}

function openQuickPurchase(id, name) {
    document.getElementById('quick-purchase-item-id').value = id;
    document.getElementById('quick-purchase-item-name').textContent = name;
    document.getElementById('quick-purchase-quantity').value = '';
    document.getElementById('quick-purchase-modal').classList.remove('hidden');
    document.getElementById('quick-purchase-quantity').focus();
}

async function deletePurchase(id) {
    if (!(await showConfirm('Are you sure you want to delete this purchase? This will also update the inventory.'))) return;

    await api(`/purchases/${id}`, { method: 'DELETE' });
    await loadPurchases();
}

// Settings modal functions
function openSettingsModal() {
    document.getElementById('settings-modal').classList.remove('hidden');
}

async function downloadBackup() {
    try {
        const response = await fetch('/api/backup/download', { credentials: 'include' });

        if (response.status === 401) {
            showLogin();
            return;
        }

        if (!response.ok) {
            const error = await response.json();
            showToast('Download failed: ' + (error.error || 'Unknown error'), 'error');
            return;
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `inventory_backup_${new Date().toISOString().slice(0, 10)}.db`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    } catch (err) {
        showToast('Download failed: ' + err.message, 'error');
    }
}

async function triggerRestoreUpload() {
    if (!(await showConfirm('Warning: This will replace ALL current data with the backup file. This cannot be undone. Continue?'))) return;

    document.getElementById('restore-file-input').click();
}

async function handleRestoreUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/backup/upload', {
            method: 'POST',
            credentials: 'include',
            body: formData
        });

        if (response.status === 401) {
            showLogin();
            return;
        }

        const result = await response.json();

        if (result.success) {
            showToast('Database restored successfully. The page will now reload.', 'success');
            window.location.reload();
        } else {
            showToast('Restore failed: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (err) {
        showToast('Restore failed: ' + err.message, 'error');
    }

    // Reset file input
    e.target.value = '';
}

// FAB - Open purchase selector
async function openFabPurchase() {
    // Make sure we have items loaded
    if (consumables.length === 0) {
        consumables = await api('/consumables');
    }

    if (consumables.length === 0) {
        showToast('No items available. Add items first in Manage Items.', 'info');
        return;
    }

    // For simplicity, navigate to purchases view
    switchView('purchases');
    // Focus on the item select
    setTimeout(() => {
        document.getElementById('purchase-item').focus();
    }, 100);
}

// Group items by category
function groupItemsByCategory(items) {
    const grouped = {};
    items.forEach(item => {
        const key = item.category_id;
        if (!grouped[key]) {
            grouped[key] = {
                id: item.category_id,
                name: item.category_name,
                icon: item.category_icon,
                items: []
            };
        }
        grouped[key].items.push(item);
    });
    return Object.values(grouped);
}

// Toggle category collapse state
function toggleCategory(categoryId, containerId) {
    const key = `${containerId}-${categoryId}`;
    collapsedCategories[key] = !collapsedCategories[key];
    localStorage.setItem('collapsedCategories', JSON.stringify(collapsedCategories));

    const header = document.querySelector(`[data-category-id="${categoryId}"][data-container="${containerId}"]`);
    const content = document.getElementById(`category-content-${containerId}-${categoryId}`);

    if (header && content) {
        if (collapsedCategories[key]) {
            header.classList.add('collapsed');
            content.classList.add('collapsed');
        } else {
            header.classList.remove('collapsed');
            content.classList.remove('collapsed');
            // Reset max-height for smooth animation
            content.style.maxHeight = content.scrollHeight + 'px';
        }
    }
}

// Check if mobile viewport
function isMobileView() {
    return window.innerWidth <= 768;
}

// Render items grid with category grouping (mobile) or flat (desktop)
function renderItemsGridGrouped(containerId, items, showUrgent) {
    const container = document.getElementById(containerId);

    if (items.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No items to display</p></div>';
        return;
    }

    // On mobile, group by category
    if (isMobileView()) {
        const grouped = groupItemsByCategory(items);

        container.innerHTML = grouped.map(group => {
            const key = `${containerId}-${group.id}`;
            const isCollapsed = collapsedCategories[key];
            const collapsedClass = isCollapsed ? 'collapsed' : '';

            return `
                <div class="category-group">
                    <div class="category-header ${collapsedClass}"
                         data-category-id="${group.id}"
                         data-container="${containerId}">
                        <span class="toggle-icon">▼</span>
                        <span class="category-title">${escapeHtml(group.icon)} ${escapeHtml(group.name)}</span>
                        <span class="category-count">${group.items.length}</span>
                    </div>
                    <div id="category-content-${containerId}-${group.id}"
                         class="category-content ${collapsedClass}"
                         style="${!isCollapsed ? 'max-height: 2000px;' : ''}">
                        <div class="items-grid">
                            ${renderItemCards(group.items, showUrgent)}
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // Add collapse toggle listeners
        container.querySelectorAll('.category-header').forEach(header => {
            header.addEventListener('click', () => {
                toggleCategory(header.dataset.categoryId, header.dataset.container);
            });
        });
    } else {
        // Desktop: render cards directly (container already has items-grid class)
        container.innerHTML = renderItemCards(items, showUrgent);
    }

    // Add event listeners for buttons
    container.querySelectorAll('.btn-purchase').forEach(btn => {
        btn.addEventListener('click', () => openQuickPurchase(parseInt(btn.dataset.id), btn.dataset.name));
    });
    container.querySelectorAll('.btn-edit').forEach(btn => {
        btn.addEventListener('click', () => openEditModal(parseInt(btn.dataset.id)));
    });
}

// Render individual item cards HTML
function renderItemCards(items, showUrgent) {
    return items.map(item => {
        const urgentClass = item.needs_purchase ? 'urgent' : (item.low_stock ? 'warning' : '');
        const daysClass = (item.days_until_empty === null || item.days_until_empty <= 0) ? 'urgent' : (item.days_until_empty <= 7 ? 'warning' : '');
        const daysText = item.days_until_empty === null ? 'N/A'
            : item.days_until_empty <= 0 ? 'Empty!'
            : `${item.days_until_empty}d left`;

        return `
            <div class="item-card ${urgentClass}">
                <div class="item-header">
                    <div>
                        <div class="item-name">${escapeHtml(item.name)}</div>
                        <div class="item-category">${escapeHtml(item.category_icon)} ${escapeHtml(item.category_name)}</div>
                    </div>
                </div>
                <div class="item-stats">
                    <div>
                        <span class="item-quantity">${item.current_quantity || 0}</span>
                        <span class="item-unit">${escapeHtml(item.unit)}</span>
                    </div>
                    <span class="item-days ${daysClass}">${daysText}</span>
                </div>
                <div class="item-actions">
                    <button class="btn-purchase" data-id="${item.id}" data-name="${escapeHtml(item.name)}">
                        + Purchase
                    </button>
                    <button class="btn-edit" data-id="${item.id}">Edit</button>
                </div>
            </div>
        `;
    }).join('');
}

// Category management functions
function initEmojiPicker(pickerId, mode) {
    const picker = document.getElementById(pickerId);
    picker.innerHTML = CATEGORY_EMOJIS.map(emoji =>
        `<button type="button" data-emoji="${emoji}">${emoji}</button>`
    ).join('');

    picker.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', () => {
            const emoji = btn.dataset.emoji;
            if (mode === 'add') {
                selectedCategoryIcon = emoji;
                document.getElementById('category-icon-btn').textContent = emoji;
            } else {
                editCategoryIcon = emoji;
                document.getElementById('edit-category-icon-btn').textContent = emoji;
            }
            // Highlight selected
            picker.querySelectorAll('button').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            picker.classList.add('hidden');
        });
    });
}

function toggleEmojiPicker(pickerId, buttonId, mode) {
    const picker = document.getElementById(pickerId);
    picker.classList.toggle('hidden');

    // Highlight the currently selected emoji
    if (!picker.classList.contains('hidden')) {
        const currentIcon = mode === 'add' ? selectedCategoryIcon : editCategoryIcon;
        picker.querySelectorAll('button').forEach(btn => {
            btn.classList.toggle('selected', btn.dataset.emoji === currentIcon);
        });
    }
}

async function renderCategoryList() {
    const container = document.getElementById('categories-list');

    if (categories.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No categories</p></div>';
        return;
    }

    // Fetch all consumables to get accurate counts (not affected by filter)
    const allConsumables = await api('/consumables');
    const itemCounts = {};
    allConsumables.forEach(item => {
        itemCounts[item.category_id] = (itemCounts[item.category_id] || 0) + 1;
    });

    container.innerHTML = categories.map(cat => {
        const count = itemCounts[cat.id] || 0;
        return `
            <div class="category-list-item" data-category-row-id="${cat.id}">
                <span class="category-list-icon">${escapeHtml(cat.icon)}</span>
                <span class="category-list-name">${escapeHtml(cat.name)}</span>
                <span class="category-list-count">${count} item${count !== 1 ? 's' : ''}</span>
                <button class="category-menu-btn" data-id="${cat.id}">&#8942;</button>
            </div>
        `;
    }).join('');

    container.querySelectorAll('.category-menu-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            openCategoryDropdown(parseInt(btn.dataset.id), btn);
        });
    });
}

function closeCategoryDropdown() {
    if (activeCategoryDropdown) {
        activeCategoryDropdown.remove();
        activeCategoryDropdown = null;
    }
}

function openCategoryDropdown(categoryId, anchorButton) {
    // If same button clicked, toggle off
    if (activeCategoryDropdown && activeCategoryDropdown.dataset.categoryId == categoryId) {
        closeCategoryDropdown();
        return;
    }

    // Close any existing dropdown first
    closeCategoryDropdown();

    // Create dropdown menu
    const dropdown = document.createElement('div');
    dropdown.className = 'category-dropdown';
    dropdown.dataset.categoryId = categoryId;

    const editBtn = document.createElement('button');
    editBtn.className = 'category-dropdown-item';
    editBtn.textContent = 'Edit';
    editBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        closeCategoryDropdown();
        openEditCategoryModal(categoryId);
    });

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'category-dropdown-item danger';
    deleteBtn.textContent = 'Delete';
    deleteBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        closeCategoryDropdown();
        quickDeleteCategory(categoryId);
    });

    dropdown.appendChild(editBtn);
    dropdown.appendChild(deleteBtn);

    // Append to the category row so it positions relative to it
    const row = anchorButton.closest('.category-list-item');
    row.appendChild(dropdown);
    activeCategoryDropdown = dropdown;
}

// FAB — context-aware: opens add-category modal on manage view, purchase on others
async function handleFabClick() {
    if (currentView === 'manage') {
        openAddCategoryModal();
    } else {
        await openFabPurchase();
    }
}

// Open the Add Category modal
function openAddCategoryModal() {
    // Reset form state
    selectedCategoryIcon = '📦';
    document.getElementById('category-icon-btn').textContent = '📦';
    document.getElementById('new-category-name').value = '';
    document.getElementById('emoji-picker').classList.add('hidden');

    // Show the modal
    document.getElementById('add-category-modal').classList.remove('hidden');

    // Focus the name input
    setTimeout(() => {
        document.getElementById('new-category-name').focus();
    }, 100);
}

async function handleAddCategory() {
    const nameInput = document.getElementById('new-category-name');
    const name = nameInput.value.trim();

    if (!name) {
        showToast('Please enter a category name.', 'error');
        nameInput.focus();
        return;
    }

    try {
        const result = await api('/categories', {
            method: 'POST',
            body: JSON.stringify({ name: name, icon: selectedCategoryIcon })
        });

        if (result.success) {
            nameInput.value = '';
            selectedCategoryIcon = '📦';
            document.getElementById('category-icon-btn').textContent = '📦';
            document.getElementById('emoji-picker').classList.add('hidden');
            closeModal('add-category-modal');
            showToast('Category added!', 'success');
            await loadCategories();
            renderCategoryList();
        }
    } catch (err) {
        // The api() helper already handles 401; other errors bubble up here
    }
}

function openEditCategoryModal(id) {
    const cat = categories.find(c => c.id === id);
    if (!cat) return;

    document.getElementById('edit-category-id').value = cat.id;
    document.getElementById('edit-category-name').value = cat.name;
    editCategoryIcon = cat.icon || '📦';
    document.getElementById('edit-category-icon-btn').textContent = editCategoryIcon;
    document.getElementById('edit-emoji-picker').classList.add('hidden');
    document.getElementById('edit-category-modal').classList.remove('hidden');
}

async function handleEditCategory(e) {
    e.preventDefault();

    const id = document.getElementById('edit-category-id').value;
    const name = document.getElementById('edit-category-name').value.trim();

    if (!name) {
        showToast('Category name is required.', 'error');
        return;
    }

    try {
        const result = await api(`/categories/${id}`, {
            method: 'PUT',
            body: JSON.stringify({ name: name, icon: editCategoryIcon })
        });

        if (result.success) {
            document.getElementById('edit-category-modal').classList.add('hidden');
            await loadCategories();
            renderCategoryList();
        }
    } catch (err) {
        // Error handled by api() helper
    }
}

async function handleDeleteCategory() {
    const id = document.getElementById('edit-category-id').value;
    const name = document.getElementById('edit-category-name').value;

    if (!(await showConfirm(`Are you sure you want to delete "${name}"?`))) return;

    try {
        const response = await fetch(`/api/categories/${id}`, {
            method: 'DELETE',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();

        if (response.ok && result.success) {
            closeModal('edit-category-modal');
            await loadCategories();
            renderCategoryList();
        } else {
            showToast(result.error || 'Failed to delete category.', 'error');
        }
    } catch (err) {
        showToast('Failed to delete category: ' + err.message, 'error');
    }
}

async function quickDeleteCategory(id) {
    const cat = categories.find(c => c.id === id);
    if (!cat) return;

    if (!(await showConfirm(`Are you sure you want to delete "${cat.name}"?`))) return;

    try {
        const response = await fetch(`/api/categories/${id}`, {
            method: 'DELETE',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();

        if (response.ok && result.success) {
            await loadCategories();
            renderCategoryList();
        } else {
            showToast(result.error || 'Failed to delete category.', 'error');
        }
    } catch (err) {
        showToast('Failed to delete category: ' + err.message, 'error');
    }
}

// Easter egg - floating hearts animation
function triggerHeartsAnimation() {
    const container = document.getElementById('hearts-container');
    const heartColors = ['#ff6b6b', '#ee5a5a', '#ff8787', '#f06595', '#e64980', '#ff85a1'];
    const heartSymbols = ['♥', '❤', '💕', '💗', '💖'];

    // Close the settings modal
    document.getElementById('settings-modal').classList.add('hidden');

    // Create multiple hearts
    for (let i = 0; i < 30; i++) {
        setTimeout(() => {
            const heart = document.createElement('span');
            heart.className = 'floating-heart';
            heart.textContent = heartSymbols[Math.floor(Math.random() * heartSymbols.length)];
            heart.style.left = Math.random() * 100 + 'vw';
            heart.style.bottom = '-20px';
            heart.style.color = heartColors[Math.floor(Math.random() * heartColors.length)];
            heart.style.fontSize = (1 + Math.random() * 1.5) + 'rem';
            heart.style.animationDuration = (3 + Math.random() * 2) + 's';

            container.appendChild(heart);

            // Remove heart after animation
            setTimeout(() => heart.remove(), 5000);
        }, i * 100);
    }
}
