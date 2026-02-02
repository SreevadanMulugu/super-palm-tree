// SuperPalmTree Web UI logic (monochrome UI)

const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const messagesEl = document.getElementById("messages");
const welcomeEl = document.getElementById("welcome");
const chatArea = document.getElementById("chatArea");
const inputField = document.getElementById("inputField");
const sendBtn = document.getElementById("sendBtn");
const statusProgress = document.getElementById("statusProgress");

function appendMessage(role, text) {
  if (welcomeEl) {
    welcomeEl.style.display = "none";
  }
  if (messagesEl.style.display === "none") {
    messagesEl.style.display = "flex";
  }

  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = role === "user" ? "You" : "AI";

  const bubble = document.createElement("div");
  bubble.className = "message-content";
  bubble.textContent = text;

  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  messagesEl.appendChild(wrapper);

  chatArea.scrollTop = chatArea.scrollHeight;
}

async function pollStatus() {
  try {
    const res = await fetch("/api/status");
    if (!res.ok) throw new Error("status HTTP " + res.status);
    const data = await res.json();

    const ready = !!data.ready;
    const phase = data.phase || "starting";
    const msg = data.status_message || (ready ? "Ready" : "Starting...");
    const progress = typeof data.progress === "number" ? data.progress : 0;

    statusText.textContent = msg;
    if (ready) {
      statusDot.classList.add("ready");
    } else {
      statusDot.classList.remove("ready");
    }

    if (statusProgress) {
      const clamped = Math.max(0, Math.min(100, progress));
      statusProgress.style.width = clamped + "%";
    }
  } catch (e) {
    statusText.textContent = "Waiting for backend...";
    statusDot.classList.remove("ready");
    if (statusProgress) {
      statusProgress.style.width = "0%";
    }
  } finally {
    setTimeout(pollStatus, 1000);
  }
}

async function sendMessage() {
  const text = (inputField.value || "").trim();
  if (!text) return;

  appendMessage("user", text);
  inputField.value = "";
  sendBtn.disabled = true;

  const typing = document.createElement("div");
  typing.className = "message assistant";
  typing.innerHTML =
    '<div class="message-avatar">AI</div><div class="typing"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>';
  messagesEl.appendChild(typing);
  chatArea.scrollTop = chatArea.scrollHeight;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const data = await res.json();
    messagesEl.removeChild(typing);
    appendMessage("assistant", data.response || data.error || "No response");
  } catch (e) {
    messagesEl.removeChild(typing);
    appendMessage("assistant", "Error contacting backend.");
  } finally {
    sendBtn.disabled = !inputField.value.trim();
  }
}

if (inputField && sendBtn) {
  inputField.addEventListener("input", () => {
    sendBtn.disabled = !inputField.value.trim();
  });

  inputField.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!sendBtn.disabled) sendMessage();
    }
  });

  sendBtn.addEventListener("click", sendMessage);
}

pollStatus();

