# Nextcloud MCP - Future Roadmap

This document outlines potential future enhancements and features for the Nextcloud Model-Context-Protocol (MCP) API. These are ideas for further development to make the system more robust, feature-rich, and user-friendly.

---

## I. Advanced File & Folder Management

### 1. Share Link Management (List, Modify, Revoke)
*   **List Shares:** Endpoint to retrieve all active public share links created by the MCP, including their paths, URLs, and current settings (e.g., password protected, expiry).
*   **Modify Share:** Endpoint to update an existing share link (e.g., add/remove password, set/change expiry date, change permissions).
*   **Revoke Share:** Endpoint to invalidate a public share link.

### 2. Granular Permissions (Private Shares)
*   **Share with User/Group:** Endpoints to create private shares with specific Nextcloud users or groups, defining read/write/delete permissions.
*   **List Private Shares:** Retrieve details of private shares.
*   **Modify Private Share:** Adjust permissions or recipients of private shares.
*   **Unshare:** Remove private sharing.

### 3. Batch Operations
*   **Batch Delete:** Delete multiple files/folders in a single request.
*   **Batch Move/Copy:** Move or copy multiple items.

### 4. Versioning/History
*   **List Versions:** Retrieve a list of available historical versions for a given file.
*   **Restore Version:** Revert a file to a previous version.

### 5. Trash/Recycle Bin Management
*   **List Trash:** View items in the Nextcloud trash bin.
*   **Restore from Trash:** Recover a deleted item.
*   **Empty Trash:** Permanently delete all items from the trash.

## II. Enhanced Metadata & Search

### 1. Custom Metadata/Tagging
*   **Set/Get Custom Properties:** Allow attaching arbitrary key-value metadata or tags to files/folders.

### 2. Full-Text Search
*   **Search Content:** Endpoint to search for text within the content of files (if Nextcloud's search capabilities can be exposed via API).

## III. Monitoring & Robustness

### 1. Detailed Health/Status Endpoints
*   **Storage Usage:** Report total storage, used space, and available space.
*   **Nextcloud Connectivity Check:** Verify the MCP can connect to the Nextcloud instance and authenticate.

### 2. Asynchronous Task Management
*   For very large file operations (e.g., zipping huge folders, complex batch operations), return a task ID immediately and provide a separate endpoint to check the status of the long-running task.

## IV. Performance & Scalability

### 1. Streaming for Large Files
*   Modify upload/download endpoints to support streaming file content, rather than loading entire files into memory.

### 2. Pagination, Sorting, and Filtering for Listings
*   Add parameters to `list_directory` to control the number of items returned per page, sort order (name, date, size), and filter by type or name.

## V. Integration & Extensibility

### 1. Webhooks/Notifications
*   Allow registering webhook URLs that Nextcloud (or the MCP) can call when specific events occur (e.g., file added, file modified, folder deleted).
