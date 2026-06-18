function sendToWhatsApp() {
  let name = document.getElementById("name").value;
  let phone = document.getElementById("phone").value;
  let service = document.getElementById("service").value;
  let message = document.getElementById("message").value;
let text =
`درخواست جدید سرویس:
👤 نام و نام خانوادگی: ${name}
📱 شماره تماس: ${phone}
🛠 خدمات انتخابی: ${service}
📝 جزئیات درخواست: ${message}`;

  let url = "https://wa.me/+989050780371?text=" + encodeURIComponent(text);

  window.open(url, "_blank");
}