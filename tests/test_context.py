import pytest
from unittest.mock import AsyncMock, MagicMock
from nextcloud_mcp import Ctx, NextcloudConfig
from nextcloud_mcp.exceptions import (
    UploadFailedError,
    ShareCreationFailedError,
    FolderCreationError,
    DeletionError,
    FileReadError,
    DirectoryListingError,
    MoveRenameError,
    CopyError,
)


@pytest.fixture
def config():
    """Provides a mock NextcloudConfig for tests."""
    return NextcloudConfig(
        instance_url="https://test.nextcloud.com",
        username="testuser",
        password="testpass",
        usage_folder="TestUploads",
    )


@pytest.fixture
def ctx(config):
    """Provides a Ctx instance with a mocked httpx client."""
    ctx_instance = Ctx(config)
    ctx_instance.client = AsyncMock()
    return ctx_instance


@pytest.mark.asyncio
async def test_save_file_success(ctx, config):
    """Tests successful file saving and share link creation."""
    # Mock the WebDAV upload response
    ctx.client.put.return_value = MagicMock(status_code=201)

    # Mock the OCS Share API response
    mock_share_response = MagicMock(
        status_code=200,
        json=lambda: {
            "ocs": {
                "meta": {"statuscode": 100},
                "data": {"url": "https://test.nextcloud.com/s/sharelink"},
            }
        },
    )
    ctx.client.post.return_value = mock_share_response

    file_path = "test.txt"
    content = "Hello, world!"
    public_url = await ctx.save_file(file_path, content)

    assert public_url == "https://test.nextcloud.com/s/sharelink"

    # Verify WebDAV call
    expected_upload_url = f"{config.instance_url}/remote.php/dav/files/{config.username}/{config.usage_folder}/{file_path}"
    ctx.client.put.assert_called_once_with(expected_upload_url, content=content)

    # Verify OCS call
    expected_share_url = (
        f"{config.instance_url}/ocs/v2.php/apps/files_sharing/api/v1/shares"
    )
    expected_payload = {
        "path": f"{config.usage_folder}/{file_path}",
        "shareType": 3,
        "permissions": 1,
    }
    ctx.client.post.assert_called_once_with(expected_share_url, json=expected_payload)


@pytest.mark.asyncio
async def test_upload_failed(ctx):
    """Tests that UploadFailedError is raised on WebDAV upload failure."""
    ctx.client.put.return_value = MagicMock(status_code=500, text="Server Error")

    with pytest.raises(
        UploadFailedError, match="Upload failed with status 500: Server Error"
    ):
        await ctx.save_file("test.txt", "content")


@pytest.mark.asyncio
async def test_share_creation_request_failed(ctx):
    """Tests that ShareCreationFailedError is raised on OCS API request failure."""
    ctx.client.put.return_value = MagicMock(status_code=201)
    ctx.client.post.return_value = MagicMock(status_code=404, text="Not Found")

    with pytest.raises(
        ShareCreationFailedError,
        match="Request to create share failed with status 404: Not Found",
    ):
        await ctx.save_file("test.txt", "content")


@pytest.mark.asyncio
async def test_share_creation_ocs_api_error(ctx):
    """Tests that ShareCreationFailedError is raised on OCS API logical error."""
    ctx.client.put.return_value = MagicMock(status_code=201)
    mock_share_response = MagicMock(
        status_code=200,
        json=lambda: {
            "ocs": {"meta": {"statuscode": 999, "message": "Invalid path"}}
        },
    )
    ctx.client.post.return_value = mock_share_response

    with pytest.raises(
        ShareCreationFailedError, match=r"OCS API Error: Invalid path \(Code: 999\)"
    ):
        await ctx.save_file("test.txt", "content")


@pytest.mark.asyncio
async def test_share_creation_missing_url_in_response(ctx):
    """Tests error handling when the public URL is missing from the OCS response."""
    ctx.client.put.return_value = MagicMock(status_code=201)
    mock_share_response = MagicMock(
        status_code=200,
        json=lambda: {"ocs": {"meta": {"statuscode": 100}, "data": {}}},
    )
    ctx.client.post.return_value = mock_share_response

    with pytest.raises(
        ShareCreationFailedError, match="Could not find public URL in OCS response"
    ):
        await ctx.save_file("test.txt", "content")


