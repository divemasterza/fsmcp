# Nextcloud MCP

This project provides a Model-Context-Protocol (MCP) for saving files to a Nextcloud instance and immediately receiving a publicly available share URL.

## Features

-   **Save & Share:** Upload files to a designated Nextcloud folder and automatically generate a public, read-only share link.
-   **File and Folder Management:** Create and delete files and folders.
-   **Configurable:** All Nextcloud connection details are configurable via environment variables.
-   **Robust:** Built with modern Python libraries (`httpx`, `pydantic`) and includes error handling.
-   **Asynchronous:** Uses `asyncio` for non-blocking I/O operations.

## Quickstart

### 1. Prerequisites

-   Python 3.8+
-   A Nextcloud account with WebDAV access enabled.

### 2. Installation

Clone the repository and install the required dependencies:

```bash
git clone https://github.com/your-username/nextcloud-mcp.git
cd nextcloud-mcp
pip install -e .
```

### 3. Configuration

This project uses environment variables for configuration. Create a `.env` file in the project root and add the following variables:

```
NEXTCLOUD_INSTANCE_URL="https://your-nextcloud-instance.com"
NEXTCLOUD_USERNAME="your_username"
NEXTCLOUD_PASSWORD="your_password"
# Optional: Specify a folder to save files in.
# If not set, files will be saved in the root directory.
NEXTCLOUD_USAGE_FOLDER="MyUploads"

# API Key for securing the FastAPI endpoints.
# Generate a strong, random key and keep it secret!
API_KEY="your_super_secret_api_key"
```

You can get a secure app password from your Nextcloud account settings under **Security > Devices & sessions**.

### 4. Usage (Library)

The `save_and_share.py` script provides a simple example of how to use the library.

```bash
python save_and_share.py
```

### 5. Usage (FastAPI)

To run the FastAPI server, first ensure you have installed the `fastapi` and `uvicorn` dependencies:

```bash
pip install -e '.[test]' # This installs core and test dependencies
pip install "fastapi[all]" uvicorn
```

Then, you can start the server:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://0.0.0.0:8000`. You can access the interactive API documentation (Swagger UI) at `http://0.0.0.0:8000/docs`.

**Authentication:** All API endpoints now require a Bearer Token. You must include an `Authorization` header in your requests with the value `Bearer <YOUR_API_KEY>` where `<YOUR_API_KEY>` is the value from your `API_KEY` in the `.env` file.

**API Endpoints:**

*   **`POST /save_file`**: Save a file to Nextcloud and get a public share link.
    ```bash
    curl -X POST "http://0.0.0.0:8000/save_file" \
         -H "Authorization: Bearer your_super_secret_api_key" \
         -H "Content-Type: application/json" \
         -d '{"path": "my_new_file.txt", "content": "Hello World!", "is_base64": false}'
    ```

*   **`GET /read_file`**: Read a file from Nextcloud.
    ```bash
    curl -X GET "http://0.0.0.0:8000/read_file?path=my_new_file.txt" \
         -H "Authorization: Bearer your_super_secret_api_key"
    ```

*   **`PUT /alter_file`**: Alter (overwrite) a file in Nextcloud.
    ```bash
    curl -X PUT "http://0.0.0.0:8000/alter_file" \
         -H "Authorization: Bearer your_super_secret_api_key" \
         -H "Content-Type: application/json" \
         -d '{"path": "my_new_file.txt", "content": "Altered content!", "is_base64": false}'
    ```

*   **`GET /list_directory`**: List contents of a directory in Nextcloud.
    ```bash
    curl -X GET "http://0.0.0.0:8000/list_directory?path=my_folder" \
         -H "Authorization: Bearer your_super_secret_api_key"
    ```

*   **`POST /create_folder`**: Create a folder in Nextcloud.
    ```bash
    curl -X POST "http://0.0.0.0:8000/create_folder" \
         -H "Authorization: Bearer your_super_secret_api_key" \
         -H "Content-Type: application/json" \
         -d '{"path": "my_new_folder"}'
    ```

*   **`POST /move_item`**: Move or rename a file or folder in Nextcloud.
    ```bash
    curl -X POST "http://0.0.0.0:8000/move_item" \
         -H "Authorization: Bearer your_super_secret_api_key" \
         -H "Content-Type: application/json" \
         -d '{"source_path": "old_name.txt", "destination_path": "new_name.txt"}'
    ```

*   **`POST /copy_item`**: Copy a file or folder in Nextcloud.
    ```bash
    curl -X POST "http://0.0.0.0:8000/copy_item" \
         -H "Authorization: Bearer your_super_secret_api_key" \
         -H "Content-Type: application/json" \
         -d '{"source_path": "original.txt", "destination_path": "copy.txt"}'
    ```

*   **`DELETE /delete_file`**: Delete a file from Nextcloud.
    ```bash
    curl -X DELETE "http://0.0.0.0:8000/delete_file" \
         -H "Authorization: Bearer your_super_secret_api_key" \
         -H "Content-Type: application/json" \
         -d '{"path": "my_new_file.txt"}'
    ```


*   **`DELETE /delete_folder`**: Delete a folder from Nextcloud.
    ```bash
    curl -X DELETE "http://0.0.0.0:8000/delete_folder" \
         -H "Authorization: Bearer your_super_secret_api_key" \
         -H "Content-Type: application/json" \
         -d '{"path": "my_new_folder"}'
    ```


```
