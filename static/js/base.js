(function() {
    function getCSRF() {
        const el = document.querySelector('[name=csrfmiddlewaretoken]');
        return el ? el.value : '';
    }

    function showToast(message, type) {
        const stack = document.getElementById('toast-stack');
        if (!stack) return;
        const toast = document.createElement('div');
        toast.className = 'cart-toast ' + (type === 'error' || type === 'danger' ? 'error' : 'success');
        toast.textContent = message;
        toast.style.position = 'relative';
        toast.style.transform = 'translateX(120%)';
        stack.appendChild(toast);
        requestAnimationFrame(function() {
            toast.style.transform = 'translateX(0)';
        });
        setTimeout(function() {
            toast.style.transform = 'translateX(120%)';
            setTimeout(function() { toast.remove(); }, 300);
        }, 3000);
    }

    function updateBadge(count) {
        const badge = document.getElementById('cart-count-badge');
        if (!badge) return;
        badge.textContent = count;
        badge.style.display = count > 0 ? '' : 'none';
    }

    function renderSearchSuggestions(items) {
        if (!window.searchSuggestionsBox) return;
        if (!items.length) {
            window.searchSuggestionsBox.innerHTML = '<div class="empty">No suggestions found.</div>';
            window.searchSuggestionsBox.classList.add('show');
            return;
        }
        window.searchSuggestionsBox.innerHTML = items.map(function(item) {
            return '<a href="' + item.url + '"><strong>' + item.title + '</strong>' +
                (item.brand ? ' <span style="color:#555;font-size:12px;">(' + item.brand + ')</span>' : '') +
                '<div style="font-size:12px;color:#777;">$' + item.price + '</div></a>';
        }).join('');
        window.searchSuggestionsBox.classList.add('show');
    }

    function hideSearchSuggestions() {
        if (!window.searchSuggestionsBox) return;
        window.searchSuggestionsBox.classList.remove('show');
        window.searchSuggestionsBox.innerHTML = '';
    }

    function initSearchSuggestions() {
        const searchInput = document.getElementById('site-search-input');
        window.searchSuggestionsBox = document.getElementById('search-suggestions');
        if (!searchInput || !window.searchSuggestionsBox || !window.suggestionsUrl) return;

        let searchTimeout = null;
        searchInput.addEventListener('input', function() {
            const query = this.value.trim();
            clearTimeout(searchTimeout);
            if (!query) {
                hideSearchSuggestions();
                return;
            }
            searchTimeout = setTimeout(function() {
                fetch(window.suggestionsUrl + '?q=' + encodeURIComponent(query), {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' },
                })
                .then(function(res) { return res.json(); })
                .then(function(data) {
                    renderSearchSuggestions(data.suggestions || []);
                })
                .catch(function() {
                    hideSearchSuggestions();
                });
            }, 250);
        });

        document.addEventListener('click', function(event) {
            if (!searchInput.contains(event.target) && !window.searchSuggestionsBox.contains(event.target)) {
                hideSearchSuggestions();
            }
        });
    }

    function initAjaxForms() {
        document.addEventListener('submit', function(event) {
            const form = event.target;
            if (!form.action) return;
            const action = form.action;
            const isCart = action.includes('/cart/add/');
            const isWishlist = action.includes('/wishlist/toggle/') || action.includes('/toggle_wishlist');
            if (!isCart && !isWishlist) return;

            event.preventDefault();
            const btn = form.querySelector('button[type="submit"]');
            const originalText = btn ? btn.textContent : '';
            if (btn) { btn.disabled = true; btn.textContent = isCart ? 'Adding...' : 'Updating...'; }

            const formData = new FormData(form);
            fetch(form.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken') || getCSRF(),
                },
                body: formData,
            })
            .then(function(res) { return res.json(); })
            .then(function(data) {
                if (data.success) {
                    showToast('✓ ' + data.message, 'success');
                    if (isCart && data.cart_count !== undefined) {
                        updateBadge(data.cart_count);
                    }
                    if (isWishlist && btn) {
                        btn.classList.toggle('active', data.in_wishlist);
                        btn.textContent = data.button_label || btn.textContent;
                    }
                } else {
                    showToast('✗ ' + data.message, 'error');
                }
            })
            .catch(function() {
                showToast('Something went wrong. Please try again.', 'error');
            })
            .finally(function() {
                if (btn) { btn.disabled = false; btn.textContent = originalText; }
            });
        });
    }

    function initMessages() {
        if (!window._djangoMessages || !window._djangoMessages.length) return;
        window._djangoMessages.forEach(function(msg, i) {
            setTimeout(function() {
                const prefix = (msg.type === 'error' || msg.type === 'danger') ? '✗ ' : '✓ ';
                showToast(prefix + msg.text, msg.type);
            }, i * 200);
        });
    }

    function init() {
        initMessages();
        initSearchSuggestions();
        initAjaxForms();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();