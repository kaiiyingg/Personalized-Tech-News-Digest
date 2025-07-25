// Topics navigation functionality
function scrollToTopic(topicId) {
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
    
    // Close dropdown after selection
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