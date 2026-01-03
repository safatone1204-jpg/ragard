/**
 * Page Context Detection and Author Extraction
 * Detects page type and extracts author context based on platform
 */

// Page context types
const PageContextType = {
  REDDIT_SOCIAL: 'reddit_social',
  TWITTER_SOCIAL: 'twitter_social',
  STOCKTWITS_SOCIAL: 'stocktwits_social',
  GENERIC_SOCIAL: 'generic_social',
  ARTICLE: 'article',
  GENERIC: 'generic'
};

/**
 * Detect the type of page being analyzed
 */
function getPageContextType(hostname, document) {
  try {
    const hostnameLower = hostname.toLowerCase();
    
    // Reddit
    if (hostnameLower.includes('reddit.com')) {
      return PageContextType.REDDIT_SOCIAL;
    }
    
    // Twitter/X
    if (hostnameLower.includes('twitter.com') || hostnameLower.includes('x.com')) {
      return PageContextType.TWITTER_SOCIAL;
    }
    
    // Stocktwits
    if (hostnameLower.includes('stocktwits.com')) {
      return PageContextType.STOCKTWITS_SOCIAL;
    }
    
    // Check for article indicators
    const hasArticle = document.querySelector('article');
    const ogType = document.querySelector('meta[property="og:type"]')?.getAttribute('content')?.toLowerCase();
    const hasAuthorMeta = document.querySelector('meta[name="author"]');
    
    if (hasArticle || ogType === 'article' || hasAuthorMeta) {
      // Verify it's actually an article (has significant content)
      if (hasArticle) {
        const articleText = hasArticle.innerText || hasArticle.textContent || '';
        if (articleText.trim().length > 200) {
          return PageContextType.ARTICLE;
        }
      } else if (ogType === 'article' || hasAuthorMeta) {
        return PageContextType.ARTICLE;
      }
    }
    
    // Generic fallback
    return PageContextType.GENERIC;
  } catch (e) {
    console.warn('[Ragard] Error detecting page context:', e);
    return PageContextType.GENERIC;
  }
}

/**
 * Extract author context based on page type
 */
function extractAuthorContext(contextType, document, location) {
  try {
    const hostname = location.hostname;
    const url = location.href;
    
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
      
      case PageContextType.GENERIC:
      default:
        return extractGenericAuthor(document, location, baseContext);
    }
  } catch (e) {
    console.warn('[Ragard] Error extracting author context:', e);
    return {
      platform: 'generic',
      authorDisplayName: null,
      authorHandle: null,
      authorProfileUrl: null,
      authorMetadata: {}
    };
  }
}

/**
 * Extract Reddit author context
 */
function extractRedditAuthor(document, location, baseContext) {
  try {
    baseContext.platform = 'reddit';
    
    // Find author link
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
      } else {
        const text = authorLink.innerText || authorLink.textContent || '';
        const cleaned = text.replace(/^u\//, '').trim();
        if (cleaned) {
          baseContext.authorHandle = `u/${cleaned}`;
          baseContext.authorDisplayName = cleaned;
          baseContext.authorProfileUrl = `https://www.reddit.com/user/${cleaned}`;
        }
      }
    }
    
    // Try to extract karma (if visible on page)
    try {
      const karmaEl = document.querySelector('[data-testid="karma"]') ||
                      document.querySelector('.karma');
      if (karmaEl) {
        const karmaText = karmaEl.innerText || karmaEl.textContent || '';
        const karmaMatch = karmaText.match(/([\d,]+)/);
        if (karmaMatch) {
          baseContext.authorMetadata.karma_or_points = parseInt(karmaMatch[1].replace(/,/g, ''), 10);
        }
      }
    } catch (e) {
      // Ignore karma extraction errors
    }
    
    return baseContext;
  } catch (e) {
    console.warn('[Ragard] Error extracting Reddit author:', e);
    return baseContext;
  }
}

/**
 * Extract Twitter/X author context
 */