@pytest.mark.asyncio
async def test_read_file_success(ctx, config):
    """Tests successful file reading."""
    mock_content = b"This is test content."
    mock_mime_type = "text/plain"
    ctx.client.get.return_value = MagicMock(
        status_code=200,
        content=mock_content,
        headers={"Content-Type": mock_mime_type},
    )
    file_path = "read_test.txt"
    content, mime_type = await ctx.read_file(file_path)

    assert content == mock_content
    assert mime_type == mock_mime_type

    expected_url = f"{config.instance_url}/remote.php/dav/files/{config.username}/{config.usage_folder}/{file_path}"
    ctx.client.get.assert_called_once_with(expected_url)


@pytest.mark.asyncio
async def test_read_file_not_found(ctx):
    """Tests that FileReadError is raised when file is not found."""
    ctx.client.get.return_value = MagicMock(status_code=404)
    with pytest.raises(FileReadError, match="File not found: non_existent.txt"):
        await ctx.read_file("non_existent.txt")


@pytest.mark.asyncio
async def test_read_file_failed(ctx):
    """Tests that FileReadError is raised on other read failures."""
    ctx.client.get.return_value = MagicMock(status_code=500, text="Server Error")
    with pytest.raises(
        FileReadError, match="Failed to read file with status 500: Server Error"
    ):
        await ctx.read_file("failed_read.txt")


@pytest.mark.asyncio
async def test_list_directory_success(ctx, config):
    """Tests successful directory listing."""
    mock_xml_response = b'''<?xml version="1.0"?>
<d:multistatus xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns" xmlns:nc="http://nextcloud.org/ns">
  <d:response>
    <d:href>/remote.php/dav/files/testuser/TestUploads/test_folder/</d:href>
    <d:propstat>
      <d:prop>
        <d:resourcetype><d:collection/></d:resourcetype>
        <d:displayname>test_folder</d:displayname>
        <d:getlastmodified>Thu, 17 Jul 2025 10:00:00 GMT</d:getlastmodified>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
  <d:response>
    <d:href>/remote.php/dav/files/testuser/TestUploads/test_folder/file1.txt</d:href>
    <d:propstat>
      <d:prop>
        <d:resourcetype/>
        <d:displayname>file1.txt</d:displayname>
        <d:getcontenttype>text/plain</d:getcontenttype>
        <d:getcontentlength>123</d:getcontentlength>
        <d:getlastmodified>Thu, 17 Jul 2025 10:01:00 GMT</d:getlastmodified>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
  <d:response>
    <d:href>/remote.php/dav/files/testuser/TestUploads/test_folder/subfolder/</d:href>
    <d:propstat>
      <d:prop>
        <d:resourcetype><d:collection/></d:resourcetype>
        <d:displayname>subfolder</d:displayname>
        <d:getlastmodified>Thu, 17 Jul 2025 10:02:00 GMT</d:getlastmodified>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
</d:multistatus>'''

    expected_propfind_body = """<?xml version=\"1.0\"?>
<d:propfind xmlns:d=\"DAV:\" xmlns:oc=\"http://owncloud.org/ns\" xmlns:nc=\"http://nextcloud.org/ns\">
  <d:prop>
    <d:displayname/>
    <d:getcontenttype/>
    <d:getcontentlength/>
    <d:getlastmodified/>
    <d:resourcetype/>
  </d:prop>
</d:propfind>"""
    expected_headers = {"Content-Type": "application/xml", "Depth": "1"}

    ctx.client.request.return_value = MagicMock(
        status_code=207,
        content=mock_xml_response,
        headers={"Content-Type": "application/xml"},
    )
    folder_path = "test_folder"
    items = await ctx.list_directory(folder_path)

    assert len(items) == 2  # Should not include the folder itself
    assert items[0]["name"] == "file1.txt"
    assert items[0]["type"] == "file"
    assert items[0]["size"] == 123
    assert items[0]["mime_type"] == "text/plain"
    assert items[0]["last_modified"] == "Thu, 17 Jul 2025 10:01:00 GMT"

    assert items[1]["name"] == "subfolder"
    assert items[1]["type"] == "folder"
    assert items[1]["size"] is None
    assert items[1]["mime_type"] is None
    assert items[1]["last_modified"] == "Thu, 17 Jul 2025 10:02:00 GMT"

    expected_url = f"{config.instance_url}/remote.php/dav/files/{config.username}/{config.usage_folder}/{folder_path}"
    ctx.client.request.assert_called_once_with(
        "PROPFIND", expected_url, content=expected_propfind_body, headers=expected_headers
    )


