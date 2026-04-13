import os

TARGETS = {
    "Character.tres": "Character",
    "World.tres": "World",
    "Traders.tres": "Traders",
    "Tent.tres": "Tent",
    "Cabin.tres": "Cabin",
    "Preferences.tres": "Preferences",
    "Validator.tres": "Validator",
}

IGNORED_DIRS = {"_phase1_backups", "__pycache__"}


def find_root_save_files(root_path, logger=print):
    found = {}
    logger(f"Scanning live root save files in: {root_path}")
    if not os.path.isdir(root_path):
        return found
    for file_name in sorted(os.listdir(root_path)):
        full_path = os.path.join(root_path, file_name)
        if not os.path.isfile(full_path):
            continue
        if file_name in TARGETS:
            key = TARGETS[file_name]
            found[key] = full_path
            logger(f"Found live root {key}: {full_path}")
    return found


def find_save_files(root_path, logger=print):
    found = {}
    logger(f"Scanning for save files under: {root_path}")
    for root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for file_name in files:
            if file_name in TARGETS:
                key = TARGETS[file_name]
                found[key] = os.path.join(root, file_name)
                logger(f"Found {key}: {found[key]}")
    return found


def find_character_profiles(characters_root, logger=print):
    profiles = []
    logger(f"Scanning character folders under: {characters_root}")
    if not os.path.isdir(characters_root):
        return profiles
    for name in sorted(os.listdir(characters_root)):
        profile_dir = os.path.join(characters_root, name)
        if not os.path.isdir(profile_dir):
            continue
        files = find_root_save_files(profile_dir, logger=logger)
        if "Character" in files or "World" in files:
            profiles.append({"profile_dir": profile_dir, "files": files, "is_live_root": False})
            logger(f"Found character profile: {profile_dir}")
    logger(f"Total character profiles found: {len(profiles)}")
    return profiles
