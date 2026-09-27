# Panther VPN deployment

## Fixed network identity

Panther LAN **must remain** `192.168.1.111`.

Current public IPv4 observed from Panther: `5.127.143.74`.

## Router

Forward only:

- UDP 500 -> `192.168.1.111:500`
- UDP 4500 -> `192.168.1.111:4500`

## Panther

1. Keep the existing strongSwan installation and certificates.
2. Install the connection from `ipsec.conf`.
3. Configure the EAP account in `/etc/ipsec.secrets`.
4. Enable IPv4 forwarding.
5. Apply forwarding/NAT rules for `10.250.0.0/24`.
6. Enable/start strongSwan.
7. Verify UDP 500/4500 and IKEv2 status.
8. Test from an external client.

## Certificate requirement

The existing server certificate has `192.168.1.111` as CN/SAN. A Windows client connecting to the public address needs a deliberate certificate identity strategy; preferably use a stable DNS name and issue the server certificate for that identity. Do not put private CA/server keys in GitHub.

## Client pool

`10.250.0.0/24`

## Secrets

Never commit `/etc/ipsec.secrets`, CA private keys, server private keys, or real EAP passwords.
