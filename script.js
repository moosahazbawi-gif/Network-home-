function sendToWhatsApp() {
  let name = document.getElementById("name").value;
  let phone = document.getElementById("phone").value;
  let service = document.getElementById("service").value;
  let message = document.getElementById("message").value;

  let text =
`طلب خدمة جديد:
👤 الاسم: ${name}
📱 الهاتف: ${phone}
🛠 الخدمة: ${service}
📝 التفاصيل: ${message}`;

  let url = "https://wa.me/989000000000?text=" + encodeURIComponent(text);

  window.open(url, "_blank");
}