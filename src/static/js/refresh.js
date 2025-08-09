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
    const refreshText = refreshBtn?.querySelector('span');
    
    refreshInProgress = true;
    
    // Show loading state in navigation button
    if (refreshIcon) {
        refreshIcon.className = 'fas fa-spinner fa-spin';
    }
    if (refreshText) {
        refreshText.textContent = 'Refreshing...';
    }
    if (refreshBtn) {
        refreshBtn.disabled = true;
        refreshBtn.style.opacity = '0.7';
    }
    
    showNotification('Starting refresh process... Processing 3 most recent articles per feed (AI disabled for memory optimization).', 'info');
    
    try {
        // Start ingest process
        const ingestResponse = await fetch('/api/jobs/ingest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            // Add timeout to prevent hanging
            signal: AbortSignal.timeout(180000) // 3 minute timeout
        });
        
        if (ingestResponse.status === 429) {
            showNotification('Another refresh is already running. Please wait and try again.', 'warning');
            return;
        }
        
        if (ingestResponse.status === 502) {
            throw new Error('Server temporarily unavailable. This usually happens during heavy processing. Please try again in a few moments.');
        }
        
        if (!ingestResponse.ok) {
            const errorText = await ingestResponse.text();
            throw new Error(`Ingest failed: ${ingestResponse.status} - ${errorText}`);
        }
        
        const ingestResult = await ingestResponse.json();
        console.log('Ingest completed:', ingestResult);
        
        // Update button to show cleanup phase
        if (refreshText) {
            refreshText.textContent = 'Optimizing...';
        }
        showNotification('Processing articles... Almost done!', 'info');
        
        const cleanupResponse = await fetch('/api/jobs/cleanup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            signal: AbortSignal.timeout(60000) // 1 minute timeout for cleanup
        });
        
        if (!cleanupResponse.ok) {
            console.warn('Cleanup failed, but continuing...');
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
        
        // Handle specific errors with user-friendly messages
        let errorMessage = error.message;
        if (error.name === 'TimeoutError' || error.message.includes('timeout')) {
            errorMessage = 'Request timed out. The server is taking longer than expected. Please try again.';
        } else if (error.message.includes('502')) {
            errorMessage = 'Server temporarily overloaded. Please wait a moment and try again.';
        }
        
        showNotification('Refresh failed: ' + errorMessage, 'error');
    } finally {
        // Always reset button state
        refreshInProgress = false;
        if (refreshIcon) {
            refreshIcon.className = 'fas fa-sync-alt';
        }
        if (refreshText) {
            refreshText.textContent = 'Refresh';
        }
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.style.opacity = '1';
        }
    }
}

function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.refresh-notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'refresh-notification';
    
    // Set colors based on type
    let backgroundColor, borderColor;
    switch(type) {
        case 'success':
            backgroundColor = '#10B981';
            borderColor = '#059669';
            break;
        case 'warning':
            backgroundColor = '#F59E0B';
            borderColor = '#D97706';
            break;
        case 'error':
            backgroundColor = '#EF4444';
            borderColor = '#DC2626';
            break;
        default: // info
            backgroundColor = '#3B82F6';
            borderColor = '#2563EB';
    }
    
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        max-width: 400px;
        background: ${backgroundColor};
        border: 2px solid ${borderColor};
        border-radius: 8px;
        padding: 12px 16px;
        color: white;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        line-height: 1.4;
    `;
    
    notification.innerHTML = `
        <i class="fas ${getIcon(type)}"></i>
        <span style="flex: 1;">${message}</span>
        <button type="button" class="notification-close" style="
            background: none;
            border: none;
            color: white;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            padding: 0;
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: background-color 0.2s;
            margin-left: 8px;
        " title="Close">×</button>
    `;
    
    // Add close button functionality
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
        // Clear the auto-remove timer if user closes manually
        if (notification.autoRemoveTimer) {
            clearTimeout(notification.autoRemoveTimer);
        }
        notification.remove();
    });
    
    // Hover effect for close button
    closeBtn.addEventListener('mouseenter', () => {
        closeBtn.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
    });
    closeBtn.addEventListener('mouseleave', () => {
        closeBtn.style.backgroundColor = 'transparent';
    });
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds (but longer for errors so user can read them)
    const duration = type === 'error' ? 8000 : 5000;
    const autoRemoveTimer = setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, duration);
    
    // Store timer on notification so we can clear it if user closes manually
    notification.autoRemoveTimer = autoRemoveTimer;
    
    return notification;
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
