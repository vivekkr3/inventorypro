// ==========================================================================
// InventoryPro - Butter-Smooth Motion, Micro-Interactions & POS Logic
// ==========================================================================

document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // --- 1. Responsive Sidebar Toggle ---
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            sidebar.classList.toggle('show');
            if (overlay) overlay.classList.toggle('show');
        });
    }

    if (overlay && sidebar) {
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('show');
            overlay.classList.remove('show');
        });
    }

    // --- 2. Topbar & Landing Navbar Scroll Detection ---
    const topbar = document.querySelector('.topbar');
    const landingNav = document.querySelector('.landing-nav');

    window.addEventListener('scroll', () => {
        const isScrolled = window.scrollY > 20;
        if (topbar) {
            topbar.classList.toggle('scrolled', isScrolled);
        }
        if (landingNav) {
            landingNav.classList.toggle('scrolled', isScrolled);
        }
    }, { passive: true });

    // --- 3. Cascading Smooth Scroll-Reveal ---
    const revealElements = document.querySelectorAll('.reveal-on-scroll, .reveal-init');
    if (revealElements.length > 0) {
        const revealObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('reveal-active');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -30px 0px'
        });

        revealElements.forEach((el, index) => {
            el.classList.add('reveal-init');
            el.style.transitionDelay = `${(index % 4) * 70}ms`;
            revealObserver.observe(el);
        });
    }

    // --- 4. Quartic Eased Animated Counters ---
    const counters = document.querySelectorAll('.counter-value, [data-counter]');
    if (counters.length > 0) {
        const counterObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounterNumber(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.25 });

        counters.forEach(counter => counterObserver.observe(counter));
    }

    function animateCounterNumber(el) {
        const target = parseFloat(el.getAttribute('data-target') || el.innerText.replace(/[^0-9.-]+/g, '')) || 0;
        const prefix = el.getAttribute('data-prefix') || '';
        const suffix = el.getAttribute('data-suffix') || '';
        const isDecimal = el.getAttribute('data-decimal') === 'true' || (target % 1 !== 0 && target < 100);
        const duration = parseInt(el.getAttribute('data-duration')) || 1400;
        const startTime = performance.now();

        function formatNum(num) {
            if (isDecimal) {
                return num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            }
            return Math.floor(num).toLocaleString('en-IN');
        }

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out quartic: 1 - (1 - progress)^4
            const easeOutQuartic = 1 - Math.pow(1 - progress, 4);
            const currentVal = target * easeOutQuartic;

            el.textContent = prefix + formatNum(currentVal) + suffix;

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                el.textContent = prefix + formatNum(target) + suffix;
            }
        }

        requestAnimationFrame(update);
    }

    // --- 5. Precision Live Clock ---
    const clockEl = document.getElementById('liveClock');
    if (clockEl) {
        function updateClock() {
            const now = new Date();
            clockEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        }
        updateClock();
        setInterval(updateClock, 1000);
    }

    // --- 6. Smooth Scroll Anchors ---
    document.querySelectorAll('a[href^="#"]:not([href="#"])').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // --- 7. Graceful Alert Dismissal ---
    document.querySelectorAll('.alert-dismissible').forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s var(--ease-spring), transform 0.4s var(--ease-spring)';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-6px)';
            setTimeout(() => alert.remove(), 400);
        }, 5500);
    });

    // --- 8. Initialize Tooltips ---
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => new bootstrap.Tooltip(el));
    }

    // --- 9. Instant Client-Side Table Filter ---
    document.querySelectorAll('[data-table-search]').forEach(input => {
        const tableId = input.getAttribute('data-table-search');
        const targetTable = document.getElementById(tableId);
        if (!targetTable) return;

        input.addEventListener('input', function() {
            const query = this.value.toLowerCase().trim();
            const rows = targetTable.querySelectorAll('tbody tr:not(.no-filter)');
            let visibleCount = 0;

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(query)) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });

            // Empty state placeholder
            let emptyMsg = targetTable.parentElement.querySelector('.search-empty-state');
            if (visibleCount === 0 && query !== '') {
                if (!emptyMsg) {
                    emptyMsg = document.createElement('div');
                    emptyMsg.className = 'search-empty-state text-center py-4 text-muted small';
                    emptyMsg.innerHTML = '<i class="fas fa-search fa-2x mb-2 d-block opacity-25"></i>No matching records found for "<strong>' + query + '</strong>"';
                    targetTable.parentElement.appendChild(emptyMsg);
                }
            } else if (emptyMsg) {
                emptyMsg.remove();
            }
        });
    });

    // --- 10. Copy to Clipboard Micro-Interaction ---
    document.querySelectorAll('.sku-badge, [data-copy]').forEach(el => {
        el.addEventListener('click', function(e) {
            const textToCopy = this.getAttribute('data-copy') || this.innerText.trim();
            if (navigator.clipboard) {
                navigator.clipboard.writeText(textToCopy).then(() => {
                    showToast(`Copied "${textToCopy}" to clipboard!`, 'info');
                });
            }
        });
    });

    // --- 11. Theme Initialization & Sync ---
    updateThemeToggleIcons(getActiveTheme());
});

