// Background script for Ragard extension
// Handles tab management, side panel opening, and messaging

// Configure side panel behavior
async function configureSidePanel() {
  try {
    // Set panel behavior to open on action click
    await chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
    console.log('[Ragard] Side panel configured to open on icon click');
  } catch (err) {
    console.error('[Ragard] Error configuring side panel behavior:', err);
    // Fallback: try setting options
    try {
      await chrome.sidePanel.setOptions({
        path: 'sidePanel.html',
        enabled: true
      });
      console.log('[Ragard] Side panel options set as fallback');
    } catch (optionsErr) {
      console.error('[Ragard] Error setting side panel options:', optionsErr);
    }
  }
}

// Configure on install
chrome.runtime.onInstalled.addListener(() => {
  configureSidePanel();
});

// Configure on startup
chrome.runtime.onStartup.addListener(() => {
  configureSidePanel();
});

// Also configure immediately when background script loads
configureSidePanel();

// Fallback: Manual open if auto-open doesn't work
chrome.action.onClicked.addListener(async (tab) => {
  try {
    console.log('[Ragard] Extension icon clicked, attempting to open side panel');
    await chrome.sidePanel.open({ windowId: tab.windowId });
    console.log('[Ragard] Side panel opened successfully');
  } catch (err) {
    console.error('[Ragard] Error opening side panel manually:', err);
    // Try to configure and open again
    try {
      await configureSidePanel();
      await chrome.sidePanel.open({ windowId: tab.windowId });
    } catch (retryErr) {
      console.error('[Ragard] Retry also failed:', retryErr);
    }
  }
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // When user is logged in on Ragard website, content script sends token so sidebar uses same account
  if (message.type === 'RAGARD_SYNC_TOKEN' && message.token) {
    chrome.storage.local.set({ ragardToken: message.token }, () => {
      if (chrome.runtime.lastError) {
        console.warn('[Ragard] Failed to store synced token:', chrome.runtime.lastError);
      }
    });
    sendResponse({ ok: true });
    return false;
  }

  if (message.type === 'FIND_RAGARD_TAB') {
    // Find existing Ragard tab with matching URL pattern
    const urlPattern = message.url;
    chrome.tabs.query({}, (tabs) => {
      const ragardTabs = tabs.filter(tab => {
        if (!tab.url) return false;
        // Check if tab URL matches Ragard web app (production or local)
        return tab.url.includes('ragardai.com/stocks/') || 
               tab.url.includes('localhost:3000/stocks/') ||
               tab.url.includes('127.0.0.1:3000/stocks/');
      });
      sendResponse(ragardTabs);
    });
    return true; // Keep channel open for async response
  }
  
  if (message.type === 'FOCUS_TAB') {
    chrome.tabs.update(message.tabId, { active: true });
    chrome.windows.update(sender.tab.windowId, { focused: true });
    sendResponse({ success: true });
    return true;
  }
  
  if (message.type === 'OPEN_OR_FOCUS_RAGARD') {
    const targetUrl = message.url;
    
    // First, try to find any existing Ragard tab (localhost:3000)
    chrome.tabs.query({}, (tabs) => {
      const existingRagardTab = tabs.find(tab => {
        if (!tab.url) return false;
        // Check if tab is a Ragard tab (production or local)
        return tab.url.includes('ragardai.com') || 
               tab.url.includes('localhost:3000') ||
               tab.url.includes('127.0.0.1:3000');
      });
      
      if (existingRagardTab) {
        // Focus existing Ragard tab and update URL to the new analysis page
        chrome.tabs.update(existingRagardTab.id, { 
          active: true,
          url: targetUrl 
        });
        chrome.windows.update(existingRagardTab.windowId, { focused: true });
        sendResponse({ success: true, tabId: existingRagardTab.id });
      } else {
        // Open new tab
        chrome.tabs.create({ url: targetUrl });
        sendResponse({ success: true, newTab: true });
      }
    });
    return true; // Keep channel open for async response
  }
});

