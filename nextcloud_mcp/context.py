import httpx
from typing import Union
from .config import NextcloudConfig
from .exceptions import (
    UploadFailedError,
    ShareCreationFailedError,
    FolderCreationError,
    DeletionError,
)


class Ctx:
    """The main context for interacting with the Nextcloud MCP."""

    def __init__(self, config: NextcloudConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            auth=(config.username, config.password),
            headers={
                "OCS-APIRequest": "true",
                "Accept": "application/json",
            },
        )

    def _get_remote_path(self, path: str) -> str:
        """Constructs the full remote path including the usage_folder."""
        sanitized_path = path.lstrip("/")
        return (
            f"{self.config.usage_folder}/{sanitized_path}"
            if self.config.usage_folder
            else sanitized_path
        )

    async def save_file(self, path: str, content: Union[bytes, str]) -> str:
        """
        Saves a file to Nextcloud and returns a public share link.

        Args:
            path: The relative path for the file (e.g., "subfolder/data.txt").
            content: The file content as bytes or a string.

        Returns:
            The public URL for the shared file.
        """
        remote_path = self._get_remote_path(path)
        await self._upload_file_webdav(remote_path, content)
        public_url = await self._create_public_share(remote_path)
        return public_url

    async def create_folder(self, path: str):
        """
        Creates a folder in Nextcloud.

        Args:
            path: The relative path for the folder (e.g., "subfolder/new-folder").
        """
        remote_path = self._get_remote_path(path)
        mkcol_url = f"{self.config.instance_url}/remote.php/dav/files/{self.config.username}/{remote_path}"

        response = await self.client.request("MKCOL", mkcol_url)

        # 201 = Created. 405 = Already exists, which we can consider success.
        if response.status_code not in [201, 405]:
            raise FolderCreationError(
                f"Failed to create folder with status {response.status_code}: {response.text}"
            )

    async def delete_file(self, path: str):
        """
        Deletes a file from Nextcloud.

        Args:
            path: The relative path of the file to delete.
        """
        await self._delete_path(path)

    async def delete_folder(self, path: str):
        """
        Deletes a folder from Nextcloud.

        Args:
            path: The relative path of the folder to delete.
        """
        await self._delete_path(path)

    async def _delete_path(self, path: str):
        """Deletes a file or folder at the given path via WebDAV DELETE."""
        remote_path = self._get_remote_path(path)
        delete_url = f"{self.config.instance_url}/remote.php/dav/files/{self.config.username}/{remote_path}"

        response = await self.client.delete(delete_url)

        # 204 = Success/No Content. 404 = Not Found (already deleted).
        if response.status_code not in [204, 404]:
            raise DeletionError(
                f"Deletion failed with status {response.status_code}: {response.text}"
            )

    async def _upload_file_webdav(self, remote_path: str, content: Union[bytes, str]):
        """Uploads the file via WebDAV PUT request."""
        upload_url = f"{self.config.instance_url}/remote.php/dav/files/{self.config.username}/{remote_path}"
        
        response = await self.client.put(upload_url, content=content)

        # 201 = Created, 204 = Overwritten/No Content
        if response.status_code not in [201, 204]:
            raise UploadFailedError(
                f"Upload failed with status {response.status_code}: {response.text}"
            )

    async def _create_public_share(self, remote_path: str) -> str:
        """Creates a public share link via the OCS API."""
        share_api_url = f"{self.config.instance_url}/ocs/v2.php/apps/files_sharing/api/v1/shares"
        
        payload = {
            "path": remote_path,
            "shareType": 3,  # 3 = Public Link
            "permissions": 1, # 1 = Read-only
        }
        
        response = await self.client.post(share_api_url, json=payload)

        if response.status_code != 200:
            raise ShareCreationFailedError(
                f"Request to create share failed with status {response.status_code}: {response.text}"
            )

        # Parse the JSON response
        try:
            data = response.json()
            ocs = data.get("ocs", {})
            meta = ocs.get("meta", {})
            status_code = meta.get("statuscode")

            # Nextcloud OCS API returns status code 100 for success on creation
            if status_code not in [100, 200]:
                message = meta.get("message", "Unknown OCS API error.")
                raise ShareCreationFailedError(f"OCS API Error: {message} (Code: {status_code})")

            share_data = ocs.get("data", {})
            share_url = share_data.get("url")
            
            if not share_url:
                raise ShareCreationFailedError("Could not find public URL in OCS response.")
            return share_url
        except (ValueError, KeyError) as e:
            raise ShareCreationFailedError(f"Failed to parse OCS API JSON response: {e}") from e