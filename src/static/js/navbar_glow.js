// Navbar glow effect that follows mouse cursor
document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('mousemove', function(e) {
            const rect = link.getBoundingClientRect();
            
            // Calculate mouse position relative to the link element
            const x = ((e.clientX - rect.left) / rect.width) * 100;
            const y = ((e.clientY - rect.top) / rect.height) * 100;
            
            // Keep the glow within reasonable bounds
            const clampedX = Math.max(10, Math.min(90, x));
            const clampedY = Math.max(10, Math.min(90, y));
            
            link.style.setProperty('--mouse-x', clampedX + '%');
            link.style.setProperty('--mouse-y', clampedY + '%');
        });
        
        link.addEventListener('mouseleave', function() {
            // Reset to center when mouse leaves
            link.style.setProperty('--mouse-x', '50%');
            link.style.setProperty('--mouse-y', '50%');
        });
    });
});