@pytest.mark.asyncio
async def test_list_directory_failed(ctx):
    """Tests that DirectoryListingError is raised on listing failure."""
    ctx.client.request.return_value = MagicMock(status_code=500, text="Server Error")
    with pytest.raises(
        DirectoryListingError, match="Failed to list directory with status 500: Server Error"
    ):
        await ctx.list_directory("non_existent_folder")


@pytest.mark.asyncio
async def test_move_item_success(ctx, config):
    """Tests successful item move/rename."""
    ctx.client.request.return_value = MagicMock(status_code=201)
    source_path = "old_name.txt"
    destination_path = "new_name.txt"
    await ctx.move_item(source_path, destination_path)

    expected_source_url = f"{config.instance_url}/remote.php/dav/files/{config.username}/{config.usage_folder}/{source_path}"
    expected_destination_url = f"{config.instance_url}/remote.php/dav/files/{config.username}/{config.usage_folder}/{destination_path}"
    ctx.client.request.assert_called_once_with(
        "MOVE", expected_source_url, headers={"Destination": expected_destination_url}
    )


@pytest.mark.asyncio
async def test_move_item_failed(ctx):
    """Tests that MoveRenameError is raised on move/rename failure."""
    ctx.client.request.return_value = MagicMock(status_code=500, text="Server Error")
    with pytest.raises(
        MoveRenameError, match="Failed to move/rename item with status 500: Server Error"
    ):
        await ctx.move_item("source.txt", "dest.txt")


@pytest.mark.asyncio
async def test_move_item_failed(ctx):
    """Tests that MoveRenameError is raised on move/rename failure."""
    ctx.client.request.return_value = MagicMock(status_code=500, text="Server Error")
    with pytest.raises(
        MoveRenameError, match="Failed to move/rename item with status 500: Server Error"
    ):
        await ctx.move_item("source.txt", "dest.txt")


@pytest.mark.asyncio
async def test_copy_item_success(ctx, config):
    """Tests successful item copy."""
    ctx.client.request.return_value = MagicMock(status_code=201)
    source_path = "original.txt"
    destination_path = "copy.txt"
    await ctx.copy_item(source_path, destination_path)

    expected_source_url = f"{config.instance_url}/remote.php/dav/files/{config.username}/{config.usage_folder}/{source_path}"
    expected_destination_url = f"{config.instance_url}/remote.php/dav/files/{config.username}/{config.usage_folder}/{destination_path}"
    ctx.client.request.assert_called_once_with(
        "COPY", expected_source_url, headers={"Destination": expected_destination_url}
    )


@pytest.mark.asyncio
async def test_copy_item_failed(ctx):
    """Tests that CopyError is raised on copy failure."""
    ctx.client.request.return_value = MagicMock(status_code=500, text="Server Error")
    with pytest.raises(
        CopyError, match="Failed to copy item with status 500: Server Error"
    ):
        await ctx.copy_item("source.txt", "dest.txt")


@pytest.mark.asyncio
async def test_move_item_failed(ctx):
    """Tests that MoveRenameError is raised on move/rename failure."""
    ctx.client.request.return_value = MagicMock(status_code=500, text="Server Error")
    with pytest.raises(
        MoveRenameError, match="Failed to move/rename item with status 500: Server Error"
    ):
        await ctx.move_item("source.txt", "dest.txt")


