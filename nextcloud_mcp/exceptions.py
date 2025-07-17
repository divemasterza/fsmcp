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

class FileReadError(NextcloudMcpError):
    """Raised when reading a file fails."""
    pass

class DirectoryListingError(NextcloudMcpError):
    """Raised when listing a directory fails."""
    pass

class MoveRenameError(NextcloudMcpError):
    """Raised when moving or renaming a file/folder fails."""
    pass

class CopyError(NextcloudMcpError):
    """Raised when copying a file or folder fails."""
    pass

class FolderDownloadError(NextcloudMcpError):
    """Raised when downloading a folder as a zip fails."""
    pass
