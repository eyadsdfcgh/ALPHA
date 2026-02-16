/* Global Chat JavaScript */

(function () {
    'use strict';

    function initChat() {
        // State
        let isAdmin = false;
        let lastMessageId = 0;
        let isChatOpen = false;

        // Inject CSS
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = '/static/chat.css';
        document.head.appendChild(link);

        // Chat HTML Template
        const chatHtml = `
            <div class="chat-widget" id="chatWidget" style="direction: rtl;">
                <button class="chat-button" id="chatToggleBtn">💬</button>
                <div class="chat-window" id="chatWindow">
                    <div class="chat-header">
                        <h3 style="margin:0; font-size: 16px;">📢 محادثة ALPHA</h3>
                        <span style="cursor:pointer; font-size: 20px;" id="closeChat">×</span>
                    </div>
                    <div class="chat-messages" id="chatMessages">
                        <div class="message-item" style="text-align:center">
                            <div class="message-content" style="color:rgba(255,255,255,0.4)">جاري تحميل الرسائل...</div>
                        </div>
                    </div>
                    <div class="chat-input-area" id="adminInput" style="display: none;">
                        <textarea class="chat-input" id="chatInput" placeholder="اكتب رسالة للطلاب..."></textarea>
                        <button class="send-btn" id="sendMsgBtn">إرسال للكل 🚀</button>
                    </div>
                </div>
            </div>
        `;

        // Inject Chat into Page
        document.body.insertAdjacentHTML('beforeend', chatHtml);

        // DOM Elements
        const toggleBtn = document.getElementById('chatToggleBtn');
        const windowEl = document.getElementById('chatWindow');
        const messagesEl = document.getElementById('chatMessages');
        const closeBtn = document.getElementById('closeChat');
        const adminInput = document.getElementById('adminInput');
        const sendBtn = document.getElementById('sendMsgBtn');
        const inputField = document.getElementById('chatInput');

        // Initial check for admin
        function checkAdminStatus() {
            fetch('/api/users')
                .then(res => {
                    if (res.ok) {
                        isAdmin = true;
                        adminInput.style.display = 'block';
                    }
                })
                .catch(() => { isAdmin = false; });
        }

        // Toggle Chat
        toggleBtn.addEventListener('click', () => {
            isChatOpen = !isChatOpen;
            windowEl.classList.toggle('active', isChatOpen);
            if (isChatOpen) {
                scrollToBottom();
                fetchMessages();
            }
        });

        closeBtn.addEventListener('click', () => {
            isChatOpen = false;
            windowEl.classList.remove('active');
        });

        // Fetch Messages
        async function fetchMessages() {
            try {
                const res = await fetch('/api/messages');
                const messages = await res.json();

                if (messages.length === 0) {
                    messagesEl.innerHTML = '<div style="text-align:center; color:rgba(255,255,255,0.4); margin-top:20px">لا توجد رسائل حالياً</div>';
                    return;
                }

                messagesEl.innerHTML = '';
                messages.forEach(msg => {
                    const item = document.createElement('div');
                    item.className = 'message-item';
                    item.innerHTML = `
                        <div class="message-sender">${msg.sender}</div>
                        <div class="message-content">${msg.content}</div>
                        <div class="message-time">${msg.timestamp}</div>
                    `;
                    messagesEl.appendChild(item);
                });

                lastMessageId = messages[messages.length - 1].id;
                if (isChatOpen) scrollToBottom();
            } catch (err) {
                console.error('Chat error:', err);
            }
        }

        function scrollToBottom() {
            messagesEl.scrollTop = messagesEl.scrollHeight;
        }

        // Send Message
        sendBtn.addEventListener('click', async () => {
            const content = inputField.value.trim();
            if (!content) return;

            sendBtn.disabled = true;
            sendBtn.textContent = 'جاري...';

            try {
                const res = await fetch('/api/messages', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content })
                });

                if (res.ok) {
                    inputField.value = '';
                    fetchMessages();
                } else {
                    alert('فشل الإرسال');
                }
            } catch (err) {
                alert('خطأ في الاتصال');
            } finally {
                sendBtn.disabled = false;
                sendBtn.textContent = 'إرسال للكل 🚀';
            }
        });

        setInterval(fetchMessages, 5000);
        checkAdminStatus();
        fetchMessages();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initChat);
    } else {
        initChat();
    }

})();
