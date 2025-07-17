import asyncio
import base64
import os
from typing import Union # Import Union
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv

from nextcloud_mcp import Ctx, from_env, NextcloudMcpError

# Load environment variables at startup
load_dotenv()

app = FastAPI(
    title="Nextcloud MCP API",
    description="API to interact with Nextcloud for file and folder management.",
    version="1.0.0",
)

# --- Bearer Token Authentication ---
API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY environment variable not set. Please set it for authentication.")

security_scheme = HTTPBearer()

async def get_api_key(credentials: HTTPAuthorizationCredentials = Security(security_scheme)):
    if credentials.credentials == API_KEY:
        return credentials.credentials
    raise HTTPException(status_code=403, detail="Could not validate credentials")

# Initialize Ctx globally (or per request if preferred, but global is simpler for this example)
# This will raise ConfigError if environment variables are not set
try:
    config = from_env()
    nextcloud_ctx = Ctx(config)
except NextcloudMcpError as e:
    print(f"FATAL: Configuration error: {e}")
    # Exit or handle gracefully, as the app cannot function without config
    # For a simple example, we'll let it raise and fail at startup
    raise

class SaveFileRequest(BaseModel):
    path: str
    content: str  # Base64 encoded for binary, or plain text
    is_base64: bool = False

class PathRequest(BaseModel):
    path: str

class MoveItemRequest(BaseModel):
    source_path: str
    destination_path: str

class CopyItemRequest(BaseModel):
    source_path: str
    destination_path: str

class ReadFileResponse(BaseModel):
    content: str  # Base64 encoded
    mime_type: str

class DirectoryItem(BaseModel):
    name: str
    type: str # 'file' or 'folder'
    size: Union[int, None] = None
    last_modified: Union[str, None] = None # ISO 8601 string
    mime_type: Union[str, None] = None

class DirectoryListingResponse(BaseModel):
    items: list[DirectoryItem]

@app.post("/save_file", summary="Save a file to Nextcloud and get a public share link", dependencies=[Security(get_api_key)])
async def save_file_endpoint(request: SaveFileRequest):
    try:
        file_content = request.content
        if request.is_base64:
            file_content = base64.b64decode(request.content)

        public_url = await nextcloud_ctx.save_file(request.path, file_content)
        return {"message": "File saved and shared successfully", "public_url": public_url}
    except NextcloudMcpError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.get("/read_file", summary="Read a file from Nextcloud", response_model=ReadFileResponse, dependencies=[Security(get_api_key)])
async def read_file_endpoint(path: str):
    try:
        content_bytes, mime_type = await nextcloud_ctx.read_file(path)
        return {"content": base64.b64encode(content_bytes).decode('utf-8'), "mime_type": mime_type}
    except NextcloudMcpError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.put("/alter_file", summary="Alter (overwrite) a file in Nextcloud", dependencies=[Security(get_api_key)])
async def alter_file_endpoint(request: SaveFileRequest):
    try:
        file_content = request.content
        if request.is_base64:
            file_content = base64.b64decode(request.content)

        # Reusing save_file as it overwrites existing files
        await nextcloud_ctx.save_file(request.path, file_content)
        return {"message": f"File '{request.path}' altered successfully"}
    except NextcloudMcpError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.get("/list_directory", summary="List contents of a directory in Nextcloud", response_model=DirectoryListingResponse, dependencies=[Security(get_api_key)])
async def list_directory_endpoint(path: str = "."):
    try:
        items = await nextcloud_ctx.list_directory(path)
        return {"items": items}
    except NextcloudMcpError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.post("/move_item", summary="Move or rename a file or folder in Nextcloud", dependencies=[Security(get_api_key)])
async def move_item_endpoint(request: MoveItemRequest):
    try:
        await nextcloud_ctx.move_item(request.source_path, request.destination_path)
        return {"message": f"Item moved/renamed from '{request.source_path}' to '{request.destination_path}' successfully"}
    except NextcloudMcpError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.post("/copy_item", summary="Copy a file or folder in Nextcloud", dependencies=[Security(get_api_key)])
async def copy_item_endpoint(request: CopyItemRequest):
    try:
        await nextcloud_ctx.copy_item(request.source_path, request.destination_path)
        return {"message": f"Item copied from '{request.source_path}' to '{request.destination_path}' successfully"}
    except NextcloudMcpError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.post("/create_folder", summary="Create a folder in Nextcloud", dependencies=[Security(get_api_key)])
async def create_folder_endpoint(request: PathRequest):
    try:
        await nextcloud_ctx.create_folder(request.path)
        return {"message": f"Folder '{request.path}' created successfully"}
    except NextcloudMcpError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.delete("/delete_file", summary="Delete a file from Nextcloud", dependencies=[Security(get_api_key)])
async def delete_file_endpoint(request: PathRequest):
    try:
        await nextcloud_ctx.delete_file(request.path)
        return {"message": f"File '{request.path}' deleted successfully"}
    except NextcloudMcpError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.delete("/delete_folder", summary="Delete a folder from Nextcloud", dependencies=[Security(get_api_key)])
async def delete_folder_endpoint(request: PathRequest):
    try:
        await nextcloud_ctx.delete_folder(request.path)
        return {"message": f"Folder '{request.path}' deleted successfully"}
    except NextcloudMcpError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

# Optional: Root endpoint for health check
@app.get("/", summary="Health check")
async def read_root():
    return {"status": "Nextcloud MCP API is running"}
