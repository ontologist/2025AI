// AI-300 Bot Chat Interface
// Connects to backend API with RAG and Web Search capabilities

class AI300BotChat {
    constructor() {
        // Determine API URL based on environment
        this.apiUrl = this.getApiUrl();
        this.conversationHistory = [];
        this.currentUserId = this.getUserId();
        this.currentLanguage = 'en';
        this.isLoading = false;
        
        this.init();
    }
    
    getApiUrl() {
        // Check if we're on localhost (development)
        const isLocal = window.location.hostname === 'localhost' || 
                       window.location.hostname === '127.0.0.1' ||
                       window.location.hostname === '';
        
        // Check if we're on HTTPS (GitHub Pages)
        const isHttps = window.location.protocol === 'https:';
        
        if (isLocal) {
            // Local development - use HTTP on port 8003
            const port = localStorage.getItem('bot_api_port') || '8003';
            return `http://localhost:${port}/api`;
        } else if (isHttps) {
            // HTTPS page (GitHub Pages) - need HTTPS API via Cloudflare Tunnel
            const cloudflareUrl = localStorage.getItem('bot_cloudflare_url');
            if (cloudflareUrl) {
                return `${cloudflareUrl}/api`;
            }
            // Fallback: Default Cloudflare Tunnel URL (configure this)
            return 'https://ai300bot.tijerino.ai/api';
        } else {
            // HTTP page - can use HTTP API with fixed IP
            const port = localStorage.getItem('bot_api_port') || '8003';
            return `http://192.218.175.132:${port}/api`;
        }
    }
    
    getUserId() {
        let userId = localStorage.getItem('ai300_user_id');
        if (!userId) {
            userId = 'user_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('ai300_user_id', userId);
        }
        return userId;
    }
    
    init() {
        this.setupEventListeners();
        this.loadConversationHistory();
        this.showWelcomeMessage();
    }
    
    showWelcomeMessage() {
        const messagesContainer = document.getElementById('bot-messages');
        if (!messagesContainer || messagesContainer.children.length > 0) return;
        
        const welcomeEn = "👋 Hello! I'm AI-300 Bot, your assistant for the Basic Artificial Intelligence course. I can help you understand AI concepts, search algorithms, probability, and machine learning. Ask me anything!";
        const welcomeJa = "👋 こんにちは！AI-300ボットです。人工知能基礎コースのアシスタントとして、AIの概念、探索アルゴリズム、確率、機械学習について質問にお答えします。何でも聞いてください！";
        
        this.addMessageToUI('assistant', this.currentLanguage === 'ja' ? welcomeJa : welcomeEn);
    }
    
    setupEventListeners() {
        const sendButton = document.getElementById('bot-send-btn');
        const messageInput = document.getElementById('bot-message-input');
        const languageToggle = document.getElementById('bot-language-toggle');
        const clearButton = document.getElementById('bot-clear-btn');
        
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
        
        if (clearButton) {
            clearButton.addEventListener('click', () => this.clearConversation());
        }
    }
    
    loadConversationHistory() {
        const saved = localStorage.getItem('ai300_conversation');
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
        localStorage.setItem('ai300_conversation', JSON.stringify(this.conversationHistory));
    }
    
    updateLanguageUI() {
        const chatContainer = document.getElementById('bot-chat-container');
        if (chatContainer) {
            chatContainer.setAttribute('data-lang', this.currentLanguage);
        }
        
        // Update placeholder text
        const messageInput = document.getElementById('bot-message-input');
        if (messageInput) {
            messageInput.placeholder = this.currentLanguage === 'ja' 
                ? 'AIについて質問してください...' 
                : 'Ask about AI concepts...';
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
            
            // Call API
            const response = await fetch(`${this.apiUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true',
                },
                body: JSON.stringify({
                    user_id: this.currentUserId,
                    message: message,
                    language: this.currentLanguage,
                    conversation_history: history,
                    use_rag: true,
                    use_web_search: true
                })
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`API error: ${response.status} - ${errorText.substring(0, 100)}`);
            }
            
            const responseText = await response.text();
            let data;
            try {
                data = JSON.parse(responseText);
            } catch (parseError) {
                if (responseText.includes('html') || responseText.length === 0) {
                    throw new Error('Service unavailable. Please check if the backend is running.');
                }
                throw new Error(`Invalid response: ${responseText.substring(0, 200)}`);
            }
            
            // Add messages to history
            this.conversationHistory.push({ role: 'user', content: message });
            this.conversationHistory.push({ role: 'assistant', content: data.response });
            this.saveConversationHistory();
            
            // Add bot response to UI with source indicators
            let responseWithSources = data.response;
            if (data.web_search_used) {
                responseWithSources += '\n\n🔍 _Web search was used to enhance this response._';
            }
            this.addMessageToUI('assistant', responseWithSources);
            
        } catch (error) {
            console.error('Chat error:', error);
            
            let errorMessage = '';
            if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                const isHttps = window.location.protocol === 'https:';
                const apiIsHttp = this.apiUrl.startsWith('http://');
                
                if (isHttps && apiIsHttp) {
                    errorMessage = this.currentLanguage === 'ja'
                        ? '⚠️ HTTPSページからHTTP APIに接続できません。ローカルでテストする場合は、http://localhost で開いてください。'
                        : '⚠️ Cannot connect to HTTP API from HTTPS page. For local testing, open at http://localhost';
                } else {
                    errorMessage = this.currentLanguage === 'ja'
                        ? '⚠️ APIサーバーに接続できません。バックエンドが起動しているか確認してください。'
                        : '⚠️ Cannot connect to API server. Please ensure the backend is running at ' + this.apiUrl;
                }
            } else {
                errorMessage = this.currentLanguage === 'ja'
                    ? '⚠️ エラーが発生しました: ' + error.message
                    : '⚠️ An error occurred: ' + error.message;
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
        
        const botName = this.currentLanguage === 'ja' ? 'AI-300 ボット' : 'AI-300 Bot';
        const userName = this.currentLanguage === 'ja' ? 'あなた' : 'You';
        
        if (role === 'user') {
            messageDiv.innerHTML = `
                <div class="bot-message-content">
                    <strong>${userName}:</strong> ${this.escapeHtml(content)}
                </div>
            `;
        } else if (role === 'assistant') {
            messageDiv.innerHTML = `
                <div class="bot-message-content">
                    <strong>🤖 ${botName}:</strong> ${this.formatBotResponse(content)}
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
            .replace(/_(.+?)_/g, '<em>$1</em>')
            .replace(/`(.+?)`/g, '<code>$1</code>')
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
        const confirmMsg = this.currentLanguage === 'ja' 
            ? '会話履歴をクリアしますか？'
            : 'Clear conversation history?';
            
        if (confirm(confirmMsg)) {
            this.conversationHistory = [];
            this.saveConversationHistory();
            const messagesContainer = document.getElementById('bot-messages');
            if (messagesContainer) {
                messagesContainer.innerHTML = '';
            }
            this.showWelcomeMessage();
        }
    }
}

// Initialize chat when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.ai300BotChat = new AI300BotChat();
    });
} else {
    window.ai300BotChat = new AI300BotChat();
}
