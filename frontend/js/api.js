// ── API Base Helpers ──────────────────────────────────────────────────────
const API = 'http://localhost:8000/api';

function getToken() { return localStorage.getItem('hb_token'); }
function getUser() { return JSON.parse(localStorage.getItem('hb_user') || 'null'); }
function getRole() { return localStorage.getItem('hb_role'); }

function setAuth(data) {
  localStorage.setItem('hb_token', data.access_token);
  localStorage.setItem('hb_role', data.role);
  localStorage.setItem('hb_user', JSON.stringify({ id: data.user_id, name: data.name, role: data.role }));
}

function clearAuth() {
  localStorage.removeItem('hb_token');
  localStorage.removeItem('hb_role');
  localStorage.removeItem('hb_user');
}

async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = { ...(options.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  // Don't set Content-Type for FormData (browser handles it)
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    if (options.body && typeof options.body === 'object') {
      options.body = JSON.stringify(options.body);
    }
  }

  const res = await fetch(`${API}${path}`, { ...options, headers });
  if (res.status === 401) { clearAuth(); window.location.href = '/login.html'; return; }
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Something went wrong');
  return data;
}

// ── Toast Notifications ───────────────────────────────────────────────────
function showToast(message, type = 'success') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
  toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(100%)'; setTimeout(() => toast.remove(), 300); }, 3500);
}

// ── Navbar Auth State ─────────────────────────────────────────────────────
function initNavbar() {
  const user = getUser();
  const role = getRole();
  const authEl = document.getElementById('nav-auth');
  if (!authEl) return;

  if (user) {
    const dashUrl = role === 'farmer' ? '/farmer-dashboard.html' : '/business-dashboard.html';
    authEl.innerHTML = `
      <a href="${dashUrl}" class="nav-user">
        <div class="avatar">${user.name.charAt(0).toUpperCase()}</div>
        <span>${user.name}</span>
      </a>
      <button class="btn btn-secondary btn-sm" onclick="logout()">Logout</button>`;
  } else {
    authEl.innerHTML = `
      <a href="/login.html" class="btn btn-secondary btn-sm">Login</a>
      <a href="/register.html" class="btn btn-primary btn-sm">Register</a>`;
  }

  // Navbar scroll effect
  window.addEventListener('scroll', () => {
    document.querySelector('.navbar')?.classList.toggle('scrolled', window.scrollY > 50);
  });
}

function logout() {
  clearAuth();
  window.location.href = '/';
}

// ── Cart Badge ────────────────────────────────────────────────────────────
async function updateCartBadge() {
  if (getRole() !== 'business') return;
  try {
    const cart = await apiFetch('/cart/');
    const badge = document.getElementById('cart-badge');
    if (badge) badge.textContent = cart.item_count || '';
  } catch (_) {}
}

// ── Auth Guard ────────────────────────────────────────────────────────────
function requireAuth(role = null) {
  const user = getUser();
  if (!user) { window.location.href = '/login.html'; return false; }
  if (role && user.role !== role) {
    showToast(`This page is for ${role}s only`, 'error');
    window.location.href = user.role === 'farmer' ? '/farmer-dashboard.html' : '/marketplace.html';
    return false;
  }
  return true;
}

// ── Formatting Helpers ────────────────────────────────────────────────────
function fmtCurrency(amount) { return `₹${parseFloat(amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`; }
function fmtDate(dt) { return new Date(dt).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }); }
function categoryEmoji(cat) {
  const map = { Vegetables: '🥦', Fruits: '🍎', Grains: '🌾', Dairy: '🥛', Spices: '🌶️', Other: '📦' };
  return map[cat] || '📦';
}

// ── Product Card Builder ──────────────────────────────────────────────────
function buildProductCard(product, showCart = false) {
  const emoji = categoryEmoji(product.category);
  const imageHtml = product.image_path
    ? `<img src="${product.image_path}" alt="${product.name}">`
    : `<div class="placeholder">${emoji}</div>`;
  const organicBadge = product.is_organic ? `<span class="badge badge-organic">🌿 Organic</span>` : '';

  return `
    <div class="card product-card" id="product-${product.id}">
      <div class="card-image">
        ${imageHtml}
        <div class="badges">
          ${organicBadge}
          <span class="badge badge-category">${product.category || 'Other'}</span>
        </div>
      </div>
      <div class="card-body">
        <div class="product-name">${product.name}</div>
        <div class="farm-info">🏡 ${product.farm_name || 'Farm'} · 📍 ${product.farmer_location || ''}</div>
        <div class="min-order">Min order: ${product.min_order_qty} ${product.unit}</div>
        <div class="price-row">
          <div>
            <span class="price">${fmtCurrency(product.price_per_unit)}</span>
            <span class="unit">/${product.unit}</span>
          </div>
          ${showCart ? `
            <button class="btn btn-primary btn-sm" onclick="addToCart(${product.id}, ${product.min_order_qty}, '${product.unit}')">
              🛒 Add
            </button>` : `
            <a href="/product-detail.html?id=${product.id}" class="btn btn-outline btn-sm">View</a>`}
        </div>
      </div>
    </div>`;
}

document.addEventListener('DOMContentLoaded', () => { initNavbar(); });
