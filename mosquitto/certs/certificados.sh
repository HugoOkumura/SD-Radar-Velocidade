# Criar CA (Autoridade Certificadora)
openssl req -new -x509 -days 3650 -extensions v3_ca -keyout ca.key -out ca.crt -subj "/CN=MQTT CA"

# Criar chave do servidor
openssl genrsa -out server.key 2048

# Criar CSR (Certificate Signing Request)
openssl req -new -out server.csr -key server.key -subj "/CN=mosquitto"

# Assinar certificado do servidor
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 3650 -sha256

# Remover arquivos temporários
rm server.csr ca.key ca.srl