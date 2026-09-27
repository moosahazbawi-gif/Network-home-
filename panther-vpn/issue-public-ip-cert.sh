#!/usr/bin/env bash
set -euo pipefail

CA_KEY=/etc/ipsec.d/private/panther-ca-key.pem
CA_CERT=/etc/ipsec.d/cacerts/panther-ca-cert.pem
SERVER_KEY=/etc/ipsec.d/private/panther-server-key.pem
SERVER_CERT=/etc/ipsec.d/certs/panther-server-cert.pem
TMP=/tmp/panther-vpn-cert
PUBLIC_IP="5.127.143.74"

umask 077
mkdir -p "$TMP"

openssl req -new -newkey rsa:3072 -nodes \
  -keyout "$SERVER_KEY.new" \
  -out "$TMP/server.csr" \
  -subj "/CN=$PUBLIC_IP"

cat > "$TMP/server-ext.cnf" <<EOF
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=IP:$PUBLIC_IP
EOF

openssl x509 -req -sha256 -days 825 \
  -in "$TMP/server.csr" \
  -CA "$CA_CERT" -CAkey "$CA_KEY" -CAcreateserial \
  -out "$SERVER_CERT.new" \
  -extfile "$TMP/server-ext.cnf"

openssl verify -CAfile "$CA_CERT" "$SERVER_CERT.new"

install -m 600 "$SERVER_KEY.new" "$SERVER_KEY"
install -m 644 "$SERVER_CERT.new" "$SERVER_CERT"
rm -rf "$TMP"

echo "Installed IKEv2 server certificate for IP SAN $PUBLIC_IP"
