// Fast View batching and slider logic
let articles = [];
let currentIdx = 0;
let totalUnreadArticles = 0; // Total unread articles available from API
let articlesRead = 0;  // Start with 0, will increment as user reads
let batchSize = 8; // Initial batch size for Fast View
let offset = 0;
let loading = false;
let sessionStartTime = Date.now(); // Track when session started

// Fisher-Yates shuffle to mix articles of different topics
function shuffleArray(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

// Using global refresh button from navbar instead

// Keyboard support for navigation only
document.addEventListener('keydown', function(e) {
    // Removed refresh shortcut - using global refresh from navbar instead
});

function renderFlashcard(article) {
  if (!article) return '';
  
  // Clean up summary: remove common unwanted content and HTML tags
  let cleanSummary = article.summary || '';
  
  // First strip HTML tags completely
  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = cleanSummary;
  cleanSummary = tempDiv.textContent || tempDiv.innerText || '';
  
  // Remove Hacker News style metadata (Article URL:, Comments URL:, Points:, # Comments:)
  cleanSummary = cleanSummary.replace(/Article URL:\s*https?:\/\/[^\s]+/gi, '');
  cleanSummary = cleanSummary.replace(/Comments URL:\s*https?:\/\/[^\s]+/gi, '');
  cleanSummary = cleanSummary.replace(/Points:\s*\d+/gi, '');
  cleanSummary = cleanSummary.replace(/#\s*Comments:\s*\d+/gi, '');
  
  // Remove table of contents indicators
  cleanSummary = cleanSummary.replace(/Table of contents[\s\S]*?(?=\n\n|\n[A-Z]|$)/gi, '');
  cleanSummary = cleanSummary.replace(/Contents[\s\S]*?(?=\n\n|\n[A-Z]|$)/gi, '');
  
  // Remove common article artifacts
  cleanSummary = cleanSummary.replace(/\s*\.\s*$/g, ''); // trailing periods
  cleanSummary = cleanSummary.replace(/\n+/g, ' '); // multiple newlines
  cleanSummary = cleanSummary.replace(/\s+/g, ' '); // multiple spaces
  cleanSummary = cleanSummary.trim();
  
  // If summary is too long (likely full article), truncate intelligently
  if (cleanSummary.length > 300) {
    // Find the end of the first sentence or two
    const sentences = cleanSummary.split(/[.!?]+/);
    let truncated = sentences[0];
    if (sentences.length > 1 && truncated.length < 150) {
      truncated += '. ' + sentences[1];
    }
    cleanSummary = truncated + (truncated.endsWith('.') ? '' : '...');
  }
  
  // Ensure we have meaningful content
  if (!cleanSummary || cleanSummary.length < 10) {
    cleanSummary = `Read this ${article.topic || 'tech'} article from ${article.source_name || 'this source'}.`;
  }
  
  return `
    <div class="fast-horizontal-card" data-article-id="${article.id}" style="background: #23262f; border-radius: 1.1rem; box-shadow: 0 4px 16px rgba(0,0,0,0.18); padding: 1.5rem 1.8rem; min-width: 340px; max-width: 550px; width: 100%; max-height: 70vh; display: flex; flex-direction: column; align-items: flex-start; justify-content: flex-start; overflow: hidden;">
      <div class="fast-card-title" style="font-size: 1.15rem; font-weight: 800; color: #fff; margin: 0 0 0.6rem 0; line-height: 1.3; max-height: 2.6em; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">${article.title}</div>
      <div class="fast-card-topic" style="margin-bottom: 0.6rem;">
        <span class="topic-badge" style="background: #8B5CF6; color: white; padding: 0.2rem 0.6rem; border-radius: 1rem; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; max-width: 140px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: inline-block;">${article.topic || 'Tech News'}</span>
      </div>
      ${article.image_url ? `<div class="fast-card-image" style="margin-bottom: 0.8rem; width: 100%; height: 150px; border-radius: 0.6rem; overflow: hidden; background: #1a1a1a; display: flex; align-items: center; justify-content: center;"><img src="${article.image_url}" alt="Article image" style="width: 100%; height: 100%; object-fit: cover; object-position: center; border-radius: 0.6rem;" onerror="this.parentElement.style.display='none'"></div>` : ''}
      <div class="fast-card-meta" style="margin-bottom: 0.6rem;">
        <span style="background: linear-gradient(135deg, #9333ea, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-size: 0.8rem; font-weight: 700; text-shadow: 0 0 10px rgba(147, 51, 234, 0.5);">${article.source_name}</span>
        <span style="color: #b3b3b3; font-size: 0.75rem; margin-left: 0.5rem;">${article.published_at ? article.published_at.slice(0,10) : 'No date'}</span>
      </div>
      <div class="fast-card-summary" style="font-size: 0.95rem; color: #e0e0e0; margin-bottom: 1rem; line-height: 1.4; max-height: 6em; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; flex-grow: 1; word-wrap: break-word; word-break: break-word; white-space: normal; width: 100%;">${cleanSummary}</div>
      <div class="fast-card-actions" style="margin-top: auto; display: flex; align-items: center; gap: 0.8rem;">
        <a href="${article.article_url}" target="_blank" class="fast-read-more-btn" style="background: #8B5CF6; color: white; padding: 0.4rem 1rem; border-radius: 0.5rem; text-decoration: none; font-size: 0.8rem; font-weight: 600; transition: background 0.2s;">
          Read More <i class="ph ph-arrow-up-right"></i>
        </a>
        <button type="button" id="heart-${article.id}" class="heart-button${article.is_liked ? ' active' : ''}" data-article-id="${article.id}" title="${article.is_liked ? 'Unlike' : 'Like'}"><div class="heart-animation"></div></button>
      </div>
    </div>
  `;
}

function updateStats() {
  // Show current position (1-based) without showing total
  // Focus on article progression rather than overwhelming with total count
  if (articles.length === 0) {
    document.getElementById('articles-read').textContent = 0;
    document.getElementById('total-articles').style.display = 'none';
    return;
  }
  
  const currentPosition = currentIdx + 1;
  document.getElementById('articles-read').textContent = currentPosition;
  // Hide the "of X" part to simplify the display
  document.getElementById('total-articles').style.display = 'none';
}

function showFlashcard(idx) {
  const slider = document.getElementById('flashcard-slider');
  slider.innerHTML = '';
  if (articles[idx]) {
    slider.innerHTML = renderFlashcard(articles[idx]);
    // Attach heart button functionality to the newly created button
    attachHeartButtonListener(articles[idx]);
  }
}

// Heart button functionality for fast view
function attachHeartButtonListener(article) {
  const heartButton = document.getElementById(`heart-${article.id}`);
  if (heartButton) {
    heartButton.addEventListener('click', function(e) {
      e.preventDefault();
      
      const articleId = article.id;
      const isCurrentlyLiked = heartButton.classList.contains('active');
      
      console.log('Fast view heart clicked - Article ID:', articleId, 'Currently liked:', isCurrentlyLiked);
      
      // Optimistically update UI
      if (isCurrentlyLiked) {
        heartButton.classList.remove('active');
        heartButton.title = 'Like';
      } else {
        heartButton.classList.add('active');
        heartButton.title = 'Unlike';
        // Add a simple animation with better styling
        heartButton.style.transition = 'transform 0.2s ease';
        heartButton.style.transform = 'scale(1.3)';
        setTimeout(() => {
          heartButton.style.transform = 'scale(1)';
        }, 200);
      }
      
      // Update the article object
      article.is_liked = !isCurrentlyLiked;
      
      // Make API call
      const endpoint = isCurrentlyLiked ? 'unlike' : 'like';
      const apiUrl = `/api/content/${articleId}/${endpoint}`;
      
      console.log('Making API call to:', apiUrl);
      
      fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log('Success:', data.message);
        // UI already updated optimistically
      })
      .catch(error => {
        console.error('Error updating like status:', error);
        
        // Revert UI changes on error
        if (isCurrentlyLiked) {
          heartButton.classList.add('active');
          heartButton.title = 'Unlike';
        } else {
          heartButton.classList.remove('active');
          heartButton.title = 'Like';
        }
        
        // Revert article object
        article.is_liked = isCurrentlyLiked;
        
        alert('Failed to update favorite status. Please try again.');
      });
    });
  }
}

