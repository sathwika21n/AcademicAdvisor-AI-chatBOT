const chatLog = document.getElementById("chatLog");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const bubbleTemplate = document.getElementById("bubbleTemplate");
const majorInput = document.getElementById("majorInput");
const yearInput = document.getElementById("yearInput");
const interestsInput = document.getElementById("interestsInput");
const completedInput = document.getElementById("completedInput");
const quickButtons = document.querySelectorAll(".quick-btn");

const history = [];

const openingMessage =
  "Hi, I am your AI academic advisor. I can build a 4-year schedule, check prerequisites, suggest electives, and warn about graduation requirements.";
appendMessage("assistant", openingMessage);

quickButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    chatInput.value = btn.dataset.message || "";
    chatInput.focus();
  });
});

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
      body: JSON.stringify({
        message,
        history,
        profile: {
          major: majorInput.value.trim(),
          year: yearInput.value.trim(),
          interests: interestsInput.value.trim(),
          completed_courses: completedInput.value.trim(),
        },
      }),
    });

    if (!response.ok) {
      throw new Error(`Server error (${response.status})`);
    }

    const data = await response.json();
    const reply = data.reply || "Please share a bit more detail so I can help.";
    appendMessage("assistant", reply);
    history.push({ role: "assistant", content: reply });
  } catch (error) {
    appendMessage(
      "assistant",
      "I am having trouble connecting right now. Please try again in a moment."
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
