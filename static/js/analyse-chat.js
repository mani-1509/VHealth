document.addEventListener("DOMContentLoaded", async function () {
  let analysis = localStorage.getItem("picchat_analysis") || "Let's chat!";
  const chatMessages = document.getElementById("chat-messages");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const chatLoader = document.getElementById("chat-loader");

  // Show the analysis as a system message (UI only)
  chatMessages.innerHTML = `<div class="system-msg">${marked.parse(
    analysis
  )}</div>`;

  // Clean conversation history
  let history = [];

  // Set system behavior
  const followupPrompt = `
You're still the same certified AI health and fitness coach — smart, chill, and Gen Z-coded.

The user just got a full nutrition analysis from you based on their meal and health goal.

Now, your only job is to follow up with ONE friendly, casual question or encouragement to keep the convo going.

Be short, positive, and conversational (1-2 lines max)  
Use Gen Z slang, emojis, or reactions where it fits  
Don’t repeat the nutrition info  
Just vibe like a helpful, funny gym friend texting after a good chat

Examples:
- "That meal sounded solid! You gonna track your dinner too?"
- "You’re on a roll! Wanna plan tomorrow’s lunch together?"
- "Kinda proud of that pick tbh You feeling good after it?"
- "Lowkey want some dal now ngl What’s next on the menu?"
- "Alright Chef you tryna keep this streak alive or nah?"

Keep it vibey and low-pressure. Goal = keep them engaged.
`.trim();

  // Inject system prompt
  history.unshift({ role: "system", content: followupPrompt });

  // Inject image description as user message
  history.push({ role: "user", content: analysis });

  // Get first AI message
  const firstAI = await callBotAPI(null, history);
  appendMessage(firstAI.reply, "bot", firstAI.think);
  history.push({ role: "assistant", content: firstAI.reply });

  // Handle user chat input
  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = chatInput.value.trim();
    if (!msg) return;

    appendMessage(msg, "user");
    chatInput.value = "";
    history.push({ role: "user", content: msg });

    chatLoader.style.display = "flex";
    const botResult = await callBotAPI(null, history);
    chatLoader.style.display = "none";

    appendMessage(botResult.reply, "bot", botResult.think);
    history.push({ role: "assistant", content: botResult.reply });
    chatMessages.scrollTop = chatMessages.scrollHeight;
  });

  // Append message to chat UI
  function appendMessage(text, sender, think = null) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `${sender} message animate-in`;

    if (sender === "bot") {
      msgDiv.innerHTML = marked.parse(text);
    } else {
      msgDiv.textContent = text;
    }

    if (think && think.trim() !== "") {
      const details = document.createElement("details");
      details.className = "think-toggle";
      details.style.marginTop = "10px";
      details.style.cursor = "pointer";
      const summary = document.createElement("summary");
      summary.textContent = "Show AI's thinking🤔";
      summary.className = "think-summary";
      const thinkText = document.createElement("div");
      thinkText.textContent = think;
      thinkText.className = "think-content";
      details.appendChild(summary);
      details.appendChild(thinkText);
      msgDiv.appendChild(details);
    }

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    setTimeout(() => {
      msgDiv.classList.remove("animate-in");
    }, 400);
  }

  // API call to backend
  async function callBotAPI(message, history = null) {
    try {
      const res = await fetch("/chat_api", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(history ? { history } : { user_message: message }),
      });
      const data = await res.json();
      return {
        reply: data.reply || "Something went wrong!",
        think: data.thinking || "",
      };
    } catch {
      return { reply: "Something went wrong!", think: "" };
    }
  }
});
