// Fast View batching and slider logic
let articles = [];
let currentIdx = 0;
let offset = 0;
const limit = 10;
let totalArticles = parseInt(document.getElementById('total-articles').textContent) || 0;
let articlesRead = parseInt(document.getElementById('articles-read').textContent) || 0;

function renderFlashcard(article) {
  if (!article) return '';
  return `
    <div class="horizontal-flashcard" data-article-id="${article.id}">
      <div class="horizontal-flashcard-image">
        ${article.image_url ? `<img src="${article.image_url}" alt="Article image">` : `<div class="horizontal-placeholder-image"><i class="ph ph-newspaper"></i></div>`}
      </div>
      <div class="horizontal-flashcard-content">
        <div class="horizontal-flashcard-header">
          <h2 class="horizontal-flashcard-title">${article.title}</h2>
          <div class="horizontal-flashcard-meta">
            <span class="source">${article.source_name}</span>
            <span class="date">${article.published_at || 'No date'}</span>
            <span class="topic">${article.topic}</span>
          </div>
        </div>
        <p class="horizontal-flashcard-summary">${article.summary}</p>
        <div class="horizontal-flashcard-actions">
          <a href="${article.article_url}" target="_blank" class="horizontal-read-more-btn">
            Read Full Article <i class="ph ph-arrow-up-right"></i>
          </a>
          <div class="horizontal-action-buttons">
            <button type="button" id="heart-${article.id}" class="heart-button${article.is_liked ? ' active' : ''}" data-article-id="${article.id}" title="${article.is_liked ? 'Unlike' : 'Like'}"><div class="heart-animation"></div></button>
          </div>
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
  document.getElementById('show-more-btn').style.display = 'none';
  document.getElementById('no-more-articles').style.display = 'block';
  document.getElementById('no-more-articles').innerHTML = `<h3>No more articles to swipe!</h3><p>Check back later for new content.</p>`;
}

function fetchArticlesBatch() {
  fetch(`/api/fast_articles?offset=${offset}&limit=${limit}`)
    .then(res => res.json())
    .then(data => {
      if (data.articles && data.articles.length > 0) {
        articles = data.articles;
        currentIdx = 0;
        showFlashcard(currentIdx);
        document.getElementById('show-more-btn').style.display = articles.length > 1 ? 'block' : 'none';
        document.getElementById('no-more-articles').style.display = 'none';
      } else {
        showNoMoreArticles();
      }
    });
}

document.addEventListener('DOMContentLoaded', function() {
  fetchArticlesBatch();

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
        currentIdx++;
        showFlashcard(currentIdx);
        articlesRead++;
        updateStats();
      } else {
        // End of batch, fetch next batch
        offset += limit;
        fetchArticlesBatch();
        articlesRead++;
        updateStats();
      }
    });
  }

  document.getElementById('show-more-btn').addEventListener('click', function() {
    // Fallback: acts like right arrow
    if (currentIdx < articles.length - 1) {
      currentIdx++;
      showFlashcard(currentIdx);
      articlesRead++;
      updateStats();
    } else {
      offset += limit;
      fetchArticlesBatch();
      articlesRead++;
      updateStats();
    }
  });
});