// ==========================================================================
// Theme Management (Light / Dark Mode)
// ==========================================================================

function getActiveTheme() {
    return document.documentElement.getAttribute('data-bs-theme') || 
           localStorage.getItem('inventory_theme') || 
           (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
}

function applyTheme(theme, notify = true) {
    document.documentElement.setAttribute('data-bs-theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('inventory_theme', theme);
    updateThemeToggleIcons(theme);

    window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));

    if (notify) {
        showToast(theme === 'dark' ? 'Dark theme enabled' : 'Light theme enabled', 'info');
    }
}

function toggleTheme() {
    const current = getActiveTheme();
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next, true);
}

function updateThemeToggleIcons(theme) {
    document.querySelectorAll('.btn-theme-toggle, [data-theme-toggle]').forEach(btn => {
        const moon = btn.querySelector('.theme-icon-moon');
        const sun = btn.querySelector('.theme-icon-sun');
        if (theme === 'dark') {
            if (moon) moon.classList.add('d-none');
            if (sun) sun.classList.remove('d-none');
            btn.setAttribute('title', 'Switch to Light Mode');
            btn.setAttribute('aria-label', 'Switch to Light Mode');
        } else {
            if (moon) moon.classList.remove('d-none');
            if (sun) sun.classList.add('d-none');
            btn.setAttribute('title', 'Switch to Dark Mode');
            btn.setAttribute('aria-label', 'Switch to Dark Mode');
        }
    });
}

// Chart.js Dark Mode Auto-Adapter
if (typeof window !== 'undefined') {
    window.addEventListener('themeChanged', function(e) {
        if (typeof Chart !== 'undefined' && Chart.instances) {
            const isDark = e.detail.theme === 'dark';
            const gridColor = isDark ? 'rgba(255, 255, 255, 0.07)' : '#f1f5f9';
            const textColor = isDark ? '#94a3b8' : '#64748b';

            Object.values(Chart.instances).forEach(chart => {
                if (chart.options && chart.options.scales) {
                    Object.values(chart.options.scales).forEach(scale => {
                        if (scale.grid) scale.grid.color = gridColor;
                        if (scale.ticks) scale.ticks.color = textColor;
                    });
                }
                chart.update();
            });
        }
    });
}

// Global Smooth Toast Notification
function showToast(message, type = 'info') {
    let container = document.getElementById('globalToastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'globalToastContainer';
        container.style.position = 'fixed';
        container.style.bottom = '24px';
        container.style.right = '24px';
        container.style.zIndex = '99999';
        container.style.display = 'flex';
        container.style.flexDirection = 'column';
        container.style.gap = '8px';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'toast-alert';
    toast.style.background = '#0f172a';
    toast.style.color = '#fff';
    toast.style.padding = '10px 18px';
    toast.style.borderRadius = '10px';
    toast.style.boxShadow = '0 10px 30px rgba(0,0,0,0.3)';
    toast.style.fontSize = '0.85rem';
    toast.style.fontWeight = '500';
    toast.style.display = 'flex';
    toast.style.alignItems = 'center';
    toast.style.gap = '10px';
    toast.style.transition = 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)';
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(12px) scale(0.95)';

    const icon = type === 'success' ? 'fa-circle-check text-success' : 'fa-info-circle text-info';
    toast.innerHTML = `<i class="fas ${icon}"></i><span>${message}</span>`;
    container.appendChild(toast);

    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0) scale(1)';
    });

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(12px) scale(0.95)';
        setTimeout(() => toast.remove(), 300);
    }, 3200);
}

// ==========================================================================
// Billing & POS Calculations
// ==========================================================================

let lineItemIndex = 0;

