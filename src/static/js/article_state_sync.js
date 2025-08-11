/**
 * Cross-page state synchronization for article likes/unlikes
 * Uses localStorage to track changes and window storage events for real-time updates
 */

// Listen for storage changes from other tabs/pages
window.addEventListener('storage', function(e) {
  if (e.key === 'article_state_change') {
    const data = JSON.parse(e.newValue);
    handleArticleStateChange(data);
  }
});

// Broadcast article state change to other tabs/pages
function broadcastArticleStateChange(articleId, isLiked, action, articleData = null) {
  const data = {
    articleId: articleId,
    isLiked: isLiked,
    action: action, // 'like' or 'unlike'
    timestamp: Date.now(),
    page: window.location.pathname,
    articleData: articleData // Include article data for adding to favorites
  };
  
  localStorage.setItem('article_state_change', JSON.stringify(data));
  
  // Clear after a short delay to allow other pages to process
  setTimeout(() => {
    localStorage.removeItem('article_state_change');
  }, 100);
}

// Handle article state changes from other pages
function handleArticleStateChange(data) {
  const { articleId, isLiked, action, page } = data;
  
  // Don't process our own changes
  if (page === window.location.pathname) {
    return;
  }
  
  console.log(`[State Sync] Article ${articleId} ${action} from ${page}`);
  
  // Update heart buttons on current page
  updateHeartButtonState(articleId, isLiked);
  
  // Handle page-specific updates
  if (window.location.pathname === '/favorites') {
    if (!isLiked) {
      // Remove article from favorites page if unliked
      removeArticleFromFavorites(articleId);
    } else {
      // Add article to favorites page if liked from another page
      // Use data.articleData if present, else fallback to minimal info
      addArticleToFavorites(articleId, data.articleData || data);
    }
  } else {
    // On any other page, if unliked, remove from fast view
    if (!isLiked && window.location.pathname === '/fast') {
      removeArticleFromFast(articleId);
    }
    // If liked and on discover/fast, broadcast to favorites
    if (isLiked && (window.location.pathname === '/fast' || window.location.pathname === '/' || window.location.pathname === '/index')) {
      // If the favorites page is open in another tab, it will handle the add
      // No-op here, as the broadcast already includes articleData
    }
  }
}

// Update heart button state for a specific article
function updateHeartButtonState(articleId, isLiked) {
  const heartButton = document.querySelector(`button[data-article-id="${articleId}"]`);
  if (heartButton) {
    const $button = $(heartButton);
    
    if (isLiked) {
      $button.addClass('active');
      $button.attr('aria-pressed', 'true');
      $button.attr('aria-label', 'Unlike this article');
      $button.attr('title', 'Unlike');
    } else {
      $button.removeClass('active');
      $button.attr('aria-pressed', 'false');
      $button.attr('aria-label', 'Like this article');
      $button.attr('title', 'Like');
    }
  }
}

