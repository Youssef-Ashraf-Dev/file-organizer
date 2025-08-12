import os
import shutil
import argparse


# Mapping of file extensions to categories
# This dictionary maps file extensions to their respective categories.
FILE_EXT_MAPPINGS = {
    # Images
    ".jpg": "Images", ".jpeg": "Images", ".png": "Images", ".gif": "Images",
    # Documents
    ".pdf": "Documents", ".docx": "Documents", ".txt": "Documents", ".pptx": "Documents",
    ".xlsx": "Documents", ".csv": "Documents",
    # Videos
    ".mp4": "Videos", ".mov": "Videos", ".avi": "Videos", "mkv": "Videos", "ts": "Videos",
    # Audio
    ".mp3": "Audio", ".wav": "Audio", ".flac": "Audio",
    # Archives
    ".zip": "Archives", ".rar": "Archives", ".tar": "Archives", ".gz": "Archives", ".7z": "Archives",
    # Code files
    ".py": "Code", ".js": "Code", ".html": "Code", ".css": "Code", ".java": "Code",
}
# Default category for files that do not match any known extension
OTHER_CATEGORY = "Others"

def organize_folder(folder_path):
    """
    Scans a folder and organizes files into subdirectories based on their extension.
    
    Args:
        folder_path (str): The path to the folder to be organized.
    """
    print(f"Scanning folder: {folder_path}")

    # Loop through each item in the directory
    for item_name in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item_name)

        # Skip directories and hidden files
        if not os.path.isfile(item_path) or item_name.startswith('.'):
            continue

        # Get the file extension (e.g., '.txt')
        file_extension = os.path.splitext(item_name)[1].lower()

        # Find the category, defaulting to OTHER_CATEGORY
        category = FILE_EXT_MAPPINGS.get(file_extension, OTHER_CATEGORY)
        
        # Create the destination folder if it doesn't exist
        dest_folder_path = os.path.join(folder_path, category)
        os.makedirs(dest_folder_path, exist_ok=True)

        # Move the file
        dest_path = os.path.join(dest_folder_path, item_name)
        print(f"Moving '{item_name}' -> '{category}/'")
        shutil.move(item_path, dest_path)

    print("Organization complete.")


def main():
    """Main function to parse arguments and start the organization."""
    parser = argparse.ArgumentParser(description="Organize files in a directory by type.")
    parser.add_argument("folder", type=str, help="The path to the folder to organize.")
    
    args = parser.parse_args()
    target_folder = args.folder

    # check if the path exists and is a directory
    if not os.path.isdir(target_folder):
        print(f"Error: Path '{target_folder}' is not a valid directory.")
        return # Exit gracefully

    organize_folder(target_folder)


# Standard entry point for a Python script
if __name__ == "__main__":
    main()