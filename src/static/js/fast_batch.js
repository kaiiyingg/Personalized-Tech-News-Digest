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
    <div class="fast-horizontal-card" data-article-id="${article.id}">
      <div class="fast-card-content">
        <div class="fast-card-topic">
          <span class="fast-topic-badge">${article.topic || 'Tech News'}</span>
        </div>
        <h2 class="fast-card-title full-title">${article.title}</h2>
        <div class="fast-card-meta">
          <span class="fast-card-source">${article.source_name}</span>
          <span class="fast-card-date">${article.published_at ? article.published_at.slice(0,10) : 'No date'}</span>
        </div>
        <div class="fast-card-actions">
          <a href="${article.article_url}" target="_blank" class="fast-read-more-btn">
            Read Full Article <i class="ph ph-arrow-up-right"></i>
          </a>
          <button type="button" id="heart-${article.id}" class="heart-button${article.is_liked ? ' active' : ''}" data-article-id="${article.id}" title="${article.is_liked ? 'Unlike' : 'Like'}"><div class="heart-animation"></div></button>
        </div>
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
  fetch(`/api/fast_articles?offset=${offset}&limit=${batchSize}`)
    .then(res => res.json())
    .then(data => {
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
    .catch(() => { loading = false; });
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
