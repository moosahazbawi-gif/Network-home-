function submitRequest(e) {
  e.preventDefault();

  const name = document.querySelector("#name").value;
  const phone = document.querySelector("#phone").value;
  const service = document.querySelector("#service").value;
  const message = document.querySelector("#message").value;

  const request = {
    id: Date.now(),
    name,
    phone,
    service,
    message,
    date: new Date().toLocaleString()
  };

  let requests = JSON.parse(localStorage.getItem("requests")) || [];
  requests.push(request);
  localStorage.setItem("requests", JSON.stringify(requests));

  alert("تم إرسال الطلب بنجاح ✔️");

  document.querySelector("form").reset();
}