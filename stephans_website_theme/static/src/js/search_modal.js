/**
 * Stephan's Predictive Global Search Autocomplete Modal Controller
 * Pixel-perfect match to Stephan's Pet Store Design
 */
(function () {
  'use strict';

  var SearchModal = {
    isOpen: false,
    debounceTimer: null,
    selectedIndex: -1,
    currentResults: [],

    init: function () {
      this.bindEvents();
    },

    bindEvents: function () {
      var self = this;

      // Open on clicking header search input or icon
      document.addEventListener('click', function (e) {
        var openTrigger = e.target.closest('.stephans-searchbar__input, .stephans-searchbar__box, [data-open-search="true"], a[aria-label="Search"]');
        if (openTrigger) {
          e.preventDefault();
          self.open();
        }

        // Close triggers
        if (e.target.closest('#stephans-search-close, #stephans-search-backdrop')) {
          e.preventDefault();
          self.close();
        }

        // Clear input
        if (e.target.closest('#stephans-search-clear')) {
          e.preventDefault();
          var input = document.getElementById('stephans-search-modal-input');
          if (input) {
            input.value = '';
            input.focus();
            self.handleInputChange('');
          }
        }

        // Popular search pill click
        var pill = e.target.closest('.stephans-search-pill');
        if (pill) {
          e.preventDefault();
          var query = pill.getAttribute('data-query');
          var input = document.getElementById('stephans-search-modal-input');
          if (input && query) {
            input.value = query;
            input.focus();
            self.handleInputChange(query);
          }
        }
      });

      // Global keyboard shortcuts (Ctrl+K, Cmd+K, Esc)
      document.addEventListener('keydown', function (e) {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
          e.preventDefault();
          if (self.isOpen) {
            self.close();
          } else {
            self.open();
          }
        } else if (e.key === 'Escape' && self.isOpen) {
          e.preventDefault();
          self.close();
        }
      });

      // Live search input handling & Arrow key navigation
      var searchInput = document.getElementById('stephans-search-modal-input');
      if (searchInput) {
        searchInput.addEventListener('input', function (e) {
          self.handleInputChange(e.target.value);
        });

        searchInput.addEventListener('keydown', function (e) {
          if (e.key === 'ArrowDown') {
            e.preventDefault();
            self.moveSelection(1);
          } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            self.moveSelection(-1);
          } else if (e.key === 'Enter') {
            e.preventDefault();
            self.handleEnter();
          }
        });
      }
    },

    open: function () {
      this.isOpen = true;
      var modal = document.getElementById('stephans-search-modal');
      var backdrop = document.getElementById('stephans-search-backdrop');
      var input = document.getElementById('stephans-search-modal-input');

      if (modal) modal.classList.add('is-open');
      if (backdrop) backdrop.classList.add('is-open');
      document.body.style.overflow = 'hidden';

      if (input) {
        setTimeout(function () {
          input.focus();
        }, 100);
      }
    },

    close: function () {
      this.isOpen = false;
      var modal = document.getElementById('stephans-search-modal');
      var backdrop = document.getElementById('stephans-search-backdrop');
      if (modal) modal.classList.remove('is-open');
      if (backdrop) backdrop.classList.remove('is-open');
      document.body.style.overflow = '';
      this.selectedIndex = -1;
    },

    handleInputChange: function (value) {
      var self = this;
      var q = value.trim();
      var clearBtn = document.getElementById('stephans-search-clear');
      var initialSec = document.getElementById('stephans-search-initial');
      var resultsSec = document.getElementById('stephans-search-results-area');
      var loadingEl = document.getElementById('stephans-search-loading');
      var prodsGroup = document.getElementById('stephans-search-products-group');
      var taxGroup = document.getElementById('stephans-search-tax-group');
      var noResultsEl = document.getElementById('stephans-search-no-results');

      if (clearBtn) {
        clearBtn.style.display = q.length > 0 ? 'inline-block' : 'none';
      }

      if (q.length < 2) {
        if (initialSec) initialSec.style.display = 'block';
        if (resultsSec) resultsSec.style.display = 'none';
        if (prodsGroup) prodsGroup.style.display = 'none';
        if (taxGroup) taxGroup.style.display = 'none';
        if (noResultsEl) noResultsEl.style.display = 'none';
        self.selectedIndex = -1;
        self.currentResults = [];
        return;
      }

      // Query >= 2 chars: Show results container and loading spinner
      if (initialSec) initialSec.style.display = 'none';
      if (resultsSec) resultsSec.style.display = 'block';
      if (loadingEl) loadingEl.style.display = 'flex';
      if (prodsGroup) prodsGroup.style.display = 'none';
      if (taxGroup) taxGroup.style.display = 'none';
      if (noResultsEl) noResultsEl.style.display = 'none';

      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(function () {
        self.performSearch(q);
      }, 220);
    },

    performSearch: function (query) {
      var self = this;
      var loadingEl = document.getElementById('stephans-search-loading');
      var prodsGroup = document.getElementById('stephans-search-products-group');
      var prodsList = document.getElementById('stephans-search-products-list');
      var taxGroup = document.getElementById('stephans-search-tax-group');
      var taxList = document.getElementById('stephans-search-tax-list');
      var noResultsEl = document.getElementById('stephans-search-no-results');
      var countEl = document.getElementById('stephans-results-count');
      var seeAllEl = document.getElementById('stephans-search-see-all');

      fetch('/stephans/api/search?q=' + encodeURIComponent(query), {
        headers: { 'Accept': 'application/json' }
      })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          if (loadingEl) loadingEl.style.display = 'none';
          var products = data.products || data.results || [];
          var categories = data.categories || [];
          var brands = data.brands || [];
          var totalCount = data.count || products.length;

          self.currentResults = [];
          self.selectedIndex = 0;

          // Update footer See All link
          if (countEl) countEl.textContent = totalCount;
          if (seeAllEl) seeAllEl.href = '/shop?search=' + encodeURIComponent(query);

          var hasProducts = products.length > 0;
          var hasTax = categories.length > 0 || brands.length > 0;

          if (!hasProducts && !hasTax) {
            if (noResultsEl) noResultsEl.style.display = 'block';
            if (prodsGroup) prodsGroup.style.display = 'none';
            if (taxGroup) taxGroup.style.display = 'none';
            return;
          }

          if (noResultsEl) noResultsEl.style.display = 'none';

          // 1. Render Products
          if (hasProducts && prodsGroup && prodsList) {
            prodsGroup.style.display = 'block';
            prodsList.innerHTML = products.map(function (item, idx) {
              self.currentResults.push({ type: 'product', url: item.url || ('/shop/product/' + item.id) });
              var brandCat = (item.brand ? item.brand + ' · ' : '') + (item.category || 'Pet Food');
              return (
                '<a href="' + (item.url || ('/shop/product/' + item.id)) + '" class="stephans-search-product-item ' + (idx === 0 ? 'is-selected' : '') + '" data-idx="' + (self.currentResults.length - 1) + '">' +
                  '<div class="stephans-search-product-thumb">' +
                    '<img src="' + item.image_url + '" alt="' + item.name + '" loading="lazy"/>' +
                  '</div>' +
                  '<div class="stephans-search-product-meta">' +
                    '<h4 class="stephans-search-product-title">' + item.name + '</h4>' +
                    '<div class="stephans-search-product-sub">' + brandCat + '</div>' +
                  '</div>' +
                  '<div class="stephans-search-product-price">' + item.price_formatted + '</div>' +
                '</a>'
              );
            }).join('');
          } else if (prodsGroup) {
            prodsGroup.style.display = 'none';
          }

          // 2. Render Categories & Brands
          if (hasTax && taxGroup && taxList) {
            taxGroup.style.display = 'block';
            var taxHtml = '';

            categories.forEach(function (cat) {
              self.currentResults.push({ type: 'category', url: cat.url });
              taxHtml += (
                '<a href="' + cat.url + '" class="stephans-search-tax-item" data-idx="' + (self.currentResults.length - 1) + '">' +
                  '<span class="stephans-search-tax-name">' + cat.name + '</span>' +
                  '<span class="stephans-search-tax-badge">Category</span>' +
                '</a>'
              );
            });

            brands.forEach(function (brand) {
              self.currentResults.push({ type: 'brand', url: brand.url });
              taxHtml += (
                '<a href="' + brand.url + '" class="stephans-search-tax-item stephans-search-tax-item--brand" data-idx="' + (self.currentResults.length - 1) + '">' +
                  '<span class="stephans-search-tax-name stephans-search-tax-name--brand">' + brand.name + '</span>' +
                  '<span class="stephans-search-tax-badge">Brand</span>' +
                '</a>'
              );
            });

            taxList.innerHTML = taxHtml;
          } else if (taxGroup) {
            taxGroup.style.display = 'none';
          }
        })
        .catch(function (err) {
          if (loadingEl) loadingEl.style.display = 'none';
          console.error('Stephan\'s search error:', err);
        });
    },

    moveSelection: function (dir) {
      if (!this.currentResults || this.currentResults.length === 0) return;

      var items = document.querySelectorAll('.stephans-search-product-item, .stephans-search-tax-item');
      if (items.length === 0) return;

      items.forEach(function (el) { el.classList.remove('is-selected'); });

      this.selectedIndex += dir;
      if (this.selectedIndex < 0) {
        this.selectedIndex = items.length - 1;
      } else if (this.selectedIndex >= items.length) {
        this.selectedIndex = 0;
      }

      var activeItem = items[this.selectedIndex];
      if (activeItem) {
        activeItem.classList.add('is-selected');
        activeItem.scrollIntoView({ block: 'nearest' });
      }
    },

    handleEnter: function () {
      if (this.selectedIndex >= 0 && this.currentResults[this.selectedIndex]) {
        window.location.href = this.currentResults[this.selectedIndex].url;
      } else {
        var input = document.getElementById('stephans-search-modal-input');
        var q = input ? input.value.trim() : '';
        if (q) {
          window.location.href = '/shop?search=' + encodeURIComponent(q);
        }
      }
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      SearchModal.init();
    });
  } else {
    SearchModal.init();
  }

  window.StephansSearchModal = SearchModal;
})();
