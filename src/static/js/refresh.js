// Content refresh functionality for TechPulse
// Handles both article ingestion and smart cleanup

// Track refresh state to prevent multiple simultaneous refreshes
let isRefreshing = false;

// Content refresh functionality
async function refreshContent() {
    // Prevent multiple simultaneous refreshes
    if (isRefreshing) {
        showNotification('Refresh already in progress. Please wait for it to complete.', 'info');
        return;
    }
    
    const btn = document.getElementById('refresh-content-btn');
    const originalText = btn.innerHTML;
    
    try {
        isRefreshing = true;
        btn.innerHTML = '<span>🔄 <span class="loading-spinner"></span> Refreshing...</span>';
        btn.style.pointerEvents = 'none'; // Disable clicking
        btn.style.opacity = '0.7'; // Visual indication that it's disabled
        
        // Step 1: Fetch fresh articles
        showNotification('Fetching latest tech articles from multiple sources... This may take a moment.', 'info');
        
        const ingestResponse = await fetch('/api/jobs/ingest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            credentials: 'same-origin',
            signal: AbortSignal.timeout(120000) // 2 minute timeout
        });
        
        if (!ingestResponse.ok) {
            const errorText = await ingestResponse.text();
            throw new Error(`Ingestion failed: ${ingestResponse.status} - ${errorText}`);
        }
        
        const ingestResult = await ingestResponse.json();
        console.log('Ingestion result:', ingestResult);
        
        // Step 2: Clean up old articles to manage storage
        btn.innerHTML = '<span>🧹 <span class="loading-spinner"></span> Optimizing...</span>';
        showNotification('Organizing and optimizing content... Almost done!', 'info');
        
        const cleanupResponse = await fetch('/api/jobs/cleanup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            credentials: 'same-origin',
            signal: AbortSignal.timeout(60000) // 1 minute timeout for cleanup
        });
        
        if (!cleanupResponse.ok) {
            console.warn('Cleanup failed, but continuing...');
        }
        
        btn.innerHTML = '<span>✅ <span class="loading-spinner"></span> Complete!</span>';
        showNotification('Content refreshed successfully! Loading your personalized feed with the latest articles...', 'success');
        
        // Reload page after short delay to show fresh content
        setTimeout(() => {
            window.location.reload();
        }, 2000);
        
    } catch (error) {
        console.error('Refresh failed:', error);
        btn.innerHTML = '<span>❌ Failed</span>';
        
        // Show user-friendly error message
        let errorMessage = 'Unable to refresh content at the moment. ';
        if (error.message.includes('500')) {
            errorMessage += 'Our servers are working hard to process your request. Please wait a moment and try again.';
        } else if (error.message.includes('Network')) {
            errorMessage += 'Please check your internet connection and try again.';
        } else {
            errorMessage += 'This usually resolves quickly. Please try again in a few moments.';
        }
        
        showNotification(errorMessage, 'error');
        
        // Reset button after error
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.style.pointerEvents = 'auto';
            btn.style.opacity = '1';
            isRefreshing = false;
        }, 4000);
    } finally {
        // Ensure refresh state is always reset, even if something unexpected happens
        if (isRefreshing) {
            setTimeout(() => {
                isRefreshing = false;
                if (btn.style.pointerEvents === 'none') {
                    btn.innerHTML = originalText;
                    btn.style.pointerEvents = 'auto';
                    btn.style.opacity = '1';
                }
            }, 10000); // Fallback reset after 10 seconds
        }
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
    
    // Add loading spinner for info messages
    const messageContent = document.createElement('span');
    if (type === 'info') {
        messageContent.innerHTML = `<span class="loading-spinner" style="margin-right: 8px;"></span>${message}`;
    } else {
        messageContent.textContent = message;
    }
    
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
    notification.appendChild(messageContent);
    notification.appendChild(closeBtn);
    document.body.appendChild(notification);
    
    // Auto-remove after duration (longer for info messages since they have important loading info)
    const duration = type === 'info' ? 4000 : 5000;
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
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .loading-spinner {
            display: inline-block;
            width: 12px;
            height: 12px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: #ffffff;
            animation: spin 1s ease-in-out infinite;
            margin: 0 4px;
            vertical-align: middle;
        }
    `;
    document.head.appendChild(style);
}

// Initialize styles when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeNotificationStyles);
