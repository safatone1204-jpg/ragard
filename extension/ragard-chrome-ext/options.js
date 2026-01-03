/**
 * Options page script for Ragard extension
 */

// Load current settings
async function loadSettings() {
  const apiUrl = await window.ragardConfig?.getApiBaseUrl() || 'http://localhost:8000';
  const webAppUrl = await window.ragardConfig?.getWebAppBaseUrl() || 'http://localhost:3000';
  
  document.getElementById('api-base-url').value = apiUrl;
  document.getElementById('web-app-base-url').value = webAppUrl;
}

// Save settings
async function saveSettings() {
  const apiUrl = document.getElementById('api-base-url').value.trim();
  const webAppUrl = document.getElementById('web-app-base-url').value.trim();
  
  // Validate URLs
  try {
    new URL(apiUrl);
  } catch {
    showStatus('Invalid API Base URL format', 'error');
    return;
  }
  
  try {
    new URL(webAppUrl);
  } catch {
    showStatus('Invalid Web App Base URL format', 'error');
    return;
  }
  
  // Save to config
  if (window.ragardConfig) {
    await window.ragardConfig.setApiBaseUrl(apiUrl);
    await window.ragardConfig.setWebAppBaseUrl(webAppUrl);
    showStatus('Settings saved successfully!', 'success');
  } else {
    showStatus('Error: Config module not loaded', 'error');
  }
}

// Test connection
async function testConnection() {
  const apiUrl = document.getElementById('api-base-url').value.trim();
  
  if (!apiUrl) {
    showStatus('Please enter an API Base URL first', 'error');
    return;
  }
  
  // Validate URL format
  try {
    new URL(apiUrl);
  } catch {
    showStatus('Invalid API Base URL format', 'error');
    return;
  }
  
  showStatus('Testing connection...', 'testing');
  
  try {
    const healthUrl = `${apiUrl}/health`;
    const response = await fetch(healthUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      mode: 'cors',
      credentials: 'omit',
    });
    
    if (response.ok) {
      const data = await response.json();
      showStatus(`✓ Connection successful! Status: ${data.status || 'healthy'}`, 'success');
    } else {
      showStatus(`✗ Connection failed: ${response.status} ${response.statusText}`, 'error');
    }
  } catch (error) {
    showStatus(`✗ Connection error: ${error.message}`, 'error');
  }
}

// Show status message
function showStatus(message, type) {
  const statusEl = document.getElementById('status');
  statusEl.textContent = message;
  statusEl.className = `status ${type}`;
  
  // Auto-hide success messages after 3 seconds
  if (type === 'success') {
    setTimeout(() => {
      statusEl.className = 'status';
      statusEl.textContent = '';
    }, 3000);
  }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
  loadSettings();
  
  document.getElementById('save-settings').addEventListener('click', saveSettings);
  document.getElementById('test-connection').addEventListener('click', testConnection);
});

