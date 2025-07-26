// Enhanced navigation for horizontal flashcard with proper arrow functionality
// Uses proper arrow icons and implements smooth navigation

$(document).ready(function() {
  console.log('Fast navigation initialized');
  
  // Previous button: go back in history
  $('#prev-article-btn').on('click', function(e) {
    e.preventDefault();
    console.log('Previous button clicked');
    
    // Add loading state
    $(this).prop('disabled', true);
    $(this).find('i').removeClass('ph-caret-left').addClass('ph-circle-notch ph-spin');
    
    // Navigate back
    setTimeout(() => {
      window.history.back();
    }, 200);
  });

  // Next button: reload page to get next article
  $('#next-article-btn').on('click', function(e) {
    e.preventDefault();
    console.log('Next button clicked');
    
    // Add loading state
    $(this).prop('disabled', true);
    $(this).find('i').removeClass('ph-caret-right').addClass('ph-circle-notch ph-spin');
    
    // Get next article
    setTimeout(() => {
      window.location.reload();
    }, 200);
  });
  
  // Keyboard navigation
  $(document).on('keydown', function(e) {
    // Left arrow key
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      $('#prev-article-btn').click();
    }
    // Right arrow key
    else if (e.key === 'ArrowRight') {
      e.preventDefault();
      $('#next-article-btn').click();
    }
  });
  
  console.log('Keyboard navigation enabled (use arrow keys)');
});
