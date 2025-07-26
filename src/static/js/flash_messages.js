// Auto-dismiss flash messages after 5 seconds - Simplified version
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flashes li');
    
    // If there are multiple messages, keep only the last one (most recent)
    if (flashMessages.length > 1) {
        for (let i = 0; i < flashMessages.length - 1; i++) {
            flashMessages[i].remove();
        }
    }
    
    // Get the remaining messages after cleanup
    const remainingMessages = document.querySelectorAll('.flashes li');
    
    remainingMessages.forEach(function(message) {
        // Auto-dismiss after 3 seconds
        setTimeout(function() {
            dismissMessage(message);
        }, 3000);
    });
    
    function dismissMessage(message) {
        message.classList.add('fade-out');
        setTimeout(function() {
            if (message.parentNode) {
                message.parentNode.removeChild(message);
                
                // If no more messages, hide the container
                const flashContainer = document.querySelector('.flashes');
                if (flashContainer && flashContainer.children.length === 0) {
                    flashContainer.style.display = 'none';
                }
            }
        }, 300);
    }
});
