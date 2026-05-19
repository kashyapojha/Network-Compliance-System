#!/bin/bash
#
# Setup script for FreeRADIUS certificates
# Copies CA and server certificates to FreeRADIUS directory
#

set -e

# Paths
CERT_DIR="../../certificates"
RADIUS_CERT_DIR="./certs"

# Create FreeRADIUS certs directory
mkdir -p "$RADIUS_CERT_DIR"

# Copy CA certificate
cp "$CERT_DIR/ca/ca_cert.pem" "$RADIUS_CERT_DIR/ca.pem"
echo "Copied CA certificate"

# Copy server certificate (if exists)
if [ -f "$CERT_DIR/ca/server.pem" ]; then
    cp "$CERT_DIR/ca/server.pem" "$RADIUS_CERT_DIR/server.pem"
    echo "Copied server certificate"
fi

# Copy server private key (if exists)
if [ -f "$CERT_DIR/ca/server.key" ]; then
    cp "$CERT_DIR/ca/server.key" "$RADIUS_CERT_DIR/server.key"
    echo "Copied server private key"
fi

# Generate DH parameters if not exists
if [ ! -f "$RADIUS_CERT_DIR/dh.pem" ]; then
    openssl dhparam -out "$RADIUS_CERT_DIR/dh.pem" 2048
    echo "Generated DH parameters"
fi

# Set permissions
chmod 644 "$RADIUS_CERT_DIR"/*.pem
chmod 600 "$RADIUS_CERT_DIR/server.key"

echo "Certificate setup complete"
