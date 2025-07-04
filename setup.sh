#!/bin/bash

secret=$(openssl rand -hex 32)
echo "JWT_SECRET_KEY=$secret" > .env

echo ".env file created with a secure JWT secret."
