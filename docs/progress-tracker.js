// AI-300 Student Progress Tracker
// Tracks page views, bot interactions, assignments, and quizzes

class ProgressTracker {
    constructor() {
        this.apiUrl = this.getApiUrl();
        this.userEmail = null;
        this.progress = null;
        this.viewedPages = [];
        this.pageStartTime = Date.now();
        
        this.init();
    }
    
    getApiUrl() {
        const isLocal = window.location.hostname === 'localhost' || 
                       window.location.hostname === '127.0.0.1';
        
        if (isLocal) {
            const port = localStorage.getItem('bot_api_port') || '8003';
            return `http://localhost:${port}/api`;
        } else {
            const cloudflareUrl = localStorage.getItem('bot_cloudflare_url');
            if (cloudflareUrl) {
                return `${cloudflareUrl}/api`;
            }
            return 'https://ai300bot.tijerino.ai/api';
        }
    }
    
    async init() {
        // Try to get user email from Cloudflare Access cookie or localStorage
        this.userEmail = this.getUserEmail();
        
        if (!this.userEmail) {
            console.log('Progress tracking: No user email found, waiting for authentication...');
            // Check periodically for authentication
            setTimeout(() => this.init(), 5000);
            return;
        }
        
        // Load cached progress from localStorage
        this.loadLocalProgress();
        
        // Sync with server
        await this.syncProgress();
        
        // Track current page view
        this.trackPageView();
        
        // Set up page unload handler to record time spent
        window.addEventListener('beforeunload', () => this.recordTimeSpent());
        
        // Update progress display
        this.updateProgressDisplay();
        
        console.log('Progress tracking initialized for:', this.userEmail);
    }
    
