# File Organizer Script

This is a command-line utility to organize files in a folder by type (Images, Documents, Videos, Audio, Archives, Others). 
The script plans moves first, supports a dry-run simulation, resolves name collisions safely, and prints a clear summary with totals.

## Language and Tools
- Language: Python 3
- Standard Libraries: argparse, os, shutil, pathlib, collections
- No external packages required

## Features
- Plans first, then executes for predictable results
- Simulation mode (-s) to preview all moves
- Collision-safe renaming (e.g., "file (1).pdf", "file (2).pdf", ...)
- Skips common system/hidden metadata files (e.g., desktop.ini, thumbs.db)
- Clean, grouped output with per-category and total counts

## Categories
- Images: .jpg, .jpeg, .png, .gif, .webp
- Documents: .pdf, .docx, .txt, .pptx, .xlsx, .csv
- Videos: .mp4, .mov, .avi, .mkv, .ts
- Audio: .mp3, .wav, .aac
- Archives: .zip, .rar, .7z
- Others: any extension not mapped above

## How to Run
1. Clone the repository:
   git clone https://github.com/Youssef-Ashraf-Dev/file-organizer.git
2. Ensure you have Python 3 installed and available on PATH.
3. Run the script, providing the folder to organize.

## Example Output (Simulation)
```
Folder: D:\Downloads\test_files
Scanning...
==================================================
--- SIMULATION MODE ---
==================================================
Planned moves: 6 file(s)
  Documents (3):
    - report.pdf -> report.pdf
    - plan.docx -> plan.docx
    - notes.txt -> notes.txt
  Images (2):
    - image.png -> image.png
    - photo.jpg -> photo.jpg
  Archives (1):
    - archive.zip -> archive.zip

Total files that would be moved: 6
==================================================
--- SUMMARY ---
==================================================
  Archives: 1 file(s)
  Documents: 3 file(s)
  Images: 2 file(s)

  TOTAL: 6 file(s)
==================================================
```

## Notes
- Only files in the specified folder’s top level are organized; subfolders are not scanned.
- Name collisions are resolved by appending an incrementing suffix to the filename stem.
- Common Windows system files (e.g., desktop.ini, thumbs.db) and dotfiles are ignored.
- Safe to re-run; already organized files will reside in their category folders.