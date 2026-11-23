/**
 * Stephan's Predictive Global Search Autocomplete Modal Controller
 * Pixel-perfect match to Stephan's Pet Store Design
 */
(function () {
  'use strict';

  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function escapeAttr(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  var SearchModal = {
    isOpen: false,
    debounceTimer: null,
    selectedIndex: -1,
    currentResults: [],
    abortController: null,
    querySeq: 0,
    currentQuery: '',
    lastFocusedElement: null,

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
          var headerInp = openTrigger.querySelector ? openTrigger.querySelector('.stephans-searchbar__input') : null;
          if (!headerInp && openTrigger.classList && openTrigger.classList.contains('stephans-searchbar__input')) {
            headerInp = openTrigger;
          }
          var initialVal = headerInp && headerInp.value ? headerInp.value.trim() : '';
          self.open(initialVal);
          return;
        }

        // Close triggers
        if (e.target.closest('#stephans-search-close, #stephans-search-backdrop')) {
          e.preventDefault();
          self.close();
          return;
        }

        // Clear input icon inside input field
        if (e.target.closest('#stephans-search-input-clear')) {
          e.preventDefault();
          var input = document.getElementById('stephans-search-modal-input');
          if (input) {
            input.value = '';
            input.focus();
            self.handleInputChange('');
          }
          return;
        }

        // Empty state: View popular brands action
        if (e.target.closest('#stephans-search-view-brands')) {
          e.preventDefault();
          var input = document.getElementById('stephans-search-modal-input');
          if (input) {
            input.value = '';
            self.handleInputChange('');
            var initialSec = document.getElementById('stephans-search-initial');
            if (initialSec) {
              var brandsGrid = initialSec.querySelector('.stephans-search-brands-wrap');
              if (brandsGrid) {
                brandsGrid.scrollIntoView({ behavior: 'smooth', block: 'start' });
              }
            }
          }
          return;
        }

        // Search Error state: Retry button
        if (e.target.closest('#stephans-search-retry-btn')) {
          e.preventDefault();
          if (self.currentQuery) {
            self.performSearch(self.currentQuery);
          }
          return;
        }

        // Suggestion / Popular search pill click
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
          return;
        }
      });

      // Global keyboard shortcuts (Ctrl+K, Cmd+K, Esc, Tab trapping)
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
        } else if (e.key === 'Tab' && self.isOpen) {
          self.handleTabTrapping(e);
        }
      });

      // Live search input handling & Arrow key navigation (event delegation so it never fails if DOM loads after script)
      document.addEventListener('input', function (e) {
        if (e.target && e.target.id === 'stephans-search-modal-input') {
          self.handleInputChange(e.target.value);
        }
      });

      document.addEventListener('paste', function (e) {
        if (e.target && e.target.id === 'stephans-search-modal-input') {
          setTimeout(function () {
            var inp = document.getElementById('stephans-search-modal-input');
            if (inp) {
              inp.setSelectionRange(0, 0);
              inp.scrollLeft = 0;
              self.handleInputChange(inp.value);
            }
          }, 15);
        }
      });

      document.addEventListener('change', function (e) {
        if (e.target && e.target.id === 'stephans-search-modal-input') {
          self.handleInputChange(e.target.value);
        }
      });

      document.addEventListener('keydown', function (e) {
        if (e.target && e.target.id === 'stephans-search-modal-input') {
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
        }
      });
    },

    open: function (prefillValue) {
      var self = this;
      this.isOpen = true;
      this.lastFocusedElement = document.activeElement;
      var modal = document.getElementById('stephans-search-modal');
      var backdrop = document.getElementById('stephans-search-backdrop');
      var input = document.getElementById('stephans-search-modal-input');

      if (modal) {
        modal.classList.add('is-open');
        modal.setAttribute('aria-hidden', 'false');
      }
      if (backdrop) {
        backdrop.classList.add('is-open');
        backdrop.setAttribute('aria-hidden', 'false');
      }
      if (input) {
        input.setAttribute('aria-expanded', 'true');
        if (typeof prefillValue === 'string' && prefillValue.trim()) {
          input.value = prefillValue.trim();
        }
        setTimeout(function () {
          input.focus();
          if (input.value) {
            self.handleInputChange(input.value);
          }
        }, 60);
      }
      document.body.style.overflow = 'hidden';
    },

    close: function () {
      this.isOpen = false;
      var modal = document.getElementById('stephans-search-modal');
      var backdrop = document.getElementById('stephans-search-backdrop');
      var input = document.getElementById('stephans-search-modal-input');

      if (this.abortController) {
        this.abortController.abort();
        this.abortController = null;
      }

      if (modal) {
        modal.classList.remove('is-open');
        modal.setAttribute('aria-hidden', 'true');
      }
      if (backdrop) {
        backdrop.classList.remove('is-open');
        backdrop.setAttribute('aria-hidden', 'true');
      }
      if (input) {
        input.setAttribute('aria-expanded', 'false');
        input.removeAttribute('aria-activedescendant');
      }
      document.body.style.overflow = '';
      this.selectedIndex = -1;

      if (this.lastFocusedElement && typeof this.lastFocusedElement.focus === 'function') {
        try {
          this.lastFocusedElement.focus();
        } catch (e) {}
      }
    },

    handleTabTrapping: function (e) {
      var modal = document.getElementById('stephans-search-modal');
      if (!modal) return;

      var focusables = modal.querySelectorAll('input:not([disabled]), button:not([disabled]), a[href]:not([disabled]), [tabindex]:not([tabindex="-1"])');
      var visibleFocusables = Array.prototype.filter.call(focusables, function (el) {
        return el.offsetParent !== null;
      });

      if (visibleFocusables.length === 0) return;

      var firstEl = visibleFocusables[0];
      var lastEl = visibleFocusables[visibleFocusables.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === firstEl) {
          e.preventDefault();
          lastEl.focus();
        }
      } else {
        if (document.activeElement === lastEl) {
          e.preventDefault();
          firstEl.focus();
        }
      }
    },

    updateKeyboardShortcuts: function (hasResults) {
      var emptyMsg = document.getElementById('stephans-shortcut-empty');
      var resultsMsg = document.getElementById('stephans-shortcut-results');
      if (emptyMsg) emptyMsg.style.display = hasResults ? 'none' : 'inline-flex';
      if (resultsMsg) resultsMsg.style.display = hasResults ? 'inline-flex' : 'none';
    },

    handleInputChange: function (value) {
      var self = this;
      var q = value.trim();
      self.currentQuery = q;

      var clearBtn = document.getElementById('stephans-search-input-clear');
      var initialSec = document.getElementById('stephans-search-initial');
      var resultsSec = document.getElementById('stephans-search-results-area');
      var loadingEl = document.getElementById('stephans-search-loading');
      var prodsGroup = document.getElementById('stephans-search-products-group');
      var taxGroup = document.getElementById('stephans-search-tax-group');
      var noResultsEl = document.getElementById('stephans-search-no-results');
      var errorEl = document.getElementById('stephans-search-error-state');
      var seeAllEl = document.getElementById('stephans-search-see-all');

      if (clearBtn) {
        clearBtn.style.display = q.length > 0 ? 'flex' : 'none';
      }

      if (q.length < 2) {
        if (self.abortController) {
          self.abortController.abort();
          self.abortController = null;
        }
        if (initialSec) initialSec.style.display = 'block';
        if (resultsSec) resultsSec.style.display = 'none';
        if (prodsGroup) prodsGroup.style.display = 'none';
        if (taxGroup) taxGroup.style.display = 'none';
        if (noResultsEl) noResultsEl.style.display = 'none';
        if (errorEl) errorEl.style.display = 'none';
        if (seeAllEl) seeAllEl.style.display = 'none';

        self.selectedIndex = -1;
        self.currentResults = [];
        self.updateKeyboardShortcuts(false);
        return;
      }

      // Query >= 2 chars: Show results container and loading spinner
      if (initialSec) initialSec.style.display = 'none';
      if (resultsSec) resultsSec.style.display = 'block';
      if (loadingEl) loadingEl.style.display = 'flex';
      if (prodsGroup) prodsGroup.style.display = 'none';
      if (taxGroup) taxGroup.style.display = 'none';
      if (noResultsEl) noResultsEl.style.display = 'none';
      if (errorEl) errorEl.style.display = 'none';
      if (seeAllEl) seeAllEl.style.display = 'none';

      self.updateKeyboardShortcuts(false);

      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(function () {
        self.performSearch(q);
      }, 200);
    },

    performSearch: function (query) {
      var self = this;
      var loadingEl = document.getElementById('stephans-search-loading');
      var prodsGroup = document.getElementById('stephans-search-products-group');
      var prodsList = document.getElementById('stephans-search-products-list');
      var taxGroup = document.getElementById('stephans-search-tax-group');
      var taxList = document.getElementById('stephans-search-tax-list');
      var noResultsEl = document.getElementById('stephans-search-no-results');
      var failedQueryEl = document.getElementById('stephans-search-failed-query');
      var errorEl = document.getElementById('stephans-search-error-state');
      var countEl = document.getElementById('stephans-results-count');
      var seeAllEl = document.getElementById('stephans-search-see-all');

      // Abort any existing in-flight request
      if (this.abortController) {
        this.abortController.abort();
      }
      this.abortController = new AbortController();
      var thisSeq = ++this.querySeq;

      fetch('/stephans/api/search?q=' + encodeURIComponent(query), {
        headers: { 'Accept': 'application/json' },
        signal: this.abortController.signal
      })
        .then(function (res) {
          if (!res.ok) throw new Error('Search network error: ' + res.status);
          return res.json();
        })
        .then(function (data) {
          // Stale response guard
          if (thisSeq !== self.querySeq) return;

          if (loadingEl) loadingEl.style.display = 'none';
          if (errorEl) errorEl.style.display = 'none';

          var products = data.products || data.results || [];
          var categories = data.categories || [];
          var brands = data.brands || [];
          var totalCount = data.count !== undefined ? data.count : products.length;

          self.currentResults = [];
          // Index starts at -1 so first item is NOT auto-skipped on first arrow press
          self.selectedIndex = -1;

          var hasProducts = products.length > 0;
          var hasTax = categories.length > 0 || brands.length > 0;

          // 1. Result Count / Footer Link Rules
          if (hasProducts) {
            if (countEl) countEl.textContent = totalCount;
            if (seeAllEl) {
              seeAllEl.style.display = 'inline-flex';
              seeAllEl.href = '/shop?search=' + encodeURIComponent(query);
              seeAllEl.innerHTML = 'View all <span id="stephans-results-count">' + escapeHtml(totalCount) + '</span> results &rarr;';
            }
            self.updateKeyboardShortcuts(true);
          } else if (brands.length > 0) {
            // No product results but brand matches
            var matchedBrand = brands[0];
            if (seeAllEl) {
              seeAllEl.style.display = 'inline-flex';
              seeAllEl.href = matchedBrand.url || ('/shop?search=' + encodeURIComponent(matchedBrand.name));
              seeAllEl.innerHTML = 'View ' + escapeHtml(matchedBrand.name) + ' products &rarr;';
            }
            self.updateKeyboardShortcuts(true);
          } else {
            // Nothing matches: Hide result-count link completely
            if (seeAllEl) seeAllEl.style.display = 'none';
            self.updateKeyboardShortcuts(false);
          }

          // 2. Empty State Handling
          if (!hasProducts && !hasTax) {
            if (noResultsEl) {
              noResultsEl.style.display = 'block';
              if (failedQueryEl) failedQueryEl.textContent = query;
            }
            if (prodsGroup) prodsGroup.style.display = 'none';
            if (taxGroup) taxGroup.style.display = 'none';
            return;
          }

          if (noResultsEl) noResultsEl.style.display = 'none';

          // 3. Render Products Securely
          if (hasProducts && prodsGroup && prodsList) {
            prodsGroup.style.display = 'block';
            var prodsHtml = products.map(function (item) {
              var targetUrl = item.url || ('/shop/product/' + item.id);
              self.currentResults.push({ type: 'product', url: targetUrl });
              var itemIdx = self.currentResults.length - 1;
              var brandCat = (item.brand ? item.brand + ' · ' : '') + (item.category || 'Pet Food');

              return (
                '<a href="' + escapeAttr(targetUrl) + '" class="stephans-search-product-item" id="stephans-search-item-' + itemIdx + '" data-idx="' + itemIdx + '" role="option" aria-selected="false">' +
                  '<div class="stephans-search-product-thumb">' +
                    '<img src="' + escapeAttr(item.image_url) + '" alt="' + escapeAttr(item.name) + '" loading="lazy"/>' +
                  '</div>' +
                  '<div class="stephans-search-product-meta">' +
                    '<h4 class="stephans-search-product-title">' + escapeHtml(item.name) + '</h4>' +
                    '<div class="stephans-search-product-sub">' + escapeHtml(brandCat) + '</div>' +
                  '</div>' +
                  '<div class="stephans-search-product-price">' + escapeHtml(item.price_formatted) + '</div>' +
                '</a>'
              );
            }).join('');
            prodsList.innerHTML = prodsHtml;
          } else if (prodsGroup) {
            prodsGroup.style.display = 'none';
          }

          // 4. Render Categories & Brands Securely
          if (hasTax && taxGroup && taxList) {
            taxGroup.style.display = 'block';
            var taxHtml = '';

            categories.forEach(function (cat) {
              self.currentResults.push({ type: 'category', url: cat.url });
              var itemIdx = self.currentResults.length - 1;
              taxHtml += (
                '<a href="' + escapeAttr(cat.url) + '" class="stephans-search-tax-item" id="stephans-search-item-' + itemIdx + '" data-idx="' + itemIdx + '" role="option" aria-selected="false">' +
                  '<span class="stephans-search-tax-name">' + escapeHtml(cat.name) + '</span>' +
                  '<span class="stephans-search-tax-badge">Category</span>' +
                '</a>'
              );
            });

            brands.forEach(function (brand) {
              self.currentResults.push({ type: 'brand', url: brand.url });
              var itemIdx = self.currentResults.length - 1;
              taxHtml += (
                '<a href="' + escapeAttr(brand.url) + '" class="stephans-search-tax-item stephans-search-tax-item--brand" id="stephans-search-item-' + itemIdx + '" data-idx="' + itemIdx + '" role="option" aria-selected="false">' +
                  '<span class="stephans-search-tax-name stephans-search-tax-name--brand">' + escapeHtml(brand.name) + '</span>' +
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
          if (err.name === 'AbortError') return; // Expected cancellation

          if (thisSeq !== self.querySeq) return;
          if (loadingEl) loadingEl.style.display = 'none';
          if (prodsGroup) prodsGroup.style.display = 'none';
          if (taxGroup) taxGroup.style.display = 'none';
          if (noResultsEl) noResultsEl.style.display = 'none';
          if (seeAllEl) seeAllEl.style.display = 'none';

          if (errorEl) errorEl.style.display = 'block';
          self.updateKeyboardShortcuts(false);
          console.error('Stephan\'s search error:', err);
        });
    },

    moveSelection: function (dir) {
      if (!this.currentResults || this.currentResults.length === 0) return;

      var items = document.querySelectorAll('.stephans-search-product-item, .stephans-search-tax-item');
      if (items.length === 0) return;

      items.forEach(function (el) {
        el.classList.remove('is-selected');
        el.setAttribute('aria-selected', 'false');
      });

      // Initial press of ArrowDown starts at 0, ArrowUp starts at last
      if (this.selectedIndex === -1) {
        this.selectedIndex = dir > 0 ? 0 : (items.length - 1);
      } else {
        this.selectedIndex += dir;
        if (this.selectedIndex < 0) {
          this.selectedIndex = items.length - 1;
        } else if (this.selectedIndex >= items.length) {
          this.selectedIndex = 0;
        }
      }

      var activeItem = items[this.selectedIndex];
      var input = document.getElementById('stephans-search-modal-input');
      if (activeItem) {
        activeItem.classList.add('is-selected');
        activeItem.setAttribute('aria-selected', 'true');
        activeItem.scrollIntoView({ block: 'nearest' });
        if (input && activeItem.id) {
          input.setAttribute('aria-activedescendant', activeItem.id);
        }
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
