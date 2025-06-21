document.addEventListener("DOMContentLoaded", function () {
  const emotionBtn = document.getElementById("pic-btn");
  const emotionResult = document.getElementById("pic-result");
  const loader = document.getElementById("loader");
  const video = document.getElementById("video");
  const startChatBtn = document.getElementById("start-chat-btn");
  const imageUpload = document.getElementById("image-upload");
  const imageUrlInput = document.getElementById("image-url");

  // Modal elements
  const mealModal = document.getElementById("meal-modal");
  const mealDescInput = document.getElementById("meal-desc-input");
  const goalInput = document.getElementById("goal-input");
  const modalOk = document.getElementById("modal-ok");
  const modalCancel = document.getElementById("modal-cancel");

  let analysisResult = "";
  let imagePayload = {};
  let onModalSubmit = null;

  emotionBtn.onclick = async function () {
    loader.style.display = "block";
    emotionResult.innerText = "";
    startChatBtn.style.display = "none";

    imagePayload = {};

    const url = imageUrlInput.value.trim();
    if (url) {
      imagePayload = { image_url: url };
    } else if (imageUpload.files && imageUpload.files[0]) {
      const file = imageUpload.files[0];
      const base64 = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const result = reader.result.split(",")[1];
          resolve(result);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
      imagePayload = { image_base64: base64 };
    } else if (video && video.srcObject && video.readyState >= 2) {
      const tempCanvas = document.createElement("canvas");
      tempCanvas.width = video.videoWidth || 320;
      tempCanvas.height = video.videoHeight || 240;
      const ctx = tempCanvas.getContext("2d");
      ctx.drawImage(video, 0, 0, tempCanvas.width, tempCanvas.height);
      const base64 = tempCanvas.toDataURL("image/png").split(",")[1];
      imagePayload = { image_base64: base64 };
    } else {
      loader.style.display = "none";
      emotionResult.innerText =
        "Please provide an image using URL, file upload, or webcam.";
      return;
    }

    // Show modal for meal description and goal
    mealDescInput.value = "";
    goalInput.value = "";
    mealModal.style.display = "flex";

    onModalSubmit = (meal_description, user_goal) => {
      fetch("/analyse_pic", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...imagePayload,
          user_message: "Analyze this meal.",
          meal_description: meal_description || "",
          user_goal: user_goal || "",
        }),
      })
        .then((res) => res.json())
        .then((data) => {
          loader.style.display = "none";
          analysisResult = data.reply || data.message || "No response.";
          let html = analysisResult.replace(/```html|```/g, "").trim();
          emotionResult.innerHTML = html; // NOT innerText
          startChatBtn.style.display = "block";
        })
        .catch(() => {
          loader.style.display = "none";
          emotionResult.innerText = "Error analyzing picture.";
        });
    };
  };

  modalOk.onclick = function () {
    const meal_description = mealDescInput.value.trim();
    const user_goal = goalInput.value.trim();
    if (!meal_description) {
      mealDescInput.classList.add("input-error");
      mealDescInput.focus();
      return;
    }
    mealDescInput.classList.remove("input-error");
    mealModal.style.display = "none";
    if (onModalSubmit) onModalSubmit(meal_description, user_goal);
  };

  modalCancel.onclick = function () {
    mealModal.style.display = "none";
    loader.style.display = "none";
    emotionResult.innerText = "Meal description is required.";
  };

  startChatBtn.onclick = function () {
    localStorage.setItem("analyse-chat", analysisResult);
    window.location.href = "/analyse-chat";
  };
});
