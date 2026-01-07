// AI Chatbot with Google Gemini Integration

document.addEventListener('DOMContentLoaded', () => {
    setupChatbot();
});

function setupChatbot() {
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');
    const chatbotHeader = document.getElementById('chatbotHeader');
    const chatbotToggle = document.getElementById('chatbotToggle');
    const chatbot = document.getElementById('chatbot');
    
    if (!chatForm) {
        console.error('Chatbot form elements not found');
        return;
    }
    
    // Toggle chatbot
    if (chatbotHeader) {
        chatbotHeader.addEventListener('click', () => {
            chatbot.classList.toggle('minimized');
            chatbotToggle.textContent = chatbot.classList.contains('minimized') ? '+' : '−';
        });
    }
    
    // Handle chat form submission
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const message = chatInput.value.trim();
        if (!message) return;
        
        // Add user message
        addMessage(message, 'user');
        chatInput.value = '';
        chatInput.focus();
        
        // Show typing indicator
        const typingDiv = addTypingIndicator();
        
        try {
            console.log('Sending message:', message);
            
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });
            
            console.log('Response status:', response.status);
            
            const data = await response.json();
            console.log('Response data:', data);
            
            // Remove typing indicator
            if (typingDiv && typingDiv.parentNode) {
                typingDiv.remove();
            }
            
            // Add bot response
            if (data.response) {
                addMessage(data.response, 'bot');
            } else if (data.error) {
                addMessage('Error: ' + data.error, 'bot');
            } else {
                addMessage('Unable to get a response. Please try again.', 'bot');
            }
        } catch (error) {
            console.error('Chatbot error:', error);
            if (typingDiv && typingDiv.parentNode) {
                typingDiv.remove();
            }
            addMessage('Sorry, I encountered an error: ' + error.message + '. Please try again.', 'bot');
        }
    });
    
    // Add suggested questions
    addSuggestedQuestions();
}

function addMessage(text, sender) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = sender === 'user' ? 'user-message' : 'bot-message';
    
    const p = document.createElement('p');
    p.textContent = text;
    messageDiv.appendChild(p);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'bot-message typing-indicator';
    typingDiv.innerHTML = `
        <p>
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
        </p>
    `;
    
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return typingDiv;
}

function addSuggestedQuestions() {
    const chatMessages = document.getElementById('chatMessages');
    const suggestionsDiv = document.createElement('div');
    suggestionsDiv.className = 'bot-message';
    suggestionsDiv.innerHTML = `
        <p style="margin-bottom: 0.75rem; font-weight: 600;">Quick questions you can ask:</p>
        <div style="display: flex; flex-direction: column; gap: 0.5rem;">
            <button class="suggestion-btn" onclick="askQuestion('What are the seasonal trends for dairy products?')">
                Seasonal trends for dairy? 🥛
            </button>
            <button class="suggestion-btn" onclick="askQuestion('Which products have high demand in festivals?')">
                High demand in festivals? 🎉
            </button>
            <button class="suggestion-btn" onclick="askQuestion('How to manage inventory for summer?')">
                Summer inventory tips? ☀️
            </button>
            <button class="suggestion-btn" onclick="askQuestion('Suggest pricing strategy for new products')">
                Pricing strategies? 💰
            </button>
        </div>
    `;
    
    chatMessages.appendChild(suggestionsDiv);
}

function askQuestion(question) {
    const chatInput = document.getElementById('chatInput');
    chatInput.value = question;
    document.getElementById('chatForm').dispatchEvent(new Event('submit'));
}

// Add CSS for chatbot animations
const chatbotStyle = document.createElement('style');
chatbotStyle.textContent = `
    .typing-indicator {
        display: flex;
        gap: 0.25rem;
    }
    
    .typing-indicator .dot {
        width: 8px;
        height: 8px;
        background: #667eea;
        border-radius: 50%;
        display: inline-block;
        animation: typing 1.4s infinite;
    }
    
    .typing-indicator .dot:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    .typing-indicator .dot:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    @keyframes typing {
        0%, 60%, 100% {
            transform: translateY(0);
        }
        30% {
            transform: translateY(-10px);
        }
    }
    
    .suggestion-btn {
        padding: 0.75rem 1rem;
        background: white;
        border: 2px solid #667eea;
        border-radius: 8px;
        color: #667eea;
        font-size: 0.875rem;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: left;
        font-family: 'Poppins', sans-serif;
    }
    
    .suggestion-btn:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        transform: translateX(5px);
    }
`;
document.head.appendChild(chatbotStyle);