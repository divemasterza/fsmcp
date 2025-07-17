import pytest
from unittest.mock import AsyncMock, MagicMock
from nextcloud_mcp import Ctx, NextcloudConfig
from nextcloud_mcp.exceptions import (
    UploadFailedError,
    ShareCreationFailedError,
    FolderCreationError,
    DeletionError,
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
