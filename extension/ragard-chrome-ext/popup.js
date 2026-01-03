// Open side panel when popup is clicked
document.addEventListener("DOMContentLoaded", async () => {
  try {
    const [tab] = await chrome.tabs.query({
      active: true,
      currentWindow: true,
    });

    if (tab) {
      // Open side panel
      chrome.sidePanel.open({ windowId: tab.windowId });
    }
    
    // Close popup immediately
    window.close();
  } catch (err) {
    console.error("Error in popup:", err);
    window.close();
  }
});

