import os
import shutil
import argparse


# Mapping of file extensions to categories
# This dictionary maps file extensions to their respective categories.
FILE_EXT_MAPPINGS = {
    # Images
    ".jpg": "Images", ".jpeg": "Images", ".png": "Images", ".gif": "Images", ".webp" : "Images",
    # Documents
    ".pdf": "Documents", ".docx": "Documents", ".txt": "Documents", ".pptx": "Documents", ".xlsx": "Documents", ".csv": "Documents",
    # Videos
    ".mp4": "Videos", ".mov": "Videos", ".avi": "Videos", ".mkv": "Videos", ".ts": "Videos",
    # Audio
    ".mp3": "Audio", ".wav": "Audio", ".aac": "Audio",
    # Archives
    ".zip": "Archives", ".rar": "Archives", ".7z": "Archives",
}
# Default category for files that do not match any known extension
OTHER_CATEGORY = "Others"

# Filenames to always ignore (common hidden/system metadata files)
# Using lowercase and comparing with item_name.lower()
SKIP_FILENAMES = {
    "desktop.ini",     # Windows folder view settings
    "thumbs.db",       # Windows thumbnail cache
    "ehthumbs.db",     # Windows enhanced thumbnail cache
    "autorun.inf",     # Removable media autorun metadata
}


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


def organize_folder(folder_path: str, simulate: bool = False) -> None:
    """
    Scans a folder and organizes files into subdirectories based on their extension.

    Args:
        folder_path: The path to the folder to be organized.
        simulate: If True, only show what would happen without moving files.
    """
    print(f"Scanning folder: {folder_path}" + (" [SIMULATION]" if simulate else ""))

    # Dictionary to track the number of files moved per category
    files_moved_count = {}

    # Track simulated destination paths to resolve collisions predictably within a single run
    simulated_taken_paths = set() if simulate else None

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

        # Skip known system/hidden files regardless of attributes
        if item_name.lower() in SKIP_FILENAMES:
            print(f"Skipping system file '{item_name}' — OS metadata; not moved.")
            continue

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
            if not simulate:
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
            if simulate:
                # Compute the final destination path as _safe_move would, without moving
                dest_dir = os.path.dirname(dest_path)
                base_name_with_ext = os.path.basename(dest_path)
                base_name, ext = os.path.splitext(base_name_with_ext)
                candidate_path = dest_path
                counter = 1
                while os.path.exists(candidate_path) or candidate_path in simulated_taken_paths:
                    candidate_path = os.path.join(dest_dir, f"{base_name} ({counter}){ext}")
                    counter += 1

                moved_to = os.path.relpath(candidate_path, start=folder_path)
                print(f"Would move '{item_name}' -> '{moved_to}'")
                files_moved_count[category] = files_moved_count.get(category, 0) + 1
                simulated_taken_paths.add(candidate_path)
            else:
                final_path = _safe_move(item_path, dest_path)
                # Show a relative path inside the target folder for clarity to the user
                moved_to = os.path.relpath(final_path, start=folder_path)
                print(f"Moved '{item_name}' -> '{moved_to}'")
                # Update the count for this category
                files_moved_count[category] = files_moved_count.get(category, 0) + 1
        except (PermissionError, OSError) as exc:
            print(f"Warning: Skipping '{item_name}' — {exc}")
            continue

    # Display summary of files moved per category
    print("\n" + "="*50)
    print("SIMULATION SUMMARY" if simulate else "ORGANIZATION SUMMARY")
    print("="*50)
    
    if files_moved_count:
        total_files = sum(files_moved_count.values())
        print(f"Total files {'to move' if simulate else 'moved'}: {total_files}")
        print()
        for category, count in sorted(files_moved_count.items()):
            print(f"  {category}: {count} file{'s' if count != 1 else ''}")
    else:
        print("No files were moved." if not simulate else "No files would be moved.")
    
    print("="*50)
    print("Simulation complete." if simulate else "Organization complete.")


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
    # New simulate flag
    parser.add_argument(
        "-s", "--simulate",
        action="store_true",
        help="Show what would happen without moving files.",
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
        organize_folder(target_folder_path, simulate=args.simulate)
    except KeyboardInterrupt:
        print("Operation cancelled by user.")
    except Exception as exc:  # Catch-all to ensure a user-friendly message
        print(f"An unexpected error occurred: {exc}")


# Standard entry point for a Python script
if __name__ == "__main__":
    main()