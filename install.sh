#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "===================================================="
echo " Nextcloud MCP API - Automated Docker Deployment "
echo "===================================================="

# --- 1. Check for .env file and create if not exists ---
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "New .env file created. Please fill in your Nextcloud and API details."
fi

# --- 2. Load existing .env variables (if any) ---
# This is a safe way to load variables without executing arbitrary code
# and only if the file exists.
if [ -f .env ]; then
    export $(grep -v '^\s*#' .env | xargs)
fi

# --- 3. Prompt for Nextcloud Credentials if missing or are placeholders ---

# Function to prompt for a variable and update .env
prompt_and_update_env() {
    local var_name=$1
    local prompt_text=$2
    local placeholder_value=$3 # New: placeholder value to check against
    local current_value=$(eval echo \$$var_name)

    # Check if current_value is empty OR matches the placeholder
    if [ -z "$current_value" ] || [ "$current_value" == "$placeholder_value" ]; then
        read -p "Enter $prompt_text: " new_value
        if [ -z "$new_value" ]; then
            echo "$prompt_text cannot be empty. Exiting."
            exit 1
        fi
        # Update the .env file using sed
        # Use a temporary file for sed output to avoid issues with in-place editing
        sed -i.bak "s|^#*\s*${var_name}=.*|${var_name}=\"$new_value\"|g" .env
        rm .env.bak
        export $var_name="$new_value"
        echo "Updated $var_name in .env"
    else
        echo "$prompt_text is already set in .env (current value: $current_value)"
    fi
}

prompt_and_update_env "NEXTCLOUD_INSTANCE_URL" "Nextcloud Instance URL (e.g., https://your.nextcloud.com)" "https://your-nextcloud-instance.com"
prompt_and_update_env "NEXTCLOUD_USERNAME" "Nextcloud Username" "your_username"
prompt_and_update_env "NEXTCLOUD_PASSWORD" "Nextcloud Password (App password recommended)" "your_password"
prompt_and_update_env "API_KEY" "API Key for FastAPI (generate a strong, random key)" "your_super_secret_api_key"

# Optional: Prompt for NEXTCLOUD_USAGE_FOLDER if not set
# Note: This one doesn't strictly need a placeholder check as it's optional and can be empty
if [ -z "$NEXTCLOUD_USAGE_FOLDER" ] || [ "$NEXTCLOUD_USAGE_FOLDER" == "MCP-Uploads" ]; then
    read -p "Enter Nextcloud Usage Folder (optional, leave empty for root, current: $NEXTCLOUD_USAGE_FOLDER): " new_usage_folder
    # Update the .env file only if a value was provided or if it was the placeholder
    if [ -n "$new_usage_folder" ] || [ "$NEXTCLOUD_USAGE_FOLDER" == "MCP-Uploads" ]; then
        sed -i.bak "s|^#*\s*NEXTCLOUD_USAGE_FOLDER=.*|NEXTCLOUD_USAGE_FOLDER=\"$new_usage_folder\"|g" .env
        rm .env.bak
        export NEXTCLOUD_USAGE_FOLDER="$new_usage_folder"
        echo "Updated NEXTCLOUD_USAGE_FOLDER in .env"
    else
        echo "NEXTCLOUD_USAGE_FOLDER left empty."
    fi
fi

# --- 4. Prompt for Deployment Variables if missing or are placeholders ---
prompt_and_update_env "DOMAIN_NAME" "Domain Name for your API (e.g., api.yourdomain.com)" "your.domain.com"
prompt_and_update_env "CERTBOT_EMAIL" "Email for Certbot notifications" "your.email@example.com"

# --- 5. Prepare Nginx directory ---
echo "Ensuring nginx configuration directory exists..."
mkdir -p nginx

# --- 6. Obtain SSL Certificates (First Run) ---
echo "\n--- Obtaining initial SSL certificates with Certbot ---"
echo "This step will temporarily run Nginx on port 80 to verify your domain."
echo "Please ensure your domain's DNS is pointing to this server's IP address."
read -p "Press Enter to continue..."

# Start Nginx temporarily to allow Certbot to verify domain
docker compose up --build -d nginx

# Run Certbot to get certificates
docker compose run --rm certbot

# Stop Nginx after certificates are obtained
docker compose stop nginx

# --- 7. Start the Full Stack ---
echo "\n--- Starting the full Nextcloud MCP API stack ---"
echo "Your API will be available at https://$DOMAIN_NAME"
read -p "Press Enter to continue..."

docker compose up --build -d

echo "\n===================================================="
echo " Deployment Complete! "
echo " Your Nextcloud MCP API should now be running at https://$DOMAIN_NAME "
echo " Access API docs at https://$DOMAIN_NAME/docs "
echo "===================================================="
