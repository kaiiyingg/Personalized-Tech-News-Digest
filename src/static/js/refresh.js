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
        showNotification(`Refresh failed: ${error.message}. Please try again.`, 'error');
        
        // Reset button after error
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.style.pointerEvents = 'auto';
        }, 3000);
    }
}

// Simple notification system
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
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        z-index: 10000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        animation: slideIn 0.3s ease;
        background: ${backgroundColor};
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Remove after 4 seconds (longer for info messages)
    const duration = type === 'info' ? 2000 : 4000;
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, duration);
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
