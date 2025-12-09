/**
 * Auto-refresh functionality for TechPulse
 * Handles automatic content refresh on login triggers
 */

class AutoRefresh {
    constructor() {
        this.isRefreshing = false;
        this.refreshTimeout = null;
        this.init();
    }

    init() {
        // Check if auto-refresh should be triggered
        if (window.autoRefreshEnabled) {
            this.triggerAutoRefresh();
        } 
    }

    triggerAutoRefresh() {
        console.log('Auto-refresh triggered after login');
        
        // Wait for page to fully load, then trigger refresh
        this.refreshTimeout = setTimeout(() => {
            this.performRefresh();
        }, 2000);
    }

    performRefresh() {
        if (this.isRefreshing) {
            console.log('Refresh already in progress');
            return;
        }

        this.isRefreshing = true;
        console.log('Starting automatic content refresh...');

        // Check if we're on the fast view page
        const isOnFastView = window.location.pathname === '/fast';
        
        if (isOnFastView && typeof window.refreshFastView === 'function') {
            // For fast view, just refresh the articles without API call
            console.log('Refreshing fast view articles...');
            window.refreshFastView();
            this.isRefreshing = false;
            return;
        }

        // Call the API endpoint for refresh (for main page)
        fetch('/api/jobs/ingest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            console.log('Auto-refresh response:', data);
            if (data.success) {
                this.showSuccessMessage();
                // Reload page to show new content
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                this.showErrorMessage(data.error || 'Auto-refresh failed');
            }
        })
        .catch(error => {
            console.error('Auto-refresh error:', error);
            this.showErrorMessage('Network error during auto-refresh');
        })
        .finally(() => {
            this.isRefreshing = false;
        });
    }

    showSuccessMessage() {
        this.showMessage('Content automatically refreshed! Loading new articles...', 'success');
    }

    showErrorMessage(message) {
        this.showMessage(`Auto-refresh failed: ${message}`, 'error');
    }

    showMessage(text, type = 'info') {
        // Create or update message element
        let messageEl = document.getElementById('refresh-message');
        if (!messageEl) {
            messageEl = document.createElement('div');
            messageEl.id = 'refresh-message';
            messageEl.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: 600;
                z-index: 1000;
                transition: all 0.3s ease;
                max-width: 300px;
            `;
            document.body.appendChild(messageEl);
        }

        // Set message styling based on type
        const styles = {
            success: {
                background: 'linear-gradient(135deg, #059669, #10b981)',
                color: 'white',
                border: '1px solid #047857'
            },
            error: {
                background: 'linear-gradient(135deg, #dc2626, #ef4444)',
                color: 'white',
                border: '1px solid #b91c1c'
            },
            info: {
                background: 'linear-gradient(135deg, #8B5CF6, #a855f7)',
                color: 'white',
                border: '1px solid #7c3aed'
            }
        };

        const style = styles[type] || styles.info;
        Object.assign(messageEl.style, style);
        messageEl.textContent = text;

        // Auto-hide after 4 seconds
        setTimeout(() => {
            if (messageEl && messageEl.parentNode) {
                messageEl.style.opacity = '0';
                setTimeout(() => {
                    if (messageEl && messageEl.parentNode) {
                        messageEl.parentNode.removeChild(messageEl);
                    }
                }, 300);
            }
        }, 4000);
    }

    cleanup() {
        if (this.refreshTimeout) {
            clearTimeout(this.refreshTimeout);
        }
    }
}

// Initialize auto-refresh when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.autoRefreshInstance = new AutoRefresh();
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.autoRefreshInstance) {
        window.autoRefreshInstance.cleanup();
    }
});
