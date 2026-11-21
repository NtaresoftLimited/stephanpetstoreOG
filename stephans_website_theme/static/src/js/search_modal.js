/**
 * Stephan's Predictive Search Autocomplete Modal Controller
 * Intercepts search triggers, debounces live queries against Odoo catalog,
 * and renders instant product cards and popular tags.
 */
(function () {
  'use strict';

  var SearchModal = {
    isOpen: false,
    debounceTimer: null,

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

      // Global shortcut: Ctrl+K or Cmd+K or "/"
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

      // Live search input handling
      var searchInput = document.getElementById('stephans-search-modal-input');
      if (searchInput) {
        searchInput.addEventListener('input', function (e) {
          self.handleInputChange(e.target.value);
        });

        searchInput.addEventListener('keydown', function (e) {
          if (e.key === 'Enter') {
            var q = e.target.value.trim();
            if (q) {
              window.location.href = '/shop?search=' + encodeURIComponent(q);
            }
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
    },

    handleInputChange: function (value) {
      var self = this;
      var q = value.trim();
      var clearBtn = document.getElementById('stephans-search-clear');
      var initialSec = document.getElementById('stephans-search-initial');
      var resultsSec = document.getElementById('stephans-search-results-area');
      var loadingEl = document.getElementById('stephans-search-loading');
      var listEl = document.getElementById('stephans-search-results-list');
      var noResultsEl = document.getElementById('stephans-search-no-results');

      if (clearBtn) {
        clearBtn.style.display = q.length > 0 ? 'flex' : 'none';
      }

      if (q.length < 2) {
        if (initialSec) initialSec.style.display = 'block';
        if (resultsSec) resultsSec.style.display = 'none';
        if (listEl) listEl.innerHTML = '';
        if (noResultsEl) noResultsEl.style.display = 'none';
        return;
      }

      // Query >= 2 chars: Show results container and loading spinner
      if (initialSec) initialSec.style.display = 'none';
      if (resultsSec) resultsSec.style.display = 'block';
      if (loadingEl) loadingEl.style.display = 'flex';
      if (noResultsEl) noResultsEl.style.display = 'none';

      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(function () {
        self.performSearch(q);
      }, 250);
    },

    performSearch: function (query) {
      var loadingEl = document.getElementById('stephans-search-loading');
      var listEl = document.getElementById('stephans-search-results-list');
      var noResultsEl = document.getElementById('stephans-search-no-results');

      fetch('/stephans/api/search?q=' + encodeURIComponent(query), {
        headers: { 'Accept': 'application/json' }
      })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          if (loadingEl) loadingEl.style.display = 'none';
          var results = data.results || [];

          if (results.length === 0) {
            if (noResultsEl) noResultsEl.style.display = 'block';
            if (listEl) listEl.innerHTML = '';
          } else {
            if (noResultsEl) noResultsEl.style.display = 'none';
            if (listEl) {
              listEl.innerHTML = results.map(function (item) {
                return (
                  '<a href="/shop/product/' + item.id + '" class="stephans-search-result-item">' +
                    '<div class="stephans-search-result-thumb">' +
                      '<img src="' + item.image_url + '" alt="' + item.name + '" loading="lazy"/>' +
                    '</div>' +
                    '<div class="stephans-search-result-meta">' +
                      '<h4 class="stephans-search-result-title">' + item.name + '</h4>' +
                      '<span class="stephans-search-result-cat">' + (item.category || 'General') + '</span>' +
                    '</div>' +
                    '<div class="stephans-search-result-price">' + item.price_formatted + '</div>' +
                  '</a>'
                );
              }).join('');
            }
          }
        })
        .catch(function (err) {
          if (loadingEl) loadingEl.style.display = 'none';
          console.error('Stephan\'s search error:', err);
        });
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
