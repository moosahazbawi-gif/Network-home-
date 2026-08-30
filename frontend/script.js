async function submitRequest(e) {
  e.preventDefault();
  const body = {
    name: document.getElementById("name").value,
    phone: document.getElementById("phone").value,
    service: document.getElementById("service").value,
    message: document.getElementById("message").value
  };
  await fetch("/api/request", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  alert("Sent ✔");
}

async function askPanther() {
  const input = document.getElementById("pantherPrompt");
  const output = document.getElementById("pantherAnswer");
  const button = document.getElementById("pantherSend");
  const prompt = input.value.trim();
  if (!prompt) return;
  button.disabled = true;
  output.textContent = "...";
  try {
    const r = await fetch("/api/panther/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt })
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || "Panther unavailable");
    output.textContent = data.answer || "لا توجد إجابة";
  } catch (err) {
    output.textContent = `خطأ: ${err.message}`;
  } finally {
    button.disabled = false;
  }
}

document.getElementById("pantherSend")?.addEventListener("click", askPanther);
document.getElementById("pantherPrompt")?.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) askPanther();
});