@pytest.mark.asyncio
async def test_copy_item_success(ctx, config):
    """Tests successful item copy."""
    ctx.client.request.return_value = MagicMock(status_code=201)
    source_path = "original.txt"
    destination_path = "copy.txt"
    await ctx.copy_item(source_path, destination_path)

    expected_source_url = f"{config.instance_url}/remote.php/dav/files/{config.username}/{config.usage_folder}/{source_path}"
    expected_destination_url = f"{config.instance_url}/remote.php/dav/files/{config.username}/{config.usage_folder}/{destination_path}"
    ctx.client.request.assert_called_once_with(
        "COPY", expected_source_url, headers={"Destination": expected_destination_url}
    )


@pytest.mark.asyncio
async def test_copy_item_failed(ctx):
    """Tests that CopyError is raised on copy failure."""
    ctx.client.request.return_value = MagicMock(status_code=500, text="Server Error")
    with pytest.raises(
        CopyError, match="Failed to copy item with status 500: Server Error"
    ):
        await ctx.copy_item("source.txt", "dest.txt")


@pytest.mark.asyncio
async def test_create_folder_success(ctx, config):
    """Tests successful folder creation."""
    ctx.client.request.return_value = MagicMock(status_code=201)
    folder_path = "new-folder"
    await ctx.create_folder(folder_path)

    expected_url = f"{config.instance_url}/remote.php/dav/files/{config.username}/{config.usage_folder}/{folder_path}"
    ctx.client.request.assert_called_once_with("MKCOL", expected_url)


@pytest.mark.asyncio
async def test_create_folder_already_exists(ctx, config):
    """Tests that creating an existing folder is handled gracefully."""
    ctx.client.request.return_value = MagicMock(
        status_code=405
    )  # Method Not Allowed (already exists)
    await ctx.create_folder("existing-folder")


@pytest.mark.asyncio
async def test_create_folder_failed(ctx):
    """Tests that FolderCreationError is raised on failure."""
    ctx.client.request.return_value = MagicMock(status_code=500, text="Server Error")
    with pytest.raises(
        FolderCreationError,
        match="Failed to create folder with status 500: Server Error",
    ):
        await ctx.create_folder("new-folder")


@pytest.mark.asyncio
async def test_delete_file_success(ctx, config):
    """Tests successful file deletion."""
    ctx.client.delete.return_value = MagicMock(status_code=204)
    file_path = "file-to-delete.txt"
    await ctx.delete_file(file_path)

    expected_url = f"{config.instance_url}/remote.php/dav/files/{config.username}/{config.usage_folder}/{file_path}"
    ctx.client.delete.assert_called_once_with(expected_url)


@pytest.mark.asyncio
async def test_delete_file_not_found(ctx):
    """Tests that deleting a non-existent file is handled gracefully."""
    ctx.client.delete.return_value = MagicMock(status_code=404)
    await ctx.delete_file("not-found.txt")


@pytest.mark.asyncio
async def test_delete_file_failed(ctx):
    """Tests that DeletionError is raised on file deletion failure."""
    ctx.client.delete.return_value = MagicMock(status_code=500, text="Server Error")
    with pytest.raises(
        DeletionError, match="Deletion failed with status 500: Server Error"
    ):
        await ctx.delete_file("file.txt")


@pytest.mark.asyncio
async def test_delete_folder_success(ctx, config):
    """Tests successful folder deletion."""
    ctx.client.delete.return_value = MagicMock(status_code=204)
    folder_path = "folder-to-delete"
    await ctx.delete_folder(folder_path)

    expected_url = f"{config.instance_url}/remote.php/dav/files/{config.username}/{config.usage_folder}/{folder_path}"
    ctx.client.delete.assert_called_once_with(expected_url)


@pytest.mark.asyncio
async def test_delete_folder_not_found(ctx):
    """Tests that deleting a non-existent folder is handled gracefully."""
    ctx.client.delete.return_value = MagicMock(status_code=404)
    await ctx.delete_folder("not-found-folder")


@pytest.mark.asyncio
async def test_delete_folder_failed(ctx):
    """Tests that DeletionError is raised on folder deletion failure."""
    ctx.client.delete.return_value = MagicMock(status_code=500, text="Server Error")
    with pytest.raises(
        DeletionError, match="Deletion failed with status 500: Server Error"
    ):
        await ctx.delete_folder("folder")
