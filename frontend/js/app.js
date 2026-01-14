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

    // Navigation (top)
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => switchView(btn.dataset.view));
    });

    // Navigation (mobile)
    document.querySelectorAll('.mobile-nav-btn').forEach(btn => {
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

    // Update top nav active state
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });

    // Update mobile nav active state
    document.querySelectorAll('.mobile-nav-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });

    switch (view) {
        case 'dashboard':
            await loadDashboard();
            break;
        case 'inventory':
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

    renderItemsGrid('needs-purchase-list', needsPurchase, true);
    renderItemsGrid('low-stock-list', lowStock, false);
}

async function loadInventory() {
    const categoryFilter = document.getElementById('inventory-category-filter').value;
    const endpoint = categoryFilter ? `/consumables?category_id=${categoryFilter}` : '/consumables';
    consumables = await api(endpoint);
    renderInventoryList();
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
    renderManageList();
}

// Render functions
function renderItemsGrid(containerId, items, showUrgent) {
    const container = document.getElementById(containerId);

    if (items.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No items to display</p></div>';
        return;
    }

    container.innerHTML = items.map(item => {
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

    // Add event listeners (safer than inline onclick)
    container.querySelectorAll('.btn-purchase').forEach(btn => {
        btn.addEventListener('click', () => openQuickPurchase(parseInt(btn.dataset.id), btn.dataset.name));
    });
    container.querySelectorAll('.btn-edit').forEach(btn => {
        btn.addEventListener('click', () => openEditModal(parseInt(btn.dataset.id)));
    });
}

function renderInventoryList() {
    const container = document.getElementById('inventory-list');

    if (consumables.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No items in inventory</p></div>';
        return;
    }

    container.innerHTML = consumables.map(item => {
        const usageRate = item.custom_usage_rate || item.default_usage_rate;
        return `
            <div class="list-item">
                <div>
                    <div class="list-item-name">${escapeHtml(item.name)}</div>
                    <div class="list-item-category">${escapeHtml(item.category_icon)} ${escapeHtml(item.category_name)}</div>
                </div>
                <div class="list-item-quantity">${item.current_quantity || 0} ${escapeHtml(item.unit)}</div>
                <div class="list-item-usage">${usageRate} per ${escapeHtml(item.usage_rate_period)}</div>
                <div>Min: ${item.min_stock_level}</div>
                <button class="btn-edit" data-id="${item.id}">Edit</button>
            </div>
        `;
    }).join('');

    container.querySelectorAll('.btn-edit').forEach(btn => {
        btn.addEventListener('click', () => openEditModal(parseInt(btn.dataset.id)));
    });
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

function renderPurchasesTable(purchases) {
    const container = document.getElementById('purchases-list');

    if (purchases.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No purchases recorded</p></div>';
        return;
    }

    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Item</th>
                    <th>Quantity</th>
                    <th>Price</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                ${purchases.map(p => `
                    <tr>
                        <td>${escapeHtml(p.purchase_date)}</td>
                        <td>${escapeHtml(p.consumable_name)}</td>
                        <td>${p.quantity} ${escapeHtml(p.unit)}</td>
                        <td>${(p.price !== null && p.price !== undefined) ? '$' + Number(p.price).toFixed(2) : '-'}</td>
                        <td><button class="btn-delete" data-id="${p.id}">Delete</button></td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    container.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', () => deletePurchase(parseInt(btn.dataset.id)));
    });
}

function renderManageList() {
    const container = document.getElementById('manage-items-list');

    if (consumables.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No items to manage</p></div>';
        return;
    }

    container.innerHTML = consumables.map(item => {
        const usageRate = item.custom_usage_rate || item.default_usage_rate;
        return `
            <div class="list-item">
                <div>
                    <div class="list-item-name">${escapeHtml(item.name)}</div>
                    <div class="list-item-category">${escapeHtml(item.category_icon)} ${escapeHtml(item.category_name)}</div>
                </div>
                <div class="list-item-quantity">${item.current_quantity || 0} ${escapeHtml(item.unit)}</div>
                <div class="list-item-usage">${usageRate} per ${escapeHtml(item.usage_rate_period)}</div>
                <div>Min: ${item.min_stock_level}</div>
                <button class="btn-edit" data-id="${item.id}">Edit</button>
            </div>
        `;
    }).join('');

    container.querySelectorAll('.btn-edit').forEach(btn => {
        btn.addEventListener('click', () => openEditModal(parseInt(btn.dataset.id)));
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
        usage_rate_period: document.getElementById('new-item-usage-period').value,
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
        usage_rate_period: document.getElementById('edit-item-usage-period').value,
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

    if (confirm(`Are you sure you want to delete "${name}"? This will also delete all purchase history for this item.`)) {
        await api(`/consumables/${id}`, { method: 'DELETE' });
        document.getElementById('edit-modal').classList.add('hidden');
        await switchView(currentView);
    }
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
    document.getElementById('edit-item-usage-period').value = item.usage_rate_period;
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
    if (confirm('Are you sure you want to delete this purchase? This will also update the inventory.')) {
        await api(`/purchases/${id}`, { method: 'DELETE' });
        await loadPurchases();
    }
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
            alert('Download failed: ' + (error.error || 'Unknown error'));
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
        alert('Download failed: ' + err.message);
    }
}

function triggerRestoreUpload() {
    if (confirm('Warning: This will replace ALL current data with the backup file. This cannot be undone. Continue?')) {
        document.getElementById('restore-file-input').click();
    }
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
            alert('Database restored successfully. The page will now reload.');
            window.location.reload();
        } else {
            alert('Restore failed: ' + (result.error || 'Unknown error'));
        }
    } catch (err) {
        alert('Restore failed: ' + err.message);
    }

    // Reset file input
    e.target.value = '';
}
