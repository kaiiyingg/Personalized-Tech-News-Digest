// Navigation for flashcard left/right buttons
// Each time you click a navigation button, the page reloads and the server sends the next (or previous) article.
// Requires Phosphor Icons (ph-skip-back, ph-skip-forward)

$(document).ready(function() {
  // Previous button: go back in history
  $('#prev-article-btn').on('click', function(e) {
    e.preventDefault();
    window.history.back();
  });

  // Next button: reload page to get next article
  $('#next-article-btn').on('click', function(e) {
    e.preventDefault();
    window.location.reload();
  });
});
