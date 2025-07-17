import asyncio
import time
from dotenv import load_dotenv
from nextcloud_mcp import Ctx, from_env, NextcloudMcpError


async def main():
    """Example of using the Nextcloud MCP for various file and folder operations."""
    load_dotenv()
    print("Attempting to load configuration from environment...")

    try:
        config = from_env()
        ctx = Ctx(config)
        print(f"✓ Configuration loaded for user '{config.username}'.")

        timestamp = int(time.time())
        base_folder = f"mcp-demo-{timestamp}"
        filename = "my-test-file.txt"
        file_path = f"{base_folder}/{filename}"
        content = f"Hello from Python MCP at {timestamp}"

        # 1. Create a new folder
        print(f"\n> 1. Creating folder: '{base_folder}'...")
        await ctx.create_folder(base_folder)
        print("   ✅ Folder created.")

        # 2. Save a file into the new folder
        print(f"\n> 2. Saving file: '{file_path}'...")
        public_url = await ctx.save_file(path=file_path, content=content)
        print("   ✅ File saved and shared successfully!")
        print(f"      Public URL: {public_url}")

        # 3. Delete the file
        print(f"\n> 3. Deleting file: '{file_path}'...")
        await ctx.delete_file(file_path)
        print("   ✅ File deleted.")

        # 4. Delete the folder
        print(f"\n> 4. Deleting folder: '{base_folder}'...")
        await ctx.delete_folder(base_folder)
        print("   ✅ Folder deleted.")

        print("\n🎉 Demo finished successfully!")

    except NextcloudMcpError as e:
        print(f"\n❌ An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