function extractTwitterAuthor(document, location, baseContext) {
  try {
    baseContext.platform = 'twitter';
    
    // Try to find author info in various Twitter/X selectors
    const authorLink = document.querySelector('a[href*="/"]')?.closest('article')?.querySelector('a[href^="/"]') ||
                      document.querySelector('[data-testid="User-Name"] a') ||
                      document.querySelector('a[href^="/"][role="link"]');
    
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
    
    // Try to find display name
    const displayNameEl = document.querySelector('[data-testid="User-Name"] span') ||
                         document.querySelector('article [dir="ltr"] span');
    if (displayNameEl && !displayNameEl.textContent.startsWith('@')) {
      baseContext.authorDisplayName = displayNameEl.textContent.trim();
    }
    
    // Try to extract followers (if visible)
    try {
      const followersText = document.body.innerText || '';
      const followersMatch = followersText.match(/([\d,]+)\s*(?:followers?|follower)/i);
      if (followersMatch) {
        baseContext.authorMetadata.followers = parseInt(followersMatch[1].replace(/,/g, ''), 10);
      }
    } catch (e) {
      // Ignore follower extraction errors
    }
    
    return baseContext;
  } catch (e) {
    console.warn('[Ragard] Error extracting Twitter author:', e);
    return baseContext;
  }
}

/**
 * Extract Stocktwits author context
 */
function extractStocktwitsAuthor(document, location, baseContext) {
  try {
    baseContext.platform = 'stocktwits';
    
    // Stocktwits typically has username in URL or page
    const urlMatch = location.pathname.match(/\/user\/([^/]+)/);
    if (urlMatch) {
      const username = urlMatch[1];
      baseContext.authorHandle = `@${username}`;
      baseContext.authorDisplayName = username;
      baseContext.authorProfileUrl = `https://stocktwits.com/${username}`;
    }
    
    // Try to find display name
    const displayNameEl = document.querySelector('.user-name') ||
                         document.querySelector('[class*="username"]');
    if (displayNameEl) {
      baseContext.authorDisplayName = displayNameEl.textContent.trim();
    }
    
    return baseContext;
  } catch (e) {
    console.warn('[Ragard] Error extracting Stocktwits author:', e);
    return baseContext;
  }
}

/**
 * Extract article author context
 */
function extractArticleAuthor(document, location, baseContext) {
  try {
    baseContext.platform = 'article_site';
    const hostname = location.hostname;
    
    // Try meta author tag
    const authorMeta = document.querySelector('meta[name="author"]');
    if (authorMeta) {
      baseContext.authorDisplayName = authorMeta.getAttribute('content')?.trim();
    }
    
    // Try byline elements
    const bylineSelectors = [
      '.byline',
      '[itemprop="author"]',
      '.author',
      '[class*="author"]',
      '[class*="byline"]',
      'article .author',
      'article [rel="author"]'
    ];
    
    for (const selector of bylineSelectors) {
      const byline = document.querySelector(selector);
      if (byline) {
        const text = byline.innerText || byline.textContent || '';
        const link = byline.querySelector('a');
        
        if (link) {
          baseContext.authorProfileUrl = link.href;
          baseContext.authorDisplayName = link.textContent.trim() || text.trim();
        } else if (text.trim()) {
          baseContext.authorDisplayName = text.trim();
        }
        
        if (baseContext.authorDisplayName) break;
      }
    }
    
    // Derive domain reputation
    const reputableDomains = [
      'wsj.com', 'bloomberg.com', 'reuters.com', 'ft.com', 'cnbc.com',
      'nytimes.com', 'washingtonpost.com', 'theguardian.com', 'forbes.com',
      'marketwatch.com', 'yahoo.com', 'fool.com', 'seekingalpha.com'
    ];
    
    const hostnameLower = hostname.toLowerCase();
    if (reputableDomains.some(domain => hostnameLower.includes(domain))) {
      baseContext.authorMetadata.domainReputation = 'high';
    } else {
      // Check if it has proper article structure
      const hasArticle = document.querySelector('article');
      const hasProperStructure = hasArticle && (hasArticle.innerText || '').length > 500;
      baseContext.authorMetadata.domainReputation = hasProperStructure ? 'medium' : 'low';
    }
    
    return baseContext;
  } catch (e) {
    console.warn('[Ragard] Error extracting article author:', e);
    return baseContext;
  }
}

/**
 * Extract generic author context (fallback)
 */
function extractGenericAuthor(document, location, baseContext) {
  try {
    baseContext.platform = 'generic';
    const hostname = location.hostname;
    
    // Use site name as "author"
    baseContext.authorDisplayName = hostname.replace(/^www\./, '');
    baseContext.authorProfileUrl = `${location.protocol}//${hostname}/`;
    
    return baseContext;
  } catch (e) {
    console.warn('[Ragard] Error extracting generic author:', e);
    return baseContext;
  }
}

// Export for use in content script
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    PageContextType,
    getPageContextType,
    extractAuthorContext
  };
}

