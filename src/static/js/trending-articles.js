/**
 * Trending Articles Component with Chrome AI Summarizer Integration
 */
class TrendingArticles {
    /**
     * Initialize TrendingArticles component
     */
    constructor() {
        this.summarizerSession = null;
        this.isSupported = false;
        this.currentDownloadArticleId = null;
        this.summaryType = 'tldr'; // default type
        this.summaryLength = 'short'; // default length
        this.initializeComponent();
    }

    /**
     * Check if Chrome AI Summarizer is supported
     * @returns {Promise<boolean>} True if AI summarization is available
     */
    async checkAISupport() {
        try {
            console.log('[TrendingArticles] Checking AI support...');
            
            if (!('Summarizer' in self)) {
                console.log('[TrendingArticles] Summarizer API not available.');
                return false;
            }
            
            const availability = await self.Summarizer.availability();
            console.log('[TrendingArticles] AI availability:', availability);
            
            if (availability === 'unavailable') {
                console.log('[TrendingArticles] AI Summarizer not available on this device.');
                return false;
            }
            
            if (availability === 'downloadable') {
                console.log('[TrendingArticles] AI model will be downloaded automatically on first use');
                return false;
            }
            
            console.log('[TrendingArticles] AI support detected!');
            return true;
        } catch (error) {
            console.warn('[TrendingArticles] AI support check failed:', error);
            return false;
        }
    }

    /**
     * Update download progress in the UI
     * @param {string} percentage - Download percentage
     */
    updateDownloadProgress(percentage) {
        if (!this.currentDownloadArticleId) return;
        
        const summaryContainer = document.getElementById(`summary-${this.currentDownloadArticleId}`);
        if (summaryContainer) {
            // If download is complete (100%), switch to regular summarizing state
            if (parseFloat(percentage) >= 100) {
                summaryContainer.innerHTML = `
                    <div class="ai-summary-loading">
                        <div class="loading-spinner-circular"></div>
                        <span>AI model downloaded! Summarizing in progress...</span>
                    </div>
                `;
            } else {
                // Show download progress
                summaryContainer.innerHTML = `
                    <div class="ai-summary-loading">
                        <div class="loading-spinner"></div>
                        <div class="download-progress">
                            <div class="download-text">First-time setup: Downloading AI model...</div>
                            <div class="progress-bar" style="width: 100%; height: 20px; background: #f0f0f0; border-radius: 10px; overflow: hidden; margin: 10px 0;">
                                <div class="progress-fill" style="width: ${percentage}%; height: 100%; background: linear-gradient(90deg, #007bff, #0056b3); transition: width 0.3s ease;"></div>
                            </div>
                            <div class="progress-percentage" style="font-weight: bold; color: #007bff; font-size: 1.1em;">${percentage}%</div>
                            <div class="download-info" style="font-size: 0.8rem; color: #666; margin-top: 8px;">This is a one-time download (~1.5GB). Future summarizations will be instant!</div>
                        </div>
                    </div>
                `;
            }
        }
    }

    /**
     * Initialize the component and set up event listeners
     */
    initializeComponent() {
        document.addEventListener('DOMContentLoaded', async () => {
            this.isSupported = await this.checkAISupport();
            await this.loadUserPreferences();
            this.setupEventListeners();
            this.updateButtonStates();
        });
    }

