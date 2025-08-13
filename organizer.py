"""File Organizer"""

from __future__ import annotations

import os
import shutil
import argparse
from pathlib import Path
from collections import Counter
from typing import TypedDict, List, Tuple


class MoveOp(TypedDict):
    """A single planned move operation.

    Attributes:
        source: The original file path to move.
        destination: The final path (including any collision-safe renaming).
    """

    source: Path
    destination: Path


# Mapping of file extensions to categories. Extend as needed.
FILE_EXT_MAPPINGS = {
    # Images
    ".jpg": "Images", ".jpeg": "Images", ".png": "Images", ".gif": "Images", ".webp": "Images",
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

# Filenames to always ignore (common hidden/system metadata files).
# Compare against lowercase to make checks case-insensitive.
SKIP_FILENAMES = {
    "desktop.ini",     # Windows folder view settings
    "thumbs.db",       # Windows thumbnail cache
    "ehthumbs.db",     # Windows enhanced thumbnail cache
    "autorun.inf",     # Removable media autorun metadata
}


def plan_organization(folder_path: Path) -> Tuple[List[MoveOp], Counter]:
    """Produce a collision-safe plan for organizing a folder.

    This is a pure planning step with no side effects on disk. Files are
    assigned to a destination subfolder based on their extension. When a
    filename collision is detected (on disk or within the same planning run),
    a numeric suffix " (n)" is appended to the stem to ensure uniqueness.

    Args:
        folder_path: Directory to scan and plan organization for. Only files in
            the top level of this directory are considered; subdirectories are ignored.

    Returns:
        A tuple of:
            - plan: Ordered list of planned moves, each with source and destination paths.
            - summary: Counter mapping category name -> number of files in that category.
    """
    plan: List[MoveOp] = []
    summary = Counter()
    # Track destination paths chosen during planning to avoid in-plan collisions.
    planned_destinations: set[Path] = set()

    for item_path in folder_path.iterdir():
        # Skip directories, known system files, and dotfiles.
        if not item_path.is_file() or item_path.name.lower() in SKIP_FILENAMES or item_path.name.startswith('.'):
            continue

        category = FILE_EXT_MAPPINGS.get(item_path.suffix.lower(), OTHER_CATEGORY)
        summary[category] += 1

        dest_dir = folder_path / category
        dest_path = dest_dir / item_path.name

        # Resolve collisions against both on-disk files and already planned destinations.
        counter = 1
        while dest_path.exists() or dest_path in planned_destinations:
            dest_path = dest_dir / f"{item_path.stem} ({counter}){item_path.suffix}"
            counter += 1

        planned_destinations.add(dest_path)
        plan.append({"source": item_path, "destination": dest_path})

    return plan, summary


def execute_plan(plan: List[MoveOp]) -> Tuple[int, int]:
    """Execute a previously generated move plan.

    Creates destination folders on demand and moves files per the plan.
    Errors moving individual files are caught and reported without aborting
    the entire run.

    Args:
        plan: The list produced by plan_organization.

    Returns:
        A tuple of:
            - moved_count: Number of files successfully moved.
            - skipped_count: Number of files that were skipped due to errors.
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


def main() -> None:
    """Entry point: parse CLI args, plan, and simulate or execute.

    Prints a scan banner, then either a grouped simulation of the planned
    moves or executes them and reports totals, followed by a categorized
    summary of detected files.
    """
    parser = argparse.ArgumentParser(description="Organize files in a directory by type.")
    parser.add_argument("folder", type=str, help="The path to the folder to organize.")
    parser.add_argument("-s", "--simulate", action="store_true", help="Show what would happen without moving files.")
    args = parser.parse_args()

    target_folder = Path(args.folder).expanduser().resolve()

    if not target_folder.is_dir():
        print(f"Error: Path '{target_folder}' is not a valid directory.")
        return

    try:
        # Scan banner printed in both modes for clarity.
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
                grouped: dict[str, list[MoveOp]] = {}
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
            print(f"\n  TOTAL: {sum(summary.values())} file(s)\n" + "=" * 50)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()