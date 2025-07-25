$(document).ready(function() {
  var scaleCurve = mojs.easing.path('M0,100 L25,99.9999983 C26.2328835,75.0708847 19.7847843,0 100,0');
  
  $('.heart-button').each(function() {
    var el = this;
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
      
      // Optimistically update UI
      if (isCurrentlyLiked) {
        button.removeClass('active');
      } else {
        timeline.play();
        button.addClass('active');
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
        },
        error: function(xhr, status, error) {
          // Revert UI changes on error
          if (isCurrentlyLiked) {
            button.addClass('active');
          } else {
            button.removeClass('active');
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
          alert('Error: ' + errorMsg + ' (Status: ' + xhr.status + ')');
        }
      });
    });
  });
});
