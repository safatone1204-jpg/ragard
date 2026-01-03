/**
 * Ragard Side Panel - Universal Panel UI
 * This panel is shared across all tabs using Chrome's Side Panel API
 */

(function() {
  'use strict';

  // Preferences
  let preferences = {
    disabledDomains: [],
    showTickers: true,
    showNarratives: true,
    showHistory: true,
    showSeenOften: true,
  };

  // Ticker fetch cache to prevent duplicate requests
  const tickerCache = new Map();
  const TICKER_CACHE_TTL = 60000; // 1 minute cache

  // Active timeout IDs
  let activeTimeout = null;
  let activeStorageTimeout = null;
  
  // Analysis tracking for preventing overlapping analyses
  let activeAnalysisId = null;
  let isAnalyzing = false;
  let nextAnalysisId = 0;
  
  // Current analysis data (stored when rendered, used for saving)
  let currentAnalysisData = null;
  let currentAnalysisUrl = null;
  let currentAnalysisTitle = null;
  
  // Auth state (separate module - does NOT touch analyze button)
  // Uses the separate authStatus.js module
  let authState = {
    isLoggedIn: false,
    userId: null,
    username: null
  };
  
  // Saved Analyses Local Storage Utility
  const SAVED_ANALYSES_STORAGE_KEY = 'ragard_saved_analyses';
  const PENDING_SYNC_KEY = 'ragard_pending_sync';
  
  /**
   * Get all saved analyses from local storage
   * @returns {Promise<Array>}
   */
  async function getSavedAnalyses() {
    return new Promise((resolve) => {
      chrome.storage.local.get([SAVED_ANALYSES_STORAGE_KEY], (result) => {
        const analyses = result[SAVED_ANALYSES_STORAGE_KEY];
        if (Array.isArray(analyses)) {
          resolve(analyses);
        } else {
          resolve([]);
        }
      });
    });
  }
  
  /**
   * Save or update an analysis in local storage
   * @param {Object} analysisData - Analysis data to save
   * @returns {Promise<Object>} - The saved analysis object with id
   */
  async function upsertSavedAnalysis(analysisData) {
    const analyses = await getSavedAnalyses();
    
    // Generate ID if not provided
    let analysisId = analysisData.id;
    if (!analysisId) {
      if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        analysisId = crypto.randomUUID();
      } else {
        const hash = btoa(analysisData.url + Date.now()).substring(0, 16).replace(/[^a-zA-Z0-9]/g, '');
        analysisId = `analysis_${hash}_${Date.now()}`;
      }
    }
    
    // Create analysis fingerprint for deduplication (hash of url + analysis key parts)
    const fingerprint = btoa(JSON.stringify({
      url: analysisData.url,
      ticker: analysisData.ticker,
      score: analysisData.score,
      modelVersion: analysisData.modelVersion
    })).substring(0, 32);
    
    // Check if analysis with same fingerprint exists
    const existingIndex = analyses.findIndex(a => a.fingerprint === fingerprint);
    const now = new Date().toISOString();
    
    const savedAnalysis = {
      id: analysisId,
      url: analysisData.url,
      title: analysisData.title || '',
      hostname: analysisData.hostname || '',
      ticker: analysisData.ticker || '',
      analysis: analysisData.analysis || {},
      score: analysisData.score || null,
      signals: analysisData.signals || null,
      summaryText: analysisData.summaryText || null,
      contentType: analysisData.contentType || 'unknown',
      modelVersion: analysisData.modelVersion || null,
      excerpt: analysisData.excerpt || null,
      faviconUrl: analysisData.faviconUrl || null,
      fingerprint: fingerprint,
      createdAt: existingIndex >= 0 ? analyses[existingIndex].createdAt : now,
      updatedAt: now,
      analyzedAt: now,
      pendingSync: analysisData.pendingSync !== false // Default to true if not explicitly false
    };
    
    if (existingIndex >= 0) {
      // Update existing analysis (keep original createdAt)
      analyses[existingIndex] = savedAnalysis;
    } else {
      // Add new analysis
      analyses.push(savedAnalysis);
    }
    
    // Save back to storage
    return new Promise((resolve, reject) => {
      chrome.storage.local.set({ [SAVED_ANALYSES_STORAGE_KEY]: analyses }, () => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          resolve(savedAnalysis);
        }
      });
    });
  }
  
  /**
   * Mark an analysis as synced (pendingSync = false)
   * @param {string} id - Analysis ID
   */
  async function markSynced(id) {
    const analyses = await getSavedAnalyses();
    const index = analyses.findIndex(a => a.id === id);
    if (index >= 0) {
      analyses[index].pendingSync = false;
      chrome.storage.local.set({ [SAVED_ANALYSES_STORAGE_KEY]: analyses });
    }
  }
  
  /**
   * Sync pending analyses to backend
   */
  async function syncPendingAnalyses() {
    try {
      const authToken = await getAuthToken();
      if (!authToken) {
        return; // Not logged in, skip sync
      }
      
      const analyses = await getSavedAnalyses();
      const pending = analyses.filter(a => a.pendingSync === true);
      
      for (const analysis of pending) {
        try {
          // Prepare snapshot with all analysis data + metadata
          const snapshot = {
            ...analysis.analysis,
            url: analysis.url,
            title: analysis.title,
            hostname: analysis.hostname,
            score: analysis.score,
            signals: analysis.signals,
            summaryText: analysis.summaryText,
            contentType: analysis.contentType,
            modelVersion: analysis.modelVersion,
            excerpt: analysis.excerpt,
            faviconUrl: analysis.faviconUrl,
            analyzedAt: analysis.analyzedAt
          };
          
          const apiBaseUrl = await window.ragardConfig?.getApiBaseUrl() || 'http://localhost:8000';
          const response = await fetch(`${apiBaseUrl}/api/saved-analyses`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${authToken}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              ticker: analysis.ticker,
              snapshot: snapshot
            }),
            mode: 'cors',
            credentials: 'omit'
          });
          
          if (response.ok) {
            await markSynced(analysis.id);
            console.log('[Ragard] Synced analysis:', analysis.id);
          } else {
            console.warn('[Ragard] Failed to sync analysis:', analysis.id, response.status);
          }
        } catch (err) {
          console.warn('[Ragard] Error syncing analysis:', analysis.id, err);
        }
      }
    } catch (err) {
      console.warn('[Ragard] Error in syncPendingAnalyses:', err);
    }
  }
  
  // Auth status check function (uses separate module, does NOT call analyzePost)
  async function checkAuthStatus(force = false) {
    try {
      // Use the separate authStatus module
      const authStatusModule = window.ragardAuthStatus;
      if (!authStatusModule || !authStatusModule.getAuthStatus) {
        console.warn('[Ragard] Auth status module not loaded');
        return authState;
      }
      
      // If forcing refresh, clear cache first
      if (force && authStatusModule.clearCache) {
        authStatusModule.clearCache();
      }
      
      const status = await authStatusModule.getAuthStatus(force);
      console.log('[Ragard] Received auth status from module:', JSON.stringify(status, null, 2));
      authState = {
        isLoggedIn: status.isAuthenticated || false,
        userId: status.userId || null,
        username: status.username || null
      };
      console.log('[Ragard] Updated authState:', JSON.stringify(authState, null, 2));
      console.log('[Ragard] isLoggedIn:', authState.isLoggedIn, 'userId:', authState.userId, 'username:', authState.username);
      return authState;
    } catch (err) {
      console.warn('[Ragard] Auth check failed:', err);
      // Don't update state on error, keep last known state
      return authState;
    }
  }

  // Load preferences
  chrome.storage.local.get(['ragard_preferences'], (result) => {
    if (result.ragard_preferences) {
      Object.assign(preferences, result.ragard_preferences);
    }
    init();
  });

  // Track if we're currently rendering to prevent duplicate renders
  let isRendering = false;
  
  // Track last rendered analysis to prevent duplicate renders
  let lastRenderedAnalysisUrl = null;
  let lastRenderedAnalysisTimestamp = 0;

  // Listen for analysis updates from content scripts
  // FALLBACK PATH: Only renders if callback didn't already render (for tab switches, etc.)
  chrome.storage.onChanged.addListener((changes, areaName) => {
    if (areaName === 'local' && changes.ragard_current_analysis) {
      const newAnalysis = changes.ragard_current_analysis.newValue;
      if (newAnalysis && newAnalysis.data && !isRendering) {
        // Check if we already rendered this analysis (from callback fast path)
        const isDuplicate = (
          lastRenderedAnalysisUrl === newAnalysis.url &&
          newAnalysis.timestamp &&
          Math.abs(newAnalysis.timestamp - lastRenderedAnalysisTimestamp) < 2000 // Within 2 seconds
        );
        
        if (isDuplicate) {
          // Already rendered from callback, skip to avoid duplicate
          return;
        }
        
        // Clear any active timeouts since we got the result
        if (activeTimeout) {
          clearTimeout(activeTimeout);
          activeTimeout = null;
        }
        if (activeStorageTimeout) {
          clearTimeout(activeStorageTimeout);
          activeStorageTimeout = null;
        }
        
        // FALLBACK PATH: Render from storage (for tab switches or when callback didn't fire)
        (async () => {
          try {
            isRendering = true;
            // Check if there's an analysis in progress and verify it matches
            chrome.storage.local.get(['ragard_analysis_in_progress'], (progressResult) => {
              const inProgress = progressResult.ragard_analysis_in_progress;
              
              // If there's an in-progress analysis for this URL, clear it and render
              if (inProgress && inProgress.url === newAnalysis.url) {
                chrome.storage.local.remove(['ragard_analysis_in_progress']);
                renderAnalysis(newAnalysis.data).catch(err => {
                  console.warn('[Ragard] Error rendering synced analysis:', err);
                  isRendering = false;
                }).then(() => {
                  isRendering = false;
                  // Track that we rendered this analysis
                  lastRenderedAnalysisUrl = newAnalysis.url;
                  lastRenderedAnalysisTimestamp = newAnalysis.timestamp || Date.now();
                });
              } else {
                // No matching in-progress, but render anyway (might be from another tab or old)
                // The panel is universal, so show whatever analysis is available
                renderAnalysis(newAnalysis.data).catch(err => {
                  console.warn('[Ragard] Error rendering synced analysis:', err);
                  isRendering = false;
                }).then(() => {
                  isRendering = false;
                  // Track that we rendered this analysis
                  lastRenderedAnalysisUrl = newAnalysis.url;
                  lastRenderedAnalysisTimestamp = newAnalysis.timestamp || Date.now();
                });
              }
            });
          } catch (err) {
            console.warn('[Ragard] Error rendering synced analysis:', err);
            isRendering = false;
          }
        })();
      }
    }
  });

  // Helper function to get auth token
  async function getAuthToken() {
    // First try chrome.storage.local (extension storage)
    return new Promise((resolve) => {
      chrome.storage.local.get(['ragard_auth_token', 'ragardToken'], (result) => {
        let token = result.ragard_auth_token || result.ragardToken;
        
        // If not found in extension storage, try to get from main app's localStorage
        if (!token) {
          // Get web app URL from config
          (async () => {
            const webAppUrl = await window.ragardConfig?.getWebAppBaseUrl() || 'http://localhost:3000';
            const urlPattern = webAppUrl.replace(/\/$/, '') + '/*';
            chrome.tabs.query({ url: [urlPattern, 'http://127.0.0.1:3000/*'] }, (tabs) => {
            if (tabs && tabs.length > 0) {
              chrome.scripting.executeScript({
                target: { tabId: tabs[0].id },
                func: () => localStorage.getItem('ragardToken')
              }, (results) => {
                if (results && results[0] && results[0].result) {
                  token = results[0].result;
                  // Cache it for future use
                  if (token) {
                    chrome.storage.local.set({ ragardToken: token });
                  }
                }
                resolve(token || null);
              });
            } else {
              resolve(null);
            }
          });
          })();
        } else {
          resolve(token);
        }
      });
    });
  }

  // Get trust level color
  function getTrustColor(trustLevel) {
    if (trustLevel === 'high') return { hex: '#22c55e', rgb: '34, 197, 94' };
    if (trustLevel === 'medium') return { hex: '#fbbf24', rgb: '251, 191, 36' };
    if (trustLevel === 'low') return { hex: '#f97373', rgb: '249, 115, 115' };
    return { hex: '#9ca3af', rgb: '148, 163, 184' };
  }

  // Get sentiment color
  function getSentimentColor(sentiment) {
    if (sentiment === 'bullish') return { hex: '#22c55e', rgb: '34, 197, 94' };
    if (sentiment === 'bearish') return { hex: '#f97373', rgb: '249, 115, 115' };
    if (sentiment === 'mixed') return { hex: '#fbbf24', rgb: '251, 191, 36' };
    return { hex: '#9ca3af', rgb: '148, 163, 184' };
  }

  // Get regard score color (gradient HSL interpolation)
  function getRegardColor(score) {
    if (score === null || score === undefined) return { hex: '#9CA3AF', rgb: '156, 163, 175' };
    
    const clampedScore = Math.max(0, Math.min(100, score));
    let hue, saturation, lightness;
    
    if (clampedScore <= 50) {
      // Green (120deg) to Yellow (60deg)
      const t = clampedScore / 50;
      hue = 120 - (t * 60); // 120 -> 60
      saturation = 70 + (t * 10); // 70% -> 80%
      lightness = 50 - (t * 5); // 50% -> 45%
    } else {
      // Yellow (60deg) to Red (0deg)
      const t = (clampedScore - 50) / 50;
      hue = 60 - (t * 60); // 60 -> 0
      saturation = 80 + (t * 15); // 80% -> 95%
      lightness = 45 - (t * 5); // 45% -> 40%
    }
    
    const hsl = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
    // Convert HSL to RGB
    const rgb = hslToRgb(hue, saturation, lightness);
    return { hex: hsl, rgb: `${rgb.r}, ${rgb.g}, ${rgb.b}`, hsl: hsl };
  }

  // Helper to convert HSL to RGB
  function hslToRgb(h, s, l) {
    s /= 100;
    l /= 100;
    const c = (1 - Math.abs(2 * l - 1)) * s;
    const x = c * (1 - Math.abs((h / 60) % 2 - 1));
    const m = l - c / 2;
    let r, g, b;
    if (h < 60) {
      r = c; g = x; b = 0;
    } else if (h < 120) {
      r = x; g = c; b = 0;
    } else if (h < 180) {
      r = 0; g = c; b = x;
    } else if (h < 240) {
      r = 0; g = x; b = c;
    } else if (h < 300) {
      r = x; g = 0; b = c;
    } else {
      r = c; g = 0; b = x;
    }
    return {
      r: Math.round((r + m) * 255),
      g: Math.round((g + m) * 255),
      b: Math.round((b + m) * 255)
    };
  }

  // Render author section with type-aware information
  function renderAuthorSection(author, authorContext, authorAnalysis) {
    if (!authorContext && !author && !authorAnalysis) {
      return '';
    }
    
    // Determine display values
    const platform = authorContext?.platform || 'reddit';
    const displayName = authorContext?.authorDisplayName || author || 'Unknown';
    const handle = authorContext?.authorHandle || (author ? (author.startsWith('u/') ? author : `u/${author}`) : null);
    const profileUrl = authorContext?.authorProfileUrl || null;
    const metadata = authorContext?.authorMetadata || {};
    
    // Platform display name
    const platformNames = {
      'reddit': 'Reddit',
      'twitter': 'Twitter/X',
      'stocktwits': 'Stocktwits',
      'article_site': 'Article Site',
      'generic': 'Generic'
    };
    const platformDisplay = platformNames[platform] || platform;
    
    let html = `
      <div class="ragard-field" style="margin-top: 8px;">
        <div class="ragard-field-label">${platform === 'article_site' ? 'Source' : 'Author'}</div>
        <div class="ragard-field-value">
          ${profileUrl ? `<a href="${profileUrl}" target="_blank" style="color: #22c55e; text-decoration: none;">${displayName}</a>` : displayName}
          ${handle && handle !== displayName ? ` <span style="color: #6b7280; font-size: 11px;">(${handle})</span>` : ''}
        </div>
        <div style="font-size: 10px; color: #6b7280; margin-top: 4px;">Platform: ${platformDisplay}</div>
    `;
    
    // Show metadata if available
    if (metadata.followers) {
      html += `<div style="font-size: 11px; color: #9ca3af; margin-top: 4px;">Followers: ${metadata.followers.toLocaleString()}</div>`;
    }
    if (metadata.karma_or_points) {
      html += `<div style="font-size: 11px; color: #9ca3af; margin-top: 4px;">Karma: ${metadata.karma_or_points.toLocaleString()}</div>`;
    }
    if (metadata.domainReputation) {
      const repColors = {
        'high': { bg: 'rgba(34, 197, 94, 0.2)', color: '#22c55e', text: 'High Reputation' },
        'medium': { bg: 'rgba(251, 191, 36, 0.2)', color: '#fbbf24', text: 'Medium Reputation' },
        'low': { bg: 'rgba(249, 115, 115, 0.2)', color: '#f97373', text: 'Low Reputation' }
      };
      const rep = repColors[metadata.domainReputation] || repColors.medium;
      html += `<div style="font-size: 10px; padding: 2px 8px; border-radius: 8px; background: ${rep.bg}; color: ${rep.color}; border: 1px solid ${rep.color}40; display: inline-block; margin-top: 4px;">${rep.text}</div>`;
    }
    
    // Show author analysis if available
    if (authorAnalysis && authorAnalysis.author_regard_score !== null && authorAnalysis.author_regard_score !== undefined) {
      html += `
        <div style="margin-top: 8px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
          ${renderRegardGauge(authorAnalysis.author_regard_score, 'sm')}
          ${authorAnalysis.trust_level
            ? `<span style="font-size: 10px; padding: 2px 8px; border-radius: 8px; background: rgba(${getTrustColor(authorAnalysis.trust_level).rgb}, 0.2); color: ${getTrustColor(authorAnalysis.trust_level).hex}; border: 1px solid rgba(${getTrustColor(authorAnalysis.trust_level).rgb}, 0.3); text-transform: capitalize;">
                  ${authorAnalysis.trust_level} trust
                </span>`
            : ''
          }
          <div class="ragard-tooltip-container" style="display: inline-block; margin-left: 4px;">
            <span style="font-size: 12px; color: #6b7280; cursor: help;">?</span>
            <div class="ragard-tooltip" style="white-space: normal; max-width: 280px;">
              <span class="ragard-tooltip-title">Author Regard Score:</span>
              <span style="color: #9ca3af; font-size: 10px; line-height: 1.2;">
                How degen this author is based on their posting style. Higher = more casino behavior.
              </span>
            </div>
          </div>
        </div>
      `;
    }
    
    // Show summary and signals if available
    if (authorAnalysis?.summary) {
      html += `<div style="font-size: 11px; color: #9ca3af; margin-top: 6px; line-height: 1.4;">${authorAnalysis.summary}</div>`;
    }
    if (authorAnalysis?.signals && Array.isArray(authorAnalysis.signals) && authorAnalysis.signals.length > 0) {
      html += `<div style="margin-top: 6px; display: flex; flex-wrap: wrap; gap: 4px;">`;
      authorAnalysis.signals.forEach(signal => {
        html += `<span style="font-size: 10px; padding: 2px 6px; border-radius: 6px; background: rgba(148, 163, 184, 0.2); color: #9ca3af;">${signal}</span>`;
      });
      html += `</div>`;
    }
    
    html += `</div>`;
    return html;
  }

  // Render Regard Score Gauge
  function renderRegardGauge(score, size = 'sm') {
    const validScore = score !== null && score !== undefined ? score : 0;
    const color = getRegardColor(validScore);
    const dimensions = size === 'lg' ? { width: 192, height: 192 } : { width: 48, height: 48 };
    const strokeWidth = size === 'lg' ? 12 : 4;
    const radius = size === 'lg' ? 80 : 20;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (validScore / 100) * circumference;
    const fontSize = size === 'lg' ? '36px' : '12px';
    
    return `
      <div style="position: relative; display: inline-flex; align-items: center; justify-content: center;">
        <svg width="${dimensions.width}" height="${dimensions.height}" style="transform: rotate(-90deg);">
          <circle
            cx="${dimensions.width / 2}"
            cy="${dimensions.height / 2}"
            r="${radius}"
            stroke="rgba(148, 163, 184, 0.3)"
            stroke-width="${strokeWidth}"
            fill="none"
          />
          <circle
            cx="${dimensions.width / 2}"
            cy="${dimensions.height / 2}"
            r="${radius}"
            stroke="${color.hsl || color.hex}"
            stroke-width="${strokeWidth}"
            fill="none"
            stroke-dasharray="${circumference}"
            stroke-dashoffset="${offset}"
            stroke-linecap="round"
            style="transition: all 0.5s;"
          />
        </svg>
        <div style="position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;">
          <span style="font-weight: 700; font-size: ${fontSize}; color: ${color.hsl || color.hex}; transition: all 0.5s;">
            ${validScore}
          </span>
        </div>
      </div>
    `;
  }

  // Render analysis results
  async function renderAnalysis(data) {
    const contentEl = document.getElementById('ragard-panel-content');
    if (!contentEl) return;
    
    // Store current analysis data for saving
    currentAnalysisData = data;
    
    // Get URL and title from stored analysis (from when analysis was requested)
    // This ensures we use the URL from the analysis tab, not the current tab
    try {
      const stored = await new Promise((resolve) => {
        chrome.storage.local.get(['ragard_current_analysis'], (result) => {
          resolve(result.ragard_current_analysis);
        });
      });
      
      if (stored && stored.url) {
        currentAnalysisUrl = stored.url;
        // Try to get title from stored analysis or from current tab as fallback
        if (stored.title) {
          currentAnalysisTitle = stored.title;
        } else {
          // Fallback: get title from current tab (but URL is from analysis)
          try {
            const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
            if (tabs[0] && tabs[0].url === stored.url) {
              currentAnalysisTitle = tabs[0].title || null;
            }
          } catch (e) {
            // Ignore
          }
        }
      } else {
        // Fallback: get from current tab if stored analysis not available
        try {
          const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
          if (tabs[0]) {
            currentAnalysisUrl = tabs[0].url || null;
            currentAnalysisTitle = tabs[0].title || null;
          }
        } catch (e) {
          console.warn('[Ragard] Could not get tab info:', e);
        }
      }
    } catch (e) {
      console.warn('[Ragard] Could not get stored analysis info:', e);
      // Fallback: get from current tab
      try {
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tabs[0]) {
          currentAnalysisUrl = tabs[0].url || null;
          currentAnalysisTitle = tabs[0].title || null;
        }
      } catch (e2) {
        console.warn('[Ragard] Could not get tab info:', e2);
      }
    }
    
    // Re-enable button after rendering
    const analyzeBtn = document.getElementById('ragard-analyze-btn');
    if (analyzeBtn) {
      analyzeBtn.disabled = false;
    }

    if (!data.ok) {
      contentEl.innerHTML = `<div class="ragard-error">Error: ${data.message || 'Unknown error'}</div>`;
      return;
    }

    const {
      subreddit,
      title,
      author,
      tickers = [],
      post_degen_score,
      post_analysis = {},
      author_analysis = null,
      author_context = null,  // New field for richer author info
    } = data || {};

    const {
      ai_summary,
      ai_sentiment,
      ai_narrative_name,
    } = post_analysis || {};

    let html = `
      <div class="ragard-section">
        <div class="ragard-section-title">Post Snapshot</div>
        ${subreddit ? `<div class="ragard-field"><div class="ragard-field-label">Subreddit</div><div class="ragard-field-value">/r/${subreddit}</div></div>` : ''}
        ${title ? `<div class="ragard-field"><div class="ragard-field-label">Title</div><div class="ragard-field-value">${title.length > 120 ? title.substring(0, 120) + '...' : title}</div></div>` : ''}
        
        ${renderAuthorSection(author, author_context, author_analysis)}
      </div>
    `;

    // Enhanced Tickers section with watchlist integration
    if (preferences.showTickers && tickers.length > 0) {
      // Normalize ticker format
      const normalizedTickers = tickers.map(t => {
        if (typeof t === 'string') {
          return { symbol: t };
        }
        return t;
      });
      
      // Fetch additional ticker data and watchlist status (with caching to prevent duplicates)
      const enrichedTickers = await Promise.all(normalizedTickers.map(async (ticker) => {
        const symbol = (ticker.symbol || ticker || '').toString().toUpperCase();
        if (!symbol) return ticker;
        
        // Check cache first
        const cacheKey = symbol;
        const cached = tickerCache.get(cacheKey);
        if (cached && (Date.now() - cached.timestamp) < TICKER_CACHE_TTL) {
          return { ...ticker, ...cached.data, symbol: symbol };
        }
        
        try {
          const apiBaseUrl = await window.ragardConfig?.getApiBaseUrl() || 'http://localhost:8000';
          const tickerResponse = await fetch(`${apiBaseUrl}/api/tickers/${symbol}`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            mode: 'cors',
            credentials: 'omit'
          });
          
          if (tickerResponse.ok) {
            const tickerData = await tickerResponse.json();
            // Cache successful responses
            tickerCache.set(cacheKey, { data: tickerData, timestamp: Date.now() });
            return { ...ticker, ...tickerData, symbol: symbol };
          } else if (tickerResponse.status === 404) {
            // Ticker doesn't exist - cache the 404 to avoid repeated requests
            tickerCache.set(cacheKey, { data: null, timestamp: Date.now() });
            return { ...ticker, symbol: symbol };
          }
        } catch (e) {
          // Network error or other issue - fallback to original ticker data
        }
        return { ...ticker, symbol: symbol };
      }));
      
      // Track "seen often"
      if (preferences.showSeenOften) {
        try {
          chrome.storage.local.get(['ragard_ticker_seen'], (result) => {
            const seen = result.ragard_ticker_seen || {};
            const now = Date.now();
            const dayMs = 24 * 60 * 60 * 1000;
            
            enrichedTickers.forEach(ticker => {
              const symbol = (ticker.symbol || ticker || '').toString().toUpperCase();
              if (!symbol) return;
              
              if (!seen[symbol]) {
                seen[symbol] = [];
              }
              seen[symbol] = seen[symbol].filter(t => now - t < 7 * dayMs);
              seen[symbol].push(now);
            });
            
            chrome.storage.local.set({ ragard_ticker_seen: seen });
          });
        } catch (e) {
          // Silently fail
        }
      }
      
      // Check watchlist status (only if logged in)
      let watchlists = [];
      let tickerWatchlistMap = new Map();
      
      // Check auth status first (force refresh to ensure we have latest status)
      await checkAuthStatus(true);
      console.log('[Ragard] Auth state after check:', JSON.stringify(authState, null, 2));
      console.log('[Ragard] authState.isLoggedIn:', authState.isLoggedIn, 'type:', typeof authState.isLoggedIn);
      
      if (authState.isLoggedIn) {
        try {
          const authToken = await getAuthToken();
          if (authToken) {
            const apiBaseUrl = await window.ragardConfig?.getApiBaseUrl() || 'http://localhost:8000';
            const watchlistResponse = await fetch(`${apiBaseUrl}/api/watchlists`, {
              headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
              },
              mode: 'cors',
              credentials: 'omit'
            });
            if (watchlistResponse.ok) {
              watchlists = await watchlistResponse.json();
              for (const ticker of enrichedTickers) {
                const symbol = (ticker.symbol || ticker || '').toString().toUpperCase();
                if (!symbol) continue;
                const inWatchlists = new Set();
                for (const wl of watchlists) {
                  try {
                    const itemsResponse = await fetch(`${apiBaseUrl}/api/watchlists/${wl.id}/items`, {
                      headers: {
                        'Authorization': `Bearer ${authToken}`,
                        'Content-Type': 'application/json'
                      },
                      mode: 'cors',
                      credentials: 'omit'
                    });
                    if (itemsResponse.ok) {
                      const items = await itemsResponse.json();
                      if (items.some(item => item.ticker === symbol)) {
                        inWatchlists.add(wl.id);
                      }
                    }
                  } catch (e) {
                    // Ignore errors
                  }
                }
                tickerWatchlistMap.set(symbol, inWatchlists);
              }
            }
          }
        } catch (e) {
          // Not authenticated or API error
        }
      }
      
      // Separate primary and secondary tickers
      const primaryTickers = enrichedTickers.filter(t => t.isPrimary === true);
      const secondaryTickers = enrichedTickers.filter(t => !t.isPrimary);
      
      html += `
        <div class="ragard-section">
          <div class="ragard-section-title">Tickers in this ${subreddit ? 'post' : 'page'}</div>
          ${primaryTickers.length > 0 ? `
            <div style="margin-bottom: 8px;">
              <div style="font-size: 10px; color: #9ca3af; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px;">Primary</div>
              ${primaryTickers.map(ticker => {
            const regardScore = ticker.regard_score;
            const regardColor = getRegardColor(regardScore !== null && regardScore !== undefined ? regardScore : 0);
            const priceStr = ticker.price !== null ? `$${ticker.price.toFixed(2)}` : 'N/A';
            const changeStr = ticker.change_1d_pct !== null && ticker.change_1d_pct !== undefined
              ? `${ticker.change_1d_pct >= 0 ? '+' : ''}${ticker.change_1d_pct.toFixed(2)}%`
              : 'N/A';
            const changeColor = ticker.change_1d_pct >= 0 ? '#22c55e' : '#f97373';
            const inWatchlist = tickerWatchlistMap.get(ticker.symbol || ticker)?.size > 0;
            
            return `
              <div class="ragard-ticker-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                  <div style="display: flex; align-items: center; gap: 8px; flex: 1;">
                    <span style="font-weight: 700; font-size: 16px; color: #e5e7eb;">${ticker.symbol}</span>
                    ${authState.isLoggedIn ? `
                      <button class="ragard-ticker-action" data-ticker="${ticker.symbol || ticker}" data-action="watchlist" data-in-watchlist="${inWatchlist}" style="padding: 2px 6px; background: ${inWatchlist ? 'rgba(34, 197, 94, 0.2)' : 'rgba(148, 163, 184, 0.1)'}; color: ${inWatchlist ? '#22c55e' : '#9ca3af'}; border: 1px solid ${inWatchlist ? 'rgba(34, 197, 94, 0.3)' : 'rgba(148, 163, 184, 0.3)'}; border-radius: 4px; cursor: pointer; font-size: 14px; line-height: 1; min-width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;">
                        ${inWatchlist ? '⭐' : '☆'}
                      </button>
                    ` : ''}
                  </div>
                  <div style="display: flex; align-items: center; gap: 6px;">
                    ${ticker.regard_score !== null && ticker.regard_score !== undefined ? renderRegardGauge(ticker.regard_score, 'sm') : '<span style="color: #9ca3af; font-size: 12px;">N/A</span>'}
                    <div class="ragard-tooltip-container" style="display: inline-block;">
                      <span style="font-size: 12px; color: #6b7280; cursor: help;">?</span>
                      <div class="ragard-tooltip" style="white-space: normal; max-width: 380px;">
                        <span class="ragard-tooltip-title">Regard Score:</span>
                        <span style="color: #9ca3af; font-size: 10px; line-height: 1.2;">
                          0 = safe/boring, 100 = ultra-degen meme. Higher = more casino risk.
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                ${!authState.isLoggedIn ? `
                  <div style="font-size: 9px; color: #6b7280; margin-top: -4px; margin-bottom: 4px; text-align: left; font-style: italic;">
                    Log in to use watchlists
                  </div>
                ` : ''}
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #9ca3af; margin-bottom: 4px;">
                  <span>${priceStr}</span>
                  <span style="color: ${changeColor}; font-weight: 600;">${changeStr}</span>
                </div>
                ${ticker.narratives && ticker.narratives.length > 0 
                  ? `<div style="display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; margin-bottom: 4px;">
                      ${ticker.narratives.map(n => `<span style="font-size: 10px; padding: 2px 6px; background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.2); border-radius: 6px; color: #22c55e;">${n}</span>`).join('')}
                    </div>`
                  : ''
                }
                ${ticker.regard_data_completeness && ticker.regard_data_completeness !== 'full'
                  ? (() => {
                      const missingFactors = ticker.regard_missing_factors || [];
                      const formatFactorName = (factor) => {
                        const names = {
                          'market_cap': 'Market Cap',
                          'profit_margins': 'Profit Margins',
                          'beta': 'Beta (Volatility)',
                          'avg_volume': 'Average Volume',
                          'short_ratio': 'Short Ratio',
                          'market_data': 'Market Data'
                        };
                        return names[factor] || factor.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                      };
                      const formattedFactors = missingFactors.length > 0 
                        ? missingFactors.map(formatFactorName).join(', ')
                        : 'Unknown data';
                      
                      return `
                        <div class="ragard-tooltip-container" style="display: inline-block; margin-top: 2px; margin-bottom: 2px;">
                          <div style="font-size: 9px; color: #fbbf24; font-style: italic; cursor: help;">
                            ⚠ Some data missing
                          </div>
                          <div class="ragard-tooltip" style="white-space: normal; max-width: 300px;">
                            <span class="ragard-tooltip-title">Missing Data:</span>
                            <ul class="ragard-tooltip-list">
                              ${missingFactors.map(factor => `<li>${formatFactorName(factor)}</li>`).join('')}
                            </ul>
                            <div style="color: #6b7280; font-size: 9px; margin-top: 2px; font-style: italic; line-height: 1.2; display: block;">
                              Score may be less accurate
                            </div>
                          </div>
                        </div>
                      `;
                    })()
                  : ''
                }
                ${preferences.showSeenOften ? `
                  <div class="ragard-seen-often" data-ticker="${ticker.symbol || ticker}" style="display: none; font-size: 10px; color: #fbbf24; margin-top: 6px; font-style: italic;">
                    💡 You keep seeing this ticker. Consider adding it to a watchlist?
                  </div>
                ` : ''}
              </div>
            `;
          }).join('')}
            </div>
          ` : ''}
          ${secondaryTickers.length > 0 ? `
            <div>
              ${primaryTickers.length > 0 ? `<div style="font-size: 10px; color: #9ca3af; margin-top: 8px; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px;">Also Mentioned</div>` : ''}
              ${secondaryTickers.map(ticker => {
            const regardScore = ticker.regard_score;
            const regardColor = getRegardColor(regardScore !== null && regardScore !== undefined ? regardScore : 0);
            const priceStr = ticker.price !== null ? `$${ticker.price.toFixed(2)}` : 'N/A';
            const changeStr = ticker.change_1d_pct !== null && ticker.change_1d_pct !== undefined
              ? `${ticker.change_1d_pct >= 0 ? '+' : ''}${ticker.change_1d_pct.toFixed(2)}%`
              : 'N/A';
            const changeColor = ticker.change_1d_pct >= 0 ? '#22c55e' : '#f97373';
            const inWatchlist = tickerWatchlistMap.get(ticker.symbol || ticker)?.size > 0;
            
            return `
              <div class="ragard-ticker-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                  <div style="display: flex; align-items: center; gap: 8px; flex: 1;">
                    <span style="font-weight: 700; font-size: 16px; color: #e5e7eb;">${ticker.symbol}</span>
                    ${authState.isLoggedIn ? `
                      <button class="ragard-ticker-action" data-ticker="${ticker.symbol || ticker}" data-action="watchlist" data-in-watchlist="${inWatchlist}" style="padding: 2px 6px; background: ${inWatchlist ? 'rgba(34, 197, 94, 0.2)' : 'rgba(148, 163, 184, 0.1)'}; color: ${inWatchlist ? '#22c55e' : '#9ca3af'}; border: 1px solid ${inWatchlist ? 'rgba(34, 197, 94, 0.3)' : 'rgba(148, 163, 184, 0.3)'}; border-radius: 4px; cursor: pointer; font-size: 14px; line-height: 1; min-width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;">
                        ${inWatchlist ? '⭐' : '☆'}
                      </button>
                    ` : ''}
                  </div>
                  <div style="display: flex; align-items: center; gap: 6px;">
                    ${ticker.regard_score !== null && ticker.regard_score !== undefined ? renderRegardGauge(ticker.regard_score, 'sm') : '<span style="color: #9ca3af; font-size: 12px;">N/A</span>'}
                    <div class="ragard-tooltip-container" style="display: inline-block;">
                      <span style="font-size: 12px; color: #6b7280; cursor: help;">?</span>
                      <div class="ragard-tooltip" style="white-space: normal; max-width: 380px;">
                        <span class="ragard-tooltip-title">Regard Score:</span>
                        <span style="color: #9ca3af; font-size: 10px; line-height: 1.2;">
                          0 = safe/boring, 100 = ultra-degen meme. Higher = more casino risk.
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                ${!authState.isLoggedIn ? `
                  <div style="font-size: 9px; color: #6b7280; margin-top: -4px; margin-bottom: 4px; text-align: left; font-style: italic;">
                    Log in to use watchlists
                  </div>
                ` : ''}
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #9ca3af; margin-bottom: 4px;">
                  <span>${priceStr}</span>
                  <span style="color: ${changeColor}; font-weight: 600;">${changeStr}</span>
                </div>
                ${ticker.narratives && ticker.narratives.length > 0 
                  ? `<div style="display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; margin-bottom: 4px;">
                      ${ticker.narratives.map(n => `<span style="font-size: 10px; padding: 2px 6px; background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.2); border-radius: 6px; color: #22c55e;">${n}</span>`).join('')}
                    </div>`
                  : ''
                }
                ${ticker.regard_data_completeness && ticker.regard_data_completeness !== 'full'
                  ? (() => {
                      const missingFactors = ticker.regard_missing_factors || [];
                      const formatFactorName = (factor) => {
                        const names = {
                          'market_cap': 'Market Cap',
                          'profit_margins': 'Profit Margins',
                          'beta': 'Beta (Volatility)',
                          'avg_volume': 'Average Volume',
                          'short_ratio': 'Short Ratio',
                          'market_data': 'Market Data'
                        };
                        return names[factor] || factor.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                      };
                      
                      return `
                        <div class="ragard-tooltip-container" style="display: inline-block; margin-top: 2px; margin-bottom: 2px;">
                          <div style="font-size: 9px; color: #fbbf24; font-style: italic; cursor: help;">
                            ⚠ Some data missing
                          </div>
                          <div class="ragard-tooltip" style="white-space: normal; max-width: 300px;">
                            <span class="ragard-tooltip-title">Missing Data:</span>
                            <ul class="ragard-tooltip-list">
                              ${missingFactors.map(factor => `<li>${formatFactorName(factor)}</li>`).join('')}
                            </ul>
                            <div style="color: #6b7280; font-size: 9px; margin-top: 2px; font-style: italic; line-height: 1.2; display: block;">
                              Score may be less accurate
                            </div>
                          </div>
                        </div>
                      `;
                    })()
                  : ''
                }
                ${preferences.showSeenOften ? `
                  <div class="ragard-seen-often" data-ticker="${ticker.symbol || ticker}" style="display: none; font-size: 10px; color: #fbbf24; margin-top: 6px; font-style: italic;">
                    💡 You keep seeing this ticker. Consider adding it to a watchlist?
                  </div>
                ` : ''}
              </div>
            `;
          }).join('')}
            </div>
          ` : ''}
        </div>
      `;
    } else if (preferences.showTickers) {
      html += `
        <div class="ragard-section">
          <div class="ragard-section-title">Tickers in this ${subreddit ? 'post' : 'page'}</div>
          <div style="color: #9ca3af; font-size: 12px;">No tickers detected.</div>
        </div>
      `;
    }
    
    // Narratives section - only show if narrative exists in backend
    if (preferences.showNarratives && ai_narrative_name) {
      try {
        const apiBaseUrl = await window.ragardConfig?.getApiBaseUrl() || 'http://localhost:8000';
        const narrativesResponse = await fetch(`${apiBaseUrl}/api/narratives?timeframe=24h`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          mode: 'cors',
          credentials: 'omit'
        });
        
        if (narrativesResponse.ok) {
          const allNarratives = await narrativesResponse.json();
          const matchingNarrative = allNarratives.find(n => 
            n.name && n.name.toLowerCase() === ai_narrative_name.toLowerCase()
          );
          
          if (matchingNarrative) {
            html += `
              <div class="ragard-section">
                <div class="ragard-section-title">Narratives in this content</div>
                <div style="padding: 8px; margin-bottom: 8px; background: rgba(11, 17, 32, 0.6); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px;">
                  <div style="font-weight: 600; font-size: 13px; color: #e5e7eb; margin-bottom: 4px;">${matchingNarrative.name}</div>
                  ${matchingNarrative.description ? `<div style="font-size: 11px; color: #9ca3af; margin-bottom: 6px;">${matchingNarrative.description}</div>` : ''}
                  <button class="ragard-narrative-action" data-narrative-id="${matchingNarrative.id}" data-narrative-name="${matchingNarrative.name}" style="padding: 4px 8px; background: rgba(34, 197, 94, 0.1); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 4px; cursor: pointer; font-size: 10px; margin-top: 6px;">
                    View in Ragard
                  </button>
                </div>
              </div>
            `;
          }
        }
      } catch (e) {
        // Silently fail
      }
    }

    // AI Take section
    html += `
      <div class="ragard-section">
        <div class="ragard-section-title">AI Take</div>
    `;

    if (ai_narrative_name) {
      html += `
        <div style="font-weight: 600; font-size: 14px; color: #e5e7eb; margin-bottom: 8px;">
          ${ai_narrative_name}
        </div>
      `;
    }

    if (ai_summary) {
      const sentences = ai_summary.split(/[.!?]+/).filter(s => s.trim().length > 0);
      html += `
        <div style="color: #e5e7eb; font-size: 12px; line-height: 1.6; margin-bottom: 12px;">
          ${sentences.slice(0, 4).map(s => s.trim()).join('. ')}${sentences.length > 4 ? '...' : ''}
        </div>
      `;
    } else {
      html += `
        <div style="color: #9ca3af; font-size: 11px; font-style: italic; margin-bottom: 12px;">
          AI summary not available yet. Using basic stub degen score.
        </div>
      `;
    }

    if (ai_sentiment) {
      const sentimentColor = getSentimentColor(ai_sentiment);
      html += `
        <div style="margin-bottom: 12px;">
          <span style="font-size: 11px; padding: 4px 10px; border-radius: 12px; background: rgba(${sentimentColor.rgb}, 0.2); color: ${sentimentColor.hex}; border: 1px solid rgba(${sentimentColor.rgb}, 0.3); text-transform: capitalize; font-weight: 600;">
            ${ai_sentiment}
          </span>
        </div>
      `;
    }
    
    html += `</div>`; // Close AI Take section
    
    // Action buttons section
    const primaryTicker = tickers.length > 0 ? (tickers[0].symbol || tickers[0]) : null;
    html += `
      <div class="ragard-section" style="margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(148, 163, 184, 0.2); padding-bottom: 0;">
    `;
    
    if (primaryTicker) {
      html += `
        <button id="ragard-full-analysis-btn" style="width: 100%; padding: 12px 16px; border-radius: 999px; border: none; background: #22c55e; color: #020617; font-weight: 600; cursor: pointer; font-size: 13px; box-shadow: 0 2px 8px rgba(34, 197, 94, 0.3); transition: all 0.2s; display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
          Full Analysis in Ragard
        </button>
      `;
      
      html += `
        <button id="ragard-save-page-btn" style="width: 100%; padding: 10px 16px; border-radius: 999px; border: 1px solid rgba(148, 163, 184, 0.3); background: rgba(148, 163, 184, 0.1); color: #9ca3af; font-weight: 600; cursor: pointer; font-size: 12px; transition: all 0.2s; display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
          Save this page under ${primaryTicker}
        </button>
      `;
    }
    
    html += `
      <button id="ragard-analyze-another-btn" style="width: 100%; padding: 12px 16px; border-radius: 999px; border: 1px solid rgba(148, 163, 184, 0.3); background: transparent; color: #9ca3af; font-weight: 600; cursor: pointer; font-size: 13px; transition: all 0.2s; display: flex; align-items: center; justify-content: center;">
        Analyze Another ${subreddit ? 'Post' : 'Page'}
      </button>
      </div>
    `;

    contentEl.innerHTML = html;
    
    // Add event listeners
    setupEventListeners(data, tickers, author, primaryTicker);
  }

  function setupEventListeners(data, tickers, author, primaryTicker) {
    const contentEl = document.getElementById('ragard-panel-content');
    if (!contentEl) return;

    // Ticker watchlist actions
    contentEl.querySelectorAll('.ragard-ticker-action').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const ticker = btn.getAttribute('data-ticker');
        const action = btn.getAttribute('data-action');
        
        if (action === 'watchlist') {
          // Check auth status first (force refresh)
          await checkAuthStatus(true);
          if (!authState.isLoggedIn) {
            alert('Please log into Ragard to use watchlists.');
            return;
          }
          
          const inWatchlist = btn.getAttribute('data-in-watchlist') === 'true';
          try {
            const authToken = await getAuthToken();
            if (!authToken) {
              alert('Please log into Ragard to use watchlists.');
              return;
            }
            
            const apiBaseUrl = await window.ragardConfig?.getApiBaseUrl() || 'http://localhost:8000';
            const watchlistResponse = await fetch(`${apiBaseUrl}/api/watchlists`, {
              headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
              },
              mode: 'cors',
              credentials: 'omit'
            });
            
            if (watchlistResponse.ok) {
              const watchlists = await watchlistResponse.json();
              // Use first watchlist, or create one if none exist
              let watchlistId = null;
              if (watchlists.length > 0) {
                watchlistId = watchlists[0].id;
              } else {
                // Create a default watchlist if none exists
                const createResponse = await fetch(`${apiBaseUrl}/api/watchlists`, {
                  method: 'POST',
                  headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                  },
                  body: JSON.stringify({ name: 'My Watchlist' }),
                  mode: 'cors',
                  credentials: 'omit'
                });
                if (createResponse.ok) {
                  const newWatchlist = await createResponse.json();
                  watchlistId = newWatchlist.id;
                }
              }
              
              if (watchlistId) {
                if (inWatchlist) {
                  const itemsResponse = await fetch(`${apiBaseUrl}/api/watchlists/${watchlistId}/items`, {
                    headers: {
                      'Authorization': `Bearer ${authToken}`,
                      'Content-Type': 'application/json'
                    },
                    mode: 'cors',
                    credentials: 'omit'
                  });
                  if (itemsResponse.ok) {
                    const items = await itemsResponse.json();
                    const item = items.find(i => i.ticker === ticker.toUpperCase());
                    if (item) {
                      await fetch(`${apiBaseUrl}/api/watchlists/${watchlistId}/items/${item.id}`, {
                        method: 'DELETE',
                        headers: {
                          'Authorization': `Bearer ${authToken}`,
                          'Content-Type': 'application/json'
                        },
                        mode: 'cors',
                        credentials: 'omit'
                      });
                    }
                  }
                } else {
                  await fetch(`${apiBaseUrl}/api/watchlists/${watchlistId}/items`, {
                    method: 'POST',
                    headers: {
                      'Authorization': `Bearer ${authToken}`,
                      'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ ticker: ticker.toUpperCase() }),
                    mode: 'cors',
                    credentials: 'omit'
                  });
                }
                // Re-render to update watchlist status
                await renderAnalysis(data);
              }
            }
          } catch (error) {
            alert('Error updating watchlist: ' + (error.message || 'Unknown error'));
          }
        }
      });
    });
    
    // Narrative actions
    contentEl.querySelectorAll('.ragard-narrative-action').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const narrativeId = btn.getAttribute('data-narrative-id');
        const narrativeName = btn.getAttribute('data-narrative-name');
        const narrativeParam = narrativeId || encodeURIComponent(narrativeName);
        chrome.runtime.sendMessage({
          type: 'OPEN_OR_FOCUS_RAGARD',
          url: `${await window.ragardConfig?.getWebAppBaseUrl() || 'http://localhost:3000'}/narratives/${narrativeParam}`
        });
      });
    });
    
    // Full Analysis button
    const fullAnalysisBtn = document.getElementById('ragard-full-analysis-btn');
    if (fullAnalysisBtn && primaryTicker) {
      fullAnalysisBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const primarySymbol = typeof primaryTicker === 'string' ? primaryTicker : primaryTicker.symbol;
        const authorParam = author ? `?author=${encodeURIComponent(author.replace('u/', '').trim())}` : '';
        const webAppUrl = await window.ragardConfig?.getWebAppBaseUrl() || 'http://localhost:3000';
        const ragardUrl = `${webAppUrl}/stocks/${encodeURIComponent(primarySymbol)}${authorParam}`;
        chrome.runtime.sendMessage({
          type: 'OPEN_OR_FOCUS_RAGARD',
          url: ragardUrl
        }, (response) => {
          if (chrome.runtime.lastError) {
            window.open(ragardUrl, '_blank');
          }
        });
      });
    }
    
    // Save Analysis button
    const savePageBtn = document.getElementById('ragard-save-page-btn');
    if (savePageBtn && primaryTicker) {
      savePageBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const symbol = typeof primaryTicker === 'string' ? primaryTicker : primaryTicker.symbol;
        
        // Validate: Check if analysis exists
        if (!currentAnalysisData || !currentAnalysisData.ok) {
          alert('Run analysis first to save.');
          return;
        }
        
        // Store original button state
        const originalText = savePageBtn.textContent;
        const originalBg = savePageBtn.style.background;
        const originalColor = savePageBtn.style.color;
        const originalCursor = savePageBtn.style.cursor;
        
        // Show loading state
        savePageBtn.disabled = true;
        savePageBtn.style.cursor = 'wait';
        savePageBtn.textContent = 'Saving...';
        savePageBtn.style.background = 'rgba(148, 163, 184, 0.2)';
        savePageBtn.style.color = '#94a3b8';
        
        try {
          // Use the URL and title from when the analysis was done, not the current tab
          if (!currentAnalysisUrl) {
            throw new Error('Analysis URL not available. Please run analysis again.');
          }
          
          const currentUrl = currentAnalysisUrl;
          const currentTitle = currentAnalysisTitle || '';
          
          // Get favicon from the analysis URL (try to get it from the stored URL)
          let faviconUrl = null;
          try {
            // Try to get favicon from the analysis URL's domain
            const urlObj = new URL(currentUrl);
            faviconUrl = `https://www.google.com/s2/favicons?domain=${urlObj.hostname}&sz=32`;
          } catch (e) {
            // Ignore favicon errors
          }
          
          // Check if URL is saveable
          let hostname = '';
          try {
            const urlObj = new URL(currentUrl);
            if (urlObj.protocol === 'chrome:' || urlObj.protocol === 'edge:' || urlObj.protocol === 'chrome-extension:' || urlObj.protocol === 'moz-extension:') {
              throw new Error('Cannot save this type of page (browser internal page)');
            }
            hostname = urlObj.hostname;
          } catch (urlError) {
            throw new Error('Invalid URL format');
          }
          
          // Extract analysis metadata
          const analysis = currentAnalysisData;
          const primaryTickerData = analysis.tickers && analysis.tickers.length > 0 ? analysis.tickers[0] : null;
          const score = primaryTickerData?.regard_score || null;
          const signals = primaryTickerData?.signals || null;
          const summaryText = analysis.summary || analysis.ai_narrative || null;
          
          // Determine content type
          let contentType = 'unknown';
          if (currentUrl.includes('reddit.com')) contentType = 'forum';
          else if (currentUrl.includes('twitter.com') || currentUrl.includes('x.com')) contentType = 'social';
          else if (hostname.includes('news') || hostname.includes('blog')) contentType = 'news';
          else if (document.querySelector('article')) contentType = 'news';
          
          // Prepare analysis data for saving
          const analysisToSave = {
            url: currentUrl,
            title: currentTitle,
            hostname: hostname,
            ticker: symbol.toUpperCase(),
            analysis: analysis, // Full analysis object
            score: score,
            signals: signals,
            summaryText: summaryText,
            contentType: contentType,
            excerpt: currentTitle.substring(0, 280), // Simple excerpt from title
            faviconUrl: faviconUrl,
            pendingSync: true // Will be set to false after successful backend save
          };
          
          // Save locally first (always works, even offline)
          const savedAnalysis = await upsertSavedAnalysis(analysisToSave);
          const isUpdate = savedAnalysis.createdAt !== savedAnalysis.updatedAt;
          
          // Try backend save (best-effort, non-blocking)
          let backendSaveSuccess = false;
          let backendError = null;
          
          try {
            const authToken = await getAuthToken();
            if (authToken) {
              try {
                // Prepare snapshot with full analysis + metadata
                const snapshot = {
                  ...analysis,
                  url: currentUrl,
                  title: currentTitle,
                  hostname: hostname,
                  score: score,
                  signals: signals,
                  summaryText: summaryText,
                  contentType: contentType,
                  excerpt: analysisToSave.excerpt,
                  faviconUrl: faviconUrl,
                  analyzedAt: savedAnalysis.analyzedAt
                };
                
                const apiBaseUrl = await window.ragardConfig?.getApiBaseUrl() || 'http://localhost:8000';
                const response = await fetch(`${apiBaseUrl}/api/saved-analyses`, {
                  method: 'POST',
                  headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                  },
                  body: JSON.stringify({
                    ticker: symbol.toUpperCase(),
                    snapshot: snapshot
                  }),
                  mode: 'cors',
                  credentials: 'omit'
                });
                
                if (response.ok) {
                  backendSaveSuccess = true;
                  await markSynced(savedAnalysis.id);
                } else {
                  const errorText = await response.text().catch(() => 'Unknown error');
                  backendError = `Backend save failed (${response.status}): ${errorText}`;
                }
              } catch (backendErr) {
                backendError = backendErr.message;
                console.warn('[Ragard] Backend save error:', backendErr);
              }
            }
          } catch (authErr) {
            // Not logged in - that's fine, local save succeeded
            console.log('[Ragard] Not logged in, saved locally only');
          }
          
          // Show success state
          savePageBtn.disabled = false;
          savePageBtn.style.cursor = 'pointer';
          if (backendSaveSuccess) {
            savePageBtn.textContent = isUpdate ? '✓ Updated!' : '✓ Saved!';
          } else if (authState.isLoggedIn) {
            savePageBtn.textContent = '✓ Saved locally';
            console.warn('[Ragard] Backend save failed (local save succeeded):', backendError);
          } else {
            savePageBtn.textContent = '✓ Saved locally';
          }
          savePageBtn.style.background = 'rgba(34, 197, 94, 0.2)';
          savePageBtn.style.color = '#22c55e';
          
          // Reset button after 2 seconds
          setTimeout(() => {
            savePageBtn.textContent = originalText;
            savePageBtn.style.background = originalBg;
            savePageBtn.style.color = originalColor;
            savePageBtn.style.cursor = originalCursor;
          }, 2000);
          
        } catch (error) {
          // Show error state
          savePageBtn.disabled = false;
          savePageBtn.style.cursor = 'pointer';
          savePageBtn.textContent = 'Error saving';
          savePageBtn.style.background = 'rgba(239, 68, 68, 0.2)';
          savePageBtn.style.color = '#ef4444';
          
          const errorMsg = error.message || 'Could not save analysis';
          console.error('[Ragard] Save analysis error:', error);
          alert(errorMsg);
          
          // Reset button after 3 seconds
          setTimeout(() => {
            savePageBtn.textContent = originalText;
            savePageBtn.style.background = originalBg;
            savePageBtn.style.color = originalColor;
            savePageBtn.style.cursor = originalCursor;
          }, 3000);
        }
      });
    }
    
    // Analyze Another button
    const analyzeAnotherBtn = document.getElementById('ragard-analyze-another-btn');
    if (analyzeAnotherBtn) {
      analyzeAnotherBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        resetPanelToInitial();
      });
    }
  }

  // Reset panel to initial state
  function resetPanelToInitial() {
    const contentEl = document.getElementById('ragard-panel-content');
    if (!contentEl) return;
    
    contentEl.innerHTML = `
      <div style="color: #9ca3af; font-size: 12px; line-height: 1.5; text-align: center; padding: 20px 0;">
        <div style="margin-bottom: 12px;">Click the button below to analyze this page.</div>
        <button id="ragard-analyze-btn" style="width: 100%; padding: 12px 16px; border-radius: 999px; border: none; background: #22c55e; color: #020617; font-weight: 600; cursor: pointer; font-size: 13px; margin-top: 8px; box-shadow: 0 2px 8px rgba(34, 197, 94, 0.3); transition: all 0.2s; display: flex; align-items: center; justify-content: center;">
          Analyze Page
        </button>
      </div>
    `;
    
    const analyzeBtn = document.getElementById('ragard-analyze-btn');
    if (analyzeBtn) {
      analyzeBtn.addEventListener('click', () => {
        requestAnalysis();
      });
    }
  }

  // Show loading state
  function showLoading() {
    const contentEl = document.getElementById('ragard-panel-content');
    if (!contentEl) return;

    const analyzeBtn = document.getElementById('ragard-analyze-btn');
    if (analyzeBtn) {
      analyzeBtn.disabled = true;
    }

    contentEl.innerHTML = `
      <div class="ragard-loading" style="flex-direction: column; gap: 12px;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <div class="ragard-loading-dot"></div>
          <div class="ragard-loading-dot"></div>
          <div class="ragard-loading-dot"></div>
        </div>
        <div style="display: flex; flex-direction: column; align-items: center; gap: 6px;">
          <span style="font-size: 13px; font-weight: 500;">Analyzing page with Ragard...</span>
          <span style="font-size: 11px; color: #6b7280; text-align: center; line-height: 1.4;">Analysis may take longer if you switch tabs</span>
        </div>
      </div>
    `;
  }

  // Request analysis from current tab's content script
  async function requestAnalysis() {
    // CRITICAL DEBUG: Confirm this function is called
    console.log("[RAGARD] requestAnalysis called - analyze button clicked");
    
    // Generate new analysis ID
    const analysisId = ++nextAnalysisId;
    activeAnalysisId = analysisId;
    isAnalyzing = true;
    
    // Disable button and show loading immediately
    const analyzeBtn = document.getElementById('ragard-analyze-btn');
    if (analyzeBtn) {
      analyzeBtn.disabled = true;
    }
    showLoading();
    
    // Clear any existing timeouts
    if (activeTimeout) {
      clearTimeout(activeTimeout);
      activeTimeout = null;
    }
    if (activeStorageTimeout) {
      clearTimeout(activeStorageTimeout);
      activeStorageTimeout = null;
    }
    
    // Clear old analysis when starting new one
    chrome.storage.local.remove(['ragard_current_analysis']);
    
    try {
      // Get current active tab and store its ID/URL for verification
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tabs[0]) {
        throw new Error('No active tab found');
      }
      
      const tab = tabs[0];
      const analysisTabId = tab.id;
      const analysisUrl = tab.url;
      
      // Check cache first (optional - silent failure if storage unavailable)
      try {
        const cacheKey = `ragard_analysis_cache_${analysisUrl}`;
        const cacheResult = await new Promise((resolve) => {
          chrome.storage.local.get([cacheKey], (result) => {
            resolve(result[cacheKey]);
          });
        });
        
        if (cacheResult && cacheResult.data && cacheResult.timestamp) {
          const cacheAge = Date.now() - cacheResult.timestamp;
          const cacheTTL = 10 * 60 * 1000; // 10 minutes TTL
          
          // Check if this analysis is still current
          if (activeAnalysisId === analysisId && cacheAge < cacheTTL) {
            console.log('[RAGARD] Using cached analysis result');
            // Get title from the tab when caching
            let cachedTitle = null;
            try {
              const tab = await chrome.tabs.get(analysisTabId);
              cachedTitle = tab.title || null;
            } catch (e) {
              // Ignore if tab not available
            }
            
            chrome.storage.local.set({
              ragard_current_analysis: {
                data: cacheResult.data,
                timestamp: Date.now(),
                url: analysisUrl,
                title: cachedTitle
              }
            });
            
            // Render cached result
            renderAnalysis(cacheResult.data).catch(err => {
              console.error('[Ragard] Error rendering cached analysis:', err);
              if (activeAnalysisId === analysisId) {
                showError('Error rendering cached analysis results.');
              }
            });
            
            // Clear analysis state
            if (activeAnalysisId === analysisId) {
              activeAnalysisId = null;
              isAnalyzing = false;
            }
            return;
          }
        }
      } catch (cacheErr) {
        // Silently fail cache check - continue with fresh analysis
        console.log('[RAGARD] Cache check failed, continuing with fresh analysis');
      }
      
      // Store the analysis context so we can verify results match
      chrome.storage.local.set({
        ragard_analysis_in_progress: {
          tabId: analysisTabId,
          url: analysisUrl,
          timestamp: Date.now()
        }
      });
      
      // Check if content script is available, inject if needed
      let contentScriptReady = false;
      try {
        // Try to ping the content script
        await chrome.tabs.sendMessage(tab.id, { type: 'PING' });
        contentScriptReady = true;
      } catch (e) {
        // Content script not ready, try to inject it
        try {
          await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ['contentScript.js']
          });
          // Wait a bit for script to initialize
          await new Promise(resolve => setTimeout(resolve, 300));
          contentScriptReady = true;
        } catch (injectErr) {
          console.error('[Ragard] Could not inject content script:', injectErr);
          chrome.storage.local.remove(['ragard_analysis_in_progress']);
          showError('Could not access page content. Please refresh the page and try again.');
          return;
        }
      }
      
      // Poll storage periodically to check if result arrived (in case callback doesn't fire)
      // Declare outside so it's accessible in callback
      let storageCheckInterval = setInterval(() => {
        // Check if this analysis is still current
        if (activeAnalysisId !== analysisId) {
          if (storageCheckInterval) {
            clearInterval(storageCheckInterval);
            storageCheckInterval = null;
          }
          return;
        }
        
        chrome.storage.local.get(['ragard_current_analysis', 'ragard_analysis_in_progress'], (result) => {
          const inProgress = result.ragard_analysis_in_progress;
          const storedAnalysis = result.ragard_current_analysis;
          
          // Check again if analysis is still current
          if (activeAnalysisId !== analysisId) {
            return;
          }
          
          // If we have a stored analysis for the URL we're analyzing, render it
          if (storedAnalysis && storedAnalysis.url === analysisUrl && storedAnalysis.data) {
            // Got the result via storage - render if not already rendered
            if (lastRenderedAnalysisUrl !== analysisUrl) {
              if (storageCheckInterval) {
                clearInterval(storageCheckInterval);
                storageCheckInterval = null;
              }
              if (activeTimeout) {
                clearTimeout(activeTimeout);
                activeTimeout = null;
              }
              chrome.storage.local.remove(['ragard_analysis_in_progress']);
              
              // Final check before rendering
              if (activeAnalysisId === analysisId) {
                renderAnalysis(storedAnalysis.data).catch(err => {
                  console.error('[Ragard] Error rendering analysis:', err);
                  if (activeAnalysisId === analysisId) {
                    showError('Error rendering analysis results.');
                  }
                });
                lastRenderedAnalysisUrl = analysisUrl;
                lastRenderedAnalysisTimestamp = storedAnalysis.timestamp || Date.now();
                
                // Clear analysis state
                if (activeAnalysisId === analysisId) {
                  activeAnalysisId = null;
                  isAnalyzing = false;
                }
                
                // Cache result (optional - silent failure if storage unavailable)
                try {
                  const cacheKey = `ragard_analysis_cache_${analysisUrl}`;
                  chrome.storage.local.set({
                    [cacheKey]: {
                      data: storedAnalysis.data,
                      timestamp: Date.now()
                    }
                  });
                } catch (cacheErr) {
                  // Silently fail cache write
                  console.log('[RAGARD] Cache write failed (non-critical)');
                }
              }
            }
          }
          
          // If analysis is no longer in progress, stop checking
          if (!inProgress || inProgress.tabId !== analysisTabId) {
            if (storageCheckInterval) {
              clearInterval(storageCheckInterval);
              storageCheckInterval = null;
            }
          }
        });
      }, 500); // Check every 500ms
      
      // Set up extended timeout warning (60 seconds) - show message but keep polling
      let timeoutWarningShown = false;
      activeTimeout = setTimeout(() => {
        // Check if this analysis is still current
        if (activeAnalysisId !== analysisId) {
          activeTimeout = null;
          return;
        }
        
        // Before showing warning, check if we got the result via storage
        chrome.storage.local.get(['ragard_current_analysis', 'ragard_analysis_in_progress'], (result) => {
          const inProgress = result.ragard_analysis_in_progress;
          const storedAnalysis = result.ragard_current_analysis;
          
          // Check again if analysis is still current
          if (activeAnalysisId !== analysisId) {
            activeTimeout = null;
            return;
          }
          
          // If we have a stored analysis for the URL we're analyzing, clear timeout
          if (storedAnalysis && storedAnalysis.url === analysisUrl && storedAnalysis.data) {
            activeTimeout = null;
            return;
          }
          
          // If analysis is still in progress, show warning but keep polling
          if (inProgress && inProgress.tabId === analysisTabId && !timeoutWarningShown) {
            timeoutWarningShown = true;
            // Update loading message to indicate it's taking longer with cancel button
            const contentEl = document.getElementById('ragard-panel-content');
            if (contentEl && activeAnalysisId === analysisId) {
              contentEl.innerHTML = `
                <div class="ragard-loading">
                  <div style="text-align: center;">
                    <div style="margin-bottom: 8px; font-weight: 600;">Still analyzing...</div>
                    <div style="font-size: 11px; color: #6b7280; margin-bottom: 16px;">This page is taking longer than usual. Please wait.</div>
                    <div style="display: flex; gap: 4px; justify-content: center; margin-bottom: 16px;">
                      <div class="ragard-loading-dot"></div>
                      <div class="ragard-loading-dot"></div>
                      <div class="ragard-loading-dot"></div>
                    </div>
                    <button id="ragard-cancel-analysis-btn" style="padding: 8px 16px; border-radius: 6px; border: 1px solid rgba(148, 163, 184, 0.3); background: rgba(148, 163, 184, 0.1); color: #9ca3af; font-weight: 600; cursor: pointer; font-size: 12px;">
                      Cancel Analysis
                    </button>
                  </div>
                </div>
              `;
              
              // Add cancel button handler
              const cancelBtn = document.getElementById('ragard-cancel-analysis-btn');
              if (cancelBtn) {
                cancelBtn.addEventListener('click', () => {
                  if (activeAnalysisId === analysisId) {
                    // Clear timeouts and intervals
                    if (storageCheckInterval) {
                      clearInterval(storageCheckInterval);
                      storageCheckInterval = null;
                    }
                    if (activeTimeout) {
                      clearTimeout(activeTimeout);
                      activeTimeout = null;
                    }
                    // Remove in-progress flag
                    chrome.storage.local.remove(['ragard_analysis_in_progress']);
                    // Reset state
                    activeAnalysisId = null;
                    isAnalyzing = false;
                    // Reset UI
                    resetPanelToInitial();
                  }
                });
              }
            }
            // Don't clear timeout or stop polling - keep waiting for result
            // Set another timeout for absolute maximum (5 minutes)
            setTimeout(() => {
              if (activeAnalysisId === analysisId) {
                chrome.storage.local.get(['ragard_current_analysis', 'ragard_analysis_in_progress'], (finalCheck) => {
                  const finalInProgress = finalCheck.ragard_analysis_in_progress;
                  const finalStored = finalCheck.ragard_current_analysis;
                  
                  if (activeAnalysisId !== analysisId) return;
                  
                  // If we still don't have result after 5 minutes, show error
                  if (finalInProgress && finalInProgress.tabId === analysisTabId && 
                      (!finalStored || finalStored.url !== analysisUrl)) {
                    chrome.storage.local.remove(['ragard_analysis_in_progress']);
                    if (storageCheckInterval) {
                      clearInterval(storageCheckInterval);
                      storageCheckInterval = null;
                    }
                    if (activeAnalysisId === analysisId) {
                      showError('Analysis is taking too long. The page might be too large or the backend is experiencing issues. Please try again.');
                      activeAnalysisId = null;
                      isAnalyzing = false;
                    }
                  }
                });
              }
            }, 4 * 60 * 1000); // 4 more minutes (5 minutes total)
          }
        });
      }, 60000); // 60 second warning
      
      // Send message to content script to extract page content and analyze
      chrome.tabs.sendMessage(tab.id, {
        type: 'EXTRACT_AND_ANALYZE'
      }, (response) => {
        // Clear polling interval and timeout if callback fires
        clearInterval(storageCheckInterval);
        if (activeTimeout) {
          clearTimeout(activeTimeout);
          activeTimeout = null;
        }
        
        // Verify this response is for the tab we started the analysis on
        chrome.storage.local.get(['ragard_analysis_in_progress'], (progressResult) => {
          const inProgress = progressResult.ragard_analysis_in_progress;
          
          // If no in-progress flag or tab ID doesn't match, ignore this response
          if (!inProgress || inProgress.tabId !== analysisTabId) {
            return; // Silently ignore - storage listener will handle it
          }
          
          if (chrome.runtime.lastError) {
            const errorMsg = chrome.runtime.lastError.message;
            // Don't show error if tab was closed/switched - this is expected
            if (!errorMsg.includes('Receiving end does not exist') && 
                !errorMsg.includes('message port closed')) {
              // Clear in-progress flag and show error
              chrome.storage.local.remove(['ragard_analysis_in_progress']);
              if (errorMsg.includes('Could not establish connection')) {
                showError('Could not communicate with page. Please refresh the page and try again.');
              } else {
                showError('Error: ' + errorMsg);
              }
            }
            return;
          }
          
          // Check if this analysis is still current
          if (activeAnalysisId !== analysisId) {
            console.log('[RAGARD] Analysis ID mismatch, discarding results (newer analysis in progress)');
            return;
          }
          
          if (response && response.success) {
            // FAST PATH: Render immediately from callback (no storage delay)
            // This is the old fast path - renders as soon as we get the response
            chrome.storage.local.remove(['ragard_analysis_in_progress']);
            
            // Use response.data if available, otherwise wait for storage (content script stores it)
            if (response.data) {
              // Check again before rendering (user might have clicked again)
              if (activeAnalysisId !== analysisId) {
                console.log('[RAGARD] Analysis ID changed before render, discarding');
                return;
              }
              
              // Render immediately from callback data
              renderAnalysis(response.data).catch(err => {
                console.error('[Ragard] Error rendering analysis:', err);
                if (activeAnalysisId === analysisId) {
                  showError('Error rendering analysis results.');
                }
              });
              
              // Store result for cross-tab sync (but don't wait for it)
              // Get title from the tab (async, don't block)
              chrome.tabs.get(analysisTabId, (tab) => {
                const analysisTitle = tab?.title || null;
                chrome.storage.local.set({
                  ragard_current_analysis: {
                    data: response.data,
                    timestamp: Date.now(),
                    url: analysisUrl,
                    title: analysisTitle
                  }
                });
              });
              
              // Cache result (optional - silent failure if storage unavailable)
              try {
                const cacheKey = `ragard_analysis_cache_${analysisUrl}`;
                chrome.storage.local.set({
                  [cacheKey]: {
                    data: response.data,
                    timestamp: Date.now()
                  }
                });
              } catch (cacheErr) {
                // Silently fail cache write
                console.log('[RAGARD] Cache write failed (non-critical)');
              }
              
              // Track that we rendered this analysis
              lastRenderedAnalysisUrl = analysisUrl;
              lastRenderedAnalysisTimestamp = Date.now();
              
              // Clear analysis state
              if (activeAnalysisId === analysisId) {
                activeAnalysisId = null;
                isAnalyzing = false;
              }
            } else {
              // No data in callback, content script is storing it - wait for storage listener
              // This shouldn't happen normally, but handle gracefully
              console.log('[Ragard] Callback success but no data, waiting for storage...');
            }
          } else if (response && !response.success) {
            // Analysis failed - clear in-progress and show error
            chrome.storage.local.remove(['ragard_analysis_in_progress']);
            if (activeAnalysisId === analysisId) {
              showError(response?.error || 'Failed to analyze page');
              activeAnalysisId = null;
              isAnalyzing = false;
            }
          } else if (!response) {
            // No response at all - might be a timeout or connection issue
            // Don't show error here, let timeout handler deal with it
            console.log('[Ragard] No response from content script, waiting for storage or timeout...');
          }
        });
      });
    } catch (err) {
      if (storageCheckInterval) {
        clearInterval(storageCheckInterval);
        storageCheckInterval = null;
      }
      if (activeTimeout) {
        clearTimeout(activeTimeout);
        activeTimeout = null;
      }
      chrome.storage.local.remove(['ragard_analysis_in_progress']);
      
      // Only show error if this is still the current analysis
      if (activeAnalysisId === analysisId) {
        console.error('Ragard analysis error:', err);
        showError(err.message || 'Failed to analyze page');
        activeAnalysisId = null;
        isAnalyzing = false;
      }
    }
  }

  async function showError(errorMsg) {
    const contentEl = document.getElementById('ragard-panel-content');
    if (!contentEl) return;
    
    // Re-enable button on error
    const analyzeBtn = document.getElementById('ragard-analyze-btn');
    if (analyzeBtn) {
      analyzeBtn.disabled = false;
    }
    
    let message = errorMsg || 'Failed to analyze page';
    if (message.includes('Failed to fetch') || message.includes('NetworkError')) {
      const apiBaseUrl = await window.ragardConfig?.getApiBaseUrl() || 'http://localhost:8000';
      message = `Cannot connect to backend. Make sure FastAPI is running on ${apiBaseUrl}`;
    }
    
    contentEl.innerHTML = `
      <div class="ragard-error">
        <div style="font-weight: 600; margin-bottom: 4px;">Error</div>
        <div style="font-size: 12px;">${message}</div>
        <button id="ragard-retry-btn" style="width: 100%; padding: 8px 12px; margin-top: 12px; border-radius: 999px; border: none; background: #22c55e; color: #020617; font-weight: 600; cursor: pointer; font-size: 12px;">
          Retry
        </button>
      </div>
    `;
    
    const retryBtn = document.getElementById('ragard-retry-btn');
    if (retryBtn) {
      retryBtn.addEventListener('click', requestAnalysis);
    }
  }

  // Show settings
  function showSettings() {
    const contentEl = document.getElementById('ragard-panel-content');
    if (!contentEl) return;
    
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const domain = tabs[0] ? new URL(tabs[0].url || '').hostname : '';
      const isDisabled = preferences.disabledDomains.includes(domain);
      
      contentEl.innerHTML = `
        <div style="padding: 16px;">
          <div style="font-weight: 600; font-size: 14px; color: #e5e7eb; margin-bottom: 16px;">Settings</div>
          
          <div style="margin-bottom: 16px;">
            <div style="font-size: 12px; color: #9ca3af; margin-bottom: 8px;">Disable Ragard on this site</div>
            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
              <input type="checkbox" id="ragard-disable-domain" ${isDisabled ? 'checked' : ''} style="cursor: pointer;">
              <span style="font-size: 12px; color: #e5e7eb;">Disable on ${domain}</span>
            </label>
          </div>
          
          <div style="margin-bottom: 16px;">
            <div style="font-size: 12px; color: #9ca3af; margin-bottom: 8px; font-weight: 600;">API Configuration</div>
            <div style="margin-bottom: 8px;">
              <label style="display: block; font-size: 11px; color: #9ca3af; margin-bottom: 4px;">API Base URL</label>
              <input type="text" id="ragard-api-url" placeholder="http://localhost:8000" style="width: 100%; padding: 6px 8px; background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 4px; color: #e5e7eb; font-size: 11px; font-family: monospace;">
            </div>
            <div style="margin-bottom: 12px;">
              <label style="display: block; font-size: 11px; color: #9ca3af; margin-bottom: 4px;">Web App Base URL</label>
              <input type="text" id="ragard-web-app-url" placeholder="http://localhost:3000" style="width: 100%; padding: 6px 8px; background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 4px; color: #e5e7eb; font-size: 11px; font-family: monospace;">
            </div>
          </div>
          
          <div style="margin-bottom: 16px;">
            <div style="font-size: 12px; color: #9ca3af; margin-bottom: 8px;">Show sections</div>
            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; margin-bottom: 6px;">
              <input type="checkbox" id="ragard-show-tickers" ${preferences.showTickers ? 'checked' : ''} style="cursor: pointer;">
              <span style="font-size: 12px; color: #e5e7eb;">Tickers in this page/post</span>
            </label>
            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; margin-bottom: 6px;">
              <input type="checkbox" id="ragard-show-narratives" ${preferences.showNarratives ? 'checked' : ''} style="cursor: pointer;">
              <span style="font-size: 12px; color: #e5e7eb;">Narratives in this content</span>
            </label>
            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; margin-bottom: 6px;">
              <input type="checkbox" id="ragard-show-history" ${preferences.showHistory ? 'checked' : ''} style="cursor: pointer;">
              <span style="font-size: 12px; color: #e5e7eb;">Your history</span>
            </label>
            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
              <input type="checkbox" id="ragard-show-seen-often" ${preferences.showSeenOften ? 'checked' : ''} style="cursor: pointer;">
              <span style="font-size: 12px; color: #e5e7eb;">Seen often suggestions</span>
            </label>
          </div>
          
          <button id="ragard-settings-save" style="width: 100%; padding: 10px; background: #22c55e; color: #020617; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 12px; margin-top: 12px;">
            Save Settings
          </button>
          
          <button id="ragard-settings-back" style="width: 100%; padding: 10px; background: transparent; color: #9ca3af; border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 12px; margin-top: 8px;">
            Back
          </button>
        </div>
      `;
      
      // Load current config values
      (async () => {
        const apiUrl = await window.ragardConfig?.getApiBaseUrl() || 'http://localhost:8000';
        const webAppUrl = await window.ragardConfig?.getWebAppBaseUrl() || 'http://localhost:3000';
        document.getElementById('ragard-api-url').value = apiUrl;
        document.getElementById('ragard-web-app-url').value = webAppUrl;
      })();
      
      // Save button
      document.getElementById('ragard-settings-save').addEventListener('click', async () => {
        chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
          const domain = tabs[0] ? new URL(tabs[0].url || '').hostname : '';
          const disableDomain = document.getElementById('ragard-disable-domain').checked;
          
          if (disableDomain && !preferences.disabledDomains.includes(domain)) {
            preferences.disabledDomains.push(domain);
          } else if (!disableDomain) {
            preferences.disabledDomains = preferences.disabledDomains.filter(d => d !== domain);
          }
          
          preferences.showTickers = document.getElementById('ragard-show-tickers').checked;
          preferences.showNarratives = document.getElementById('ragard-show-narratives').checked;
          preferences.showHistory = document.getElementById('ragard-show-history').checked;
          preferences.showSeenOften = document.getElementById('ragard-show-seen-often').checked;
          
          // Save API URLs
          const apiUrl = document.getElementById('ragard-api-url').value.trim();
          const webAppUrl = document.getElementById('ragard-web-app-url').value.trim();
          if (apiUrl && window.ragardConfig) {
            await window.ragardConfig.setApiBaseUrl(apiUrl);
          }
          if (webAppUrl && window.ragardConfig) {
            await window.ragardConfig.setWebAppBaseUrl(webAppUrl);
          }
          
          chrome.storage.local.set({ ragard_preferences: preferences }, () => {
            resetPanelToInitial();
          });
        });
      });
      
      // Back button
      document.getElementById('ragard-settings-back').addEventListener('click', () => {
        resetPanelToInitial();
      });
    });
  }

  function init() {
    console.log('[Ragard] Side panel loaded');
    
    // Check auth status on init (non-blocking, force refresh to get latest) - SEPARATE from analyze logic
    // This runs independently and does NOT affect the analyze button
    checkAuthStatus(true).then(() => {
      // After auth check, try to sync pending analyses
      syncPendingAnalyses().catch(err => {
        console.warn('[Ragard] Initial sync failed:', err);
      });
    }).catch(err => {
      console.warn('[Ragard] Initial auth check failed:', err);
    });
    
    // Also set up periodic refresh of auth status (every 30 seconds)
    setInterval(() => {
      checkAuthStatus(true).then(() => {
        // Sync pending analyses periodically
        syncPendingAnalyses().catch(err => {
          console.warn('[Ragard] Periodic sync failed:', err);
        });
      }).catch(err => {
        console.warn('[Ragard] Periodic auth check failed:', err);
      });
    }, 30000); // 30 seconds
    
    // Settings button
    const settingsBtn = document.getElementById('ragard-settings-btn');
    if (settingsBtn) {
      settingsBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        showSettings();
      });
    }
    
    // Analyze button - DO NOT MODIFY THIS HANDLER
    const analyzeBtn = document.getElementById('ragard-analyze-btn');
    if (analyzeBtn) {
      analyzeBtn.addEventListener('click', () => {
        console.log('[RAGARD] Analyze button clicked in init()');
        requestAnalysis();
      });
    }
    
    // Restore stored analysis if available (universal panel - shows last analysis regardless of active tab)
    // But only if there's no analysis in progress
    chrome.storage.local.get(['ragard_current_analysis', 'ragard_analysis_in_progress'], (result) => {
      // If there's an analysis in progress, show loading instead of old analysis
      if (result.ragard_analysis_in_progress) {
        showLoading();
        return;
      }
      
      if (result.ragard_current_analysis && result.ragard_current_analysis.data) {
        (async () => {
          try {
            await renderAnalysis(result.ragard_current_analysis.data);
          } catch (err) {
            console.warn('[Ragard] Error rendering stored analysis:', err);
            resetPanelToInitial();
          }
        })();
      } else {
        // No cached analysis, show initial state
        resetPanelToInitial();
      }
    });
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

