/**
 * Ragard Extension Configuration
 * Loads API and web app URLs from chrome.storage with sensible defaults
 * Auto-detects environment (production vs local) based on current tab
 */

// Production URLs (default)
const PROD_API_BASE_URL = 'https://api.ragardai.com';
const PROD_WEB_APP_BASE_URL = 'https://ragardai.com';

// Local development URLs
const LOCAL_API_BASE_URL = 'http://localhost:8000';
const LOCAL_WEB_APP_BASE_URL = 'http://localhost:3000';

// Default to production
const DEFAULT_API_BASE_URL = PROD_API_BASE_URL;
const DEFAULT_WEB_APP_BASE_URL = PROD_WEB_APP_BASE_URL;

/**
 * Detect if a URL is production or local environment
 * @param {string} url - URL to check
 * @returns {{isProduction: boolean, isLocal: boolean}}
 */
function detectEnvironmentFromUrl(url) {
  if (!url) return { isProduction: true, isLocal: false };
  
  const isProduction = url.includes('ragardai.com') || url.includes('www.ragardai.com');
  const isLocal = url.includes('localhost') || url.includes('127.0.0.1') || url.includes('0.0.0.0');
  
  return { isProduction, isLocal };
}

/**
 * Detect if current tab is on production or local environment
 * @returns {Promise<{isProduction: boolean, isLocal: boolean}>}
 */
async function detectEnvironment() {
  return new Promise((resolve) => {
    // Try to get current tab
    if (typeof chrome !== 'undefined' && chrome.tabs && chrome.tabs.query) {
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs.length > 0 && tabs[0].url) {
          resolve(detectEnvironmentFromUrl(tabs[0].url));
        } else {
          // No active tab, default to production
          resolve({ isProduction: true, isLocal: false });
        }
      });
    } else {
      // Can't query tabs (e.g., in some contexts), default to production
      resolve({ isProduction: true, isLocal: false });
    }
  });
}

/**
 * Get API base URL from storage or auto-detect based on environment
 * @returns {Promise<string>}
 */
async function getApiBaseUrl() {
  return new Promise(async (resolve) => {
    // First check if user has manually set a URL (auto-detect disabled)
    chrome.storage.sync.get(['ragard_api_base_url', 'ragard_auto_detect'], (syncResult) => {
      // If auto-detect is explicitly disabled and URL is set, use stored value
      if (syncResult.ragard_auto_detect === false && syncResult.ragard_api_base_url) {
        resolve(syncResult.ragard_api_base_url);
        return;
      }
      
      // Auto-detect is enabled by default, try to detect environment
      detectEnvironment().then(({ isProduction, isLocal }) => {
        if (isProduction) {
          resolve(PROD_API_BASE_URL);
        } else if (isLocal) {
          resolve(LOCAL_API_BASE_URL);
        } else {
          // Can't determine, use stored value or default to production
          const url = syncResult.ragard_api_base_url || DEFAULT_API_BASE_URL;
          resolve(url);
        }
      }).catch(() => {
        // Error detecting, fall back to stored or default
        const url = syncResult.ragard_api_base_url || DEFAULT_API_BASE_URL;
        resolve(url);
      });
    });
  });
}

/**
 * Get web app base URL from storage or auto-detect based on environment
 * @returns {Promise<string>}
 */
async function getWebAppBaseUrl() {
  return new Promise(async (resolve) => {
    // First check if user has manually set a URL (auto-detect disabled)
    chrome.storage.sync.get(['ragard_web_app_base_url', 'ragard_auto_detect'], (syncResult) => {
      // If auto-detect is explicitly disabled and URL is set, use stored value
      if (syncResult.ragard_auto_detect === false && syncResult.ragard_web_app_base_url) {
        resolve(syncResult.ragard_web_app_base_url);
        return;
      }
      
      // Auto-detect is enabled by default, try to detect environment
      detectEnvironment().then(({ isProduction, isLocal }) => {
        if (isProduction) {
          resolve(PROD_WEB_APP_BASE_URL);
        } else if (isLocal) {
          resolve(LOCAL_WEB_APP_BASE_URL);
        } else {
          // Can't determine, use stored value or default to production
          const url = syncResult.ragard_web_app_base_url || DEFAULT_WEB_APP_BASE_URL;
          resolve(url);
        }
      }).catch(() => {
        // Error detecting, fall back to stored or default
        const url = syncResult.ragard_web_app_base_url || DEFAULT_WEB_APP_BASE_URL;
        resolve(url);
      });
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
    detectEnvironment,
    detectEnvironmentFromUrl,
    DEFAULT_API_BASE_URL,
    DEFAULT_WEB_APP_BASE_URL,
    PROD_API_BASE_URL,
    PROD_WEB_APP_BASE_URL,
    LOCAL_API_BASE_URL,
    LOCAL_WEB_APP_BASE_URL
  };
}

// For service worker context (background.js)
if (typeof self !== 'undefined' && typeof importScripts !== 'undefined') {
  self.ragardConfig = {
    getApiBaseUrl,
    getWebAppBaseUrl,
    setApiBaseUrl,
    setWebAppBaseUrl,
    detectEnvironment,
    detectEnvironmentFromUrl,
    DEFAULT_API_BASE_URL,
    DEFAULT_WEB_APP_BASE_URL,
    PROD_API_BASE_URL,
    PROD_WEB_APP_BASE_URL,
    LOCAL_API_BASE_URL,
    LOCAL_WEB_APP_BASE_URL
  };
}

