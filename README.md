# Nextcloud MCP

This project provides a Model-Context-Protocol (MCP) for saving files to a Nextcloud instance and immediately receiving a publicly available share URL.

## Features

*   **Save & Share:** Upload files to a designated Nextcloud folder and automatically generate a public, read-only share link.
*   **File and Folder Management:** Create and delete files and folders.
*   **Configurable:** All Nextcloud connection details are configurable via environment variables.
*   **Robust:** Built with modern Python libraries (`httpx`, `pydantic`) and includes error handling.
*   **Asynchronous:** Uses `asyncio` for non-blocking I/O operations.

## Quickstart

### 1. Prerequisites

*   Python 3.8+
*   A Nextcloud account with WebDAV access enabled.
*   Docker and Docker Compose installed on your deployment server.

### 2. Installation

Clone the repository:

```bash
git clone https://github.com/your-username/nextcloud-mcp.git
cd nextcloud-mcp
```

### 3. Configuration

This project uses environment variables for configuration. Create a `.env` file in the project root and add the following variables:

```
NEXTCLOUD_INSTANCE_URL="https://your-nextcloud-instance.com"
NEXTCLOUD_USERNAME="your_username"
NEXTCLOUD_PASSWORD="your_password"
# Optional: Specify a folder to save files in.
# If not set, files will be saved in the root directory.
NEXTCLOUD_USAGE_FOLDER="MCP-Uploads"

# API Key for securing the FastAPI endpoints.
# Generate a strong, random key and keep it secret!
API_KEY="your_super_secret_api_key"

# --- Docker Compose Deployment Variables ---
# Domain name for your FastAPI application (e.g., api.example.com)
DOMAIN_NAME="your.domain.com"

# Email for Certbot (Let's Encrypt) notifications
CERTBOT_EMAIL="your.email@example.com"
```

You can get a secure app password from your Nextcloud account settings under **Security \> Devices & sessions**.

### 4. Usage (Library)

The `save_and_share.py` script provides a simple example of how to use the library.

```bash
python save_and_share.py
```

### 5. Deployment with Docker Compose (Recommended for Production)

