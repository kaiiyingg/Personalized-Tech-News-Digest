$(document).ready(function() {
  var scaleCurve = mojs.easing.path('M0,100 L25,99.9999983 C26.2328835,75.0708847 19.7847843,0 100,0');
  
  $('.heart-button').each(function() {
    var el = this;
    
    // Skip heart buttons that have custom onclick handlers (like in favorites page)
    if (el.hasAttribute('onclick')) {
      console.log('Skipping heart button with custom onclick handler');
      return;
    }
    
    var timeline = new mojs.Timeline();
    var tween1 = new mojs.Burst({
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
    var tween2 = new mojs.Tween({
      duration: 900,
      onUpdate: function(progress) {
        var scaleProgress = scaleCurve(progress);
        el.style.WebkitTransform = el.style.transform = 'scale3d(' + scaleProgress + ',' + scaleProgress + ',1)';
      }
    });
    var tween3 = new mojs.Burst({
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
      
      var button = $(this);
      var articleId = button.data('article-id');
      var isCurrentlyLiked = button.hasClass('active');
      
      console.log('Heart clicked - Article ID:', articleId, 'Currently liked:', isCurrentlyLiked);
      
      if (!articleId) {
        console.error('No article ID found for heart button');
        alert('Error: No article ID found');
        return;
      }
      
      // If unliking, show confirmation first
      if (isCurrentlyLiked) {
        // Find article title for confirmation
        var articleCard = button.closest('.topic-article-card, .horizontal-flashcard');
        var articleTitle = 'this article';
        
        if (articleCard) {
          var titleElement = articleCard.find('.article-title-full, .fast-card-title, h3');
          if (titleElement.length > 0) {
            articleTitle = '"' + titleElement.first().text().trim() + '"';
          }
        }
        
        // Show confirmation dialog
        if (!confirm('Are you sure you want to remove ' + articleTitle + ' from your favorites? This action cannot be undone.')) {
          return; // User cancelled
        }
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
      var endpoint = isCurrentlyLiked ? 'unlike' : 'like';
      var apiUrl = `/api/content/${articleId}/${endpoint}`;
      
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
          
          // Show success notification for unlike actions
          if (isCurrentlyLiked) {
            showFlashMessage('Article removed from favorites', 'info');
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
  const flashContainer = document.createElement('div');
  flashContainer.className = 'flashes';
  flashContainer.innerHTML = `<div class="alert alert-${category}">${message}</div>`;
  flashContainer.style.position = 'fixed';
  flashContainer.style.top = '20px';
  flashContainer.style.left = '50%';
  flashContainer.style.transform = 'translateX(-50%)';
  flashContainer.style.zIndex = '9999';
  flashContainer.style.backgroundColor = category === 'danger' ? '#dc3545' : category === 'success' ? '#28a745' : '#17a2b8';
  flashContainer.style.color = 'white';
  flashContainer.style.padding = '1rem 2rem';
  flashContainer.style.borderRadius = '0.5rem';
  flashContainer.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
  flashContainer.style.fontSize = '0.9rem';
  flashContainer.style.fontWeight = '600';
  flashContainer.style.transition = 'opacity 0.3s ease';
  
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
