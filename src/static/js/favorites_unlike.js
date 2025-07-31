// favorites_unlike.js
// Handles the unlike modal and article removal logic for favorites.html

let currentUnlikeButton = null;

function confirmUnlike(button) {
  const articleId = button.getAttribute('data-article-id');
  const articleTitle = button.getAttribute('data-article-title');
  
  currentUnlikeButton = button;
  document.getElementById('articleTitle').textContent = articleTitle;
  document.getElementById('unlikeModal').style.display = 'block';
}

function closeUnlikeModal() {
  document.getElementById('unlikeModal').style.display = 'none';
  currentUnlikeButton = null;
}

function executeUnlike() {
  if (!currentUnlikeButton) return;
  
  const articleId = currentUnlikeButton.getAttribute('data-article-id');
  
  // Send unlike request
  fetch(`/api/content/${articleId}/unlike`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    }
  })
  .then(response => response.json())
  .then(data => {
    if (data.message) {
      // Remove the article card from the page
      const articleCard = currentUnlikeButton.closest('.topic-article-card');
      if (articleCard) {
        articleCard.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        articleCard.style.opacity = '0';
        articleCard.style.transform = 'scale(0.95)';
        setTimeout(() => {
          articleCard.remove();
          // Check if no articles left
          const remainingCards = document.querySelectorAll('.topic-article-card');
          if (remainingCards.length === 0) {
            location.reload(); // Reload to show empty state
          }
        }, 300);
      }
      // Show success message
      showFlashMessage(data.message, 'info');
    } else {
      showFlashMessage('Failed to remove article from favorites', 'danger');
    }
    closeUnlikeModal();
  })
  .catch(error => {
    console.error('Error:', error);
    showFlashMessage('An error occurred while removing the article', 'danger');
    closeUnlikeModal();
  });
}

// Close modal when clicking outside
window.onclick = function(event) {
  const modal = document.getElementById('unlikeModal');
  if (event.target === modal) {
    closeUnlikeModal();
  }
}

// Flash message function
function showFlashMessage(message, category) {
  const flashContainer = document.createElement('div');
  flashContainer.className = 'flashes';
  flashContainer.innerHTML = `<div class="alert alert-${category}">${message}</div>`;
  flashContainer.style.position = 'fixed';
  flashContainer.style.top = '20px';
  flashContainer.style.left = '50%';
  flashContainer.style.transform = 'translateX(-50%)';
  flashContainer.style.zIndex = '9999';
  
  document.body.appendChild(flashContainer);
  
  // Auto remove after 3 seconds
  setTimeout(() => {
    flashContainer.style.opacity = '0';
    setTimeout(() => {
      if (flashContainer.parentNode) {
        flashContainer.parentNode.removeChild(flashContainer);
      }
    }, 300);
  }, 3000);
}
