/**
 * Auth Status Module - Separate from analysis logic
 * This module handles checking if the user is logged in to Ragard
 */

// API base URL will be loaded from config.js
async function getApiBase() {
  if (typeof window !== 'undefined' && window.ragardConfig) {
    return await window.ragardConfig.getApiBaseUrl();
  }
  if (typeof self !== 'undefined' && self.ragardConfig) {
    return await self.ragardConfig.getApiBaseUrl();
  }
  return 'http://localhost:8000'; // Default fallback
}

let lastAuthStatus = null;
let lastAuthCheckAt = null;
const AUTH_CACHE_MS = 2 * 60 * 1000; // 2 minutes

/**
 * Get the current authentication status from the backend
 * @param {boolean} force - If true, bypass cache and always check fresh
 * @returns {Promise<{isAuthenticated: boolean, userId?: string | null, username?: string | null}>}
 */
async function getAuthStatus(force = false) {
  const now = Date.now();
  
  // Return cached result if still valid and not forcing refresh
  if (!force && lastAuthStatus && lastAuthCheckAt && (now - lastAuthCheckAt) < AUTH_CACHE_MS) {
    console.log('[RAGARD] Using cached auth status');
    return lastAuthStatus;
  }
  
  console.log('[RAGARD] Checking auth status (force:', force, ')');
  
  try {
    // Try to get auth token from multiple sources
    let authToken = null;
    
    // ALWAYS try to get fresh token from main app's localStorage first (most reliable)
    // This ensures we get the latest token even if extension storage has stale data
    try {
      // Get web app URL from config
      const webAppUrl = await (typeof window !== 'undefined' && window.ragardConfig 
        ? window.ragardConfig.getWebAppBaseUrl() 
        : typeof self !== 'undefined' && self.ragardConfig
        ? self.ragardConfig.getWebAppBaseUrl()
        : Promise.resolve('http://localhost:3000'));
      
      // Find the Ragard app tab
      const urlPattern = webAppUrl.replace(/\/$/, '') + '/*';
      const tabs = await new Promise((resolve) => {
        chrome.tabs.query({ url: [urlPattern, 'http://127.0.0.1:3000/*', 'http://127.0.0.1:3001/*'] }, resolve);
      });
      
      // Filter to find Ragard app tabs
      const ragardTabs = tabs.filter(tab => {
        const url = tab.url || '';
        const webAppHost = new URL(webAppUrl).hostname;
        return url.includes(webAppHost) || url.includes('127.0.0.1:3000') || url.includes('127.0.0.1:3001');
      });
      
      if (ragardTabs && ragardTabs.length > 0) {
        console.log('[RAGARD] Found', ragardTabs.length, 'Ragard app tab(s), attempting to read token');
        // Try each tab until we find a token
        for (const tab of ragardTabs) {
          try {
            // Inject script to read token from main app's localStorage
            const results = await chrome.scripting.executeScript({
              target: { tabId: tab.id },
              func: () => {
                // Read token from main app's localStorage
                return localStorage.getItem('ragardToken');
              }
            });
            
            if (results && results[0] && results[0].result) {
              authToken = results[0].result;
              console.log('[RAGARD] Token from main app localStorage (tab', tab.id, '): Found (length:', authToken.length, ')');
              
              // Cache it in extension storage for future use
              if (authToken) {
                chrome.storage.local.set({ ragardToken: authToken });
                console.log('[RAGARD] Cached token in extension storage');
              }
              break; // Found token, stop looking
            }
          } catch (injectErr) {
            console.warn('[RAGARD] Could not inject script into tab', tab.id, ':', injectErr);
            // Continue to next tab
          }
        }
        
        if (!authToken) {
          console.log('[RAGARD] No token found in any Ragard app tab');
        }
      } else {
        console.log(`[RAGARD] No Ragard app tabs found (looking for ${webAppUrl})`);
      }
    } catch (e) {
      console.warn('[RAGARD] Error trying to read from main app localStorage:', e);
    }
    
    // Fallback: try chrome.storage.local (extension storage) if main app didn't have token
    if (!authToken) {
      try {
        const storageResult = await new Promise((resolve) => {
          chrome.storage.local.get(['ragard_auth_token', 'ragardToken'], resolve);
        });
        authToken = storageResult?.ragard_auth_token || storageResult?.ragardToken;
        console.log('[RAGARD] Token from chrome.storage.local (fallback):', authToken ? 'Found' : 'Not found');
      } catch (e) {
        console.warn('[RAGARD] Could not read from chrome.storage:', e);
      }
    }
    
    console.log('[RAGARD] Final auth token:', authToken ? 'Yes (length: ' + authToken.length + ')' : 'No');
    
    const headers = {
      'Accept': 'application/json'
    };
    
    // If we have a token, use Bearer auth; otherwise try cookies
    if (authToken) {
      headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    const apiBase = await getApiBase();
    const res = await fetch(`${apiBase}/api/auth/status`, {
      method: 'GET',
      headers: headers,
      mode: 'cors',
      credentials: 'include' // Include cookies as fallback
    });
    
    console.log('[RAGARD] Auth status response status:', res.status, res.statusText);
    
    if (!res.ok) {
      console.log('[RAGARD] Auth status request failed:', res.status);
      // If 401, token is expired/invalid - clear it from storage
      if (res.status === 401 && authToken) {
        console.log('[RAGARD] Token expired/invalid, clearing from storage');
        try {
          chrome.storage.local.remove(['ragard_auth_token', 'ragardToken']);
        } catch (e) {
          // Silently fail
        }
      }
      lastAuthStatus = { isAuthenticated: false };
      lastAuthCheckAt = now;
      return lastAuthStatus;
    }
    
    const data = await res.json();
    console.log('[RAGARD] Auth status response data:', JSON.stringify(data, null, 2));
    console.log('[RAGARD] data.isAuthenticated value:', data.isAuthenticated, 'type:', typeof data.isAuthenticated);
    lastAuthStatus = {
      isAuthenticated: !!data.isAuthenticated,
      userId: data.userId ?? null,
      username: data.username ?? null
    };
    lastAuthCheckAt = now;
    console.log('[RAGARD] Cached auth status:', JSON.stringify(lastAuthStatus, null, 2));
    console.log('[RAGARD] Final isAuthenticated:', lastAuthStatus.isAuthenticated, 'userId:', lastAuthStatus.userId, 'username:', lastAuthStatus.username);
    return lastAuthStatus;
  } catch (err) {
    console.error('[RAGARD] Auth status error:', err);
    lastAuthStatus = { isAuthenticated: false };
    lastAuthCheckAt = now;
    return lastAuthStatus;
  }
}

// Clear cache function
function clearCache() {
  lastAuthStatus = null;
  lastAuthCheckAt = null;
  console.log('[RAGARD] Auth cache cleared');
}

// Export for use in sidePanel.js
if (typeof window !== 'undefined') {
  window.ragardAuthStatus = { getAuthStatus, clearCache };
}