    getUserEmail() {
        // Try to get from localStorage (set after Cloudflare Access auth)
        let email = localStorage.getItem('cf_access_email');
        if (email) return email;
        
        // Try to get from sessionStorage
        email = sessionStorage.getItem('cf_access_email');
        if (email) return email;
        
        // Try to parse from CF_Authorization cookie (JWT)
        const cfAuth = this.getCookie('CF_Authorization');
        if (cfAuth) {
            try {
                const payload = JSON.parse(atob(cfAuth.split('.')[1]));
                if (payload.email) {
                    localStorage.setItem('cf_access_email', payload.email);
                    return payload.email;
                }
            } catch (e) {
                console.log('Could not parse CF_Authorization cookie');
            }
        }
        
        // Fallback: use localStorage user ID (for local development)
        const userId = localStorage.getItem('ai300_user_id');
        if (userId) {
            return `${userId}@local.dev`;
        }
        
        return null;
    }
    
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }
    
    loadLocalProgress() {
        try {
            const cached = localStorage.getItem('ai300_progress');
            if (cached) {
                const data = JSON.parse(cached);
                this.progress = data.progress;
                this.viewedPages = data.viewedPages || [];
            }
        } catch (e) {
            console.error('Error loading local progress:', e);
        }
    }
    
    saveLocalProgress() {
        try {
            localStorage.setItem('ai300_progress', JSON.stringify({
                progress: this.progress,
                viewedPages: this.viewedPages,
                lastUpdated: new Date().toISOString()
            }));
        } catch (e) {
            console.error('Error saving local progress:', e);
        }
    }
    
    async syncProgress() {
        if (!this.userEmail) return;
        
        try {
            const response = await fetch(`${this.apiUrl}/progress/sync`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: this.userEmail,
                    local_data: {
                        viewed_pages: this.viewedPages.map(p => ({path: p}))
                    }
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.progress = data.progress;
                this.viewedPages = data.viewed_pages || [];
                this.saveLocalProgress();
            }
        } catch (e) {
            console.error('Error syncing progress:', e);
        }
    }
    
    async trackPageView() {
        if (!this.userEmail) return;
        
        const pagePath = this.getCurrentPagePath();
        const pageTitle = document.title;
        
        // Check if already viewed (locally)
        if (!this.viewedPages.includes(pagePath)) {
            this.viewedPages.push(pagePath);
            this.saveLocalProgress();
        }
        
        try {
            await fetch(`${this.apiUrl}/progress/page-view`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: this.userEmail,
                    page_path: pagePath,
                    page_title: pageTitle,
                    time_spent: 0
                })
            });
        } catch (e) {
            console.error('Error tracking page view:', e);
        }
    }
    
    getCurrentPagePath() {
        let path = window.location.pathname;
        // Remove leading slash and 'docs/' if present
        path = path.replace(/^\//, '').replace(/^docs\//, '');
        // Default to index.html if empty
        if (!path || path === '') path = 'index.html';
        return path;
    }
    
    async recordTimeSpent() {
        if (!this.userEmail) return;
        
        const timeSpent = Math.floor((Date.now() - this.pageStartTime) / 1000);
        const pagePath = this.getCurrentPagePath();
        
        // Use sendBeacon for reliability on page unload
        const data = JSON.stringify({
            email: this.userEmail,
            page_path: pagePath,
            page_title: document.title,
            time_spent: timeSpent
        });
        
        navigator.sendBeacon(`${this.apiUrl}/progress/page-view`, data);
    }
    
    async recordBotInteraction(question, response, language = 'ja', topic = null) {
        if (!this.userEmail) return;
        
        try {
            await fetch(`${this.apiUrl}/progress/bot-interaction`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: this.userEmail,
                    question: question,
                    response: response,
                    language: language,
                    topic: topic
                })
            });
            
            // Update local progress count
            if (this.progress && this.progress.bot_interactions) {
                this.progress.bot_interactions.count++;
                this.saveLocalProgress();
                this.updateProgressDisplay();
            }
        } catch (e) {
            console.error('Error recording bot interaction:', e);
        }
    }
    
    async getProgress() {
        if (!this.userEmail) return null;
        
        try {
            const response = await fetch(`${this.apiUrl}/progress/${this.userEmail}`);
            if (response.ok) {
                this.progress = await response.json();
                this.saveLocalProgress();
                return this.progress;
            }
        } catch (e) {
            console.error('Error getting progress:', e);
        }
        
        return this.progress;
    }
    
    updateProgressDisplay() {
        if (!this.progress) return;
        
        // Update progress dashboard if it exists
        this.updateDashboard();
        
        // Update header progress indicator if it exists
        this.updateHeaderIndicator();
        
        // Mark viewed pages in navigation
        this.markViewedPages();
    }
    
    updateDashboard() {
        const dashboard = document.getElementById('progress-dashboard');
        if (!dashboard) return;
        
        const p = this.progress;
        
        // Update content progress
        const contentPct = p.content?.percentage || 0;
        this.updateProgressRing('content-progress', contentPct);
        this.updateProgressText('content-text', `${p.content?.viewed || 0}/${p.content?.total || 0}`);
        
        // Update bot questions
        const botCount = p.bot_interactions?.count || 0;
        this.updateProgressText('bot-count', botCount);
        
        // Update assignments
        const assignPct = p.assignments?.percentage || 0;
        this.updateProgressRing('assignment-progress', assignPct);
        this.updateProgressText('assignment-text', `${p.assignments?.completed || 0}/${p.assignments?.total || 0}`);
        
        // Update quizzes
        const quizPassed = p.quizzes?.passed || 0;
        const quizAttempted = p.quizzes?.attempted || 0;
        this.updateProgressText('quiz-text', `${quizPassed} passed`);
        this.updateProgressText('quiz-avg', `${p.quizzes?.average_score || 0}% avg`);
    }
    
    updateProgressRing(elementId, percentage) {
        const ring = document.getElementById(elementId);
        if (!ring) return;
        
        const circle = ring.querySelector('.progress-ring-circle');
        if (circle) {
            const radius = circle.r.baseVal.value;
            const circumference = 2 * Math.PI * radius;
            const offset = circumference - (percentage / 100) * circumference;
            circle.style.strokeDasharray = `${circumference} ${circumference}`;
            circle.style.strokeDashoffset = offset;
        }
        
        const text = ring.querySelector('.progress-ring-text');
        if (text) {
            text.textContent = `${Math.round(percentage)}%`;
        }
    }
    
    updateProgressText(elementId, text) {
        const el = document.getElementById(elementId);
        if (el) el.textContent = text;
    }
    
    updateHeaderIndicator() {
        const indicator = document.getElementById('header-progress');
        if (!indicator || !this.progress) return;
        
        const overallPct = this.calculateOverallProgress();
        indicator.style.width = `${overallPct}%`;
        indicator.setAttribute('title', `Overall Progress: ${Math.round(overallPct)}%`);
    }
    
    calculateOverallProgress() {
        if (!this.progress) return 0;
        
        const contentWeight = 0.4;
        const assignmentWeight = 0.4;
        const quizWeight = 0.2;
        
        const contentPct = this.progress.content?.percentage || 0;
        const assignPct = this.progress.assignments?.percentage || 0;
        const quizPct = Math.min((this.progress.quizzes?.passed || 0) * 10, 100);
        
        return contentPct * contentWeight + 
               assignPct * assignmentWeight + 
               quizPct * quizWeight;
    }
    
    markViewedPages() {
        // Add 'viewed' class to navigation links for viewed pages
        this.viewedPages.forEach(pagePath => {
            const links = document.querySelectorAll(`a[href*="${pagePath}"]`);
            links.forEach(link => {
                link.classList.add('viewed');
                if (!link.querySelector('.view-check')) {
                    const check = document.createElement('span');
                    check.className = 'view-check';
                    check.textContent = ' ✓';
                    link.appendChild(check);
                }
            });
        });
    }
    
    // Quiz methods
    async generateQuiz(weekNumber = null, numQuestions = 5) {
        if (!this.userEmail) return null;
        
        try {
            const response = await fetch(`${this.apiUrl}/quiz/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: this.userEmail,
                    week_number: weekNumber,
                    num_questions: numQuestions,
                    difficulty: 'medium'
                })
            });
            
            if (response.ok) {
                return await response.json();
            }
        } catch (e) {
            console.error('Error generating quiz:', e);
        }
        return null;
    }
    
    async submitQuiz(quizId, answers, timeTaken = 0) {
        if (!this.userEmail) return null;
        
        try {
            const response = await fetch(`${this.apiUrl}/quiz/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: this.userEmail,
                    quiz_id: quizId,
                    answers: answers,
                    time_taken: timeTaken
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                // Refresh progress after quiz
                await this.syncProgress();
                this.updateProgressDisplay();
                return result;
            }
        } catch (e) {
            console.error('Error submitting quiz:', e);
        }
        return null;
    }
}

// Initialize progress tracker when DOM is ready
let progressTracker;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        progressTracker = new ProgressTracker();
        window.progressTracker = progressTracker;
    });
} else {
    progressTracker = new ProgressTracker();
    window.progressTracker = progressTracker;
}

