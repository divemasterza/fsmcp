"""A Model-Context-Protocol (MCP) for saving files to Nextcloud and getting public share links."""

__version__ = "0.1.0"

from .config import NextcloudConfig, from_env
from .context import Ctx
from .exceptions import (
    NextcloudMcpError,
    ConfigError,
    UploadFailedError,
    ShareCreationFailedError,
    FolderCreationError,
    DeletionError,
)

__all__ = [
    "NextcloudConfig",
    "from_env",
    "Ctx",
    "NextcloudMcpError",
    "ConfigError",
    "UploadFailedError",
    "ShareCreationFailedError",
    "FolderCreationError",
    "DeletionError",
]
