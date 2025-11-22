/**
 * Attribution Tracking Pixel
 * 
 * This script tracks attribution events (impressions, clicks, conversions) 
 * for podcast sponsorship campaigns. It can be embedded on sponsor websites
 * to track when users interact with campaign links or use promo codes.
 * 
 * Usage:
 * <script src="https://your-domain.com/attribution.js"></script>
 * <script>
 *   AttributionTracker.init({
 *     apiUrl: 'https://api.your-domain.com/api/v1',
 *     campaignId: 'campaign-uuid',
 *     promoCode: 'PROMO2024' // optional
 *   });
 * </script>
 */

(function(window) {
  'use strict';

  const AttributionTracker = {
    config: {
      apiUrl: null,
      campaignId: null,
      promoCode: null,
      debug: false
    },

    /**
     * Initialize the attribution tracker
     */
    init: function(options) {
      if (!options || !options.apiUrl || !options.campaignId) {
        console.error('AttributionTracker: apiUrl and campaignId are required');
        return;
      }

      this.config.apiUrl = options.apiUrl;
      this.config.campaignId = options.campaignId;
      this.config.promoCode = options.promoCode || null;
      this.config.debug = options.debug || false;

      this.log('AttributionTracker initialized', this.config);

      // Track page impression
      this.trackImpression();

      // Track clicks on links with promo codes or campaign UTM parameters
      this.trackClicks();

      // Track conversions (form submissions, purchases, etc.)
      this.trackConversions();
    },

    /**
     * Track page impression
     */
    trackImpression: function() {
      const event = {
        event_type: 'impression',
        campaign_id: this.config.campaignId,
        promo_code: this.config.promoCode || this.getPromoCodeFromURL(),
        timestamp: new Date().toISOString(),
        page_url: window.location.href,
        referrer: document.referrer,
        user_agent: navigator.userAgent,
        utm_source: this.getURLParameter('utm_source'),
        utm_medium: this.getURLParameter('utm_medium'),
        utm_campaign: this.getURLParameter('utm_campaign'),
        utm_content: this.getURLParameter('utm_content'),
        utm_term: this.getURLParameter('utm_term')
      };

      this.sendEvent(event);
    },

    /**
     * Track clicks on campaign links
     */
    trackClicks: function() {
      const self = this;
      
      // Track clicks on links with promo codes
      document.addEventListener('click', function(e) {
        const link = e.target.closest('a');
        if (!link) return;

        const href = link.href;
        const promoCode = self.getPromoCodeFromURL(href) || self.config.promoCode;
        const hasCampaignUTM = self.hasCampaignUTM(href);

        if (promoCode || hasCampaignUTM) {
          const event = {
            event_type: 'click',
            campaign_id: self.config.campaignId,
            promo_code: promoCode,
            timestamp: new Date().toISOString(),
            link_url: href,
            link_text: link.textContent.trim(),
            page_url: window.location.href,
            utm_source: self.getURLParameter('utm_source', href),
            utm_medium: self.getURLParameter('utm_medium', href),
            utm_campaign: self.getURLParameter('utm_campaign', href)
          };

          self.sendEvent(event);
        }
      }, true);
    },

    /**
     * Track conversions (form submissions, purchases, etc.)
     */
    trackConversions: function() {
      const self = this;

      // Track form submissions
      document.addEventListener('submit', function(e) {
        const form = e.target;
        const promoCode = self.getPromoCodeFromForm(form) || self.config.promoCode;
        
        if (promoCode) {
          const event = {
            event_type: 'conversion',
            campaign_id: self.config.campaignId,
            promo_code: promoCode,
            conversion_type: 'form_submission',
            timestamp: new Date().toISOString(),
            form_action: form.action,
            page_url: window.location.href
          };

          self.sendEvent(event);
        }
      }, true);

      // Track custom conversion events
      window.addEventListener('attribution:conversion', function(e) {
        const detail = e.detail || {};
        const event = {
          event_type: 'conversion',
          campaign_id: self.config.campaignId,
          promo_code: detail.promo_code || self.config.promoCode,
          conversion_type: detail.conversion_type || 'custom',
          conversion_value: detail.conversion_value || null,
          timestamp: new Date().toISOString(),
          page_url: window.location.href,
          metadata: detail.metadata || {}
        };

        self.sendEvent(event);
      });
    },

    /**
     * Send attribution event to API
     */
    sendEvent: function(event) {
      const self = this;
      
      // Use sendBeacon for better reliability
      if (navigator.sendBeacon) {
        const data = JSON.stringify(event);
        const blob = new Blob([data], { type: 'application/json' });
        const url = this.config.apiUrl + '/attribution/events';
        
        if (navigator.sendBeacon(url, blob)) {
          this.log('Event sent via sendBeacon', event);
        } else {
          // Fallback to fetch
          this.sendEventViaFetch(event);
        }
      } else {
        // Fallback to fetch
        this.sendEventViaFetch(event);
      }
    },

    /**
     * Send event via fetch (fallback)
     */
    sendEventViaFetch: function(event) {
      const self = this;
      const url = this.config.apiUrl + '/attribution/events';
      
      fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(event),
        keepalive: true
      })
      .then(function(response) {
        if (response.ok) {
          self.log('Event sent successfully', event);
        } else {
          self.log('Failed to send event', { event, status: response.status });
        }
      })
      .catch(function(error) {
        self.log('Error sending event', { event, error: error.message });
      });
    },

    /**
     * Get promo code from URL
     */
    getPromoCodeFromURL: function(url) {
      url = url || window.location.href;
      const match = url.match(/[?&](?:promo|promocode|code|discount)=([^&]+)/i);
      return match ? decodeURIComponent(match[1]) : null;
    },

    /**
     * Get promo code from form
     */
    getPromoCodeFromForm: function(form) {
      const promoInputs = form.querySelectorAll('input[name*="promo"], input[name*="code"], input[name*="discount"]');
      for (let i = 0; i < promoInputs.length; i++) {
        const value = promoInputs[i].value.trim();
        if (value) return value;
      }
      return null;
    },

    /**
     * Check if URL has campaign UTM parameters
     */
    hasCampaignUTM: function(url) {
      url = url || window.location.href;
      return /[?&]utm_campaign=/.test(url);
    },

    /**
     * Get URL parameter value
     */
    getURLParameter: function(name, url) {
      url = url || window.location.href;
      name = name.replace(/[\[\]]/g, '\\$&');
      const regex = new RegExp('[?&]' + name + '(=([^&#]*)|&|#|$)');
      const results = regex.exec(url);
      if (!results) return null;
      if (!results[2]) return '';
      return decodeURIComponent(results[2].replace(/\+/g, ' '));
    },

    /**
     * Log debug messages
     */
    log: function(message, data) {
      if (this.config.debug) {
        console.log('[AttributionTracker]', message, data || '');
      }
    },

    /**
     * Track custom conversion
     * Usage: AttributionTracker.trackConversion({ conversion_type: 'purchase', conversion_value: 99.99 })
     */
    trackConversion: function(options) {
      const event = new CustomEvent('attribution:conversion', {
        detail: options || {}
      });
      window.dispatchEvent(event);
    }
  };

  // Export to window
  window.AttributionTracker = AttributionTracker;

  // Auto-initialize if config is provided via data attributes
  if (document.currentScript) {
    const script = document.currentScript;
    const apiUrl = script.getAttribute('data-api-url');
    const campaignId = script.getAttribute('data-campaign-id');
    const promoCode = script.getAttribute('data-promo-code');
    const debug = script.getAttribute('data-debug') === 'true';

    if (apiUrl && campaignId) {
      AttributionTracker.init({
        apiUrl: apiUrl,
        campaignId: campaignId,
        promoCode: promoCode,
        debug: debug
      });
    }
  }

})(window);
