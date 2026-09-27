# Panther VPN — IKEv2

حزمة إعداد VPN الخاصة بـ Panther-X2، مع إبقاء العنوان الداخلي الثابت `192.168.1.111`.

- LAN: `192.168.1.111`
- Gateway: `192.168.1.1`
- Public IPv4 الحالي: `5.127.143.74`
- البروتوكول: IKEv2 / strongSwan
- المنافذ: UDP 500 و UDP 4500
- شبكة العملاء: `10.250.0.0/24`

## البنية

```text
Internet
  |
  | UDP 500 / 4500
  v
5.127.143.74
  |
  v
192.168.1.111
  |
  +-- strongSwan / IKEv2
  +-- 10.250.0.0/24 VPN clients
  +-- NAT -> eth0
```

## الملفات

- `ipsec.conf` — اتصال IKEv2.
- `ipsec.secrets.example` — نموذج الأسرار، بلا أسرار حقيقية.
- `sysctl.conf` — forwarding.
- `nftables.conf` — forwarding/NAT.
- `DEPLOY.md` — ترتيب الإطلاق والتحقق.

## الشهادة

الشهادة الموجودة على Panther مرتبطة حاليًا بـ `192.168.1.111`. قبل اتصال Windows عبر العنوان الخارجي يجب أن تكون هوية شهادة الخادم مطابقة للهوية التي سيستخدمها العميل. لا تُرفع مفاتيح CA أو server private key إلى GitHub.
