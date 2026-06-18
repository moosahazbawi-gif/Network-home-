function submitRequest(e) {
  e.preventDefault();

  fetch("http://localhost:3000/api/request", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: document.getElementById("name").value,
      phone: document.getElementById("phone").value,
      service: document.getElementById("service").value,
      message: document.getElementById("message").value
    })
  });

  alert("Sent ✔");
}