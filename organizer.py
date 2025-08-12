import os
import shutil
import argparse


# Mapping of file extensions to categories
# This dictionary maps file extensions to their respective categories.
FILE_EXT_MAPPINGS = {
    # Images
    ".jpg": "Images", ".jpeg": "Images", ".png": "Images", ".gif": "Images",
    # Documents
    ".pdf": "Documents", ".docx": "Documents", ".txt": "Documents", ".pptx": "Documents", ".xlsx": "Documents", ".csv": "Documents",
    # Videos
    ".mp4": "Videos", ".mov": "Videos", ".avi": "Videos", ".mkv": "Videos", ".ts": "Videos",
    # Audio
    ".mp3": "Audio", ".wav": "Audio", ".aac": "Audio",
    # Archives
    ".zip": "Archives", ".rar": "Archives", ".7z": "Archives",
    # Code files
    ".py": "Code", ".js": "Code", ".html": "Code", ".css": "Code", ".java": "Code",
}
# Default category for files that do not match any known extension
OTHER_CATEGORY = "Others"


def _safe_move(source_path: str, destination_path: str) -> str:
    """Safely move a file, avoiding name collisions.

    If a file with the same name already exists at the destination, this function
    appends an increasing counter before the extension, e.g., "file (1).txt",
    "file (2).txt", etc.

    Returns the final destination path of the moved file.
    """
    dest_dir = os.path.dirname(destination_path)
    base_name_with_ext = os.path.basename(destination_path)
    base_name, ext = os.path.splitext(base_name_with_ext)

    candidate_path = destination_path
    counter = 1

    # Collision resolution loop: find the next available filename.
    # This can be tricky; we ensure it terminates by incrementing a counter.
    while os.path.exists(candidate_path):
        candidate_path = os.path.join(dest_dir, f"{base_name} ({counter}){ext}")
        counter += 1

    try:
        shutil.move(source_path, candidate_path)
    except PermissionError as exc:
        # Provide a friendly message that hints at common causes and remedies.
        raise PermissionError(
            f"Permission denied while moving '{os.path.basename(source_path)}'. "
            "Close any program using the file or run with appropriate permissions."
        ) from exc
    except OSError as exc:
        # Convert low-level errors into understandable context for the user.
        raise OSError(
            f"Could not move '{os.path.basename(source_path)}' to "
            f"'{candidate_path}'. Details: {exc}"
        ) from exc

    return candidate_path


def organize_folder(folder_path: str) -> None:
    """
    Scans a folder and organizes files into subdirectories based on their extension.

    Args:
        folder_path: The path to the folder to be organized.
    """
    print(f"Scanning folder: {folder_path}")

    try:
        item_names = os.listdir(folder_path)
    except PermissionError:
        print(
            "Error: You do not have permission to read this folder. "
            "Try running with appropriate permissions."
        )
        return
    except FileNotFoundError:
        print("Error: The folder was not found. It may have been moved or deleted.")
        return
    except OSError as exc:
        print(f"Error: Unable to list folder contents. Details: {exc}")
        return

    # Loop through each item in the directory
    for item_name in item_names:
        item_path = os.path.join(folder_path, item_name)

        # Skip directories and hidden files
        if not os.path.isfile(item_path) or item_name.startswith('.'):
            continue

        # Get the file extension (e.g., '.txt') in lowercase for matching
        file_extension = os.path.splitext(item_name)[1].lower()

        # Find the category, defaulting to OTHER_CATEGORY
        category = FILE_EXT_MAPPINGS.get(file_extension, OTHER_CATEGORY)

        # Create the destination folder if it doesn't exist
        dest_folder_path = os.path.join(folder_path, category)
        try:
            os.makedirs(dest_folder_path, exist_ok=True)
        except PermissionError:
            print(
                f"Warning: Skipping '{item_name}' — cannot create or access the "
                f"destination folder '{category}'."
            )
            continue
        except OSError as exc:
            print(
                f"Warning: Skipping '{item_name}' — failed to prepare destination. "
                f"Details: {exc}"
            )
            continue

        # Move the file and report the result
        dest_path = os.path.join(dest_folder_path, item_name)
        try:
            final_path = _safe_move(item_path, dest_path)
            # Show a relative path inside the target folder for clarity to the user
            moved_to = os.path.relpath(final_path, start=folder_path)
            print(f"Moved '{item_name}' -> '{moved_to}'")
        except (PermissionError, OSError) as exc:
            print(f"Warning: Skipping '{item_name}' — {exc}")
            continue

    print("Organization complete.")


def main() -> None:
    """Parse arguments and start the organization with friendly error handling."""
    parser = argparse.ArgumentParser(
        description="Organize files in a directory by type."
    )
    parser.add_argument(
        "folder",
        type=str,
        help="The path to the folder to organize.",
    )

    args = parser.parse_args()
    target_folder_path = args.folder

    # Check if the path exists and is a directory
    if not os.path.isdir(target_folder_path):
        print(f"Error: Path '{target_folder_path}' is not a valid directory.")
        return  # Exit gracefully

    # Normalize and expand the folder path for better readability in logs
    target_folder_path = os.path.abspath(os.path.expanduser(target_folder_path))

    try:
        organize_folder(target_folder_path)
    except KeyboardInterrupt:
        print("Operation cancelled by user.")
    except Exception as exc:  # Catch-all to ensure a user-friendly message
        print(f"An unexpected error occurred: {exc}")


# Standard entry point for a Python script
if __name__ == "__main__":
    main()