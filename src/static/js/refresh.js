// Content refresh functionality for TechPulse
// Handles both article ingestion and smart cleanup

// Content refresh functionality
async function refreshContent() {
    const btn = document.getElementById('refresh-content-btn');
    const originalText = btn.innerHTML;
    
    try {
        btn.innerHTML = '<span>🔄 Refreshing...</span>';
        btn.style.pointerEvents = 'none'; // Disable clicking
        
        // Step 1: Fetch fresh articles
        showNotification('Fetching latest tech articles...', 'info');
        
        const ingestResponse = await fetch('/api/jobs/ingest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            credentials: 'same-origin'
        });
        
        if (!ingestResponse.ok) {
            const errorText = await ingestResponse.text();
            throw new Error(`Ingestion failed: ${ingestResponse.status} - ${errorText}`);
        }
        
        const ingestResult = await ingestResponse.json();
        console.log('Ingestion result:', ingestResult);
        
        // Step 2: Clean up old articles to manage storage
        btn.innerHTML = '<span>🧹 Optimizing...</span>';
        showNotification('Optimizing storage...', 'info');
        
        const cleanupResponse = await fetch('/api/jobs/cleanup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            credentials: 'same-origin'
        });
        
        if (!cleanupResponse.ok) {
            console.warn('Cleanup failed, but continuing...');
        }
        
        btn.innerHTML = '<span>✅ Updated!</span>';
        showNotification('Content refreshed successfully! Loading fresh articles...', 'success');
        
        // Reload page after short delay to show fresh content
        setTimeout(() => {
            window.location.reload();
        }, 2000);
        
    } catch (error) {
        console.error('Refresh failed:', error);
        btn.innerHTML = '<span>❌ Failed</span>';
        
        // Show user-friendly error message
        let errorMessage = 'Unable to refresh content. ';
        if (error.message.includes('500')) {
            errorMessage += 'Server is experiencing issues. Please try again in a moment.';
        } else if (error.message.includes('Network')) {
            errorMessage += 'Please check your internet connection.';
        } else {
            errorMessage += 'Please try again later.';
        }
        
        showNotification(errorMessage, 'error');
        
        // Reset button after error
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.style.pointerEvents = 'auto';
        }, 3000);
    }
}

// Simple notification system with close button
function showNotification(message, type) {
    const notification = document.createElement('div');
    
    // Determine background color based on type
    let backgroundColor;
    if (type === 'success') {
        backgroundColor = '#10B981';
    } else if (type === 'info') {
        backgroundColor = '#3B82F6';
    } else {
        backgroundColor = '#EF4444';
    }
    
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        padding: 12px 45px 12px 15px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        animation: slideIn 0.3s ease;
        background: ${backgroundColor};
        max-width: 400px;
        font-size: 14px;
        line-height: 1.4;
        border: 1px solid rgba(255,255,255,0.2);
    `;
    
    // Create close button
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '×';
    closeBtn.style.cssText = `
        position: absolute;
        top: 8px;
        right: 8px;
        background: none;
        border: none;
        color: white;
        font-size: 18px;
        font-weight: bold;
        cursor: pointer;
        padding: 0;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        transition: background-color 0.2s ease;
    `;
    
    // Close button hover effect
    closeBtn.addEventListener('mouseenter', () => {
        closeBtn.style.backgroundColor = 'rgba(255,255,255,0.2)';
    });
    closeBtn.addEventListener('mouseleave', () => {
        closeBtn.style.backgroundColor = 'transparent';
    });
    
    // Close notification when button is clicked
    closeBtn.addEventListener('click', () => {
        closeNotification(notification);
    });
    
    // Add message and close button
    notification.textContent = message;
    notification.appendChild(closeBtn);
    document.body.appendChild(notification);
    
    // Auto-remove after duration (longer for info messages)
    const duration = type === 'info' ? 3000 : 5000;
    const autoRemove = setTimeout(() => {
        closeNotification(notification);
    }, duration);
    
    // Store timeout ID so we can clear it if user closes manually
    notification.autoRemove = autoRemove;
    
    return notification;
}

// Function to close notification with animation
function closeNotification(notification) {
    if (notification && notification.parentNode) {
        // Clear auto-remove timeout if it exists
        if (notification.autoRemove) {
            clearTimeout(notification.autoRemove);
        }
        
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }
}

// Add CSS for animations when script loads
function initializeNotificationStyles() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
    `;
    document.head.appendChild(style);
}

// Initialize styles when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeNotificationStyles);
