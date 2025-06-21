document.addEventListener("DOMContentLoaded", function () {
  const healthMetricForm = document.getElementById("health-metric-form");
  const loading = document.getElementById("loading");
  const tipsLoading = document.getElementById("tips-loading");
  const healthTips = document.getElementById("health-tips");

  // Handle form submission
  healthMetricForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    loading.classList.remove("hidden");

    const formData = new FormData(healthMetricForm);
    const data = Object.fromEntries(formData.entries());

    try {
      const response = await fetch("/api/health-metrics", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (!response.ok) throw new Error("Failed to submit metrics");
      healthMetricForm.reset();
      alert("Health metrics submitted successfully!");

      // Optionally, fetch new tips after submit
      if (tipsLoading && healthTips) {
        tipsLoading.classList.remove("hidden");
        healthTips.innerHTML = "";
        const tipsRes = await fetch("/api/health-tips");
        const tipsData = await tipsRes.json();
        tipsLoading.classList.add("hidden");
        healthTips.innerHTML = tipsData.health_tips
          ? `<b>Personalized Tips:</b><br>${tipsData.health_tips}`
          : "No tips available.";
      }
    } catch (error) {
      console.error("Error:", error);
      alert("Failed to submit health metrics. Please try again.");
    } finally {
      loading.classList.add("hidden");
    }
  });

  document.getElementById("get-tips-btn").onclick = async function () {
    tipsLoading.classList.remove("hidden");
    healthTips.innerHTML = "";
    // fetch tips...
    tipsLoading.classList.add("hidden");
  };
});
