// Handle topic navigation from URL parameter
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const topicParam = urlParams.get('topic');
    
    if (topicParam) {
        // Small delay to ensure page is fully loaded before scrolling
        setTimeout(function() {
            const element = document.getElementById(topicParam);
            if (element) {
                const navbar = document.querySelector('.navbar');
                const offset = navbar ? navbar.offsetHeight + 20 : 20;
                const elementPosition = element.offsetTop - offset;
                
                window.scrollTo({
                    top: elementPosition,
                    behavior: 'smooth'
                });
                
                // Clean up URL by removing the topic parameter
                const newUrl = new URL(window.location);
                newUrl.searchParams.delete('topic');
                window.history.replaceState({}, '', newUrl);
            }
        }, 300);
    }
});
