async function submitRequest(e) {
  e.preventDefault();
  const body = {
    name: document.querySelector("#name").value,
    phone: document.querySelector("#phone").value,
    service: document.querySelector("#service").value,
    message: document.querySelector("#message").value
  };
  try {
    const r = await fetch("/api/request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || "ثبت درخواست ناموفق بود");
    alert("درخواست با موفقیت انجام شد ✔️");
    document.querySelector("form").reset();
  } catch (err) {
    alert(err.message);
  }
}
