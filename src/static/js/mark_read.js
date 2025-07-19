// Automatically mark article as read when title is clicked
// Requires jQuery
$(document).ready(function() {
  $('.article-card h3 a').on('click', function(e) {
    var articleId = $(this).closest('.article-card').data('article-id');
    if (articleId) {
      $.ajax({
        url: '/api/content/' + articleId + '/read',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ is_read: true }),
        success: function(response) {
          // Optionally show a message or update UI
        },
        error: function(xhr) {
          // Optionally handle error
        }
      });
    }
  });
});
// For fast.html, you can use a similar approach if you want to mark as read on click.