function showNoMoreArticles() {
  const slider = document.getElementById('flashcard-slider');
  slider.innerHTML = `
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; color: #b3b3b3; text-align: center; padding: 2rem;">
      <div style="font-size: 3rem; margin-bottom: 1rem;">📰</div>
      <h3 style="margin: 0 0 0.5rem 0; color: #fff;">That's all for now!</h3>
      <p style="margin: 0; color: #b3b3b3;">You’re all caught up for today! Come back later for the latest tech updates.</p>
    </div>
  `;
  
  // Update stats to show just the current article count without confusing totals
  const articlesViewed = Math.max(currentIdx + 1, articles.length);
  document.getElementById('articles-read').textContent = articlesViewed;
  document.getElementById('total-articles').style.display = 'none';
}

function fetchNextBatch(refresh = false) {
  if (loading) return;
  loading = true;
  
  // Show loading indicator only if no articles loaded yet
  if (articles.length === 0) {
    showLoadingSpinner();
  }
  
  // Add timeout for slow requests
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 8000); // 8 second timeout
  
  // Add refresh parameter if needed
  const refreshParam = refresh ? '&refresh=true' : '';
  
  fetch(`/api/fast_articles?offset=${offset}&limit=${batchSize}${refreshParam}`, {
    signal: controller.signal
  })
    .then(res => {
      clearTimeout(timeoutId);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    })
    .then(data => {
      hideLoadingSpinner();
      const batch = (data.articles || []);
      console.log(`Fetched batch: offset=${offset}, received=${batch.length} articles, refresh=${refresh}`);
      
      // Update total unread count from API response
      if (data.total_unread !== undefined) {
        totalUnreadArticles = data.total_unread;
        console.log(`Total unread articles available: ${totalUnreadArticles}`);
      }
      
      if (batch.length > 0) {
        articles = articles.concat(batch);
        // Update stats to show current position (starting from 1)
        updateStats();
        if (currentIdx === 0 && articles.length > 0) {
          showFlashcard(currentIdx);
        }
        
        // Update offset for next batch - use 10 for subsequent batches
        offset += batch.length;
        batchSize = 10;
      } else {
        // No more articles available
        console.log('No more articles to fetch');
        if (articles.length === 0) {
          // Set totalUnreadArticles to 0 if no articles available
          if (data.total_unread !== undefined) {
            totalUnreadArticles = data.total_unread;
          } else {
            totalUnreadArticles = 0;
          }
          updateStats(); // Update stats to show 0 of 0
          showNoMoreArticles();
        } else {
          // Keep the total from API, or fallback to loaded articles
          if (totalUnreadArticles === 0) {
            totalUnreadArticles = articles.length;
          }
          updateStats();
        }
      }
      loading = false;
    })
    .catch(err => {
      clearTimeout(timeoutId);
      hideLoadingSpinner();
      loading = false;
      
      if (err.name === 'AbortError') {
        showError('Request timed out. Please check your connection and try again.');
      } else {
        showError('Failed to load articles. Please try again.');
      }
      
      // Show retry button if no articles loaded
      if (articles.length === 0) {
        showRetryButton();
      }
    });
}

