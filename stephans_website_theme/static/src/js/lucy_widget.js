/**
 * Stephan's Lucy AI Assistant Controller
 * Provides interactive instant pet care guidance, service booking navigation,
 * and direct WhatsApp concierge handoff.
 */
(function () {
  'use strict';

  var LucyWidget = {
    isOpen: false,

    init: function () {
      this.bindEvents();
    },

    bindEvents: function () {
      var self = this;

      // Toggle panel via FAB
      document.addEventListener('click', function (e) {
        if (e.target.closest('#stephans-lucy-fab')) {
          e.preventDefault();
          self.toggle();
        }

        // Close button
        if (e.target.closest('#stephans-lucy-close')) {
          e.preventDefault();
          self.close();
        }

        // Suggestion chip click
        var chip = e.target.closest('.stephans-lucy-chip');
        if (chip) {
          e.preventDefault();
          var prompt = chip.getAttribute('data-prompt');
          self.handleUserMessage(prompt);
        }
      });

      // Submit user custom question
      var form = document.getElementById('stephans-lucy-form');
      if (form) {
        form.addEventListener('submit', function (e) {
          e.preventDefault();
          var input = document.getElementById('stephans-lucy-input');
          if (input && input.value.trim()) {
            var msg = input.value.trim();
            input.value = '';
            self.handleUserMessage(msg);
          }
        });
      }
    },

    toggle: function () {
      if (this.isOpen) {
        this.close();
      } else {
        this.open();
      }
    },

    open: function () {
      this.isOpen = true;
      var panel = document.getElementById('stephans-lucy-panel');
      if (panel) panel.classList.add('is-open');
      this.scrollToBottom();
    },

    close: function () {
      this.isOpen = false;
      var panel = document.getElementById('stephans-lucy-panel');
      if (panel) panel.classList.remove('is-open');
    },

    handleUserMessage: function (text) {
      this.appendMessage('user', text);
      this.generateBotResponse(text);
    },

    appendMessage: function (role, content) {
      var messagesContainer = document.getElementById('stephans-lucy-messages');
      if (!messagesContainer) return;

      var bubble = document.createElement('div');
      bubble.className = 'stephans-lucy-bubble stephans-lucy-bubble--' + role;

      var contentEl = document.createElement('div');
      contentEl.className = 'stephans-lucy-bubble__content';
      contentEl.innerHTML = typeof content === 'string' ? '<p>' + content + '</p>' : content;

      bubble.appendChild(contentEl);
      messagesContainer.appendChild(bubble);
      this.scrollToBottom();
    },

    showTyping: function () {
      var messagesContainer = document.getElementById('stephans-lucy-messages');
      if (!messagesContainer) return;

      var typingEl = document.getElementById('stephans-lucy-typing');
      if (typingEl) typingEl.remove();

      typingEl = document.createElement('div');
      typingEl.id = 'stephans-lucy-typing';
      typingEl.className = 'stephans-lucy-bubble stephans-lucy-bubble--bot stephans-lucy-bubble--typing';
      typingEl.innerHTML = '<div class="stephans-lucy-bubble__content"><span class="stephans-lucy-dot"></span><span class="stephans-lucy-dot"></span><span class="stephans-lucy-dot"></span></div>';

      messagesContainer.appendChild(typingEl);
      this.scrollToBottom();
    },

    hideTyping: function () {
      var typingEl = document.getElementById('stephans-lucy-typing');
      if (typingEl) {
        typingEl.remove();
      }
    },

    generateBotResponse: function (query) {
      var self = this;
      self.showTyping();

      // Check if backend ChatGPT endpoint is available
      var useBackend = false; // Graceful fallback
      if (window.fetch && useBackend) {
        fetch('/sky/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: query })
        })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          self.hideTyping();
          if (data && data.reply) {
            self.appendMessage('bot', data.reply);
          } else {
            self.handleLocalResponse(query);
          }
        })
        .catch(function () {
          self.hideTyping();
          self.handleLocalResponse(query);
        });
      } else {
        setTimeout(function () {
          self.hideTyping();
          self.handleLocalResponse(query);
        }, 450);
      }
    },

    handleLocalResponse: function (query) {
      var q = query.toLowerCase();
      var reply = '';

      if (q.indexOf('groom') !== -1 || q.indexOf('appointment') !== -1 || q.indexOf('cut') !== -1 || q.indexOf('bath') !== -1) {
        reply = '<p>We offer professional pet grooming at both our <strong>Masaki</strong> and <strong>Mikocheni</strong> salons.</p>' +
                '<p>Services include full baths, hair trims, nail clipping, and coat treatments. You can book directly using our <a href="/grooming" style="color:#d35122;font-weight:600;">Grooming Booking Tool</a> or call us at <a href="tel:+255769324445" style="color:#d35122;font-weight:600;">+255 769 324 445</a>.</p>';
      } else if (q.indexOf('food') !== -1 || q.indexOf('dog') !== -1 || q.indexOf('cat') !== -1 || q.indexOf('eat') !== -1) {
        reply = '<p>We stock premium veterinary-approved nutrition including <strong>TropiDog</strong>, <strong>Ownat</strong>, and <strong>Josera</strong> for all life stages, breeds, and dietary sensitivities.</p>' +
                '<p>Explore our <a href="/brands/tropidog" style="color:#d35122;font-weight:600;">TropiDog Range</a> or browse all <a href="/shop" style="color:#d35122;font-weight:600;">Pet Foods in our Shop</a>.</p>';
      } else if (q.indexOf('store') !== -1 || q.indexOf('locat') !== -1 || q.indexOf('where') !== -1 || q.indexOf('masaki') !== -1 || q.indexOf('mikocheni') !== -1) {
        reply = '<p>We have two prime locations in Dar es Salaam:</p>' +
                '<p>1. <strong>Masaki:</strong> 11 Slipway Road (Monday–Saturday, 9:00 AM – 8:30 PM)<br/>' +
                '2. <strong>Mikocheni:</strong> 59 Mikocheni A (Monday–Saturday, 9:00 AM – 8:30 PM)</p>' +
                '<p><a href="/stores" style="color:#d35122;font-weight:600;">View Store Map &amp; Directions</a></p>';
      } else if (q.indexOf('deliver') !== -1 || q.indexOf('ship') !== -1 || q.indexOf('dar') !== -1 || q.indexOf('cost') !== -1) {
        reply = '<p><strong>Express Delivery across Dar es Salaam &amp; Tanzania</strong></p>' +
                '<p>Orders over <strong>TZS 100,000</strong> qualify for <strong>Free Delivery</strong> within Dar es Salaam. Same-day dispatch is available for orders placed before 3:00 PM.</p>';
      } else if (q.indexOf('flea') !== -1 || q.indexOf('tick') !== -1 || q.indexOf('bravecto') !== -1 || q.indexOf('nexgard') !== -1) {
        reply = '<p>For flea and tick prevention, we carry genuine <strong>Bravecto</strong> (chews offering 3 months of protection) and <strong>Bioline</strong> topical treatments.</p>' +
                '<p>View <a href="/brands/bravecto" style="color:#d35122;font-weight:600;">Bravecto products</a> or speak to our team for weight-specific dosages.</p>';
      } else {
        reply = '<p>We have a wide range of genuine pet essentials in stock.</p>' +
                '<p>You can search our catalog or connect directly with our pet care specialists on WhatsApp for personalized recommendations:</p>' +
                '<p><a href="https://wa.me/255769324445?text=' + encodeURIComponent('Hi Sky, I have a question about: ' + query) + '" target="_blank" style="display:inline-flex;align-items:center;background:#25d366;color:#fff;padding:6px 14px;border-radius:6px;font-size:12px;font-weight:600;text-decoration:none;">Chat on WhatsApp</a></p>';
      }

      this.appendMessage('bot', reply);
    },

    scrollToBottom: function () {
      var messagesContainer = document.getElementById('stephans-lucy-messages');
      if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      }
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      LucyWidget.init();
    });
  } else {
    LucyWidget.init();
  }

  window.StephansLucyWidget = LucyWidget;
})();
