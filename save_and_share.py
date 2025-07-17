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

        # 2. Share the newly created folder
        print(f"\n> 2. Sharing folder: '{base_folder}'...")
        folder_public_url = await ctx.share_folder(base_folder)
        print("   ✅ Folder shared successfully!")
        print(f"      Public Folder URL: {folder_public_url}")

        # 3. Save an initial file into the new folder
        print(f"\n> 3. Saving initial file: '{file_path}'...")
        public_url = await ctx.save_file(path=file_path, content=initial_content)
        print("   ✅ Initial file saved and shared successfully!")
        print(f"      Public URL: {public_url}")

        # 4. List contents of the base folder
        print(f"\n> 4. Listing contents of '{base_folder}'...")
        listed_items = await ctx.list_directory(base_folder)
        if listed_items:
            print("   ✅ Folder contents:")
            for item in listed_items:
                print(f"      - Name: {item['name']}, Type: {item['type']}, Size: {item['size']}, MIME: {item['mime_type']}")
        else:
            print("   ⚠️ Folder is empty or listing failed.")

        # 5. Move/Rename the file
        new_filename = "my-renamed-file.txt"
        new_file_path = f"{base_folder}/{new_filename}"
        print(f"\n> 5. Moving/Renaming file from '{file_path}' to '{new_file_path}'...")
        await ctx.move_item(file_path, new_file_path)
        print("   ✅ File moved/renamed successfully!")
        file_path = new_file_path # Update file_path for subsequent operations

        # 6. Copy the file
        copied_file_path = f"{base_folder}/my-copied-file.txt"
        print(f"\n> 6. Copying file from '{file_path}' to '{copied_file_path}'...")
        await ctx.copy_item(file_path, copied_file_path)
        print("   ✅ File copied successfully!")

        # 7. Download the folder as a zip
        downloaded_zip_path = f"./{base_folder}.zip"
        print(f"\n> 7. Downloading folder '{base_folder}' as zip to '{downloaded_zip_path}'...")
        zip_content = await ctx.download_folder_as_zip(base_folder)
        with open(downloaded_zip_path, "wb") as f:
            f.write(zip_content)
        print(f"   ✅ Folder downloaded as zip successfully! Size: {len(zip_content)} bytes")

        # 8. Read the content of the file (now at new_file_path)
        print(f"\n> 8. Reading file: '{file_path}'...")
        read_content_bytes, mime_type = await ctx.read_file(file_path)
        print(f"   ✅ File read successfully!")
        print(f"      Content: '{read_content_bytes.decode()}'")
        print(f"      MIME Type: {mime_type}")

        # 9. Alter (overwrite) the file content
        print(f"\n> 9. Altering file: '{file_path}'...")
        # save_file method handles overwriting if file exists
        await ctx.save_file(path=file_path, content=altered_content)
        print("   ✅ File altered successfully!")

        # 10. Read the altered content to verify
        print(f"\n> 10. Reading altered file: '{file_path}'...")
        read_altered_content_bytes, altered_mime_type = await ctx.read_file(file_path)
        print(f"   ✅ Altered file read successfully!")
        print(f"      Content: '{read_altered_content_bytes.decode()}'")
        print(f"      MIME Type: {altered_mime_type}")

        # 11. Delete the original file
        print(f"\n> 11. Deleting original file: '{file_path}'...")
        await ctx.delete_file(file_path)
        print("   ✅ Original file deleted.")

        # 12. Delete the copied file
        print(f"\n> 12. Deleting copied file: '{copied_file_path}'...")
        await ctx.delete_file(copied_file_path)
        print("   ✅ Copied file deleted.")

        # 13. Delete the folder
        print(f"\n> 13. Deleting folder: '{base_folder}'...")
        await ctx.delete_folder(base_folder)
        print("   ✅ Folder deleted.")

        print("\n🎉 Demo finished successfully!")

    except NextcloudMcpError as e:
        print(f"\n❌ An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