function showLoadingSpinner() {
  const slider = document.getElementById('flashcard-slider');
  slider.innerHTML = `
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 200px; color: #b3b3b3;">
      <div style="border: 3px solid #f3f3f3; border-top: 3px solid #8B5CF6; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin-bottom: 1rem;"></div>
      <p>Loading articles...</p>
    </div>
  `;
}

function hideLoadingSpinner() {
  // Spinner will be replaced by content or error message
}

function showError(message) {
  const slider = document.getElementById('flashcard-slider');
  slider.innerHTML = `
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 200px; color: #ff6b6b; text-align: center; padding: 2rem;">
      <div style="font-size: 2rem; margin-bottom: 1rem;">⚠️</div>
      <h3 style="margin: 0 0 0.5rem 0; color: #fff;">Oops!</h3>
      <p style="margin: 0; color: #b3b3b3;">${message}</p>
    </div>
  `;
}

function showRetryButton() {
  const slider = document.getElementById('flashcard-slider');
  slider.innerHTML += `
    <button onclick="retryFetch()" style="background: #8B5CF6; color: white; padding: 0.7rem 1.5rem; border: none; border-radius: 0.5rem; font-size: 0.9rem; font-weight: 600; cursor: pointer; margin-top: 1rem;">
      Try Again
    </button>
  `;
}

