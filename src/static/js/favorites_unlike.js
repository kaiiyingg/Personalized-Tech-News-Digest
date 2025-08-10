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
  // Remove any existing flash message
  const existing = document.querySelector('.flashes.js-flash-message');
  if (existing) existing.remove();

  const flashContainer = document.createElement('ul');
  flashContainer.className = 'flashes js-flash-message';
  flashContainer.style.position = 'fixed';
  flashContainer.style.top = '70px'; // below navbar
  flashContainer.style.left = '50%';
  flashContainer.style.transform = 'translateX(-50%)';
  flashContainer.style.zIndex = '2000';
  flashContainer.style.width = 'auto';
  flashContainer.style.maxWidth = '400px';
  flashContainer.style.minWidth = '200px';
  flashContainer.style.margin = '0';
  flashContainer.style.padding = '0';

  const li = document.createElement('li');
  li.className = category;
  li.style.position = 'relative';
  li.style.paddingRight = '2.2em';
  li.style.background = 'rgba(30,30,30,0.97)';
  li.style.color = category === 'danger' ? '#dc2626' : category === 'success' ? '#16a34a' : '#2563eb';
  li.style.borderRadius = '0.5rem';
  li.style.marginBottom = '8px';
  li.style.fontWeight = '600';
  li.style.fontSize = '0.95em';
  li.style.boxShadow = '0 2px 8px rgba(0,0,0,0.10)';
  li.style.textAlign = 'center';
  li.style.whiteSpace = 'normal';
  li.innerHTML = `<span>${message}</span>`;

  // Add close (X) button
  const closeBtn = document.createElement('button');
  closeBtn.innerHTML = '&times;';
  closeBtn.setAttribute('aria-label', 'Close notification');
  closeBtn.style.position = 'absolute';
  closeBtn.style.top = '6px';
  closeBtn.style.right = '10px';
  closeBtn.style.background = 'none';
  closeBtn.style.border = 'none';
  closeBtn.style.color = '#888';
  closeBtn.style.fontSize = '1.2em';
  closeBtn.style.cursor = 'pointer';
  closeBtn.style.lineHeight = '1';
  closeBtn.style.padding = '0';
  closeBtn.addEventListener('click', () => {
    flashContainer.remove();
  });
  li.appendChild(closeBtn);

  flashContainer.appendChild(li);
  document.body.appendChild(flashContainer);

  // Auto remove after 3 seconds
  setTimeout(() => {
    if (flashContainer.parentNode) {
      flashContainer.style.opacity = '0';
      setTimeout(() => {
        if (flashContainer.parentNode) {
          flashContainer.parentNode.removeChild(flashContainer);
        }
      }, 300);
    }
  }, 3000);
}
