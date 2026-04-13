# RTV_ModTool Beta v0.4.14

## Highlights
- Added active-profile tracking with persistent metadata
- Active character folder now shows an asterisk in the list
- Added startup sync from live root save back into the linked active character folder
- Saving from the active root save now also syncs back into the linked active character folder
- Added rolling backup management capped at 10 backups per character slot
- Cleaned up the main UI and moved file, backup, and status details into the Summary tab
- Removed the separate friendly-name layer and now use folder names directly
- Added rename support for character folders
- Added a Buy Me a Coffee button

## Player Editing
- Root save selection now correctly loads the real active root Character.tres
- Editable condition list is limited to supported manual conditions
- Dehydration, frostbite, and insanity remain visible but are no longer toggleable

## Stability
- Fixed root-save scanning so nested character files no longer override the live root file
- Fixed active-root save behavior so it no longer attempts to publish the root save onto itself
- Improved active-profile syncing and startup flow