// Add article to favorites page
function addArticleToFavorites(articleId, articleData) {
  // Check if article already exists
  const existingCard = document.querySelector(`button[data-article-id="${articleId}"]`)?.closest('.topic-article-card');
  if (existingCard) {
    return; // Article already exists, no need to add
  }

  // Only add if we have article data and we're on favorites page
  if (!articleData || window.location.pathname !== '/favorites') {
    return;
  }

  // Remove empty state if it exists
  let emptyState = document.querySelector('.empty-state');
  if (!emptyState) {
    // Look for the specific empty state content
    const headings = document.querySelectorAll('h3');
    for (const heading of headings) {
      if (heading.textContent.includes('No Favorite Articles Yet')) {
        emptyState = heading.closest('div, section');
        break;
      }
    }
  }
  
  if (emptyState) {
    emptyState.remove();
  }

  // Get or create the favorites grid
  let favoritesGrid = document.querySelector('.favorites-grid');
  if (!favoritesGrid) {
    // Create favorites grid structure if it doesn't exist
    const mainContent = document.querySelector('main .container') || document.querySelector('main');
    if (mainContent) {
      const gridSection = document.createElement('section');
      gridSection.innerHTML = `
        <div class="favorites-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1.5rem; padding: 1rem 0;">
        </div>
      `;
      mainContent.appendChild(gridSection);
      favoritesGrid = gridSection.querySelector('.favorites-grid');
    }
  }

  if (favoritesGrid) {
    // Create new article card
    const articleCard = document.createElement('div');
    articleCard.className = 'topic-article-card';
    articleCard.style.cssText = 'background: #23262f; border-radius: 1rem; padding: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.15); transition: transform 0.2s ease, box-shadow 0.2s ease; opacity: 0; transform: scale(0.95);';
    
    const truncatedTitle = articleData.title && articleData.title.length > 50 ? 
      articleData.title.substring(0, 50) + '...' : (articleData.title || 'Article');
    
    articleCard.innerHTML = `
      <article style="height: 100%; display: flex; flex-direction: column;">
        <header style="margin-bottom: 1rem;">
          <h3 style="color: #e6e6e6; font-size: 1.1rem; line-height: 1.4; margin: 0; word-wrap: break-word;">
            ${articleData.title || 'Article'}
          </h3>
        </header>
        <div style="color: #b3b3b3; font-size: 0.9rem; line-height: 1.5; margin-bottom: 1rem; flex-grow: 1; overflow: hidden;">
          ${articleData.summary || ''}
        </div>
        <footer style="display: flex; justify-content: space-between; align-items: center; margin-top: auto;">
          <a href="/read_article/${articleId}" target="_blank" rel="noopener" style="background: #8B5CF6; color: white; padding: 0.5rem 1rem; border-radius: 0.5rem; text-decoration: none; font-size: 0.85rem; font-weight: 600;">
            Read More
          </a>
          <button 
            type="button" 
            class="heart-button active"
            data-article-id="${articleId}"
            data-article-title="${truncatedTitle}"
            onclick="confirmUnlike(this)"
            aria-label="Unlike this article"
            aria-pressed="true"
            title="Unlike">
          </button>
        </footer>
      </article>
    `;

    // Add to favorites grid with animation
    favoritesGrid.appendChild(articleCard);
    
    // Trigger animation
    setTimeout(() => {
      articleCard.style.opacity = '1';
      articleCard.style.transform = 'scale(1)';
    }, 50);
  }
}

// Remove article from favorites page
function removeArticleFromFavorites(articleId) {
  const articleCard = document.querySelector(`button[data-article-id="${articleId}"]`)?.closest('.topic-article-card');
  if (articleCard) {
    articleCard.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    articleCard.style.opacity = '0';
    articleCard.style.transform = 'scale(0.95)';
    setTimeout(() => {
      if (articleCard.parentNode) {
        articleCard.remove();
        // Check if no articles left
        const remainingArticles = document.querySelectorAll('.topic-article-card');
        if (remainingArticles.length === 0) {
          // Show empty state
          const container = document.querySelector('.favorites-grid')?.parentNode;
          if (container) {
            container.innerHTML = `
              <div style="text-align: center; margin: 3rem 0; color: #888;">
                <p style="font-size: 1.2rem; margin-bottom: 1rem;">📭</p>
                <p>No favorite articles yet.</p>
                <p style="font-size: 0.9rem; color: #666;">Like articles from the discovery page to see them here!</p>
              </div>
            `;
          }
        }
      }
    }, 300);
  }
}

// Remove article from fast view
function removeArticleFromFast(articleId) {
  const articleCard = document.querySelector(`button[data-article-id="${articleId}"]`)?.closest('.horizontal-flashcard');
  if (articleCard) {
    articleCard.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    articleCard.style.opacity = '0';
    articleCard.style.transform = 'scale(0.95)';
    setTimeout(() => {
      if (articleCard.parentNode) {
        articleCard.remove();
      }
    }, 300);
  }
}

// Export functions for use by other scripts
window.ArticleStateSync = {
  broadcast: broadcastArticleStateChange,
  updateHeartButton: updateHeartButtonState
};
