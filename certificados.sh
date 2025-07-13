#!/bin/bash

# Certificados para o GRPC
# Generate CA
openssl genrsa -out ca-key.pem 4096
openssl req -new -x509 -days 365 -key ca-key.pem -out ca-cert.pem -subj "/CN=MultasCA"

# Generate server cert
openssl genrsa -out server-key.pem 4096
openssl req -new -key server-key.pem -out server.csr -subj "/CN=servico_multas"
openssl x509 -req -days 365 -in server.csr -CA ca-cert.pem -CAkey ca-key.pem -CAcreateserial -out server-cert.pem

# Copy certs to appropriate services
cp ca-cert.pem servico_leituras/
cp server-key.pem servico_multas/
cp server-cert.pem servico_multas/
cp ca-cert.pem servico_multas/

# Cleanup
rm server.csr