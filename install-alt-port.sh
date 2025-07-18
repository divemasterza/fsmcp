#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "===================================================="
echo " Nextcloud MCP API - Alternative Port Deployment "
echo "===================================================="

# --- 1. Check for .env file and create if not exists ---
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "New .env file created. Please fill in your Nextcloud and API details."
fi

# --- 2. Load existing .env variables (if any) ---
if [ -f .env ]; then
    export $(grep -v '^\\s*#' .env | grep -v '^\\s*$' | xargs)
fi

# --- 3. Function to prompt for a variable and update .env ---
prompt_and_update_env() {
    local var_name=$1
    local prompt_text=$2
    local placeholder_value=$3
    local current_value=$(eval echo \\$$var_name)

    if [ -z "$current_value" ] || [ "$current_value" == "$placeholder_value" ]; then
        read -p "Enter $prompt_text: " new_value
        if [ -z "$new_value" ]; then
            echo "$prompt_text cannot be empty. Exiting."
            exit 1
        fi
        sed -i.bak "s|^#*\\s*${var_name}=.*|${var_name}=\\\"$new_value\\\"|g" .env
        rm .env.bak
        export $var_name="$new_value"
        echo "Updated $var_name in .env"
    else
        echo "$prompt_text is already set in .env (current value: $current_value)"
    fi
}

# --- 4. Prompt for credentials ---
prompt_and_update_env "NEXTCLOUD_INSTANCE_URL" "Nextcloud Instance URL (e.g., https://your.nextcloud.com)" "https://your-nextcloud-instance.com"
prompt_and_update_env "NEXTCLOUD_USERNAME" "Nextcloud Username" "your_username"
prompt_and_update_env "NEXTCLOUD_PASSWORD" "Nextcloud Password (App password recommended)" "your_password"
prompt_and_update_env "API_KEY" "API Key for FastAPI (generate a strong, random key)" "your_super_secret_api_key"
prompt_and_update_env "DOMAIN_NAME" "Domain Name for your API (e.g., api.yourdomain.com)" "your.domain.com"
prompt_and_update_env "CERTBOT_EMAIL" "Email for Certbot notifications" "your.email@example.com"

# --- 5. Create nginx directory ---
echo "Ensuring nginx configuration directory exists..."
mkdir -p nginx

# --- 6. Build Docker images ---
echo ""
echo "--- Building Docker images ---"
/usr/local/bin/docker-compose build

# --- 7. Check if we need SSL certificates ---
echo ""
echo "--- SSL Certificate Setup ---"
echo "Note: This deployment uses alternative ports (8080 for HTTP, 8443 for HTTPS)"
echo "For SSL certificates, you have two options:"
echo "1. Skip SSL for now and access via HTTP at http://$DOMAIN_NAME:8080"
echo "2. Manually set up SSL certificates later"

read -p "Do you want to skip SSL setup for now? (y/n): " skip_ssl

if [ "$skip_ssl" == "y" ] || [ "$skip_ssl" == "Y" ]; then
    echo "Skipping SSL setup. Starting services without SSL..."
    
    # Create a simple nginx config without SSL
    cat > nginx/nginx.conf << 'NGINX_EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX_EOF
    
    # Update docker-compose to not expose 443
    cat > docker-compose.yml << 'COMPOSE_EOF'
version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    command: uvicorn api:app --host 0.0.0.0 --port 8000
    volumes:
      - .:/app
    env_file:
      - ./.env
    expose:
      - "8000"
    networks:
      - app-network

  nginx:
    image: nginx:latest
    ports:
      - "8080:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - web
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
COMPOSE_EOF

    echo ""
    echo "--- Starting the Nextcloud MCP API stack ---"
    /usr/local/bin/docker-compose up -d
    
    echo ""
    echo "===================================================="
    echo " Deployment Complete! "
    echo " Your Nextcloud MCP API is running at http://$DOMAIN_NAME:8080 "
    echo " Access API docs at http://$DOMAIN_NAME:8080/docs "
    echo " Note: This is running on HTTP only. Set up SSL manually if needed."
    echo "===================================================="
else
    echo ""
    echo "--- Setting up SSL certificates ---"
    echo "This requires temporarily stopping the existing service on port 80..."
    
    # Check if user wants to proceed with stopping the existing service
    echo "WARNING: This will temporarily stop the existing nginx service on port 80"
    read -p "Do you want to proceed? (y/n): " proceed_ssl
    
    if [ "$proceed_ssl" == "y" ] || [ "$proceed_ssl" == "Y" ]; then
        echo "Temporarily stopping existing nginx service..."
        sudo systemctl stop nginx || true
        
        echo "Setting up SSL certificates..."
        echo "Please ensure your domain $DOMAIN_NAME points to this server's IP address."
        read -p "Press Enter to continue..."
        
        # Use the original SSL setup but then move to alternative ports
        /usr/local/bin/docker-compose up -d nginx
        /usr/local/bin/docker-compose run --rm certbot
        /usr/local/bin/docker-compose stop nginx
        
        # Restore original nginx service
        sudo systemctl start nginx || true
        
        echo ""
        echo "--- Starting the full stack with SSL ---"
        /usr/local/bin/docker-compose up -d
        
        echo ""
        echo "===================================================="
        echo " Deployment Complete! "
        echo " Your Nextcloud MCP API is running at https://$DOMAIN_NAME:8443 "
        echo " Access API docs at https://$DOMAIN_NAME:8443/docs "
        echo "===================================================="
    else
        echo "SSL setup cancelled. Starting without SSL..."
        /usr/local/bin/docker-compose up -d
        
        echo ""
        echo "===================================================="
        echo " Deployment Complete! "
        echo " Your Nextcloud MCP API is running at http://$DOMAIN_NAME:8080 "
        echo " Access API docs at http://$DOMAIN_NAME:8080/docs "
        echo "===================================================="
    fi
fi
