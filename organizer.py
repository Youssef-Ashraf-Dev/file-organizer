import os
import shutil
import argparse
from pathlib import Path
from collections import Counter


# Mapping of file extensions to categories
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


def plan_organization(folder_path: Path):
    """
    Scans a folder, plans file moves including collision resolution, and generates a summary.
    This function has NO side effects (it does not move or create any files/folders).
    
    Args:
        folder_path: The Path object for the folder to be organized.

    Returns:
        A tuple containing:
        - list: A list of dictionaries representing the move plan.
        - Counter: A summary of file counts per category.
    """
    plan = []
    summary = Counter()
    planned_destinations = set() # Track planned destination paths to prevent collisions

    for item_path in folder_path.iterdir():
        if not item_path.is_file() or item_path.name.lower() in SKIP_FILENAMES or item_path.name.startswith('.'):
            continue

        category = FILE_EXT_MAPPINGS.get(item_path.suffix.lower(), OTHER_CATEGORY)
        summary[category] += 1
        
        dest_dir = folder_path / category
        dest_path = dest_dir / item_path.name

        # Resolve collisions based on what's on disk AND what's already planned
        counter = 1
        while dest_path.exists() or dest_path in planned_destinations:
            dest_path = dest_dir / f"{item_path.stem} ({counter}){item_path.suffix}"
            counter += 1
        
        planned_destinations.add(dest_path)
        plan.append({"source": item_path, "destination": dest_path})
        
    return plan, summary

def execute_plan(plan: list):
    """
    Executes a move plan created by plan_organization.
    This function has side effects (creates folders and moves files).
    
    Args:
        plan: A list of dictionaries representing the move plan.

    Returns:
        tuple[int, int]: (moved_count, skipped_count)
    """
    if not plan:
        print("No files to organize.")
        return (0, 0)

    moved_count = 0
    skipped_count = 0

    for move in plan:
        source_path = move["source"]
        dest_path = move["destination"]
        
        try:
            # Create destination folder just-in-time
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(source_path, dest_path)
            print(f"Moved '{source_path.name}' -> '{dest_path.parent.name}/{dest_path.name}'")
            moved_count += 1
        except (OSError, PermissionError) as e:
            print(f"  [SKIPPED] Could not move '{source_path.name}'. Reason: {e}")
            skipped_count += 1

    return moved_count, skipped_count

def main():
    """Main function to parse arguments and control the workflow."""
    parser = argparse.ArgumentParser(description="Organize files in a directory by type.")
    parser.add_argument("folder", type=str, help="The path to the folder to organize.")
    parser.add_argument("-s", "--simulate", action="store_true", help="Show what would happen without moving files.")
    args = parser.parse_args()

    target_folder = Path(args.folder).expanduser().resolve()
    
    if not target_folder.is_dir():
        print(f"Error: Path '{target_folder}' is not a valid directory.")
        return

    try:
        print(f"Folder: {target_folder}" + "\nScanning...")
        # 1. ALWAYS plan first
        move_plan, summary = plan_organization(target_folder)

        # 2. Decide what to do with the plan
        if args.simulate:
            print("=" * 50)
            print("--- SIMULATION MODE ---")
            print("=" * 50)
            if not move_plan:
                print("No files would be moved.")
            else:
                # Group planned moves by destination category for cleaner output
                grouped = {}
                for move in move_plan:
                    category = move['destination'].parent.name
                    grouped.setdefault(category, []).append(move)
                total = len(move_plan)
                print(f"Planned moves: {total} file(s)")
                for category in sorted(grouped.keys()):
                    print(f"  {category} ({len(grouped[category])}):")
                    for move in sorted(grouped[category], key=lambda m: m['source'].name.lower()):
                        print(f"    - {move['source'].name} -> {move['destination'].name}")
                print(f"\nTotal files that would be moved: {total}")
        else:
            print("=" * 50)
            print("--- EXECUTING ORGANIZATION ---")
            print("=" * 50)
            moved_count, skipped_count = execute_plan(move_plan)
            print(f"\nTotal files moved: {moved_count}")
            if skipped_count:
                print(f"Total files skipped: {skipped_count}")

        # 3. Always print the summary
        print("=" * 50)
        print("--- SUMMARY ---")
        print("=" * 50)
        if not summary:
            print("No files were categorized.")
        else:
            for category, count in sorted(summary.items()):
                print(f"  {category}: {count} file(s)")
            print(f"  TOTAL: {sum(summary.values())} file(s)")
            
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()