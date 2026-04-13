RTV_ModTool Beta v0.4.14

RTV_ModTool is a save-management and editing utility for Road to Vostok testing.

Please use at your own risk.

What it does:
- lets you select a live save root and manage character folders from one place
- tracks which character folder is currently linked to the active root save
- syncs the active root save back to the linked character folder on open
- lets you edit core player vitals safely
- shows world values in read-only form for reference
- creates rolling backups before restore and sync operations
- caps backups to 10 per character slot to avoid save-folder bloat

Usage:
- download the .exe from the releases section and run
- alternatively, you can download the zip, extract, and run the main.py script yourself or build the .exe yourself using the following command in the folder containing main.py:

```
py -m PyInstaller --noconfirm --onefile --windowed --icon=assets/icon.ico --add-data "assets;assets" --name RTV_ModTool_Beta_v0.4.14 main.py
```

- The --add-data option is important because it includes the custom logo and icon files in the packaged app.

Planned Features:

- Inventory, Equipment, Catalog Editing
- Alternate start location

Notes:
- character folders are shown by folder name only
- dehydration, frostbite, and insanity are display-only condition flags
- world editing is intentionally disabled to avoid breaking game state

Files included:
- main.py
- save_io.py
- save_parser.py
- save_scanner.py
- assets/icon.ico
- assets/logo.png
- CHANGELOG.md




