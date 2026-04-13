import json
import os
import re
import shutil
from datetime import datetime

from save_parser import parse_player_tres, parse_world_tres

SUPPORTED_FILENAMES = [
    "Character.tres","World.tres","Traders.tres","Tent.tres","Cabin.tres","Preferences.tres","Validator.tres",
]

FLAT_100_KEYS = ["health", "energy", "hydration", "temperature", "mental"]
FALSE_KEYS = ["dehydration", "bleeding", "fracture", "burn", "frostbite", "rupture", "insanity"]
MAX_BACKUPS_PER_SLOT = 10


def _prune_backup_root(backup_root, keep=MAX_BACKUPS_PER_SLOT, logger=print):
    if not os.path.isdir(backup_root):
        return
    folders = []
    for name in os.listdir(backup_root):
        full_path = os.path.join(backup_root, name)
        if os.path.isdir(full_path):
            try:
                mtime = os.path.getmtime(full_path)
            except OSError:
                mtime = 0
            folders.append((mtime, name, full_path))
    folders.sort(reverse=True)
    for _mtime, name, full_path in folders[keep:]:
        shutil.rmtree(full_path, ignore_errors=True)
        logger(f"Pruned old backup -> {name}")


def create_backup_folder(found_files, logger=print, prefix="backup", keep=MAX_BACKUPS_PER_SLOT):
    if not found_files:
        raise ValueError("No files supplied for backup.")
    first_path = next(iter(found_files.values()))
    source_dir = os.path.dirname(first_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = os.path.join(source_dir, "_phase1_backups")
    backup_dir = os.path.join(backup_root, f"{prefix}_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)
    for _key, path in found_files.items():
        destination = os.path.join(backup_dir, os.path.basename(path))
        shutil.copy2(path, destination)
        logger(f"Backed up -> {destination}")
    _prune_backup_root(backup_root, keep=keep, logger=logger)
    return backup_dir


def apply_updates_to_tres(path, updates, logger=print):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    for key, value in updates.items():
        replacement = "true" if isinstance(value, bool) and value else "false" if isinstance(value, bool) else str(value)
        pattern = rf"^({re.escape(key)}\s*=\s*).+$"
        def repl(match):
            return match.group(1) + replacement
        text, count = re.subn(pattern, repl, text, flags=re.MULTILINE)
        if count > 0:
            logger(f"Updated {key} -> {replacement}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def list_backups(profile_dir, logger=print):
    backup_root = os.path.join(profile_dir, "_phase1_backups")
    records = []
    if not os.path.isdir(backup_root):
        logger(f"No backup root found at: {backup_root}")
        return records
    for name in sorted(os.listdir(backup_root), reverse=True):
        full_path = os.path.join(backup_root, name)
        if os.path.isdir(full_path):
            records.append({"name": name, "path": full_path})
    logger(f"Found {len(records)} backup(s).")
    return records


def preview_backup(backup_dir, logger=print):
    result = {"backup_path": backup_dir, "player": {}, "world": {}, "missing_files": []}
    character_path = os.path.join(backup_dir, "Character.tres")
    world_path = os.path.join(backup_dir, "World.tres")
    if os.path.isfile(character_path):
        result["player"] = parse_player_tres(character_path, logger=logger)
    else:
        result["missing_files"].append("Character.tres")
    if os.path.isfile(world_path):
        result["world"] = parse_world_tres(world_path, logger=logger)
    else:
        result["missing_files"].append("World.tres")
    return result


def restore_backup(backup_dir, current_files, logger=print):
    create_backup_folder(current_files, logger=logger)
    restored_any = False
    for _key, live_path in current_files.items():
        filename = os.path.basename(live_path)
        source_path = os.path.join(backup_dir, filename)
        if os.path.isfile(source_path):
            shutil.copy2(source_path, live_path)
            logger(f"Restored {filename} -> {live_path}")
            restored_any = True
    if not restored_any:
        raise FileNotFoundError("No matching files were found in the selected backup.")


def load_profile_names(root_path, logger=print):
    path = os.path.join(root_path, "profile_names.json")
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        logger(f"Failed to load profile names: {exc}")
        return {}


def save_profile_names(root_path, names, logger=print):
    path = os.path.join(root_path, "profile_names.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(names, f, indent=2)
    logger(f"Saved friendly names to {path}")


ACTIVE_PROFILE_FILE = ".rtv_active_profile.json"


def read_active_profile(root_path, logger=print):
    path = os.path.join(root_path, ACTIVE_PROFILE_FILE)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        value = data.get("active_profile") if isinstance(data, dict) else None
        return value if isinstance(value, str) and value.strip() else None
    except Exception as exc:
        logger(f"Failed to read active profile metadata: {exc}")
        return None


def write_active_profile(root_path, profile_name, logger=print):
    os.makedirs(root_path, exist_ok=True)
    path = os.path.join(root_path, ACTIVE_PROFILE_FILE)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"active_profile": profile_name}, f, indent=2)
    logger(f"Active profile set -> {profile_name}")


def publish_profile_to_live_root(profile_dir, live_root_folder, logger=print):
    os.makedirs(live_root_folder, exist_ok=True)
    for name in SUPPORTED_FILENAMES:
        source = os.path.join(profile_dir, name)
        if os.path.isfile(source):
            dest = os.path.join(live_root_folder, name)
            shutil.copy2(source, dest)
            logger(f"Published {name} -> {dest}")


def sync_live_root_to_profile(active_profile_dir, live_root_folder, logger=print, keep=MAX_BACKUPS_PER_SLOT):
    if not os.path.isdir(active_profile_dir):
        logger(f"Startup sync skipped: active profile folder not found -> {active_profile_dir}")
        return False
    live_files = {}
    for name in SUPPORTED_FILENAMES:
        source = os.path.join(live_root_folder, name)
        if os.path.isfile(source):
            key = os.path.splitext(name)[0]
            live_files[key] = source
    if not live_files:
        logger("Startup sync skipped: no live root save files found.")
        return False
    backup_dir = None
    existing_profile_files = {}
    for name in SUPPORTED_FILENAMES:
        path = os.path.join(active_profile_dir, name)
        if os.path.isfile(path):
            key = os.path.splitext(name)[0]
            existing_profile_files[key] = path
    if existing_profile_files:
        backup_dir = create_backup_folder(existing_profile_files, logger=logger, prefix="auto_sync", keep=keep)
        logger(f"Startup sync backup created -> {backup_dir}")
    for name in SUPPORTED_FILENAMES:
        source = os.path.join(live_root_folder, name)
        if os.path.isfile(source):
            dest = os.path.join(active_profile_dir, name)
            shutil.copy2(source, dest)
            logger(f"Startup sync copied {name} -> {dest}")
    logger(f"Startup sync complete: live root -> {os.path.basename(active_profile_dir)}")
    return True


def normalize_template_character_file(path, logger=print):
    if not os.path.isfile(path):
        return
    updates = {key: 100 for key in FLAT_100_KEYS}
    updates.update({key: False for key in FALSE_KEYS})
    apply_updates_to_tres(path, updates, logger=logger)


def bootstrap_initial_character_from_live_root(characters_root, live_root_folder, logger=print):
    os.makedirs(characters_root, exist_ok=True)
    has_supported = any(os.path.isfile(os.path.join(live_root_folder, name)) for name in SUPPORTED_FILENAMES)
    if not has_supported:
        logger("Selected root does not contain recognizable live save files, so no initial character was created.")
        return None
    target_dir = os.path.join(characters_root, "Character_001")
    os.makedirs(target_dir, exist_ok=True)
    copied = copy_profile_from_source(live_root_folder, target_dir, logger=logger)
    return target_dir if copied else None


def copy_profile_from_source(source_dir, target_dir, logger=print):
    copied = False
    for name in SUPPORTED_FILENAMES:
        source = os.path.join(source_dir, name)
        if os.path.isfile(source):
            dest = os.path.join(target_dir, name)
            shutil.copy2(source, dest)
            logger(f"Copied {name} -> {dest}")
            copied = True
    return copied


def ensure_base_template(template_root, live_root_folder, logger=print):
    character_file = os.path.join(template_root, "Character.tres")
    has_template = os.path.isdir(template_root) and os.path.isfile(character_file)
    if has_template:
        logger("BaseCharacterTemplate found.")
        return "BaseCharacterTemplate"
    os.makedirs(template_root, exist_ok=True)
    copied = copy_profile_from_source(live_root_folder, template_root, logger=logger)
    if not copied:
        raise FileNotFoundError("No BaseCharacterTemplate files or live save files were found to create the template.")
    normalize_template_character_file(os.path.join(template_root, "Character.tres"), logger=logger)
    logger("BaseCharacterTemplate not found. Created template from current live save.")
    return "AutoCreatedTemplate"


def create_new_character(characters_root, template_root, live_root_folder, folder_name, logger=print):
    target_dir = os.path.join(characters_root, folder_name)
    if os.path.exists(target_dir):
        raise FileExistsError(folder_name)
    source_used = ensure_base_template(template_root, live_root_folder, logger=logger)
    os.makedirs(target_dir, exist_ok=False)
    copied = copy_profile_from_source(template_root, target_dir, logger=logger)
    if not copied:
        raise FileNotFoundError("BaseCharacterTemplate exists but did not contain supported save files.")
    return target_dir, source_used
