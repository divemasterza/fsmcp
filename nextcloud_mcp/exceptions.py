class NextcloudMcpError(Exception):
    """Base exception for the nextcloud-mcp library."""
    pass

class ConfigError(NextcloudMcpError):
    """Raised for configuration-related errors."""
    pass

class UploadFailedError(NextcloudMcpError):
    """Raised when the WebDAV file upload fails."""
    pass

class ShareCreationFailedError(NextcloudMcpError):
    """Raised when creating a public share link fails."""
    pass

class FolderCreationError(NextcloudMcpError):
    """Raised when creating a folder fails."""
    pass

class DeletionError(NextcloudMcpError):
    """Raised when deleting a file or folder fails."""
    pass
