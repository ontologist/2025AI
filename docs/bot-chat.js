// ML-101 Bot Chat Interface
// Connects to backend API - automatically detects environment

class ML101BotChat {
    constructor() {
        // Determine API URL based on environment
        this.apiUrl = this.getApiUrl();
        this.conversationHistory = [];
        this.currentUserId = null;
        this.currentUserEmail = null;
        this.currentLanguage = 'en';
        this.isLoading = false;
        this.isAuthenticated = false;
        
        // Initialize login first
        this.initAuth();
    }
    
    initAuth() {
        // Check if login is required
        const authOverride = localStorage.getItem('bot_require_auth');
        let requiresAuth;

        if (authOverride !== null) {
            requiresAuth = authOverride === 'true';
        } else {
            // Default: allow access without OTP to avoid blocking while email is unconfigured.
            requiresAuth = false;
        }
        
        if (requiresAuth) {
            // Initialize login
            this.login = new BotLogin(this.apiUrl, (userId, email) => {
                this.currentUserId = userId;
                this.currentUserEmail = email;
                this.isAuthenticated = true;
                this.init();
            });
        } else {
            // No auth required - use local storage
            this.currentUserId = this.getUserId();
            this.isAuthenticated = true;
            this.init();
        }
    }
    
    getApiUrl() {
        // Check if we're on localhost (development)
        const isLocal = window.location.hostname === 'localhost' || 
                       window.location.hostname === '127.0.0.1' ||
                       window.location.hostname === '';
        
        // Check if we're on HTTPS (GitHub Pages)
        const isHttps = window.location.protocol === 'https:';
        
        // For HTTPS pages, we need HTTPS API URL
        // For local development, HTTP is fine
        if (isLocal) {
            // Local development - use HTTP
            // Check for port override in URL hash or localStorage
            const port = localStorage.getItem('bot_api_port') || '8001';
            return `http://localhost:${port}/api`;
        } else if (isHttps) {
            // HTTPS page (GitHub Pages) - need HTTPS API
            // Check for Cloudflare Tunnel URL in localStorage or default
            const cloudflareUrl = localStorage.getItem('bot_cloudflare_url');
            if (cloudflareUrl) {
                return `${cloudflareUrl}/api`;
            }
            // Fallback: Default to latest ngrok/Cloudflare URL
            // Update this when tunnel changes
            return 'https://8073b9e974bf.ngrok-free.app/api';
        } else {
            // HTTP page - can use HTTP API with fixed IP
            const port = localStorage.getItem('bot_api_port') || '8001';
            return `http://192.218.175.132:${port}/api`;
        }
    }
    
    getUserId() {
        // Try to get user ID from localStorage or generate one
        let userId = localStorage.getItem('bot_user_id');
        if (!userId) {
            // Fallback for non-authenticated local use
            userId = 'user_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('bot_user_id', userId);
        }
        return userId;
    }
    
    init() {
        this.setupEventListeners();
        this.loadConversationHistory();
        this.checkApiUrl();
    }
    
    checkApiUrl() {
        // Show notice if API URL is not configured for HTTPS
        const isHttps = window.location.protocol === 'https:';
        const needsHttps = isHttps && (this.apiUrl.includes('YOUR_HTTPS_API_URL') || 
                                      (this.apiUrl.startsWith('http://') && !this.apiUrl.includes('localhost')));
        
        if (needsHttps) {
            const notice = document.getElementById('bot-https-notice');
            if (notice) {
                notice.style.display = 'block';
            }
            console.warn('⚠️ HTTPS API URL not configured. See docs/HTTPS-SETUP.md');
            console.warn('Current API URL:', this.apiUrl);
        }
    }
    
    setupEventListeners() {
        const sendButton = document.getElementById('bot-send-btn');
        const messageInput = document.getElementById('bot-message-input');
        const languageToggle = document.getElementById('bot-language-toggle');
        
        if (sendButton) {
            sendButton.addEventListener('click', () => this.sendMessage());
        }
        
        if (messageInput) {
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }
        
        if (languageToggle) {
            languageToggle.addEventListener('change', (e) => {
                this.currentLanguage = e.target.value;
                this.updateLanguageUI();
            });
        }
    }
    
    loadConversationHistory() {
        const saved = localStorage.getItem('ml101_conversation');
        if (saved) {
            try {
                this.conversationHistory = JSON.parse(saved);
                this.renderConversationHistory();
            } catch (e) {
                console.error('Error loading conversation:', e);
            }
        }
    }
    
    saveConversationHistory() {
        localStorage.setItem('ml101_conversation', JSON.stringify(this.conversationHistory));
    }
    
    updateLanguageUI() {
        const chatContainer = document.getElementById('bot-chat-container');
        if (!chatContainer) return;
        
        if (this.currentLanguage === 'ja') {
            chatContainer.setAttribute('data-lang', 'ja');
        } else {
            chatContainer.setAttribute('data-lang', 'en');
        }
    }
    
