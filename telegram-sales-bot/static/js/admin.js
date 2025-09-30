// Admin Panel JavaScript

// API Base URL
const API_BASE = '/api';

// Authentication
function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
}

// Check authentication
async function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (!token && !window.location.pathname.includes('/login')) {
        window.location.href = '/admin/login';
        return false;
    }
    return true;
}

// Format currency
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR') + ' ' + date.toLocaleTimeString('pt-BR');
}

// Show toast notification
function showToast(message, type = 'success') {
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = toastContainer.lastElementChild;
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const stats = await response.json();
            updateStatsDisplay(stats);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function updateStatsDisplay(stats) {
    // Update stat cards
    const elements = {
        totalProducts: document.querySelector('[data-stat="total-products"]'),
        totalRevenue: document.querySelector('[data-stat="total-revenue"]'),
        pendingOrders: document.querySelector('[data-stat="pending-orders"]'),
        totalUsers: document.querySelector('[data-stat="total-users"]')
    };
    
    if (elements.totalProducts) elements.totalProducts.textContent = stats.products.total;
    if (elements.totalRevenue) elements.totalRevenue.textContent = formatCurrency(stats.revenue.total);
    if (elements.pendingOrders) elements.pendingOrders.textContent = stats.orders.pending;
    if (elements.totalUsers) elements.totalUsers.textContent = stats.users.total;
}

// Status badge helper
function getStatusBadge(status) {
    const badges = {
        'pending': '<span class="badge badge-status-pending">Pendente</span>',
        'processing': '<span class="badge badge-status-processing">Processando</span>',
        'paid': '<span class="badge badge-status-paid">Pago</span>',
        'cancelled': '<span class="badge badge-status-cancelled">Cancelado</span>',
        'expired': '<span class="badge bg-secondary">Expirado</span>',
        'approved': '<span class="badge badge-status-paid">Aprovado</span>',
        'rejected': '<span class="badge badge-status-cancelled">Rejeitado</span>'
    };
    
    return badges[status] || `<span class="badge bg-secondary">${status}</span>`;
}

// Delete confirmation
function confirmDelete(message = 'Tem certeza que deseja excluir este item?') {
    return confirm(message);
}

// Image preview
function previewImage(input, previewElement) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            previewElement.src = e.target.result;
            previewElement.style.display = 'block';
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    await checkAuth();
    
    // Load initial data based on current page
    const path = window.location.pathname;
    
    if (path === '/admin' || path === '/admin/') {
        loadStats();
    }
    
    // Setup logout handler
    const logoutBtn = document.querySelector('[href="/auth/logout"]');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('access_token');
            window.location.href = '/admin/login';
        });
    }
    
    // Add fade-in animation to cards
    document.querySelectorAll('.card').forEach(card => {
        card.classList.add('fade-in');
    });
});

// Export functions for use in other scripts
window.adminUtils = {
    getAuthHeaders,
    formatCurrency,
    formatDate,
    showToast,
    getStatusBadge,
    confirmDelete,
    previewImage,
    debounce
};
