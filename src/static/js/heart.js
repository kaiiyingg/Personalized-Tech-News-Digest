$(document).ready(function() {
  const scaleCurve = mojs.easing.path('M0,100 L25,99.9999983 C26.2328835,75.0708847 19.7847843,0 100,0');
  
  $('.heart-button').each(function() {
    const el = this;
    
    // Skip heart buttons that have custom onclick handlers (like in favorites page)
    if (el.hasAttribute('onclick')) {
      console.log('Skipping heart button with custom onclick handler');
      return;
    }
    
    const timeline = new mojs.Timeline();
    const tween1 = new mojs.Burst({
      parent: el,
      radius: { 0: 100 },
      angle: { 0: 45 },
      y: -10,
      count: 10,
      children: {
        shape: 'circle',
        radius: 30,
        fill: [ 'red', 'white' ],
        strokeWidth: 15,
        duration: 500,
      }
    });
    const tween2 = new mojs.Tween({
      duration: 900,
      onUpdate: function(progress) {
        var scaleProgress = scaleCurve(progress);
        el.style.WebkitTransform = el.style.transform = 'scale3d(' + scaleProgress + ',' + scaleProgress + ',1)';
      }
    });
    const tween3 = new mojs.Burst({
      parent: el,
      radius: { 0: 100 },
      angle: { 0: -45 },
      y: -10,
      count: 10,
      children: {
        shape: 'circle',
        radius: 30,
        fill: [ 'white', 'red' ],
        strokeWidth: 15,
        duration: 400,
      }
    });
    timeline.add(tween1, tween2, tween3);
    
    $(el).click(function(e) {
      e.preventDefault(); // Prevent form submission
      
      const button = $(this);
      const articleId = button.data('article-id');
      const isCurrentlyLiked = button.hasClass('active');
      
      console.log('Heart clicked - Article ID:', articleId, 'Currently liked:', isCurrentlyLiked);
      
      if (!articleId) {
        console.error('No article ID found for heart button');
        alert('Error: No article ID found');
        return;
      }
      

      // If unliking, show modal confirmation (reuse modal from base.html)
      if (isCurrentlyLiked) {
        // Find article title for confirmation
        const articleCard = button.closest('.topic-article-card, .horizontal-flashcard');
        let articleTitle = 'this article';
        if (articleCard) {
          const titleElement = articleCard.find('.article-title-full, .fast-card-title, h3');
          if (titleElement.length > 0) {
            articleTitle = titleElement.first().text().trim();
          }
        }
        // Set modal title
        document.getElementById('articleTitle').textContent = articleTitle;
        // Store current button for use in executeUnlike
        window._currentUnlikeButton = button;
        // Show modal
        document.getElementById('unlikeModal').style.display = 'block';
        // Set up confirm button
        const confirmBtn = document.getElementById('confirmUnlikeBtn');
        confirmBtn.onclick = function() {
          executeUnlikeFromDiscover();
        };
        // Cancel handled by closeUnlikeModal()
        return; // Wait for modal action
      }
// Modal close function (shared)
function closeUnlikeModal() {
  document.getElementById('unlikeModal').style.display = 'none';
  window._currentUnlikeButton = null;
}

// Modal confirm unlike for discover/fast page
function executeUnlikeFromDiscover() {
  const button = window._currentUnlikeButton;
  if (!button) return closeUnlikeModal();
  const articleId = button.data('article-id');
  if (!articleId) return closeUnlikeModal();

  // Optimistically update UI
  button.removeClass('active');
  button.attr('aria-pressed', 'false');
  button.attr('aria-label', 'Like this article');
  button.attr('title', 'Like');

  // Make API call
  const apiUrl = `/api/content/${articleId}/unlike`;
  $.ajax({
    url: apiUrl,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    success: function(response) {
      showFlashMessage('Article removed from favorites', 'info');
      // Remove article from fast view if on fast page
      if (window.location.pathname === '/fast') {
        const articleCard = button.closest('.horizontal-flashcard');
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
    },
    error: function(xhr, status, error) {
      // Revert UI changes on error
      button.addClass('active');
      button.attr('aria-pressed', 'true');
      button.attr('aria-label', 'Unlike this article');
      button.attr('title', 'Unlike');
      let errorMsg;
      try {
        const responseData = JSON.parse(xhr.responseText);
        errorMsg = responseData.error || 'Failed to update favorite status';
      } catch(e) {
        errorMsg = 'Failed to update favorite status';
      }
      showFlashMessage('Error: ' + errorMsg + ' (Status: ' + xhr.status + ')', 'danger');
    }
  });
  closeUnlikeModal();
}
      
      // Optimistically update UI
      if (isCurrentlyLiked) {
        button.removeClass('active');
        button.attr('aria-pressed', 'false');
        button.attr('aria-label', 'Like this article');
        button.attr('title', 'Like');
      } else {
        timeline.play();
        button.addClass('active');
        button.attr('aria-pressed', 'true');
        button.attr('aria-label', 'Unlike this article');
        button.attr('title', 'Unlike');
      }
      
      // Make API call
      const endpoint = isCurrentlyLiked ? 'unlike' : 'like';
      const apiUrl = `/api/content/${articleId}/${endpoint}`;
      
      console.log('Making API call to:', apiUrl);
      
      $.ajax({
        url: apiUrl,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        success: function(response) {
          // UI already updated optimistically
          console.log('Success:', response.message);
          
          // Broadcast state change to other pages
          if (window.ArticleStateSync) {
            const action = isCurrentlyLiked ? 'unlike' : 'like';
            window.ArticleStateSync.broadcast(articleId, !isCurrentlyLiked, action);
          }
          
          // Show success notification and handle DOM updates
          if (isCurrentlyLiked) {
            showFlashMessage('Article removed from favorites', 'info');
            // Remove article from fast view if on fast page
            if (window.location.pathname === '/fast') {
              var articleCard = button.closest('.horizontal-flashcard');
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
          } else {
            showFlashMessage('Article added to favorites', 'success');
          }
        },
        error: function(xhr, status, error) {
          // Revert UI changes on error
          if (isCurrentlyLiked) {
            button.addClass('active');
            button.attr('aria-pressed', 'true');
            button.attr('aria-label', 'Unlike this article');
            button.attr('title', 'Unlike');
          } else {
            button.removeClass('active');
            button.attr('aria-pressed', 'false');
            button.attr('aria-label', 'Like this article');
            button.attr('title', 'Like');
          }
          
          console.log('AJAX Error Details:');
          console.log('Status:', status);
          console.log('Error:', error);
          console.log('Response Status:', xhr.status);
          console.log('Response Text:', xhr.responseText);
          
          var errorMsg;
          try {
            var responseData = JSON.parse(xhr.responseText);
            errorMsg = responseData.error || 'Failed to update favorite status';
          } catch(e) {
            errorMsg = 'Failed to update favorite status';
          }
          
          console.error('Error:', errorMsg);
          showFlashMessage('Error: ' + errorMsg + ' (Status: ' + xhr.status + ')', 'danger');
        }
      });
    });
  });
});

// Flash message function (same as in favorites_unlike.js)
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
