/**
 * Ragard Chrome Extension - Content Script
 * Extracts page content and sends to side panel for analysis
 * No UI injection - all UI is in the side panel
 */

(function() {
  'use strict';
  
  // Load page context helpers (inline to avoid separate file loading issues)
  const PageContextType = {
    REDDIT_SOCIAL: 'reddit_social',
    TWITTER_SOCIAL: 'twitter_social',
    STOCKTWITS_SOCIAL: 'stocktwits_social',
    GENERIC_SOCIAL: 'generic_social',
    ARTICLE: 'article',
    GENERIC: 'generic'
  };
  
  // Page context detection and author extraction functions (from pageContext.js)
  function getPageContextType(hostname, document) {
    try {
      const hostnameLower = hostname.toLowerCase();
      if (hostnameLower.includes('reddit.com')) return PageContextType.REDDIT_SOCIAL;
      if (hostnameLower.includes('twitter.com') || hostnameLower.includes('x.com')) return PageContextType.TWITTER_SOCIAL;
      if (hostnameLower.includes('stocktwits.com')) return PageContextType.STOCKTWITS_SOCIAL;
      
      const hasArticle = document.querySelector('article');
      const ogType = document.querySelector('meta[property="og:type"]')?.getAttribute('content')?.toLowerCase();
      const hasAuthorMeta = document.querySelector('meta[name="author"]');
      
      if (hasArticle || ogType === 'article' || hasAuthorMeta) {
        if (hasArticle) {
          const articleText = hasArticle.innerText || hasArticle.textContent || '';
          if (articleText.trim().length > 200) return PageContextType.ARTICLE;
        } else if (ogType === 'article' || hasAuthorMeta) {
          return PageContextType.ARTICLE;
        }
      }
      
      return PageContextType.GENERIC;
    } catch (e) {
      return PageContextType.GENERIC;
    }
  }
  
  function extractAuthorContext(contextType, document, location) {
    try {
      const baseContext = {
        platform: 'generic',
        authorDisplayName: null,
        authorHandle: null,
        authorProfileUrl: null,
        authorMetadata: {}
      };
      
      switch (contextType) {
        case PageContextType.REDDIT_SOCIAL:
          return extractRedditAuthor(document, location, baseContext);
        case PageContextType.TWITTER_SOCIAL:
          return extractTwitterAuthor(document, location, baseContext);
        case PageContextType.STOCKTWITS_SOCIAL:
          return extractStocktwitsAuthor(document, location, baseContext);
        case PageContextType.ARTICLE:
          return extractArticleAuthor(document, location, baseContext);
        default:
          return extractGenericAuthor(document, location, baseContext);
      }
    } catch (e) {
      return { platform: 'generic', authorDisplayName: null, authorHandle: null, authorProfileUrl: null, authorMetadata: {} };
    }
  }
  
  function extractRedditAuthor(document, location, baseContext) {
    try {
      baseContext.platform = 'reddit';
      const authorLink = document.querySelector('a[href*="/user/"]') ||
                        document.querySelector('a[data-testid="post_author_link"]') ||
                        document.querySelector('a[href^="/u/"]');
      if (authorLink) {
        const href = authorLink.getAttribute('href') || '';
        const match = href.match(/\/u(?:ser)?\/([^/?#]+)/);
        if (match) {
          const username = match[1];
          baseContext.authorHandle = `u/${username}`;
          baseContext.authorDisplayName = username;
          baseContext.authorProfileUrl = `https://www.reddit.com/user/${username}`;
        }
      }
      return baseContext;
    } catch (e) {
      return baseContext;
    }
  }
  
  function extractTwitterAuthor(document, location, baseContext) {
    try {
      baseContext.platform = 'twitter';
      const authorLink = document.querySelector('[data-testid="User-Name"] a') ||
                        document.querySelector('article a[href^="/"]');
      if (authorLink) {
        const href = authorLink.getAttribute('href') || '';
        const match = href.match(/^\/([^/]+)/);
        if (match) {
          const handle = match[1];
          baseContext.authorHandle = `@${handle}`;
          baseContext.authorDisplayName = handle;
          baseContext.authorProfileUrl = `https://twitter.com/${handle}`;
        }
      }
      return baseContext;
    } catch (e) {
      return baseContext;
    }
  }
  
  function extractStocktwitsAuthor(document, location, baseContext) {
    try {
      baseContext.platform = 'stocktwits';
      const urlMatch = location.pathname.match(/\/user\/([^/]+)/);
      if (urlMatch) {
        const username = urlMatch[1];
        baseContext.authorHandle = `@${username}`;
        baseContext.authorDisplayName = username;
        baseContext.authorProfileUrl = `https://stocktwits.com/${username}`;
      }
      return baseContext;
    } catch (e) {
      return baseContext;
    }
  }
  
  function extractArticleAuthor(document, location, baseContext) {
    try {
      baseContext.platform = 'article_site';
      const hostname = location.hostname.toLowerCase();
      
      // Extract author name from multiple sources
      const authorMeta = document.querySelector('meta[name="author"]');
      if (authorMeta) {
        baseContext.authorDisplayName = authorMeta.getAttribute('content')?.trim();
      }
      
      // Try JSON-LD structured data
      try {
        const jsonLdScripts = document.querySelectorAll('script[type="application/ld+json"]');
        for (const script of jsonLdScripts) {
          try {
            const data = JSON.parse(script.textContent);
            if (data['@type'] === 'NewsArticle' || data['@type'] === 'Article') {
              if (data.author) {
                if (typeof data.author === 'string') {
                  baseContext.authorDisplayName = data.author;
                } else if (data.author.name) {
                  baseContext.authorDisplayName = data.author.name;
                  if (data.author.url) {
                    baseContext.authorProfileUrl = data.author.url;
                  }
                }
              }
            }
          } catch (e) {
            // Skip invalid JSON
          }
        }
      } catch (e) {
        // Silently fail
      }
      
      // Try common byline selectors
      const byline = document.querySelector('.byline, [itemprop="author"], .author, article .author, .article-author, [data-author]');
      if (byline) {
        const link = byline.querySelector('a');
        if (link) {
          baseContext.authorProfileUrl = link.href;
          baseContext.authorDisplayName = link.textContent.trim() || baseContext.authorDisplayName;
        } else {
          const text = byline.textContent?.trim();
          if (text && !baseContext.authorDisplayName) {
            baseContext.authorDisplayName = text;
          }
        }
      }
      
      // Extract raw byline text
      if (byline) {
        baseContext.rawByline = byline.textContent?.trim();
      }
      
      // Determine domain reputation
      const highReputationDomains = [
        'wsj.com', 'bloomberg.com', 'reuters.com', 'ft.com', 'cnbc.com', 'nytimes.com',
        'forbes.com', 'marketwatch.com', 'fool.com', 'seekingalpha.com', 'yahoo.com',
        'nasdaq.com', 'investing.com', 'barrons.com', 'economist.com'
      ];
      const mediumReputationDomains = [
        'motleyfool.com', 'fool.com', 'benzinga.com', 'thestreet.com', 'zacks.com'
      ];
      
      let domainReputation = 'low';
      if (highReputationDomains.some(d => hostname.includes(d))) {
        domainReputation = 'high';
      } else if (mediumReputationDomains.some(d => hostname.includes(d))) {
        domainReputation = 'medium';
      } else if (document.querySelector('article')) {
        domainReputation = 'medium';
      }
      
      baseContext.authorMetadata = baseContext.authorMetadata || {};
      baseContext.authorMetadata.domainReputation = domainReputation;
      baseContext.authorMetadata.domain = hostname;
      
      // Detect article type
      const title = document.title?.toLowerCase() || '';
      const content = document.body?.textContent?.toLowerCase() || '';
      let articleType = 'news';
      if (title.includes('press release') || content.includes('press release')) {
        articleType = 'press_release';
      } else if (title.includes('opinion') || title.includes('editorial') || title.includes('op-ed')) {
        articleType = 'opinion';
      } else if (title.includes('analysis') || title.includes('research')) {
        articleType = 'analysis';
      }
      baseContext.authorMetadata.articleType = articleType;
      
      return baseContext;
    } catch (e) {
      return baseContext;
    }
  }
  
  function extractGenericAuthor(document, location, baseContext) {
    try {
      baseContext.platform = 'generic';
      const hostname = location.hostname;
      baseContext.authorDisplayName = hostname.replace(/^www\./, '');
      baseContext.authorProfileUrl = `${location.protocol}//${hostname}/`;
      return baseContext;
    } catch (e) {
      return baseContext;
    }
  }

  // Preferences
  let preferences = {
    disabledDomains: [],
  };

  // Load preferences
  chrome.storage.local.get(['ragard_preferences'], (result) => {
    if (result.ragard_preferences) {
      Object.assign(preferences, result.ragard_preferences);
    }
  });

  // Page content extraction (type-aware, works on all websites)
  function getPageContent(contextType, document, location) {
    const url = location.href;
    
    // Reddit: use existing specialized extraction
    if (contextType === PageContextType.REDDIT_SOCIAL) {
      return scrapeRedditPost();
    }
    
    // All other types: generic extraction
    try {
      let title = '';
      let content = '';
      
      // Try to get title
      const titleEl = document.querySelector('title') || 
                     document.querySelector('h1') ||
                     document.querySelector('[property="og:title"]');
      if (titleEl) {
        title = titleEl.textContent || titleEl.getAttribute('content') || '';
      }
      
      // Try common article containers
      const articleEl = document.querySelector('article') ||
                       document.querySelector('[role="main"]') ||
                       document.querySelector('main') ||
                       document.querySelector('.article') ||
                       document.querySelector('.content') ||
                       document.querySelector('#content');
      
      if (articleEl) {
        content = articleEl.innerText || articleEl.textContent || '';
      } else {
        // Fallback to body
        content = document.body.innerText || document.body.textContent || '';
      }
      
      // Truncate content to reasonable length (5000 chars)
      if (content.length > 5000) {
        content = content.substring(0, 5000) + '...';
      }
      
      return {
        url,
        title: title.trim(),
        content: content.trim(),
        source: contextType === PageContextType.ARTICLE ? 'article' : 'generic_webpage'
      };
    } catch (e) {
      console.warn('[Ragard] Error extracting page content:', e);
      return {
        url,
        title: document.title || '',
        content: document.body?.innerText?.substring(0, 5000) || '',
        source: 'generic_webpage_fallback'
      };
    }
  }
  
  // Scrape Reddit post data (existing function - keep as-is)
  function scrapeRedditPost() {
    const url = window.location.href;
    
    // Extract subreddit
    let subreddit = null;
    const subredditLink = document.querySelector('a[data-testid="subreddit-name"]') || 
                         document.querySelector('a[href^="/r/"]');
    if (subredditLink) {
      const href = subredditLink.getAttribute('href') || '';
      const match = href.match(/\/r\/([^/]+)/);
      if (match) {
        subreddit = match[1];
      } else {
        subreddit = subredditLink.innerText?.replace('r/', '') || null;
      }
    }
    // Fallback: parse from URL
    if (!subreddit) {
      const urlMatch = url.match(/\/r\/([^/]+)/);
      if (urlMatch) {
        subreddit = urlMatch[1];
      }
    }

    // Extract title
    let title = null;
    const titleEl = document.querySelector('h1[data-testid="post-title"]') ||
                   document.querySelector('h1._eYtD2XCVieq6emjKBH3m') ||
                   document.querySelector('a[data-click-id="body"] h3') ||
                   document.querySelector('h1');
    if (titleEl) {
      title = titleEl.innerText?.trim() || null;
    }

    // Extract author
    let author = null;
    const authorLink = document.querySelector('a[href*="/user/"]') ||
                       document.querySelector('a[data-testid="post_author_link"]');
    if (authorLink) {
      const href = authorLink.getAttribute('href') || '';
      const match = href.match(/\/user\/([^/]+)/);
      if (match) {
        author = match[1];
      } else {
        author = authorLink.innerText?.replace('u/', '') || null;
      }
    }

    // Extract body snippet
    let bodySnippet = '';
    const postContent = document.querySelector('div[data-testid="post-content"]') ||
                       document.querySelector('[data-click-id="text"]') ||
                       document.querySelector('.usertext-body') ||
                       document.querySelector('[data-testid="post-content"] p');
    if (postContent) {
      bodySnippet = postContent.innerText?.trim().substring(0, 500) || '';
    }

    return {
      url,
      subreddit,
      title,
      author,
      body_snippet: bodySnippet
    };
  }

  // =================================================================
  // 0) SAFE WRAPPER AROUND EXISTING ANALYSIS (LEGACY FALLBACK)
  // =================================================================
  
  // Legacy implementation - moved from extractAndAnalyze
  async function extractAndAnalyzeLegacy() {
    try {
      // Detect page context type
      const contextType = getPageContextType(window.location.hostname, document);
      
      // Extract page content (type-aware)
      const pageData = getPageContent(contextType, document, window.location);
      
      // Extract author context (type-aware)
      const authorContext = extractAuthorContext(contextType, document, window.location);
      
      // Build payload with backward-compatible fields
      const payload = {
        ...pageData,
        source: "chrome_extension_v1",
        contextType: contextType,
        authorContext: authorContext,
        // Keep existing fields for backward compatibility
        subreddit: pageData.subreddit || null,
        author: authorContext.authorHandle || authorContext.authorDisplayName || pageData.author || null,
        body_snippet: pageData.body_snippet || pageData.content?.substring(0, 500) || null,
        // Add content field for non-Reddit pages
        content: pageData.content || pageData.body_snippet || null
      };

      const apiBaseUrl = await (window.ragardConfig?.getApiBaseUrl() || Promise.resolve('http://localhost:8000'));
      const endpoint = `${apiBaseUrl}/api/extension/analyze-reddit-post`;

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(payload),
        mode: 'cors',
        credentials: 'omit'
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`Backend error ${response.status}: ${text}`);
      }

      const data = await response.json();
      
      // Store analysis result in chrome.storage for side panel
      chrome.storage.local.set({
        ragard_current_analysis: {
          data: data,
          timestamp: Date.now(),
          url: window.location.href,
          title: document.title || window.location.href
        }
      });
      
      return { success: true, data: data };
    } catch (err) {
      console.error('Ragard analysis error:', err);
      let errorMsg = err.message || 'Failed to analyze page';
        if (errorMsg.includes('Failed to fetch') || errorMsg.includes('NetworkError')) {
          const apiBaseUrl = await (window.ragardConfig?.getApiBaseUrl() || Promise.resolve('http://localhost:8000'));
          errorMsg = `Cannot connect to backend. Make sure FastAPI is running on ${apiBaseUrl}`;
        }
      return { success: false, error: errorMsg };
    }
  }

  // =================================================================
  // 1) CENTRALIZED PAGE CONTENT EXTRACTION
  // =================================================================
  
  // PageContent structure
  function getPageContentStructured(document, location) {
    const url = location.href;
    const sourceHost = location.hostname;
    const title = document.title || "";

    // Prefer main content containers where possible
    let mainText = "";
    
    // Try article, main, or role="main" elements first
    const articleEl = document.querySelector('article') ||
                     document.querySelector('main') ||
                     document.querySelector('[role="main"]') ||
                     document.querySelector('.article') ||
                     document.querySelector('.content') ||
                     document.querySelector('#content');
    
    if (articleEl) {
      mainText = articleEl.innerText || articleEl.textContent || '';
    } else {
      // Fallback to body
      mainText = document.body.innerText || document.body.textContent || '';
    }
    
    // Normalize whitespace and trim
    mainText = mainText.replace(/\s+/g, ' ').trim();
    
    // Limit to 12,000 characters to keep analysis fast
    const maxLength = 12000;
    if (mainText.length > maxLength) {
      mainText = mainText.substring(0, maxLength);
    }

    return {
      url,
      title,
      content: mainText,
      sourceHost,
    };
  }

  // =================================================================
  // 2) SPLIT REDDIT VS NON-REDDIT PATHS
  // =================================================================
  
  function isRedditHost(hostname) {
    const h = hostname.toLowerCase();
    return h.endsWith('reddit.com') || h.includes('.reddit.com');
  }

  // =================================================================
  // 3) ADVANCED NON-REDDIT TICKER/CONTEXT RESOLUTION
  // =================================================================
  
  // Common English stopwords to filter out
  const STOPWORDS_SET = new Set([
    'A', 'AND', 'IT', 'ONE', 'FOR', 'YOU', 'THE', 'AN', 'OR', 'BUT', 'IN', 'ON', 'AT', 'TO',
    'OF', 'WITH', 'BY', 'FROM', 'AS', 'IS', 'WAS', 'ARE', 'WERE', 'BE', 'BEEN', 'BEING',
    'HAVE', 'HAS', 'HAD', 'DO', 'DOES', 'DID', 'WILL', 'WOULD', 'SHOULD', 'COULD', 'MAY',
    'MIGHT', 'MUST', 'CAN', 'THIS', 'THAT', 'THESE', 'THOSE', 'I', 'HE', 'SHE', 'WE', 'THEY',
    'WHAT', 'WHICH', 'WHO', 'WHEN', 'WHERE', 'WHY', 'HOW', 'ALL', 'EACH', 'EVERY', 'BOTH',
    'FEW', 'MORE', 'MOST', 'OTHER', 'SOME', 'SUCH', 'NO', 'NOR', 'NOT', 'ONLY', 'OWN', 'SAME',
    'SO', 'THAN', 'TOO', 'VERY', 'JUST', 'NOW', 'THEN', 'HERE', 'THERE'
  ]);

  // Local candidate extraction (cheap, fast, heuristic)
  function extractTickerCandidatesLocal(pageContent) {
    const candidates = new Set();
    
    // Combine title and first part of content (first 2000 chars for speed)
    const textSource = (pageContent.title + ' ' + pageContent.content.substring(0, 2000)).toUpperCase();
    
    // 1) Find $TICKER patterns
    const dollarPattern = /\$([A-Z]{1,5})\b/g;
    let match;
    while ((match = dollarPattern.exec(textSource)) !== null) {
      const symbol = match[1];
      if (symbol.length >= 1 && symbol.length <= 5) {
        candidates.add(symbol);
      }
    }
    
    // 2) Find standalone ALL-CAPS tokens (1-5 letters)
    const capsPattern = /\b([A-Z]{1,5})\b/g;
    while ((match = capsPattern.exec(textSource)) !== null) {
      const token = match[1];
      // Filter out stopwords
      if (!STOPWORDS_SET.has(token)) {
        // For 1-2 letter tokens, only add if they appear multiple times or have context
        if (token.length >= 3) {
          candidates.add(token);
        } else if (token.length <= 2) {
          // Only add 1-2 letter tokens if they appear at least twice (more likely to be tickers)
          const count = (textSource.match(new RegExp(`\\b${token}\\b`, 'g')) || []).length;
          if (count >= 2) {
            candidates.add(token);
          }
        }
      }
    }
    
    // Convert to array and remove duplicates
    return Array.from(candidates);
  }

  // Extract company name candidates from page
  function extractCompanyNameCandidates(pageContent, document, location) {
    const candidates = new Set();
    
    // Finance keywords that indicate company mentions
    const financeKeywords = /\b(stock|shares|earnings|revenue|market cap|analyst|price target|trading|investor|shareholder|dividend|ipo|merger|acquisition)\b/gi;
    
    // 1) Extract from title
    const title = pageContent.title || '';
    if (title) {
      // Look for proper nouns (capitalized words) near finance keywords
      const titleWords = title.split(/\s+/);
      for (let i = 0; i < titleWords.length; i++) {
        const word = titleWords[i].replace(/[^\w]/g, '');
        if (word.length >= 3 && word[0] === word[0].toUpperCase() && /^[A-Z]/.test(word)) {
          // Check if near finance keyword
          const context = titleWords.slice(Math.max(0, i-3), Math.min(titleWords.length, i+4)).join(' ');
          if (financeKeywords.test(context)) {
            candidates.add(word);
          }
        }
      }
    }
    
    // 2) Extract from URL slug
    const urlPath = location.pathname || '';
    const urlParts = urlPath.split('/').filter(p => p.length > 0);
    for (const part of urlParts) {
      // Look for company-like slugs (e.g., /nvidia-earnings, /apple-stock)
      const cleaned = part.replace(/[-_]/g, ' ').split(/\s+/);
      for (const word of cleaned) {
        if (word.length >= 3 && /^[A-Z]/.test(word)) {
          candidates.add(word);
        }
      }
    }
    
    // 3) Extract from first 1-3 paragraphs
    const firstParagraphs = pageContent.content.substring(0, 1500);
    const sentences = firstParagraphs.split(/[.!?]+/).slice(0, 3);
    for (const sentence of sentences) {
      // Look for patterns like "shares of Nvidia", "chipmaker Nvidia", "Nvidia stock"
      const patterns = [
        /\b(shares?|stock|equity)\s+of\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)/g,
        /\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(stock|shares?|earnings?|revenue)/g,
        /\b(chipmaker|maker|company|firm|corporation|corp|inc|llc)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)/g,
      ];
      
      for (const pattern of patterns) {
        let match;
        while ((match = pattern.exec(sentence)) !== null) {
          const companyName = match[2] || match[1];
          if (companyName && companyName.length >= 3) {
            // Clean up the name
            const cleaned = companyName.trim().split(/\s+/).filter(w => 
              w.length >= 2 && !['Inc', 'Corp', 'LLC', 'Ltd', 'The', 'A', 'An'].includes(w)
            ).join(' ');
            if (cleaned.length >= 3) {
              candidates.add(cleaned);
            }
          }
        }
      }
    }
    
    // 4) Try to extract from JSON-LD structured data
    try {
      const jsonLdScripts = document.querySelectorAll('script[type="application/ld+json"]');
      for (const script of jsonLdScripts) {
        try {
          const data = JSON.parse(script.textContent);
          if (data['@type'] === 'Organization' || data['@type'] === 'NewsArticle') {
            if (data.name) candidates.add(data.name);
            if (data.tickerSymbol) {
              // Extract company name from ticker symbol context if available
              const org = data.publisher || data.about;
              if (org && org.name) candidates.add(org.name);
            }
          }
        } catch (e) {
          // Skip invalid JSON
        }
      }
    } catch (e) {
      // Silently fail JSON-LD extraction
    }
    
    // Filter out common non-company words
    const nonCompanies = new Set(['The', 'This', 'That', 'These', 'Those', 'Company', 'Market', 'Stock', 'Share']);
    const filtered = Array.from(candidates).filter(c => 
      c.length >= 3 && 
      !nonCompanies.has(c) &&
      !STOPWORDS_SET.has(c.toUpperCase())
    );
    
    return filtered.slice(0, 10); // Limit to top 10
  }

  // Improved analysis with ticker resolution
  async function extractAndAnalyzeImproved() {
    try {
      console.log('[RAGARD] extractAndAnalyzeImproved called');
      
      // Get structured page content
      const pageContent = getPageContentStructured(document, window.location);
      const isReddit = isRedditHost(pageContent.sourceHost);
      
      // For Reddit, use legacy path to preserve existing behavior
      if (isReddit) {
        console.log('[RAGARD] Reddit page detected, using legacy path');
        return await extractAndAnalyzeLegacy();
      }
      
      // Non-Reddit logic
      console.log('[RAGARD] Non-Reddit page, using improved ticker resolution');
      
      // Detect page context type for author extraction
      const contextType = getPageContextType(window.location.hostname, document);
      const authorContext = extractAuthorContext(contextType, document, window.location);
      
      // A) Local candidate extraction (tickers + company names)
      const localCandidates = extractTickerCandidatesLocal(pageContent);
      const companyCandidates = extractCompanyNameCandidates(pageContent, document, window.location);
      console.log('[RAGARD] Local ticker candidates:', localCandidates);
      console.log('[RAGARD] Company name candidates:', companyCandidates);
      
      // B) Backend AI/contextual resolver with timeout
      let resolvedTickers = [];
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
        
        const apiBaseUrl = await (window.ragardConfig?.getApiBaseUrl() || Promise.resolve('http://localhost:8000'));
        const resolveResponse = await fetch(`${apiBaseUrl}/api/extension/resolve-tickers`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify({
            url: pageContent.url,
            title: pageContent.title,
            contentSnippet: pageContent.content.substring(0, 4000), // Limit snippet size
            sourceHost: pageContent.sourceHost,
            candidateSymbols: localCandidates,
            candidateCompanies: companyCandidates, // NEW: Include company names
          }),
          mode: 'cors',
          credentials: 'omit',
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!resolveResponse.ok) {
          throw new Error(`resolve-tickers failed with status ${resolveResponse.status}`);
        }
        
        const resolveData = await resolveResponse.json();
        resolvedTickers = Array.isArray(resolveData.resolvedTickers) ? resolveData.resolvedTickers : [];
        console.log('[RAGARD] Resolved tickers from backend:', resolvedTickers);
      } catch (resolveErr) {
        if (resolveErr.name === 'AbortError') {
          console.error('[RAGARD] Ticker resolution timed out, falling back to legacy');
        } else {
          console.error('[RAGARD] Ticker resolution failed, falling back to legacy:', resolveErr);
        }
        // Fall back to legacy if resolver fails or times out
        return await extractAndAnalyzeLegacy();
      }
      
      // C) Final ticker selection with primary/secondary roles
      // Filter by confidence threshold (>= 0.5) and sort by role (primary first) then confidence
      const filteredTickers = resolvedTickers
        .filter(t => t.confidence >= 0.5)
        .sort((a, b) => {
          // Primary tickers first
          if (a.role === 'primary' && b.role !== 'primary') return -1;
          if (a.role !== 'primary' && b.role === 'primary') return 1;
          // Then by confidence
          return b.confidence - a.confidence;
        })
        .slice(0, 10); // Limit to top 10
      
      // Extract symbols and preserve role information
      const tickerSymbols = filteredTickers.map(t => t.symbol);
      const primaryTicker = filteredTickers.find(t => t.role === 'primary')?.symbol || tickerSymbols[0];
      
      console.log('[RAGARD] Final filtered tickers:', tickerSymbols);
      console.log('[RAGARD] Primary ticker:', primaryTicker);
      
      // If no tickers pass threshold, show message
      if (tickerSymbols.length === 0) {
        // Return a response indicating no tickers detected
        const noTickersData = {
          ok: true,
          url: pageContent.url,
          subreddit: null,
          title: pageContent.title,
          author: authorContext.authorHandle || authorContext.authorDisplayName || null,
          detected_tickers: [],
          tickers: [],
          post_degen_score: 50, // Neutral score
          post_analysis: {
            ai_summary: 'No clear tickers detected for this page.',
            ai_degen_score: 50,
            ai_sentiment: 'neutral',
            ai_narrative_name: null,
          },
          author_analysis: authorContext ? {
            author: authorContext.authorDisplayName || authorContext.authorHandle,
            author_regard_score: 50,
            trust_level: 'medium',
            summary: `Content from ${authorContext.platform} platform`,
            signals: [],
            platform: authorContext.platform
          } : null,
          author_context: authorContext ? {
            platform: authorContext.platform,
            authorDisplayName: authorContext.authorDisplayName,
            authorHandle: authorContext.authorHandle,
            authorProfileUrl: authorContext.authorProfileUrl,
            authorMetadata: authorContext.authorMetadata || {}
          } : null,
          message: 'No clear tickers detected for this page.',
        };
        
        chrome.storage.local.set({
          ragard_current_analysis: {
            data: noTickersData,
            timestamp: Date.now(),
            url: window.location.href
          }
        });
        
        return { success: true, data: noTickersData };
      }
      
      // D) Pass resolved tickers to existing analysis pipeline
      // Build payload similar to legacy but with resolved tickers
      const payload = {
        url: pageContent.url,
        source: "chrome_extension_v1",
        contextType: contextType,
        authorContext: authorContext,
        subreddit: null,
        author: authorContext.authorHandle || authorContext.authorDisplayName || null,
        body_snippet: pageContent.content.substring(0, 500),
        content: pageContent.content,
        // Pass resolved tickers explicitly
        resolvedTickers: tickerSymbols,
        primaryTicker: primaryTicker, // NEW: Pass primary ticker info
      };

      const apiBaseUrl = await (window.ragardConfig?.getApiBaseUrl() || Promise.resolve('http://localhost:8000'));
      const endpoint = `${apiBaseUrl}/api/extension/analyze-reddit-post`;

      // Add timeout for main analysis call
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(payload),
        mode: 'cors',
        credentials: 'omit',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`Backend error ${response.status}: ${text}`);
      }

      const data = await response.json();
      
      // Add primary ticker info to response if available
      if (primaryTicker && data.tickers) {
        data.primaryTicker = primaryTicker;
        // Mark primary ticker in tickers array
        data.tickers = data.tickers.map(t => {
          if (t.symbol === primaryTicker) {
            return { ...t, isPrimary: true };
          }
          return t;
        });
      }
      
      // Store analysis result
      chrome.storage.local.set({
        ragard_current_analysis: {
          data: data,
          timestamp: Date.now(),
          url: window.location.href
        }
      });
      
      return { success: true, data: data };
    } catch (err) {
      console.error('[RAGARD] extractAndAnalyzeImproved error:', err);
      // Fall back to legacy on any error
      console.log('[RAGARD] Falling back to legacy analysis');
      return await extractAndAnalyzeLegacy();
    }
  }

  // Wrapper function with fallback
  async function extractAndAnalyze() {
    console.log('[RAGARD] extractAndAnalyze wrapper called');
    try {
      return await extractAndAnalyzeImproved();
    } catch (err) {
      console.error('[RAGARD] extractAndAnalyzeImproved failed, falling back to legacy:', err);
      return await extractAndAnalyzeLegacy();
    }
  }

  // Initialize content script
  function init() {
    console.log('[Ragard] Content script loaded');
    
    // Check if domain is disabled
    const domain = new URL(window.location.href).hostname;
    if (preferences.disabledDomains.includes(domain)) {
      return; // Don't run on disabled domains
    }
    
    // Listen for messages from side panel
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      if (message.type === 'PING') {
        // Quick ping to check if content script is ready
        sendResponse({ ready: true });
        return false;
      }
      
      if (message.type === 'EXTRACT_AND_ANALYZE') {
        // Extract page content and analyze
        extractAndAnalyze().then(result => {
          // Make sure to send response before storing (callback needs it)
          sendResponse(result);
        }).catch(err => {
          console.error('[Ragard] Error in extractAndAnalyze:', err);
          sendResponse({ success: false, error: err.message || 'Unknown error' });
        });
        return true; // Keep channel open for async response
      }
      return false;
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
