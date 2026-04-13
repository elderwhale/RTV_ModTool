# RTV_ModTool Beta v0.4.14

RTV_ModTool is a save-management and editing utility for Road to Vostok testing.

⚠️ Please use at your own risk.

---

## What it does

- Select a live save root and manage character folders from one place  
- Tracks which character folder is currently linked to the active root save  
- Syncs the active root save back to the linked character folder on open  
- Lets you edit core player vitals safely  
- Shows world values in read-only form for reference  
- Creates rolling backups before restore and sync operations  
- Caps backups to 10 per character slot to avoid save-folder bloat  

---

## Usage

### Option 1: Run the executable
- Download the `.exe` from the **Releases** section  
- Run it directly  

### Option 2: Run from source
- Download the zip  
- Extract it  
- Run `main.py`  

### Option 3: Build the `.exe` yourself

Run this command in the folder containing `main.py`:

```
py -m PyInstaller --noconfirm --onefile --windowed --icon=assets/icon.ico --add-data "assets;assets" --name RTV_ModTool_Beta_v0.4.14 main.py
```
The --add-data option is important because it includes the custom logo and icon files in the packaged app.

## Planned Features
- Inventory, Equipment, Catalog Editing
- Alternate start locations

## Notes
- Character folders are shown by folder name only
- Dehydration, frostbite, and insanity are display-only condition flags
- World editing is intentionally disabled to avoid breaking game state

## Files included
- main.py
- save_io.py
- save_parser.py
- save_scanner.py
- assets/icon.ico
- assets/logo.png
- CHANGELOG.md





