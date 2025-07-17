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
        initial_content = f"Hello from Python MCP at {timestamp}"
        altered_content = f"This content was altered at {timestamp}"

        # 1. Create a new folder
        print(f"\n> 1. Creating folder: '{base_folder}'...")
        await ctx.create_folder(base_folder)
        print("   ✅ Folder created.")

        # 2. Save an initial file into the new folder
        print(f"\n> 2. Saving initial file: '{file_path}'...")
        public_url = await ctx.save_file(path=file_path, content=initial_content)
        print("   ✅ Initial file saved and shared successfully!")
        print(f"      Public URL: {public_url}")

        # 3. List contents of the base folder
        print(f"\n> 3. Listing contents of '{base_folder}'...")
        listed_items = await ctx.list_directory(base_folder)
        if listed_items:
            print("   ✅ Folder contents:")
            for item in listed_items:
                print(f"      - Name: {item['name']}, Type: {item['type']}, Size: {item['size']}, MIME: {item['mime_type']}")
        else:
            print("   ⚠️ Folder is empty or listing failed.")

        # 4. Move/Rename the file
        new_filename = "my-renamed-file.txt"
        new_file_path = f"{base_folder}/{new_filename}"
        print(f"\n> 4. Moving/Renaming file from '{file_path}' to '{new_file_path}'...")
        await ctx.move_item(file_path, new_file_path)
        print("   ✅ File moved/renamed successfully!")
        file_path = new_file_path # Update file_path for subsequent operations

        # 5. Copy the file
        copied_file_path = f"{base_folder}/my-copied-file.txt"
        print(f"\n> 5. Copying file from '{file_path}' to '{copied_file_path}'...")
        await ctx.copy_item(file_path, copied_file_path)
        print("   ✅ File copied successfully!")

        # 6. Read the content of the file (now at new_file_path)
        print(f"\n> 6. Reading file: '{file_path}'...")
        read_content_bytes, mime_type = await ctx.read_file(file_path)
        print(f"   ✅ File read successfully!")
        print(f"      Content: '{read_content_bytes.decode()}'")
        print(f"      MIME Type: {mime_type}")

        # 7. Alter (overwrite) the file content
        print(f"\n> 7. Altering file: '{file_path}'...")
        # save_file method handles overwriting if file exists
        await ctx.save_file(path=file_path, content=altered_content)
        print("   ✅ File altered successfully!")

        # 8. Read the altered content to verify
        print(f"\n> 8. Reading altered file: '{file_path}'...")
        read_altered_content_bytes, altered_mime_type = await ctx.read_file(file_path)
        print(f"   ✅ Altered file read successfully!")
        print(f"      Content: '{read_altered_content_bytes.decode()}'")
        print(f"      MIME Type: {altered_mime_type}")

        # 9. Delete the original file
        print(f"\n> 9. Deleting original file: '{file_path}'...")
        await ctx.delete_file(file_path)
        print("   ✅ Original file deleted.")

        # 10. Delete the copied file
        print(f"\n> 10. Deleting copied file: '{copied_file_path}'...")
        await ctx.delete_file(copied_file_path)
        print("   ✅ Copied file deleted.")

        # 11. Delete the folder
        print(f"\n> 11. Deleting folder: '{base_folder}'...")
        await ctx.delete_folder(base_folder)
        print("   ✅ Folder deleted.")

        print("\n🎉 Demo finished successfully!")

    except NextcloudMcpError as e:
        print(f"\n❌ An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