function addLineItem() {
    const tbody = document.getElementById('lineItems');
    if (!tbody) return;

    const row = document.createElement('tr');
    row.innerHTML = `
        <td>
            <select class="form-select form-select-sm product-select" name="items[${lineItemIndex}][product_id]" onchange="onProductSelect(this)" required>
                <option value="">Select Product</option>
                ${window.productOptions || ''}
            </select>
        </td>
        <td><input type="number" class="form-control form-control-sm qty-input text-center" name="items[${lineItemIndex}][quantity]" min="1" value="1" onchange="calculateLineTotal(this)" oninput="calculateLineTotal(this)" required></td>
        <td><input type="number" class="form-control form-control-sm price-input text-end" name="items[${lineItemIndex}][unit_price]" step="0.01" min="0" onchange="calculateLineTotal(this)" oninput="calculateLineTotal(this)" required readonly></td>
        <td class="line-total fw-bold text-end">0.00</td>
        <td class="text-center"><button type="button" class="btn btn-sm btn-outline-danger" onclick="removeLineItem(this)"><i class="fas fa-trash"></i></button></td>
    `;
    tbody.appendChild(row);
    lineItemIndex++;
}

function removeLineItem(btn) {
    const row = btn.closest('tr');
    if (row) {
        row.style.transition = 'opacity 0.2s, transform 0.2s';
        row.style.opacity = '0';
        row.style.transform = 'scale(0.96)';
        setTimeout(() => {
            row.remove();
            calculateGrandTotal();
        }, 180);
    }
}

function onProductSelect(select) {
    const row = select.closest('tr');
    const option = select.options[select.selectedIndex];
    const price = option.getAttribute('data-price') || 0;
    const priceInput = row.querySelector('.price-input');
    if (priceInput) priceInput.value = parseFloat(price).toFixed(2);
    calculateLineTotal(select);
}

function calculateLineTotal(element) {
    const row = element.closest('tr');
    const qty = parseFloat(row.querySelector('.qty-input')?.value) || 0;
    const price = parseFloat(row.querySelector('.price-input')?.value) || 0;
    const total = qty * price;
    const lineTotal = row.querySelector('.line-total');
    if (lineTotal) lineTotal.textContent = total.toFixed(2);
    calculateGrandTotal();
}

function calculateGrandTotal() {
    let subtotal = 0;
    document.querySelectorAll('.line-total').forEach(el => {
        subtotal += parseFloat(el.textContent) || 0;
    });

    const taxRate = parseFloat(document.getElementById('taxRate')?.value) || 0;
    const discount = parseFloat(document.getElementById('discount')?.value) || 0;
    const taxAmount = subtotal * (taxRate / 100);
    const grandTotal = subtotal + taxAmount - discount;

    const subtotalEl = document.getElementById('subtotal');
    const taxAmountEl = document.getElementById('taxAmount');
    const grandTotalEl = document.getElementById('grandTotal');

    if (subtotalEl) subtotalEl.textContent = '₹' + subtotal.toFixed(2);
    if (taxAmountEl) taxAmountEl.textContent = '₹' + taxAmount.toFixed(2);
    if (grandTotalEl) grandTotalEl.textContent = '₹' + grandTotal.toFixed(2);
}

function confirmDelete(url, name) {
    if (confirm(`Are you sure you want to delete "${name}"? This action cannot be undone.`)) {
        window.location.href = url;
    }
}

// ==========================================================================
// 10. Global Command Palette & Shortcuts Engine (Ctrl+K / Cmd+K)
// ==========================================================================

function openCommandPalette() {
    const backdrop = document.getElementById('cmdPaletteBackdrop');
    const input = document.getElementById('cmdPaletteInput');
    if (!backdrop) return;
    backdrop.classList.add('show');
    if (input) {
        input.value = '';
        filterCommandPalette('');
        setTimeout(() => input.focus(), 50);
    }
}

function closeCommandPalette() {
    const backdrop = document.getElementById('cmdPaletteBackdrop');
    if (backdrop) backdrop.classList.remove('show');
}

function handleCmdBackdropClick(e) {
    if (e.target.id === 'cmdPaletteBackdrop') {
        closeCommandPalette();
    }
}

function filterCommandPalette(query) {
    const cleanQ = query.toLowerCase().trim();
    const items = document.querySelectorAll('#cmdPaletteResults .cmd-item');
    const groupTitles = document.querySelectorAll('#cmdPaletteResults .cmd-group-title');
    let firstVisible = null;

    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        const keywords = item.getAttribute('data-keywords') || '';
        const match = cleanQ === '' || text.includes(cleanQ) || keywords.includes(cleanQ);
        item.style.display = match ? 'flex' : 'none';
        item.classList.remove('active');
        if (match && !firstVisible) {
            firstVisible = item;
            item.classList.add('active');
        }
    });

    groupTitles.forEach(title => {
        let sibling = title.nextElementSibling;
        let hasVisible = false;
        while (sibling && !sibling.classList.contains('cmd-group-title')) {
            if (sibling.style.display !== 'none') hasVisible = true;
            sibling = sibling.nextElementSibling;
        }
        title.style.display = hasVisible ? 'block' : 'none';
    });
}

