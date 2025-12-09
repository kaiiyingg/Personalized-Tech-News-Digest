// Automatically mark article as read when title is clicked and dim immediately
$(document).ready(function() {
  // Handle clicks on article titles (index.html)
  $(document).on('click', '.topic-article-card h3 a, .article-card h3 a', function(e) {
    var articleCard = $(this).closest('.topic-article-card, .article-card');
    var articleId = articleCard.data('article-id');
    
    if (articleId) {
      // Immediately add the read class for visual feedback
      articleCard.addClass('article-read');
      
      // Send API request to mark as read
      $.ajax({
        url: '/api/content/' + articleId + '/read',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ is_read: true }),
        success: function(response) {
          console.log('Article marked as read:', articleId);
        },
        error: function(xhr) {
          console.error('Failed to mark article as read:', xhr);
          // Remove the class if API call failed
          articleCard.removeClass('article-read');
        }
      });
    }
  });
  
  // Handle clicks on "Read More" buttons
  $(document).on('click', '.read-more-button, .read-more-btn', function(e) {
    var articleCard = $(this).closest('.topic-article-card, .article-card');
    var articleId = articleCard.data('article-id');
    
    if (articleId) {
      // Immediately add the read class for visual feedback
      articleCard.addClass('article-read');
      
      // Send API request to mark as read
      $.ajax({
        url: '/api/content/' + articleId + '/read',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ is_read: true }),
        success: function(response) {
          console.log('Article marked as read:', articleId);
        },
        error: function(xhr) {
          console.error('Failed to mark article as read:', xhr);
          articleCard.removeClass('article-read');
        }
      });
    }
  });
});
