import httpx
import xml.etree.ElementTree as ET # Re-import for WebDAV PROPFIND XML parsing
from typing import Union
from .config import NextcloudConfig
from .exceptions import (
    UploadFailedError,
    ShareCreationFailedError,
    FolderCreationError,
    DeletionError,
    FileReadError,
    DirectoryListingError,
    MoveRenameError,
    CopyError,
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

    def _get_webdav_url(self, remote_path: str) -> str:
        """Constructs the full WebDAV URL for a given remote path."""
        return f"{self.config.instance_url}/remote.php/dav/files/{self.config.username}/{remote_path}"

    async def list_directory(self, path: str) -> list[dict]:
        """
        Lists the contents of a directory in Nextcloud.

        Args:
            path: The relative path for the directory (e.g., "subfolder").

        Returns:
            A list of dictionaries, each representing an item (file or folder)
            with 'name', 'type' ('file' or 'folder'), 'size' (for files),
            and 'last_modified' (ISO 8601 string).
        """
        remote_path = self._get_remote_path(path)
        list_url = self._get_webdav_url(remote_path)

        # WebDAV PROPFIND request body to ask for specific properties
        propfind_body = """<?xml version="1.0"?>
<d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns" xmlns:nc="http://nextcloud.org/ns">
  <d:prop>
    <d:displayname/>
    <d:getcontenttype/>
    <d:getcontentlength/>
    <d:getlastmodified/>
    <d:resourcetype/>
  </d:prop>
</d:propfind>"""
        headers = {"Content-Type": "application/xml", "Depth": "1"} # Depth 1 for direct children

        try:
            response = await self.client.request("PROPFIND", list_url, content=propfind_body, headers=headers)

            if response.status_code not in [200, 207]: # 207 Multi-Status is common for PROPFIND
                raise DirectoryListingError(
                    f"Failed to list directory with status {response.status_code}: {response.text}"
                )

            root = ET.fromstring(response.content)
            # Define DAV: and Nextcloud: namespaces
            ns = {'d': 'DAV:', 'nc': 'http://nextcloud.org/ns'}
            
            items = []
            for response_elem in root.findall('d:response', ns):
                href = response_elem.find('d:href', ns).text
                # Skip the directory itself (href ending with /)
                if href.rstrip('/').endswith(remote_path.rstrip('/')):
                    continue

                propstat = response_elem.find('d:propstat', ns)
                prop = propstat.find('d:prop', ns)

                name = prop.find('d:displayname', ns).text if prop.find('d:displayname', ns) is not None else href.split('/')[-2 if href.endswith('/') else -1]
                
                resource_type_elem = prop.find('d:resourcetype', ns)
                is_collection = resource_type_elem is not None and resource_type_elem.find('d:collection', ns) is not None
                
                item_type = "folder" if is_collection else "file"
                
                size = None
                if not is_collection:
                    size_elem = prop.find('d:getcontentlength', ns)
                    if size_elem is not None and size_elem.text:
                        try:
                            size = int(size_elem.text)
                        except ValueError:
                            pass # Ignore if size is not a valid integer

                last_modified = None
                last_modified_elem = prop.find('d:getlastmodified', ns)
                if last_modified_elem is not None and last_modified_elem.text:
                    last_modified = last_modified_elem.text # ISO 8601 string

                mime_type = None
                mime_type_elem = prop.find('d:getcontenttype', ns)
                if mime_type_elem is not None and mime_type_elem.text:
                    mime_type = mime_type_elem.text

                items.append({
                    "name": name,
                    "type": item_type,
                    "size": size,
                    "last_modified": last_modified,
                    "mime_type": mime_type,
                })
            return items
        except ET.ParseError as e:
            raise DirectoryListingError(f"Failed to parse PROPFIND XML response: {e}") from e
        except Exception as e:
            raise DirectoryListingError(f"An unexpected error occurred during directory listing: {e}") from e

    async def move_item(self, source_path: str, destination_path: str):
        """
        Moves or renames a file or folder in Nextcloud.

        Args:
            source_path: The current relative path of the item.
            destination_path: The new relative path for the item.
        """
        remote_source_path = self._get_remote_path(source_path)
        remote_destination_path = self._get_remote_path(destination_path)

        move_url = self._get_webdav_url(remote_source_path)
        destination_url = self._get_webdav_url(remote_destination_path)

        headers = {"Destination": destination_url}

        response = await self.client.request("MOVE", move_url, headers=headers)

        # 201 = Created (moved to new location), 204 = No Content (overwritten existing)
        if response.status_code not in [201, 204]:
            raise MoveRenameError(
                f"Failed to move/rename item with status {response.status_code}: {response.text}"
            )

    async def copy_item(self, source_path: str, destination_path: str):
        """
        Copies a file or folder in Nextcloud.

        Args:
            source_path: The current relative path of the item.
            destination_path: The new relative path for the copied item.
        """
        remote_source_path = self._get_remote_path(source_path)
        remote_destination_path = self._get_remote_path(destination_path)

        copy_url = self._get_webdav_url(remote_source_path)
        destination_url = self._get_webdav_url(remote_destination_path)

        headers = {"Destination": destination_url}

        response = await self.client.request("COPY", copy_url, headers=headers)

        # 201 = Created (copied to new location), 204 = No Content (overwritten existing)
        if response.status_code not in [201, 204]:
            raise CopyError(
                f"Failed to copy item with status {response.status_code}: {response.text}"
            )

    async def download_folder_as_zip(self, path: str) -> bytes:
        """
        Downloads a folder from Nextcloud as a zip archive.

        Args:
            path: The relative path for the folder to download.

        Returns:
            The content of the zip file as bytes.
        """
        remote_path = self._get_remote_path(path)
        # Nextcloud provides a direct download link for folders as zip via WebDAV
        download_url = self._get_webdav_url(remote_path)

        response = await self.client.get(download_url)

        if response.status_code == 200:
            # Nextcloud typically returns application/zip for folder downloads
            if response.headers.get("Content-Type") == "application/zip":
                return response.content
            else:
                raise FolderDownloadError(f"Expected application/zip, but received {response.headers.get("Content-Type")}")
        elif response.status_code == 404:
            raise FolderDownloadError(f"Folder not found: {path}")
        else:
            raise FolderDownloadError(
                f"Failed to download folder with status {response.status_code}: {response.text}"
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

    async def read_file(self, path: str) -> tuple[bytes, str]:
        """
        Reads a file from Nextcloud and returns its content and MIME type.

        Args:
            path: The relative path of the file to read.

        Returns:
            A tuple containing (file_content_as_bytes, mime_type_string).
        """
        remote_path = self._get_remote_path(path)
        download_url = self._get_webdav_url(remote_path)

        response = await self.client.get(download_url)

        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "application/octet-stream")
            return response.content, content_type
        elif response.status_code == 404:
            raise FileReadError(f"File not found: {path}")
        else:
            raise FileReadError(
                f"Failed to read file with status {response.status_code}: {response.text}"
            )

    async def create_folder(self, path: str):
        """
        Creates a folder in Nextcloud.

        Args:
            path: The relative path for the folder (e.g., "subfolder/new-folder").
        """
        remote_path = self._get_remote_path(path)
        mkcol_url = self._get_webdav_url(remote_path)

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
        delete_url = self._get_webdav_url(remote_path)

        response = await self.client.delete(delete_url)

        # 204 = Success/No Content. 404 = Not Found (already deleted).
        if response.status_code not in [204, 404]:
            raise DeletionError(
                f"Deletion failed with status {response.status_code}: {response.text}"
            )

    async def _upload_file_webdav(
        self, remote_path: str, content: Union[bytes, str]
    ):
        """Uploads the file via WebDAV PUT request."""
        upload_url = self._get_webdav_url(remote_path)

        response = await self.client.put(upload_url, content=content)

        # 201 = Created, 204 = Overwritten/No Content
        if response.status_code not in [201, 204]:
            raise UploadFailedError(
                f"Upload failed with status {response.status_code}: {response.text}"
            )

    async def _create_public_share(self, remote_path: str) -> str:
        """Creates a public share link via the OCS API."""
        share_api_url = (
            f"{self.config.instance_url}/ocs/v2.php/apps/files_sharing/api/v1/shares"
        )

        payload = {
            "path": remote_path,
            "shareType": 3,  # 3 = Public Link
            "permissions": 1,  # 1 = Read-only
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
                raise ShareCreationFailedError(
                    f"OCS API Error: {message} (Code: {status_code})"
                )

            share_data = ocs.get("data", {})
            share_url = share_data.get("url")

            if not share_url:
                raise ShareCreationFailedError(
                    "Could not find public URL in OCS response."
                )
            return share_url
        except (ValueError, KeyError) as e:
            raise ShareCreationFailedError(
                f"Failed to parse OCS API JSON response: {e}"
            ) from e

    async def share_folder(self, path: str) -> str:
        """
        Shares a folder in Nextcloud and returns a public share link.

        Args:
            path: The relative path for the folder.

        Returns:
            The public URL for the shared folder.
        """
        remote_path = self._get_remote_path(path)
        public_url = await self._create_public_share(remote_path)
        return public_url

    async def share_folder(self, path: str) -> str:
        """
        Shares a folder in Nextcloud and returns a public share link.

        Args:
            path: The relative path for the folder.

        Returns:
            The public URL for the shared folder.
        """
        remote_path = self._get_remote_path(path)
        public_url = await self._create_public_share(remote_path)
        return public_url

    async def share_folder(self, path: str) -> str:
        """
        Shares a folder in Nextcloud and returns a public share link.

        Args:
            path: The relative path for the folder.

        Returns:
            The public URL for the shared folder.
        """
        remote_path = self._get_remote_path(path)
        public_url = await self._create_public_share(remote_path)
        return public_url
