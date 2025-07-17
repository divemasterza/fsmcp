import os
from dataclasses import dataclass
from .exceptions import ConfigError

@dataclass
class NextcloudConfig:
    """Configuration for the Nextcloud MCP context."""
    instance_url: str
    username: str
    password: str
    usage_folder: str

def from_env() -> NextcloudConfig:
    """
    Creates a NextcloudConfig from environment variables.
    Raises ConfigError if any required variable is missing.
    """
    try:
        instance_url = os.environ["NEXTCLOUD_INSTANCE_URL"].rstrip('/')
        username = os.environ["NEXTCLOUD_USERNAME"]
        password = os.environ["NEXTCLOUD_PASSWORD"]
        usage_folder = os.environ.get("NEXTCLOUD_USAGE_FOLDER", "").strip('/')

        return NextcloudConfig(
            instance_url=instance_url,
            username=username,
            password=password,
            usage_folder=usage_folder,
        )
    except KeyError as e:
        raise ConfigError(f"Environment variable {e} is not set.") from e