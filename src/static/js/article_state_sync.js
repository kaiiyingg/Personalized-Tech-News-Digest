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
function broadcastArticleStateChange(articleId, isLiked, action) {
  const data = {
    articleId: articleId,
    isLiked: isLiked,
    action: action, // 'like' or 'unlike'
    timestamp: Date.now(),
    page: window.location.pathname
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
  if (window.location.pathname === '/favorites' && !isLiked) {
    // Remove article from favorites page if unliked
    removeArticleFromFavorites(articleId);
  } else if (window.location.pathname === '/fast' && !isLiked) {
    // Remove article from fast view if unliked
    removeArticleFromFast(articleId);
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