// Add refresh function for fast view
function refreshFastView() {
  console.log('Refreshing fast view...');
  // Reset all state
  articles = [];
  currentIdx = 0;
  totalUnreadArticles = 0;
  articlesRead = 0;
  batchSize = 8;
  offset = 0;
  loading = false;
  
  // Show loading spinner
  showLoadingSpinner();
  
  // Fetch fresh articles with refresh flag
  fetchNextBatch(true);
}

// Expose refresh function globally so navbar can call it
window.refreshFastView = refreshFastView;

function retryFetch() {
  loading = false;
  offset = 0;
  articles = [];
  currentIdx = 0;
  fetchNextBatch();
}

function markArticleRead(articleId) {
  fetch(`/api/mark_read/${articleId}`, { method: 'POST' });
}

document.addEventListener('DOMContentLoaded', function() {
  fetchNextBatch();
  
  // Using global refresh button from navbar instead of local refresh button

  // Arrow navigation
  const leftBtn = document.getElementById('fast-arrow-left');
  const rightBtn = document.getElementById('fast-arrow-right');
  if (leftBtn && rightBtn) {
    leftBtn.addEventListener('click', function() {
      if (currentIdx > 0) {
        currentIdx--;
        showFlashcard(currentIdx);
        updateStats();
      }
    });
    rightBtn.addEventListener('click', function() {
      if (currentIdx < articles.length - 1) {
        // Mark current article as read before moving to next
        markArticleRead(articles[currentIdx].id);
        articlesRead++;
        currentIdx++;
        showFlashcard(currentIdx);
        updateStats();
        
        // If we're near the end (2 articles left), preload next batch
        if (articles.length - currentIdx <= 2 && !loading && totalUnreadArticles === 0) {
          // Load next batch of 10 articles
          const nextBatchSize = 10;
          fetch(`/api/fast_articles?offset=${offset}&limit=${nextBatchSize}`)
            .then(res => res.ok ? res.json() : Promise.reject())
            .then(data => {
              const batch = (data.articles || []);
              if (data.total_unread !== undefined) {
                totalUnreadArticles = data.total_unread;
              }
              if (batch.length > 0) {
                articles = articles.concat(batch);
                offset += batch.length;
                updateStats();
              } else {
                // No more articles available
                if (totalUnreadArticles === 0) {
                  totalUnreadArticles = articles.length;
                }
                updateStats();
              }
            })
            .catch(err => console.log('Failed to preload next batch:', err));
        }
      } else if (!loading && totalUnreadArticles === 0) {
        // We're at the end, try to fetch more
        markArticleRead(articles[currentIdx].id);
        articlesRead++;
        updateStats();
        
        const nextBatchSize = 10;
        fetch(`/api/fast_articles?offset=${offset}&limit=${nextBatchSize}`)
          .then(res => res.ok ? res.json() : Promise.reject())
          .then(data => {
            const batch = (data.articles || []);
            if (data.total_unread !== undefined) {
              totalUnreadArticles = data.total_unread;
            }
            if (batch.length > 0) {
              articles = articles.concat(batch);
              offset += batch.length;
              currentIdx++;
              showFlashcard(currentIdx);
              updateStats();
            } else {
              // No more articles available
              if (totalUnreadArticles === 0) {
                totalUnreadArticles = articles.length;
              }
              updateStats();
              showNoMoreArticles();
            }
          })
          .catch(err => {
            if (totalUnreadArticles === 0) {
              totalUnreadArticles = articles.length;
            }
            updateStats();
            showNoMoreArticles();
          });
      } else {
        // We're at the end and know there are no more articles
        markArticleRead(articles[currentIdx].id);
        articlesRead++;
        updateStats();
        showNoMoreArticles();
      }
    });
  }
});
