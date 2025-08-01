// Fast View batching and slider logic
let articles = [];
let currentIdx = 0;
let totalArticles = parseInt(document.getElementById('total-articles').textContent) || 0;
let articlesRead = parseInt(document.getElementById('articles-read').textContent) || 0;
let batchSize = 10; // Should match backend default
let offset = 0;
let loading = false;

// Fisher-Yates shuffle to mix articles of different topics
function shuffleArray(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function renderFlashcard(article) {
  if (!article) return '';
  return `
    <div class="fast-horizontal-card" data-article-id="${article.id}" style="background: #23262f; border-radius: 1.1rem; box-shadow: 0 4px 16px rgba(0,0,0,0.18); padding: 2.1rem 2.2rem 1.7rem 2.2rem; min-width: 340px; max-width: 540px; width: 100%; display: flex; flex-direction: column; align-items: flex-start; justify-content: flex-start;">
      <div class="fast-card-topic" style="margin-bottom: 0.4rem;">
        <span class="fast-topic-badge" style="font-size: 0.98rem; font-weight: 600; background: #3b3f4a; color: #b3b3b3; border-radius: 0.5rem; padding: 0.18em 0.7em 0.18em 0.7em;">${article.topic || 'Tech News'}</span>
      </div>
      <div class="fast-card-meta" style="margin-bottom: 0.2rem; font-size: 0.92rem; color: #b3b3b3;">
        <span class="fast-card-date">${article.published_at ? article.published_at.slice(0,10) : 'No date'}</span>
        <span style="margin: 0 0.5em;">·</span>
        <span class="fast-card-source">${article.source_name}</span>
      </div>
      <h2 class="fast-card-title full-title" style="font-size: 1.22rem; font-weight: 800; color: #fff; margin: 0 0 0.7rem 0; line-height: 1.22; max-height: 3.2em; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">${article.title}</h2>
      <div class="fast-card-summary" style="font-size: 1.01rem; color: #e0e0e0; margin-bottom: 1.1rem; line-height: 1.5; max-height: 5.5em; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical;">${article.summary || ''}</div>
      <div class="fast-card-actions" style="margin-top: auto; display: flex; align-items: center; gap: 0.9rem;">
        <a href="${article.article_url}" target="_blank" class="fast-read-more-btn" style="background: #8B5CF6; color: white; padding: 0.5rem 1.1rem; border-radius: 0.5rem; text-decoration: none; font-size: 0.93rem; font-weight: 600; transition: background 0.2s;">
          Read Full Article <i class="ph ph-arrow-up-right"></i>
        </a>
        <button type="button" id="heart-${article.id}" class="heart-button${article.is_liked ? ' active' : ''}" data-article-id="${article.id}" title="${article.is_liked ? 'Unlike' : 'Like'}"><div class="heart-animation"></div></button>
      </div>
    </div>
  `;
}

function updateStats() {
  document.getElementById('articles-read').textContent = articlesRead;
  document.getElementById('total-articles').textContent = totalArticles;
}

function showFlashcard(idx) {
  const slider = document.getElementById('flashcard-slider');
  slider.innerHTML = '';
  if (articles[idx]) {
    slider.innerHTML = renderFlashcard(articles[idx]);
  }
}


function showNoMoreArticles() {
  document.getElementById('no-more-articles').style.display = 'block';
  document.getElementById('no-more-articles').innerHTML = `<h3>No more articles to swipe!</h3><p>Check back later for new content.</p>`;
  // Hide arrows when no articles
  const leftBtn = document.getElementById('fast-arrow-left');
  const rightBtn = document.getElementById('fast-arrow-right');
  if (leftBtn) leftBtn.style.display = 'none';
  if (rightBtn) rightBtn.style.display = 'none';
}

function fetchNextBatch() {
  if (loading) return;
  loading = true;
  
  // Show loading indicator
  showLoadingSpinner();
  
  // Add timeout for slow requests
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 8000); // 8 second timeout
  
  fetch(`/api/fast_articles?offset=${offset}&limit=${batchSize}`, {
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
      if (batch.length > 0) {
        articles = articles.concat(batch);
        totalArticles = articles.length;
        updateStats();
        if (currentIdx === 0) showFlashcard(currentIdx);
      } else if (articles.length === 0) {
        showNoMoreArticles();
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

  // Arrow navigation
  const leftBtn = document.getElementById('fast-arrow-left');
  const rightBtn = document.getElementById('fast-arrow-right');
  if (leftBtn && rightBtn) {
    leftBtn.addEventListener('click', function() {
      if (currentIdx > 0) {
        currentIdx--;
        showFlashcard(currentIdx);
      }
    });
    rightBtn.addEventListener('click', function() {
      if (currentIdx < articles.length - 1) {
        markArticleRead(articles[currentIdx].id);
        currentIdx++;
        showFlashcard(currentIdx);
        articlesRead++;
        updateStats();
        // If near end, prefetch next batch
        if (articles.length - currentIdx <= 2) {
          offset += batchSize;
          fetchNextBatch();
        }
      } else if (!loading) {
        // Try to fetch next batch if not already loading
        offset += batchSize;
        fetchNextBatch();
        // If still no more articles after fetch, show message
        setTimeout(() => {
          if (currentIdx >= articles.length - 1) {
            markArticleRead(articles[currentIdx].id);
            articlesRead++;
            updateStats();
            showNoMoreArticles();
          }
        }, 500);
      }
    });
  }
});