    /**
     * Set up click handlers for summarize buttons and preference selectors
     */
    setupEventListeners() {
        // Global AI preference selectors (for discover page)
        this.setupGlobalPreferenceListeners();
        
        // Summarize button event listeners
        const summarizeButtons = document.querySelectorAll('.summarize-btn');
        summarizeButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const articleId = button.dataset.articleId;
                this.handleSummarizeClick(articleId, button);
            });
        });
        
        // Individual article preference selectors (for analytics page)
        this.setupIndividualPreferenceListeners();

        // Note: Individual article preference selectors removed - using global preferences only
    }

    /**
     * Set up global preference selectors (for discover page)
     */
    setupGlobalPreferenceListeners() {
        const globalTypeSelector = document.getElementById('global-summary-type');
        const globalLengthSelector = document.getElementById('global-summary-length');
        const globalInfoDisplay = document.getElementById('global-summary-info');
        const saveButton = document.getElementById('save-preferences-btn');

        // Update info display when selectors change (but don't save yet)
        if (globalTypeSelector) {
            globalTypeSelector.addEventListener('change', (e) => {
                const newType = e.target.value;
                const currentLength = globalLengthSelector ? globalLengthSelector.value : 'short';
                this.updateGlobalSummaryInfo(globalInfoDisplay, newType, currentLength);
                this.resetSaveButton(saveButton);
            });
        }

        if (globalLengthSelector) {
            globalLengthSelector.addEventListener('change', (e) => {
                const newLength = e.target.value;
                const currentType = globalTypeSelector ? globalTypeSelector.value : 'tldr';
                this.updateGlobalSummaryInfo(globalInfoDisplay, currentType, newLength);
                this.resetSaveButton(saveButton);
            });
        }

        // Save button click handler
        if (saveButton) {
            saveButton.addEventListener('click', async (e) => {
                e.preventDefault();
                const currentType = globalTypeSelector ? globalTypeSelector.value : 'tldr';
                const currentLength = globalLengthSelector ? globalLengthSelector.value : 'short';
                
                // Show saving state
                saveButton.disabled = true;
                saveButton.textContent = 'Saving...';
                
                try {
                    await this.saveUserPreferences(currentType, currentLength);
                    this.showSaveSuccess(saveButton);
                } catch (error) {
                    this.showSaveError(saveButton);
                }
            });
        }

        // Load and display initial preferences
        if (globalInfoDisplay) {
            this.updateGlobalSummaryInfo(globalInfoDisplay, this.summaryType, this.summaryLength);
        }
    }

    /**
     * Set up individual preference selectors (for analytics page)
     * Note: Individual selectors removed - now using global preferences
     */
    setupIndividualPreferenceListeners() {
        // Individual selectors have been removed in favor of global preferences
        // All pages now use the global preferences set on the discover page
        console.log('[TrendingArticles] Individual preference selectors disabled - using global preferences');
    }

    /**
     * Update global summary info display
     * @param {HTMLElement} infoElement - Info display element
     * @param {string} type - Summary type
     * @param {string} length - Summary length
     */
    updateGlobalSummaryInfo(infoElement, type, length) {
        if (!infoElement) return;

        const specifications = {
            'tldr': {
                'short': 'TLDR, 1 sentence',
                'medium': 'TLDR, 3 sentences', 
                'long': 'TLDR, 5 sentences'
            },
            'key-points': {
                'short': 'Key Points, 3 bullets',
                'medium': 'Key Points, 5 bullets',
                'long': 'Key Points, 7 bullets'
            }
        };
        
        const infoText = specifications[type]?.[length] || 'TLDR, 1 sentence';
        infoElement.textContent = `Current setting: ${infoText}`;
    }

    /**
     * Reset save button to default state
     * @param {HTMLElement} saveButton - Save button element
     */
    resetSaveButton(saveButton) {
        if (!saveButton) return;
        saveButton.disabled = false;
        saveButton.textContent = 'Save';
        saveButton.classList.remove('saved');
    }

    /**
     * Show save success state
     * @param {HTMLElement} saveButton - Save button element
     */
    showSaveSuccess(saveButton) {
        if (!saveButton) return;
        saveButton.disabled = false;
        saveButton.textContent = 'Saved!';
        saveButton.classList.add('saved');
        
        // Reset to normal state after 2 seconds
        setTimeout(() => {
            this.resetSaveButton(saveButton);
        }, 2000);
    }

    /**
     * Show save error state
     * @param {HTMLElement} saveButton - Save button element
     */
    showSaveError(saveButton) {
        if (!saveButton) return;
        saveButton.disabled = false;
        saveButton.textContent = 'Error - Retry';
        saveButton.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
        
        // Reset to normal state after 3 seconds
        setTimeout(() => {
            saveButton.style.background = '';
            this.resetSaveButton(saveButton);
        }, 3000);
    }

    /**
     * Update button states based on AI support
     */
    updateButtonStates() {
        const summarizeButtons = document.querySelectorAll('.summarize-btn');
        summarizeButtons.forEach(button => {
            if (!this.isSupported) {
                button.textContent = 'AI Summarize';
                button.disabled = false;
                button.classList.add('ai-disabled');
                button.title = 'Click to start AI summarization (first time will download model)';
            } else {
                button.textContent = 'AI Summarize';
                button.title = 'Generate AI summary using Chrome built-in Summarizer';
            }
        });
    }



    /**
     * Load user's saved summary preferences from database
     */
    async loadUserPreferences() {
        try {
            console.log('[TrendingArticles] Loading user preferences...');
            const response = await fetch('/api/summary_preferences', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                const preferences = await response.json();
                console.log('[TrendingArticles] Loaded preferences:', preferences);
                
                // Update default preferences
                this.summaryType = preferences.type || 'tldr';
                this.summaryLength = preferences.length || 'short';
                
                // Set all selectors to user's preferences
                this.setAllSelectorsToPreferences(preferences);
                
            } else {
                console.warn('[TrendingArticles] Failed to load preferences, using defaults');
            }
        } catch (error) {
            console.warn('[TrendingArticles] Error loading preferences:', error);
        }
    }

    /**
     * Set all summary selectors to user's preferences
     * @param {Object} preferences - User's preferences {type, length}
     */
    setAllSelectorsToPreferences(preferences) {
        // Update global selectors (discover page)
        const globalTypeSelector = document.getElementById('global-summary-type');
        const globalLengthSelector = document.getElementById('global-summary-length');
        const globalInfoDisplay = document.getElementById('global-summary-info');
        
        if (globalTypeSelector) {
            globalTypeSelector.value = preferences.type || 'tldr';
        }
        if (globalLengthSelector) {
            globalLengthSelector.value = preferences.length || 'short';
        }
        if (globalInfoDisplay) {
            this.updateGlobalSummaryInfo(globalInfoDisplay, preferences.type || 'tldr', preferences.length || 'short');
        }
    }

    /**
     * Save user's summary preferences to database
     * @param {string} type - Summary type
     * @param {string} length - Summary length
     */
    async saveUserPreferences(type, length) {
        try {
            console.log(`[TrendingArticles] Saving preferences: ${type}/${length}`);
            const response = await fetch('/api/summary_preferences', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    type: type,
                    length: length
                })
            });

            if (response.ok) {
                console.log('[TrendingArticles] Preferences saved successfully');
                
                // Update component defaults
                this.summaryType = type;
                this.summaryLength = length;
                
            } else {
                console.warn('[TrendingArticles] Failed to save preferences');
            }
        } catch (error) {
            console.warn('[TrendingArticles] Error saving preferences:', error);
        }
    }



    /**
     * Get current summary preferences 
     * @returns {Object} Object with type and length preferences
     */
    getSummaryPreferences() {
        // Get global preferences (discover page)
        const globalTypeSelector = document.getElementById('global-summary-type');
        const globalLengthSelector = document.getElementById('global-summary-length');
        
        if (globalTypeSelector && globalLengthSelector) {
            return {
                type: globalTypeSelector.value || 'tldr',
                length: globalLengthSelector.value || 'short'
            };
        }
        
        // Fallback to component defaults
        return {
            type: this.summaryType || 'tldr',
            length: this.summaryLength || 'short'
        };
    }

    /**
     * Handle click on summarize button
     * @param {string} articleId - The article ID
     * @param {HTMLElement} button - The clicked button element
     */
    async handleSummarizeClick(articleId, button) {
        console.log('[TrendingArticles] Button clicked, AI supported:', this.isSupported);
        
        this.currentDownloadArticleId = articleId;
        
        // Get current user preferences 
        const preferences = this.getSummaryPreferences();
        console.log(`[TrendingArticles] Using preferences for article ${articleId}:`, preferences);
        
        try {
            const articleContent = this.getArticleContent(articleId);
            if (!articleContent) {
                this.showError(articleId, 'Article content not found');
                return;
            }

            this.showLoadingState(articleId, button);
            const summary = await this.generateAISummary(articleContent, preferences);
            this.displaySummary(articleId, summary, button);

        } catch (error) {
            console.error('[TrendingArticles] Summarization failed:', error);
            this.resetButton(button);
            this.showFallbackMessage(articleId);
        } finally {
            this.currentDownloadArticleId = null;
        }
    }

    /**
     * Get article content from DOM
     * @param {string} articleId - The article ID
     * @returns {string|null} Article content for summarization
     */
    getArticleContent(articleId) {
        const articleCard = document.querySelector(`[data-article-id="${articleId}"]`);
        if (!articleCard) return null;

        const title = articleCard.querySelector('.article-title')?.textContent || '';
        const snippet = articleCard.querySelector('.article-snippet')?.textContent || '';
        
        const cleanTitle = title.trim();
        const cleanSnippet = snippet.trim().replace(/\.\.\.$/, '');
        
        const fullContent = `${cleanTitle}. ${cleanSnippet}`;
        
        if (fullContent.length < 50) {
            throw new Error('Insufficient content for summarization');
        }
        
        return fullContent.trim();
    }

    /**
     * Generate AI summary using Chrome's Summarizer API
     * @param {string} content - Content to summarize
     * @param {Object} preferences - User's summary preferences {type, length}
     * @returns {Promise<string>} Generated summary
     */
    async generateAISummary(content, preferences = {type: 'tldr', length: 'short'}) {
        try {
            console.log('[TrendingArticles] Starting AI summarization...');
            console.log('[TrendingArticles] Content length:', content.length);
            console.log('[TrendingArticles] Using preferences:', preferences);
            
            if (!('Summarizer' in self)) {
                throw new Error('Chrome AI Summarizer not available. Please update to Chrome 138+ stable.');
            }
            
            const availability = await self.Summarizer.availability();
            console.log('[TrendingArticles] AI availability:', availability);
            
            if (availability === 'unavailable') {
                throw new Error('Chrome AI Summarizer not available on this device');
            }
            
            // Always create a new session for different preferences
            if (this.summarizerSession) {
                this.summarizerSession.destroy();
                this.summarizerSession = null;
            }
            
            console.log('[TrendingArticles] Creating new AI summarizer session...');
            console.log(`[TrendingArticles] Using type: ${preferences.type}, length: ${preferences.length}`);
            
            const options = {
                type: preferences.type,
                format: preferences.type === 'key-points' ? 'plain-text' : 'plain-text',
                length: preferences.length,
                monitor: (m) => {
                    m.addEventListener('downloadprogress', (e) => {
                        const percentage = (e.loaded * 100).toFixed(1);
                        console.log(`[TrendingArticles] AI model download: ${percentage}%`);
                        this.updateDownloadProgress(percentage);
                    });
                }
            };
            
            this.summarizerSession = await self.Summarizer.create(options);
                console.log('[TrendingArticles] AI summarizer session created successfully');

            console.log('[TrendingArticles] Generating summary...');
            const summary = await this.summarizerSession.summarize(content, {
                context: 'This is a tech news article for summarization.'
            });
            
            if (!summary || summary.trim().length === 0) {
                throw new Error('Empty summary generated by AI');
            }

            const cleanSummary = summary.trim();
            console.log('[TrendingArticles] Summary generated successfully');
            return cleanSummary;

        } catch (error) {
            console.error('[TrendingArticles] AI summarization failed:', error);
            if (this.summarizerSession) {
                try {
                    this.summarizerSession.destroy();
                } catch (destroyError) {
                    console.warn('[TrendingArticles] Error destroying session:', destroyError);
                }
                this.summarizerSession = null;
            }
            throw error;
        }
    }

    /**
     * Show loading state in the article card
     * @param {string} articleId - Article ID
     * @param {HTMLElement} button - Button element
     */
    showLoadingState(articleId, button) {
        const summaryContainer = document.getElementById(`summary-${articleId}`);
        if (summaryContainer) {
            summaryContainer.innerHTML = `
                <div class="ai-summary-loading">
                    <div class="loading-spinner-circular"></div>
                    <span>AI summarizing in progress...</span>
                </div>
            `;
            summaryContainer.style.display = 'block';
        }

        button.disabled = true;
        button.classList.add('loading');
        button.textContent = 'Summarizing...';
    }

    /**
     * Display the generated summary
     * @param {string} articleId - Article ID
     * @param {string} summary - Generated summary
     * @param {HTMLElement} button - Button element
     */
    displaySummary(articleId, summary, button) {
        const summaryContainer = document.getElementById(`summary-${articleId}`);
        if (summaryContainer) {
            // Format the summary based on the current preferences
            const preferences = this.getSummaryPreferences();
            let formattedSummary;
            
            if (preferences.type === 'key-points') {
                // Format as bullet points with * and each on one line
                const points = summary.split(/[.\n]/).filter(point => point.trim().length > 0);
                formattedSummary = points.map(point => `*${point.trim()}`).join('<br>');
            } else {
                // Keep as regular text for TLDR
                formattedSummary = this.escapeHtml(summary);
            }
            
            summaryContainer.innerHTML = `
                <div class="ai-summary-content">
                    <div class="summary-text">${formattedSummary}</div>
                    <button class="close-summary-btn" onclick="trendingArticles.hideSummary('${articleId}')">
                        ×
                    </button>
                </div>
            `;
            summaryContainer.style.display = 'block';
            
            // Add class to allow article card to expand
            const articleCard = document.querySelector(`[data-article-id="${articleId}"]`);
            if (articleCard) {
                articleCard.classList.add('has-ai-summary');
            }
        }

        this.resetButton(button);
        // Keep the button text as "AI Summarize" instead of changing it
        button.textContent = 'AI Summarize';
    }

    /**
     * Show error message
     * @param {string} articleId - Article ID
     * @param {string} message - Error message
     */
    showError(articleId, message) {
        const summaryContainer = document.getElementById(`summary-${articleId}`);
        if (summaryContainer) {
            summaryContainer.innerHTML = `
                <div class="ai-summary-error">
                    <span class="error-icon">!</span>
                    <span>Error: ${this.escapeHtml(message)}</span>
                </div>
            `;
            summaryContainer.style.display = 'block';
        }
    }

    /**
     * Show fallback message for unsupported browsers
     * @param {string} articleId - Article ID
     */
    showFallbackMessage(articleId) {
        const summaryContainer = document.getElementById(`summary-${articleId}`);
        if (summaryContainer) {
            summaryContainer.innerHTML = `
                <div class="ai-summary-fallback">
                    <span class="fallback-icon">🤖</span>
                    <h4>Setup Chrome AI Summarizer</h4>
                    <p style="margin: 0.5rem 0; font-size: 0.85rem;">📹 <a href="https://youtu.be/gJ36dPkt7Go?si=TZZDMQi57_jxD3ca&t=85" target="_blank" style="color: #007bff;">Watch setup video explanation</a></p>
                    <div style="text-align: left; margin: 1rem 0;">
                        <p><strong>Troubleshoot in Chrome</strong></p>
                        <p style="margin-left: 1rem; font-size: 0.85rem;">• Update Chrome to version 138 or later</p>
                        <p style="margin-left: 1rem; font-size: 0.85rem;">• Enable these flags in <code>chrome://flags/</code>:</p>
                        <p style="margin-left: 2rem; font-size: 0.8rem;">→ <code>optimization-guide-on-device-model</code> = <strong>Enabled BypassPerfRequirement</strong></p>
                        <p style="margin-left: 2rem; font-size: 0.8rem;">→ <code>prompt-api-for-gemini-nano</code> = <strong>Enabled</strong></p>
                        <p style="margin-left: 2rem; font-size: 0.8rem;">→ <code>summarization-api-for-gemini-nano</code> = <strong>Enabled</strong></p>
                        
                        <p><strong>Alternative: Chrome Canary (If don't work in your Chrome browser)</strong></p>
                        <p style="margin-left: 1rem; font-size: 0.85rem;">• Go to <code>google.com/chrome/canary</code></p>
                        <p style="margin-left: 1rem; font-size: 0.85rem;">• Download and install (runs alongside regular Chrome)</p>
                        <p style="margin-left: 1rem; font-size: 0.85rem;">• Enable these flags in <code>chrome://flags/</code>:</p>
                        <p style="margin-left: 2rem; font-size: 0.8rem;">→ <code>optimization-guide-on-device-model</code> = <strong>Enabled BypassPerfRequirement</strong></p>
                        <p style="margin-left: 2rem; font-size: 0.8rem;">→ <code>prompt-api-for-gemini-nano</code> = <strong>Enabled</strong></p>
                        <p style="margin-left: 2rem; font-size: 0.8rem;">→ <code>summarization-api-for-gemini-nano</code> = <strong>Enabled</strong></p>
                        <p style="margin-left: 1rem; font-size: 0.85rem;">• Click blue "Relaunch" button</p>                    
                    </div>
                    <button class="close-summary-btn" onclick="trendingArticles.hideSummary('${articleId}')">×</button>
                </div>
            `;
            summaryContainer.style.display = 'block';
        }
    }



    /**
     * Hide the summary display
     * @param {string} articleId - Article ID
     */
    hideSummary(articleId) {
        const summaryContainer = document.getElementById(`summary-${articleId}`);
        if (summaryContainer) {
            summaryContainer.style.display = 'none';
        }

        // Remove class to return article card to original size
        const articleCard = document.querySelector(`[data-article-id="${articleId}"]`);
        if (articleCard) {
            articleCard.classList.remove('has-ai-summary');
        }

        const button = document.querySelector(`[data-article-id="${articleId}"] .summarize-btn`);
        if (button) {
            button.textContent = 'AI Summarize';
        }
    }

    /**
     * Reset button to default state
     * @param {HTMLElement} button - Button element
     */
    resetButton(button) {
        button.disabled = false;
        button.classList.remove('loading');
    }

    /**
     * Escape HTML to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} HTML-escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Cleanup method to destroy AI session
     */
    destroy() {
        if (this.summarizerSession) {
            this.summarizerSession.destroy();
            this.summarizerSession = null;
        }
    }
}

const trendingArticles = new TrendingArticles();
window.trendingArticles = trendingArticles; // Expose globally for fast view

window.addEventListener('beforeunload', () => {
    trendingArticles.destroy();
});
