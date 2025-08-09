// Refresh functionality with concurrency protection
let refreshInProgress = false;

document.addEventListener('DOMContentLoaded', function() {
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', startRefresh);
    }
    initializeNotificationStyles();
});

async function startRefresh() {
    if (refreshInProgress) {
        showNotification('Refresh already in progress. Please wait...', 'warning');
        return;
    }

    const refreshBtn = document.getElementById('refreshBtn');
    const refreshIcon = refreshBtn?.querySelector('i');
    
    refreshInProgress = true;
    
    // Show loading state
    if (refreshIcon) {
        refreshIcon.className = 'fas fa-spinner fa-spin';
    }
    if (refreshBtn) {
        refreshBtn.disabled = true;
    }
    
    showNotification('Starting refresh process... Processing 5 most recent articles per feed for optimal speed.', 'info');
    
    try {
        // Start ingest process
        const ingestResponse = await fetch('/api/jobs/ingest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (ingestResponse.status === 429) {
            showNotification('Another refresh is already running. Please wait and try again.', 'warning');
            return;
        }
        
        if (!ingestResponse.ok) {
            throw new Error(`Ingest failed: ${ingestResponse.status}`);
        }
        
        const ingestResult = await ingestResponse.json();
        console.log('Ingest completed:', ingestResult);
        
        // Start cleanup process
        showNotification('Processing articles... Almost done!', 'info');
        
        const cleanupResponse = await fetch('/api/jobs/cleanup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!cleanupResponse.ok) {
            throw new Error(`Cleanup failed: ${cleanupResponse.status}`);
        }
        
        const cleanupResult = await cleanupResponse.json();
        console.log('Cleanup completed:', cleanupResult);
        
        // Success notification
        showNotification('Refresh completed successfully! New articles have been added.', 'success');
        
        // Auto-refresh the page after a short delay
        setTimeout(() => {
            window.location.reload();
        }, 2000);
        
    } catch (error) {
        console.error('Refresh error:', error);
        showNotification('Refresh failed: ' + error.message, 'error');
    } finally {
        // Reset button state
        refreshInProgress = false;
        if (refreshIcon) {
            refreshIcon.className = 'fas fa-sync-alt';
        }
        if (refreshBtn) {
            refreshBtn.disabled = false;
        }
    }
}

function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.refresh-notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `refresh-notification alert alert-${getBootstrapClass(type)} alert-dismissible fade show`;
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        max-width: 400px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    `;
    
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas ${getIcon(type)} me-2"></i>
            <span>${message}</span>
            <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds for non-error messages
    if (type !== 'error') {
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
}

function getBootstrapClass(type) {
    const classMap = {
        'info': 'info',
        'success': 'success',
        'warning': 'warning',
        'error': 'danger'
    };
    return classMap[type] || 'info';
}

function getIcon(type) {
    const iconMap = {
        'info': 'fa-info-circle',
        'success': 'fa-check-circle',
        'warning': 'fa-exclamation-triangle',
        'error': 'fa-exclamation-circle'
    };
    return iconMap[type] || 'fa-info-circle';
}

// Add CSS for animations when script loads
function initializeNotificationStyles() {
    const style = document.createElement('style');
    style.textContent = `
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
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
}
