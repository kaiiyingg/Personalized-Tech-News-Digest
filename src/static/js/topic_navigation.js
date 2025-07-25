// Topics navigation functionality
function scrollToTopic(topicId) {
    // Check if we're on the discover page (home page)
    const isDiscoverPage = window.location.pathname === '/' || window.location.pathname === '/index';
    
    if (isDiscoverPage) {
        // We're on the discover page, scroll to the topic
        const element = document.getElementById(topicId);
        if (element) {
            const navbar = document.querySelector('.navbar');
            const offset = navbar ? navbar.offsetHeight + 20 : 20;
            const elementPosition = element.offsetTop - offset;
            
            window.scrollTo({
                top: elementPosition,
                behavior: 'smooth'
            });
        }
    } else {
        // We're on a different page, redirect to home page with topic parameter
        window.location.href = `/?topic=${topicId}`;
        return; // Don't close dropdown since we're navigating away
    }
    
    // Close dropdown after selection (only if we're staying on the same page)
    const dropdown = document.querySelector('.dropdown');
    if (dropdown) {
        dropdown.classList.remove('active');
    }
}

// Toggle dropdown on click
document.addEventListener('DOMContentLoaded', function() {
    const dropdownToggle = document.querySelector('.dropdown-toggle');
    const dropdown = document.querySelector('.dropdown');
    
    if (dropdownToggle && dropdown) {
        dropdownToggle.addEventListener('click', function(e) {
            e.preventDefault();
            dropdown.classList.toggle('active');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!dropdown.contains(e.target)) {
                dropdown.classList.remove('active');
            }
        });
    }
});