This setup uses Docker Compose to orchestrate your FastAPI application, Nginx as a reverse proxy, and Certbot for automatic HTTPS (Let's Encrypt) certificate management.

#### a. Prepare your environment

1.  **Ensure your `.env` file is configured** with all `NEXTCLOUD_*` variables, `API_KEY`, `DOMAIN_NAME`, and `CERTBOT_EMAIL`.
2.  **Create Nginx configuration directory:**
```bash
mkdir -p nginx
```
3.  **Create Nginx configuration file (`nginx/nginx.conf`):**
```nginx
server {
    listen 80;
    server_name ${DOMAIN_NAME};

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name ${DOMAIN_NAME};

    ssl_certificate /etc/letsencrypt/live/${DOMAIN_NAME}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN_NAME}/privkey.pem;

    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
*Note: Replace `${DOMAIN_NAME}` with your actual domain name in the `nginx.conf` if you are not using Docker Compose's environment variable substitution.* (Docker Compose will substitute this for you from the .env file).

#### b. Obtain SSL Certificates (First Run)

Before starting the full stack, you need to obtain initial SSL certificates from Let's Encrypt. This step temporarily runs Nginx on port 80 to allow Certbot to verify your domain.

```bash
docker compose up --build -d nginx
docker compose run --rm certbot
docker compose stop nginx
```

*   `docker compose up --build -d nginx`: Starts the Nginx container in detached mode, building the `web` service image first.
*   `docker compose run --rm certbot`: Runs the Certbot container to obtain certificates. It uses the `certbot/www` volume to serve the ACME challenge.
*   `docker compose stop nginx`: Stops Nginx after certificates are obtained.

#### c. Start the Full Stack

Once certificates are obtained, you can start all services, including your FastAPI app and Nginx with HTTPS enabled.

```bash
docker compose up --build -d
```

Your API will now be available at `https://your.domain.com`.

#### d. Renewing Certificates

Certbot certificates expire every 90 days. You should set up a cron job or a Docker Compose healthcheck/restart policy to renew them automatically. A simple way is to run:

```bash
docker compose run --rm certbot renew
docker compose kill -s SIGHUP nginx
```

#### e. Accessing the API

Your API will be available at `https://your.domain.com`. You can access the interactive API documentation (Swagger UI) at `https://your.domain.com/docs`.

**Authentication:** All API endpoints require a Bearer Token. You must include an `Authorization` header in your requests with the value `Bearer <YOUR_API_KEY>` where `<YOUR_API_KEY>` is the value from your `API_KEY` in the `.env` file.

**API Endpoints:**

*   **`POST /save_file`**: Save a file to Nextcloud and get a public share link.
```bash
    curl -X POST "https://your.domain.com/save_file" \
         -H "Authorization: Bearer your_super_secret_api_key" \
         -H "Content-Type: application/json" \
         -d '{"path": "my_new_file.txt", "content": "Hello World!", "is_base64": false}'
```

*   **`GET /read_file`**: Read a file from Nextcloud.
```bash
    curl -X GET "https://your.domain.com/read_file?path=my_new_file.txt" \
         -H "Authorization: Bearer your_super_secret_api_key"
```

*   **`PUT /alter_file`**: Alter (overwrite) a file in Nextcloud.
```bash
    curl -X PUT "https://your.domain.com/alter_file" \
         -H "Authorization: Bearer your_super_secret_api_key" \
         -H "Content-Type: application/json" \
         -d '{"path": "my_new_file.txt", "content": "Altered content!", "is_base64": false}'
```

*   **`GET /list_directory`**: List contents of a directory in Nextcloud.
```bash
    curl -X GET "https://your.domain.com/list_directory?path=my_folder" \
         -H "Authorization: Bearer your_super_secret_api_key"
```

*   **`GET /download_folder_as_zip`**: Download a folder from Nextcloud as a zip archive.
```bash
    curl -X GET "https://your.domain.com/download_folder_as_zip?path=my_folder" \
         -H "Authorization: Bearer your_super_secret_api_key" \
         --output my_folder.zip
```

*   **`POST /create_folder`**: Create a folder in Nextcloud.
```bash
    curl -X POST "https://your.domain.com/create_folder" \
         -H "Authorization: Bearer your_super_secret_api_key" \
         -H "Content-Type: application/json" \
         -d '{"path": "my_new_folder"}'
```

*   **`POST /move_item`**: Move or rename a file or folder in Nextcloud.
```bash
    curl -X POST "https://your.domain.com/move_item" \
         -H "Authorization: Bearer your_super_secret_api_key" \
         -H "Content-Type: application/json" \
         -d '{"source_path": "old_name.txt", "destination_path": "new_name.txt"}'
```

*   **`POST /copy_item`**: Copy a file or folder in Nextcloud.
```bash
    curl -X POST "https://your.domain.com/copy_item" \
         -H "Authorization: Bearer your_super_secret_api_key" \
         -H "Content-Type: application/json" \
         -d '{"source_path": "original.txt", "destination_path": "copy.txt"}'
```

*   **`POST /share_folder`**: Share a folder in Nextcloud and get a public share link.
```bash
    curl -X POST "https://your.domain.com/share_folder" \
         -H "Authorization: Bearer your_super_secret_api_key" \
         -H "Content-Type: application/json" \
         -d '{"path": "my_folder_to_share"}'
```

*   **`DELETE /delete_file`**: Delete a file from Nextcloud.
```bash
    curl -X DELETE "https://your.domain.com/delete_file?path=my_new_file.txt" \
         -H "Authorization: Bearer your_super_secret_api_key"
```

*   **`DELETE /delete_folder`**: Delete a folder from Nextcloud.
```bash
    curl -X DELETE "https://your.domain.com/delete_folder?path=my_new_folder" \
         -H "Authorization: Bearer your_super_secret_api_key"
```

## Future Enhancements (Roadmap)

For a detailed list of potential future features and improvements, please refer to the [ROADMAP.md](ROADMAP.md) file.