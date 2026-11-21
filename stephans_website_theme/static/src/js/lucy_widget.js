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

    generateBotResponse: function (query) {
      var self = this;
      var q = query.toLowerCase();

      // Show typing simulation briefly
      setTimeout(function () {
        var reply = '';

        if (q.indexOf('groom') !== -1 || q.indexOf('appointment') !== -1 || q.indexOf('cut') !== -1 || q.indexOf('bath') !== -1) {
          reply = '<p>🐾 We offer professional pet grooming at both our <strong>Masaki</strong> and <strong>Mikocheni</strong> salons!</p>' +
                  '<p>Services include full baths, hair trims, nail clipping, and flea dips. You can book directly using our <a href="/grooming" style="color:#d35122;font-weight:700;">Grooming Booking Tool →</a> or call us at <a href="tel:+255769324445" style="color:#d35122;font-weight:700;">+255 769 324 445</a>.</p>';
        } else if (q.indexOf('food') !== -1 || q.indexOf('dog') !== -1 || q.indexOf('cat') !== -1 || q.indexOf('eat') !== -1) {
          reply = '<p>🍖 We stock premium vet-approved nutrition including <strong>TropiDog</strong>, <strong>Ownat</strong>, and <strong>Josera</strong> for all life stages (Puppy, Adult, Senior, and sensitive stomachs).</p>' +
                  '<p>👉 Explore our <a href="/brands/tropidog" style="color:#d35122;font-weight:700;">TropiDog Range</a> or browse all <a href="/shop" style="color:#d35122;font-weight:700;">Pet Foods in our Shop</a>.</p>';
        } else if (q.indexOf('store') !== -1 || q.indexOf('locat') !== -1 || q.indexOf('where') !== -1 || q.indexOf('masaki') !== -1 || q.indexOf('mikocheni') !== -1) {
          reply = '<p>📍 We have two prime locations in Dar es Salaam:</p>' +
                  '<p>1. <strong>Masaki:</strong> 11 Slipway Road (Mon–Sat 9AM–8:30PM)<br/>' +
                  '2. <strong>Mikocheni:</strong> 59 Mikocheni A (Mon–Sat 9AM–8:30PM)</p>' +
                  '<p><a href="/stores" style="color:#d35122;font-weight:700;">View Store Map &amp; Directions →</a></p>';
        } else if (q.indexOf('deliver') !== -1 || q.indexOf('ship') !== -1 || q.indexOf('dar') !== -1 || q.indexOf('cost') !== -1) {
          reply = '<p>🚚 <strong>Express Delivery across Dar es Salaam &amp; Tanzania!</strong></p>' +
                  '<p>Orders over <strong>TZS 100,000</strong> qualify for <strong>FREE Delivery</strong> within Dar es Salaam. Orders are dispatched the same day for maximum convenience.</p>';
        } else if (q.indexOf('flea') !== -1 || q.indexOf('tick') !== -1 || q.indexOf('bravecto') !== -1 || q.indexOf('nexgard') !== -1) {
          reply = '<p>🛡️ For flea &amp; tick prevention, we carry genuine <strong>Bravecto</strong> (chews offering 3 months protection) and <strong>Bioline</strong> sprays/spot-ons.</p>' +
                  '<p>👉 Check <a href="/brands/bravecto" style="color:#d35122;font-weight:700;">Bravecto products</a> or speak to our team to get the exact dosage for your pet\'s weight.</p>';
        } else {
          reply = '<p>Thanks for asking! We have hundreds of genuine pet essentials in stock.</p>' +
                  '<p>You can search our catalog above, or click below to chat with a pet care specialist on WhatsApp for personalized recommendations:</p>' +
                  '<p><a href="https://wa.me/255769324445?text=' + encodeURIComponent('Hi Sky, I have a question about: ' + query) + '" target="_blank" style="display:inline-block;background:#25d366;color:#fff;padding:6px 12px;border-radius:6px;font-weight:700;text-decoration:none;">Chat on WhatsApp →</a></p>';
        }

        self.appendMessage('bot', reply);
      }, 400);
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
