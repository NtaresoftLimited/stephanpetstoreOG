/**
 * Stephan's Slide-Over Cart Drawer Controller
 * Handles real-time cart interaction, slide-over animations, and free delivery meter.
 */
(function () {
  'use strict';

  var CartDrawer = {
    isOpen: false,
    threshold: 100000,

    init: function () {
      this.bindEvents();
      this.updateHeaderBadge();
    },

    bindEvents: function () {
      var self = this;

      document.addEventListener('click', function (e) {
        // 1. Close triggers (backdrop or close icon)
        if (e.target.closest('#stephans-cart-close, #stephans-cart-backdrop')) {
          e.preventDefault();
          self.close();
          return;
        }

        // 2. Actions inside the drawer
        if (e.target.closest('#stephans-cart-drawer')) {
          // Quantity controls inside drawer
          var qtyBtn = e.target.closest('.stephans-qty-btn');
          if (qtyBtn) {
            e.preventDefault();
            var lineId = parseInt(qtyBtn.getAttribute('data-line-id'), 10);
            var action = qtyBtn.getAttribute('data-action');
            var currentQty = parseInt(qtyBtn.getAttribute('data-qty'), 10);
            var newQty = action === 'plus' ? currentQty + 1 : currentQty - 1;
            self.updateCartItem(lineId, newQty);
            return;
          }

          // Remove item button
          var removeBtn = e.target.closest('.stephans-cart-item__remove');
          if (removeBtn) {
            e.preventDefault();
            var lineId = parseInt(removeBtn.getAttribute('data-line-id'), 10);
            self.updateCartItem(lineId, 0);
            return;
          }

          // All links inside the drawer (Checkout, Cart, Products) must navigate natively
          return;
        }

        // 3. Open triggers from header / navbar / page
        var cartTrigger = e.target.closest('.stephans-action-item--cart, [data-open-cart="true"], a[href="/shop/cart"]');
        if (cartTrigger) {
          // If the user is on the cart or checkout page itself, let default navigation work
          if (window.location.pathname === '/shop/cart' || window.location.pathname.startsWith('/shop/checkout')) {
            return;
          }
          e.preventDefault();
          self.open();
        }
      });

      // ESC key closes drawer
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && self.isOpen) {
          self.close();
        }
      });

      // Intercept standard Odoo "Add to Cart" forms if present
      document.addEventListener('submit', function (e) {
        var form = e.target;
        if (form && (form.getAttribute('action') === '/shop/cart/update' || form.classList.contains('js_add_cart_variants'))) {
          // Allow default submission or trigger drawer refresh after short delay
          setTimeout(function () {
            self.fetchCartStatus(true);
          }, 800);
        }
      });
    },

    open: function () {
      this.isOpen = true;
      var drawer = document.getElementById('stephans-cart-drawer');
      var backdrop = document.getElementById('stephans-cart-backdrop');
      if (drawer) drawer.classList.add('is-open');
      if (backdrop) backdrop.classList.add('is-open');
      document.body.style.overflow = 'hidden';
      this.fetchCartStatus(false);
    },

    close: function () {
      this.isOpen = false;
      var drawer = document.getElementById('stephans-cart-drawer');
      var backdrop = document.getElementById('stephans-cart-backdrop');
      if (drawer) drawer.classList.remove('is-open');
      if (backdrop) backdrop.classList.remove('is-open');
      document.body.style.overflow = '';
    },

    fetchCartStatus: function (openIfItems) {
      var self = this;
      fetch('/stephans/api/cart_status', {
        headers: { 'Accept': 'application/json' }
      })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          self.renderCart(data);
          if (openIfItems && data.cart_quantity > 0) {
            self.open();
          }
        })
        .catch(function (err) {
          console.error('Failed to load Stephan\'s cart status:', err);
        });
    },

    updateCartItem: function (lineId, quantity) {
      var self = this;
      fetch('/stephans/api/cart_update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          line_id: lineId,
          quantity: quantity
        })
      })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          if (data.success) {
            self.fetchCartStatus(false);
          } else {
            console.warn('Cart update issue:', data.error);
          }
        })
        .catch(function (err) {
          console.error('Failed to update cart item:', err);
        });
    },

    renderCart: function (data) {
      var count = data.cart_quantity || 0;
      var total = data.amount_total || 0;
      var lines = data.lines || [];

      // Update Header & Drawer Count Badges
      var headerBadges = document.querySelectorAll('.stephans-cart-badge');
      headerBadges.forEach(function (el) {
        el.textContent = count;
        el.style.display = count > 0 ? '' : 'none';
      });

      var drawerBadge = document.getElementById('stephans-cart-badge-drawer');
      if (drawerBadge) {
        drawerBadge.textContent = count;
      }

      var emptyEl = document.getElementById('stephans-cart-empty');
      var containerEl = document.getElementById('stephans-cart-items-container');
      var subtotalEl = document.getElementById('stephans-cart-subtotal');
      var footerEl = document.getElementById('stephans-cart-footer');

      if (subtotalEl) {
        subtotalEl.textContent = 'TZS ' + total.toLocaleString();
      }

      // Free Delivery Progress Meter
      var meterText = document.getElementById('stephans-delivery-message');
      var meterFill = document.getElementById('stephans-delivery-progress');
      var pct = Math.min(100, Math.round((total / this.threshold) * 100));

      if (meterFill) {
        meterFill.style.width = pct + '%';
      }

      if (meterText) {
        if (total >= this.threshold) {
          meterText.innerHTML = '🎉 <strong>You\'ve unlocked FREE Delivery</strong> in Dar es Salaam!';
        } else {
          var remaining = this.threshold - total;
          meterText.innerHTML = 'Add <strong>TZS ' + remaining.toLocaleString() + '</strong> more for <strong>FREE Delivery</strong>';
        }
      }

      // Empty State vs Items List
      if (lines.length === 0) {
        if (emptyEl) emptyEl.style.display = 'flex';
        if (containerEl) {
          containerEl.innerHTML = '';
          containerEl.style.display = 'none';
        }
        if (footerEl) footerEl.style.display = 'none';
      } else {
        if (emptyEl) emptyEl.style.display = 'none';
        if (footerEl) footerEl.style.display = 'block';
        if (containerEl) {
          containerEl.style.display = 'flex';
          containerEl.innerHTML = lines.map(function (item) {
            return (
              '<div class="stephans-cart-item" data-line-id="' + item.id + '">' +
                '<div class="stephans-cart-item__img-wrap">' +
                  '<img src="' + item.image_url + '" alt="' + item.name + '" class="stephans-cart-item__img" loading="lazy"/>' +
                '</div>' +
                '<div class="stephans-cart-item__details">' +
                  '<h4 class="stephans-cart-item__title">' +
                    '<a href="/shop/product/' + item.product_id + '">' + item.name + '</a>' +
                  '</h4>' +
                  '<div class="stephans-cart-item__price">' + item.price_unit_formatted + '</div>' +
                  '<div class="stephans-cart-item__controls">' +
                    '<div class="stephans-qty-stepper">' +
                      '<button type="button" class="stephans-qty-btn" data-action="minus" data-line-id="' + item.id + '" data-qty="' + item.quantity + '" aria-label="Decrease quantity">−</button>' +
                      '<span class="stephans-qty-val">' + item.quantity + '</span>' +
                      '<button type="button" class="stephans-qty-btn" data-action="plus" data-line-id="' + item.id + '" data-qty="' + item.quantity + '" aria-label="Increase quantity">+</button>' +
                    '</div>' +
                    '<button type="button" class="stephans-cart-item__remove" data-line-id="' + item.id + '" aria-label="Remove item">' +
                      '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
                        '<polyline points="3 6 5 6 21 6"/>' +
                        '<path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>' +
                      '</svg>' +
                    '</button>' +
                  '</div>' +
                '</div>' +
              '</div>'
            );
          }).join('');
        }
      }
    },

    updateHeaderBadge: function () {
      // Passive check on initial page load
      fetch('/stephans/api/cart_status', {
        headers: { 'Accept': 'application/json' }
      })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          var count = data.cart_quantity || 0;
          var headerBadges = document.querySelectorAll('.stephans-cart-badge');
          headerBadges.forEach(function (el) {
            el.textContent = count;
            el.style.display = count > 0 ? '' : 'none';
          });
        })
        .catch(function () {});
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      CartDrawer.init();
    });
  } else {
    CartDrawer.init();
  }

  window.StephansCartDrawer = CartDrawer;
})();
