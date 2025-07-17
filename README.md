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
```

You can get a secure app password from your Nextcloud account settings under **Security > Devices & sessions**.

### 4. Usage

The `save_and_share.py` script provides a simple example of how to use the library.

```bash
python nextcloud_mcp/save_and_share.py
```

The script will:
1.  Load the configuration from your `.env` file.
2.  Create a new text file with a timestamp.
3.  Upload the file to your Nextcloud instance.
4.  Print the public share URL to the console.

## How It Works

The core logic is in the `Ctx` class (`nextcloud_mcp/context.py`), which handles the two main steps:

1.  **File Upload:** Uses the WebDAV protocol (`PUT` request) to upload the file to the specified path.
2.  **Share Link Creation:** Uses the Nextcloud OCS (Open Collaboration Services) API to create a public share link for the uploaded file.

## Project Structure

```
.
├── nextcloud_mcp/
│   ├── __init__.py
│   ├── config.py       # Configuration loading and validation
│   ├── context.py      # Core Ctx class for Nextcloud interaction
│   ├── exceptions.py   # Custom exception classes
│   └── save_and_share.py # Example usage script
├── tests/              # Unit tests
├── .env.example        # Example environment file
├── pyproject.toml      # Project metadata and dependencies
└── README.md
```
