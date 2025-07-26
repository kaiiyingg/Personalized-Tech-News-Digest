// Auto-dismiss flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flashes li');
    
    flashMessages.forEach(function(message) {
        // Auto-dismiss after 5 seconds
        setTimeout(function() {
            dismissMessage(message);
        }, 5000);
        
        // Allow manual dismiss on click
        message.addEventListener('click', function() {
            dismissMessage(message);
        });
        
        // Add close button with better styling
        const closeBtn = document.createElement('span');
        closeBtn.innerHTML = '&times;';
        closeBtn.style.cssText = `
            position: absolute;
            top: 6px;
            right: 8px;
            font-size: 1.2em;
            cursor: pointer;
            opacity: 0.9;
            transition: opacity 0.2s, background 0.2s;
            color: #000000;
            font-weight: bold;
            line-height: 1;
            background: rgba(0,0,0,0.1);
            border-radius: 50%;
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        closeBtn.addEventListener('mouseenter', function() {
            this.style.opacity = '1';
            this.style.background = 'rgba(255,255,255,0.2)';
        });
        closeBtn.addEventListener('mouseleave', function() {
            this.style.opacity = '0.7';
            this.style.background = 'rgba(255,255,255,0.1)';
        });
        closeBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            dismissMessage(message);
        });
        
        // Make message container relative for positioning
        message.style.position = 'relative';
        message.style.cursor = 'pointer';
        message.style.paddingRight = '35px'; // Make room for smaller close button
        message.appendChild(closeBtn);
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
