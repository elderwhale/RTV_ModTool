# RTV_ModTool Beta v0.4.14

RTV_ModTool is a save-management and editing utility for Road to Vostok testing.

⚠️ Please use at your own risk and open an issue if any bugs are encountered.

⚠️ Remember to take a backup before going out on a permadeath run!


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
- Click 'Select Save Root'
- Navigate to C:\Users\YourUser\AppData\Roaming and select the Road to Vostok folder
- Note that when this folder is selected the tool will insert folders related to backups, syncing, and character profiles then build your BaseCharacterTemplate from your initial save. **Note, I'm still figuring out the inventory system and the way it's coded. For now, start new characters until you have a goopy default loadout to work with, then use that save as your template.**
- Set values as desired and click Save Player, which saves that Character Profile to it's own folder, as well as setting it as the active one in the main game files. When the app is re-opened it will sync the active character from the game file to it's corresponding character folder.

## Planned Features
- Inventory, Equipment, Catalog Editing
- Alternate start locations
- Cat restore button :)

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