function quickSwitchStore(storeId) {
    closeCommandPalette();
    showToast(`Switching store to ${storeId}...`, 'info');
    setTimeout(() => {
        window.location.href = `/auth/login?store_id=${storeId}`;
    }, 350);
}

// Global Two-Key Chord Navigation (e.g. 'G' then 'B' -> Go to Billing)
let chordPrefix = null;
let chordTimeout = null;

function handleKeyChord(key) {
    const activeEl = document.activeElement;
    const isTyping = activeEl && (
        activeEl.tagName === 'INPUT' ||
        activeEl.tagName === 'TEXTAREA' ||
        activeEl.tagName === 'SELECT' ||
        activeEl.isContentEditable
    );
    if (isTyping) return false;

    const lower = key.toLowerCase();

    if (!chordPrefix) {
        if (lower === 'g') {
            chordPrefix = 'g';
            if (chordTimeout) clearTimeout(chordTimeout);
            chordTimeout = setTimeout(() => { chordPrefix = null; }, 1200);
            return true;
        } else if (lower === 't') {
            if (typeof toggleTheme === 'function') {
                toggleTheme();
            }
            return true;
        }
    } else if (chordPrefix === 'g') {
        clearTimeout(chordTimeout);
        chordPrefix = null;
        if (lower === 'b') {
            window.location.href = '/billing/new';
            return true;
        } else if (lower === 'd') {
            window.location.href = '/dashboard/';
            return true;
        } else if (lower === 'p') {
            window.location.href = '/products/';
            return true;
        } else if (lower === 'i') {
            window.location.href = '/inventory/';
            return true;
        } else if (lower === 'a') {
            window.location.href = '/inventory/alerts';
            return true;
        }
    }
    return false;
}

// Global Keyboard Handler (Cmd+K, Escape, Arrow Navigation, Key Chords)
document.addEventListener('keydown', function(e) {
    // 1. Toggle Command Palette on Ctrl+K or Cmd+K
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        const backdrop = document.getElementById('cmdPaletteBackdrop');
        if (backdrop && backdrop.classList.contains('show')) {
            closeCommandPalette();
        } else {
            openCommandPalette();
        }
        return;
    }

    // 2. Escape to close
    if (e.key === 'Escape') {
        closeCommandPalette();
        return;
    }

    // 3. Arrow Keys navigation in Command Palette
    const backdrop = document.getElementById('cmdPaletteBackdrop');
    if (backdrop && backdrop.classList.contains('show')) {
        const visibleItems = Array.from(document.querySelectorAll('#cmdPaletteResults .cmd-item')).filter(el => el.style.display !== 'none');
        if (!visibleItems.length) return;

        let currentIndex = visibleItems.findIndex(el => el.classList.contains('active'));

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (currentIndex >= 0) visibleItems[currentIndex].classList.remove('active');
            const nextIndex = (currentIndex + 1) % visibleItems.length;
            visibleItems[nextIndex].classList.add('active');
            visibleItems[nextIndex].scrollIntoView({ block: 'nearest' });
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (currentIndex >= 0) visibleItems[currentIndex].classList.remove('active');
            const prevIndex = (currentIndex - 1 + visibleItems.length) % visibleItems.length;
            visibleItems[prevIndex].classList.add('active');
            visibleItems[prevIndex].scrollIntoView({ block: 'nearest' });
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (currentIndex >= 0) {
                visibleItems[currentIndex].click();
            }
        }
        return;
    }

    // 4. Two-key chord shortcuts outside of inputs (e.g. 'G' then 'B' -> New POS Invoice)
    if (!e.metaKey && !e.ctrlKey && !e.altKey) {
        if (handleKeyChord(e.key)) {
            // Handled chord
        }
    }
});

// Command Palette Input Live Listener & Mouse Spotlight
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('cmdPaletteInput');
    if (input) {
        input.addEventListener('input', function() {
            filterCommandPalette(this.value);
        });
    }

    // Interactive Mouse-Tracking Spotlight Effect (Linear / Stripe style)
    const spotlightCards = document.querySelectorAll('[data-spotlight="true"], .stat-card-luxury, .card-modern');
    spotlightCards.forEach(card => {
        card.setAttribute('data-spotlight', 'true');
        card.addEventListener('mousemove', function(e) {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            card.style.setProperty('--mouse-x', `${x}px`);
            card.style.setProperty('--mouse-y', `${y}px`);
        });
    });
});