    async sendMessage() {
        const messageInput = document.getElementById('bot-message-input');
        if (!messageInput) return;
        
        const message = messageInput.value.trim();
        if (!message || this.isLoading) return;
        
        // Add user message to UI
        this.addMessageToUI('user', message);
        messageInput.value = '';
        
        // Show loading indicator
        this.setLoading(true);
        
        try {
            // Prepare conversation history for API
            const history = this.conversationHistory.map(msg => ({
                role: msg.role,
                content: msg.content
            }));
            
            // Add current message to history
            history.push({ role: 'user', content: message });
            
            // Call API
            const response = await fetch(`${this.apiUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: this.currentUserId,
                    message: message,
                    language: this.currentLanguage,
                    conversation_history: history.slice(0, -1), // Exclude current message
                    use_rag: true
                })
            });
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Add messages to history
            this.conversationHistory.push({ role: 'user', content: message });
            this.conversationHistory.push({ role: 'assistant', content: data.response });
            this.saveConversationHistory();
            
            // Add bot response to UI
            this.addMessageToUI('assistant', data.response);
            
        } catch (error) {
            console.error('Chat error:', error);
            
            // Provide more detailed error messages
            let errorMessage = '';
            if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                // Network/CORS error
                const isHttps = window.location.protocol === 'https:';
                const apiIsHttp = this.apiUrl.startsWith('http://');
                
                if (isHttps && apiIsHttp) {
                    // Mixed content error (HTTPS page trying to access HTTP API)
                    errorMessage = this.currentLanguage === 'ja'
                        ? 'セキュリティ上の理由により、HTTPSページからHTTP APIに接続できません。ローカルでテストする場合は、http://localhost:8000 でページを開いてください。'
                        : 'Cannot connect to HTTP API from HTTPS page (mixed content blocked). For local testing, open this page at http://localhost:8000 or use a proxy.';
                } else {
                    // General network error
                    errorMessage = this.currentLanguage === 'ja'
                        ? 'APIサーバーに接続できません。バックエンドサーバーが起動しているか確認してください。'
                        : 'Cannot connect to API server. Please ensure the backend server is running at ' + this.apiUrl;
                }
            } else {
                // Other errors
                errorMessage = this.currentLanguage === 'ja'
                    ? 'エラーが発生しました: ' + error.message
                    : 'An error occurred: ' + error.message;
            }
            
            this.addMessageToUI('system', errorMessage);
        } finally {
            this.setLoading(false);
        }
    }
    
    addMessageToUI(role, content) {
        const messagesContainer = document.getElementById('bot-messages');
        if (!messagesContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `bot-message bot-message-${role}`;
        
        if (role === 'user') {
            messageDiv.innerHTML = `
                <div class="bot-message-content">
                    <strong>You:</strong> ${this.escapeHtml(content)}
                </div>
            `;
        } else if (role === 'assistant') {
            messageDiv.innerHTML = `
                <div class="bot-message-content">
                    <strong>ML-101 Bot:</strong> ${this.formatBotResponse(content)}
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="bot-message-content bot-message-system">
                    ${this.escapeHtml(content)}
                </div>
            `;
        }
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    formatBotResponse(text) {
        // Basic markdown-like formatting
        return this.escapeHtml(text)
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    setLoading(loading) {
        this.isLoading = loading;
        const sendButton = document.getElementById('bot-send-btn');
        const messageInput = document.getElementById('bot-message-input');
        
        if (sendButton) {
            sendButton.disabled = loading;
            sendButton.textContent = loading 
                ? (this.currentLanguage === 'ja' ? '送信中...' : 'Sending...')
                : (this.currentLanguage === 'ja' ? '送信' : 'Send');
        }
        
        if (messageInput) {
            messageInput.disabled = loading;
        }
        
        // Show/hide loading indicator
        const loadingIndicator = document.getElementById('bot-loading');
        if (loadingIndicator) {
            loadingIndicator.style.display = loading ? 'block' : 'none';
        }
    }
    
    renderConversationHistory() {
        const messagesContainer = document.getElementById('bot-messages');
        if (!messagesContainer) return;
        
        messagesContainer.innerHTML = '';
        this.conversationHistory.forEach(msg => {
            this.addMessageToUI(msg.role, msg.content);
        });
    }
    
    clearConversation() {
        if (confirm(this.currentLanguage === 'ja' 
            ? '会話履歴をクリアしますか？'
            : 'Clear conversation history?')) {
            this.conversationHistory = [];
            this.saveConversationHistory();
            const messagesContainer = document.getElementById('bot-messages');
            if (messagesContainer) {
                messagesContainer.innerHTML = '';
            }
        }
    }
}

// Initialize chat when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.ml101BotChat = new ML101BotChat();
    });
} else {
    window.ml101BotChat = new ML101BotChat();
}

