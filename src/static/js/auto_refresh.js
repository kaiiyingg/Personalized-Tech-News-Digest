/**
 * Auto-refresh functionality for TechPulse
 * Handles automatic content refresh on login and manual refresh triggers
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
        
        // Set up manual refresh button listeners
        this.setupRefreshButtons();
    }

    triggerAutoRefresh() {
        console.log('Auto-refresh triggered after login');
        
        // Wait for page to fully load, then trigger refresh
        this.refreshTimeout = setTimeout(() => {
            this.performRefresh();
        }, 2000);
    }

    setupRefreshButtons() {
        // Find all possible refresh buttons
        const refreshSelectors = [
            '[data-refresh]',
            '.refresh-btn', 
            'button[onclick*="refresh"]',
            '.nav-refresh-btn',
            '#refresh-button'
        ];

        refreshSelectors.forEach(selector => {
            const buttons = document.querySelectorAll(selector);
            buttons.forEach(button => {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.performRefresh();
                });
            });
        });
    }

    performRefresh() {
        if (this.isRefreshing) {
            console.log('Refresh already in progress');
            return;
        }

        this.isRefreshing = true;
        console.log('Starting content refresh...');

        // Show loading state
        this.showLoadingState();

        // Call the API endpoint for refresh
        fetch('/api/jobs/ingest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            console.log('Refresh response:', data);
            if (data.success) {
                this.showSuccessMessage();
                // Reload page to show new content
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                this.showErrorMessage(data.error || 'Refresh failed');
            }
        })
        .catch(error => {
            console.error('Refresh error:', error);
            this.showErrorMessage('Network error during refresh');
        })
        .finally(() => {
            this.isRefreshing = false;
            this.hideLoadingState();
        });
    }

    showLoadingState() {
        // Update refresh buttons to show loading state
        const refreshButtons = document.querySelectorAll('[data-refresh], .refresh-btn, button[onclick*="refresh"]');
        refreshButtons.forEach(button => {
            button.disabled = true;
            const originalText = button.textContent;
            button.setAttribute('data-original-text', originalText);
            button.textContent = 'Refreshing...';
            button.style.opacity = '0.7';
        });

        // Show loading indicator if exists
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'block';
        }
    }

    hideLoadingState() {
        // Restore refresh buttons
        const refreshButtons = document.querySelectorAll('[data-refresh], .refresh-btn, button[onclick*="refresh"]');
        refreshButtons.forEach(button => {
            button.disabled = false;
            const originalText = button.getAttribute('data-original-text');
            if (originalText) {
                button.textContent = originalText;
                button.removeAttribute('data-original-text');
            }
            button.style.opacity = '1';
        });

        // Hide loading indicator
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
    }

    showSuccessMessage() {
        this.showMessage('Content refreshed successfully! Loading new articles...', 'success');
    }

    showErrorMessage(message) {
        this.showMessage(`Refresh failed: ${message}`, 'error');
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
