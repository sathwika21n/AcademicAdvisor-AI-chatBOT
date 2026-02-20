const chatLog = document.getElementById("chatLog");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const bubbleTemplate = document.getElementById("bubbleTemplate");

const history = [];

const openingMessage =
  "Hi, I’m MindHarbor. I can offer emotional support and practical coping steps. What’s on your mind today?";
appendMessage("assistant", openingMessage);

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  appendMessage("user", message);
  history.push({ role: "user", content: message });
  chatInput.value = "";
  setBusy(true);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
    });

    if (!response.ok) {
      throw new Error(`Server error (${response.status})`);
    }

    const data = await response.json();
    const reply = data.reply || "I’m here with you. Could you say a bit more?";
    appendMessage("assistant", reply);
    history.push({ role: "assistant", content: reply });
  } catch (error) {
    appendMessage(
      "assistant",
      "I’m having trouble connecting right now. Please try again in a moment."
    );
  } finally {
    setBusy(false);
    chatInput.focus();
  }
});

function appendMessage(role, text) {
  const node = bubbleTemplate.content.cloneNode(true);
  const wrap = node.querySelector(".bubble-wrap");
  const bubble = node.querySelector(".bubble");
  wrap.classList.add(role);
  bubble.textContent = text;
  chatLog.appendChild(node);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function setBusy(busy) {
  sendBtn.disabled = busy;
  sendBtn.textContent = busy ? "Sending..." : "Send";
  chatInput.disabled = busy;
}
