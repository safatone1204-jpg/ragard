/**
 * Ragard Extension Configuration
 * Loads API and web app URLs from chrome.storage with sensible defaults
 */

const DEFAULT_API_BASE_URL = 'http://localhost:8000';
const DEFAULT_WEB_APP_BASE_URL = 'http://localhost:3000';

/**
 * Get API base URL from storage or return default
 * @returns {Promise<string>}
 */
async function getApiBaseUrl() {
  return new Promise((resolve) => {
    // Try sync storage first (for cross-device sync), fallback to local
    chrome.storage.sync.get(['ragard_api_base_url'], (syncResult) => {
      if (syncResult.ragard_api_base_url) {
        resolve(syncResult.ragard_api_base_url);
      } else {
        chrome.storage.local.get(['ragard_api_base_url'], (localResult) => {
          const url = localResult.ragard_api_base_url || DEFAULT_API_BASE_URL;
          resolve(url);
        });
      }
    });
  });
}

/**
 * Get web app base URL from storage or return default
 * @returns {Promise<string>}
 */
async function getWebAppBaseUrl() {
  return new Promise((resolve) => {
    // Try sync storage first (for cross-device sync), fallback to local
    chrome.storage.sync.get(['ragard_web_app_base_url'], (syncResult) => {
      if (syncResult.ragard_web_app_base_url) {
        resolve(syncResult.ragard_web_app_base_url);
      } else {
        chrome.storage.local.get(['ragard_web_app_base_url'], (localResult) => {
          const url = localResult.ragard_web_app_base_url || DEFAULT_WEB_APP_BASE_URL;
          resolve(url);
        });
      }
    });
  });
}

/**
 * Set API base URL in storage
 * @param {string} url
 * @returns {Promise<void>}
 */
async function setApiBaseUrl(url) {
  return new Promise((resolve) => {
    // Save to both sync (for cross-device) and local (for fallback)
    chrome.storage.sync.set({ ragard_api_base_url: url }, () => {
      chrome.storage.local.set({ ragard_api_base_url: url }, () => {
        resolve();
      });
    });
  });
}

/**
 * Set web app base URL in storage
 * @param {string} url
 * @returns {Promise<void>}
 */
async function setWebAppBaseUrl(url) {
  return new Promise((resolve) => {
    // Save to both sync (for cross-device) and local (for fallback)
    chrome.storage.sync.set({ ragard_web_app_base_url: url }, () => {
      chrome.storage.local.set({ ragard_web_app_base_url: url }, () => {
        resolve();
      });
    });
  });
}

// Export for use in other extension files
if (typeof window !== 'undefined') {
  window.ragardConfig = {
    getApiBaseUrl,
    getWebAppBaseUrl,
    setApiBaseUrl,
    setWebAppBaseUrl,
    DEFAULT_API_BASE_URL,
    DEFAULT_WEB_APP_BASE_URL
  };
}

// For service worker context (background.js)
if (typeof self !== 'undefined' && typeof importScripts !== 'undefined') {
  self.ragardConfig = {
    getApiBaseUrl,
    getWebAppBaseUrl,
    setApiBaseUrl,
    setWebAppBaseUrl,
    DEFAULT_API_BASE_URL,
    DEFAULT_WEB_APP_BASE_URL
  };
}

