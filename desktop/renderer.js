const fs = require('fs');
const path = require('path');

const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

const sessionId = "desktop-session-" + Math.floor(Math.random() * 1000000);

// Auto-scroll chat to bottom
function scrollToBottom() {
  const container = document.querySelector('.chat-container');
  container.scrollTop = container.scrollHeight;
}

// Add a message to the UI
function appendMessage(role, text) {
  const msgDiv = document.createElement('div');
  msgDiv.className = `message ${role}`;
  
  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';
  contentDiv.textContent = text;
  
  msgDiv.appendChild(contentDiv);
  chatBox.appendChild(msgDiv);
  scrollToBottom();
}

async function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  // Add user message
  appendMessage('user', text);
  userInput.value = '';
  
  // Add temporary loading message
  const loadingId = 'loading-' + Date.now();
  const loadingDiv = document.createElement('div');
  loadingDiv.className = 'message ai';
  loadingDiv.id = loadingId;
  loadingDiv.innerHTML = '<div class="message-content" style="opacity: 0.5;">Thinking...</div>';
  chatBox.appendChild(loadingDiv);
  scrollToBottom();

  try {
    const response = await fetch('https://ai-2-bj4c.onrender.com/api/v1/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        session_id: sessionId
      })
    });

    const data = await response.json();
    document.getElementById(loadingId).remove();
    appendMessage('ai', data.reply || data.error || "Unknown error occurred.");
    
  } catch (error) {
    document.getElementById(loadingId).remove();
    appendMessage('ai', "Error connecting to the backend core. Ensure it is running on port 8001.");
  }
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') sendMessage();
});

// Self-Evolution feature: Watch for changes to style.css and index.html and reload dynamically
const watchPath = path.join(__dirname);
fs.watch(watchPath, (eventType, filename) => {
  if (filename === 'style.css') {
    // Hot-reload CSS without refreshing the page
    const links = document.getElementsByTagName("link");
    for (let i = 0; i < links.length; i++) {
      const link = links[i];
      if (link.rel === "stylesheet" && link.href.includes("style.css")) {
        link.href = link.href.split("?")[0] + "?v=" + new Date().getTime();
      }
    }
  } else if (filename === 'index.html') {
    // Reload the whole window if HTML changes
    window.location.reload();
  }
});
