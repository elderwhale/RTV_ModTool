
import os
import sys
import webbrowser
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, simpledialog

from save_scanner import find_character_profiles, find_root_save_files
from save_parser import parse_player_tres, parse_world_tres
from save_io import (
    create_backup_folder,
    apply_updates_to_tres,
    list_backups,
    preview_backup,
    restore_backup,
    publish_profile_to_live_root,
    bootstrap_initial_character_from_live_root,
    create_new_character,
    read_active_profile,
    write_active_profile,
    sync_live_root_to_profile,
)

class BackupManagerWindow(tk.Toplevel):
    def __init__(self, parent_app):
        super().__init__(parent_app.root)
        self.app = parent_app
        self.title("Backup Restore Manager")
        self.geometry("900x620")
        self.configure(bg=App.BG_DARK)
        self.backup_records = []
        self.selected_backup = None
        self.build_ui()
        self.refresh_backups()

    def build_ui(self):
        top = tk.Frame(self, bg=App.BG_DARK, padx=10, pady=10); top.pack(fill="x")
        tk.Label(top, text="Available Backups", font=("Segoe UI", 11, "bold"), bg=App.BG_DARK, fg="white").pack(side="left")
        self.app.make_button(top, "Refresh Backups", self.refresh_backups, width=16).pack(side="right")

        body = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg=App.BG_DARK, sashwidth=6, relief="flat"); body.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        left = tk.Frame(body, bg=App.PANEL, padx=8, pady=8); body.add(left, width=320)
        self.backup_list = tk.Listbox(left, bg=App.FIELD, fg=App.TEXT_DARK, selectbackground=App.ACCENT, selectforeground="white", relief="flat", bd=0, highlightthickness=0); self.backup_list.pack(fill="both", expand=True)
        self.backup_list.bind("<<ListboxSelect>>", self.on_select_backup)

        right = tk.Frame(body, bg=App.PANEL, padx=8, pady=8); body.add(right)
        info = ttk.LabelFrame(right, text="Backup Details", style="Section.TLabelframe", padding=10); info.pack(fill="both", expand=True)
        self.detail_text = tk.Text(info, wrap="word", bg=App.FIELD, fg=App.TEXT_DARK, relief="flat", bd=0); self.detail_text.pack(fill="both", expand=True)

        bottom = tk.Frame(self, bg=App.BG_DARK, padx=10, pady=10); bottom.pack(fill="x")
        self.path_label = tk.Label(bottom, text="No backup selected", anchor="w", justify="left", bg=App.BG_DARK, fg="white")
        self.path_label.pack(side="left", fill="x", expand=True)
        self.app.make_button(bottom, "Restore Selected Backup", self.restore_selected, width=22, accent=True).pack(side="right")

    def refresh_backups(self):
        self.backup_list.delete(0, tk.END)
        self.detail_text.delete("1.0", tk.END)
        self.path_label.config(text="No backup selected")
        self.selected_backup = None
        if not self.app.current_profile_dir:
            messagebox.showwarning("No character loaded", "Select a character folder first.")
            self.destroy()
            return
        self.backup_records = list_backups(self.app.current_profile_dir, logger=self.app.log)
        if not self.backup_records:
            self.detail_text.insert(tk.END, "No backups found.")
            return
        for record in self.backup_records:
            self.backup_list.insert(tk.END, record["name"])

    def on_select_backup(self, _event=None):
        if not self.backup_list.curselection():
            return
        index = self.backup_list.curselection()[0]
        self.selected_backup = self.backup_records[index]
        self.path_label.config(text=self.selected_backup["path"])
        preview = preview_backup(self.selected_backup["path"], logger=self.app.log)
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, format_backup_preview(preview))

    def restore_selected(self):
        if not self.selected_backup or not self.app.current_files:
            return
        answer = messagebox.askyesno("Confirm Restore", "Restore the selected backup to this character folder?\n\nA fresh pre-restore backup will be created first.")
        if not answer:
            return
        restore_backup(self.selected_backup["path"], self.app.current_files, logger=self.app.log)
        self.app.load_current_files()
        messagebox.showinfo("Restore complete", "The selected backup has been restored.")

class App:
    CONDITION_KEYS = [
        ("dehydration", "Dehydration"), ("bleeding", "Bleeding"), ("fracture", "Fracture"),
        ("burn", "Burn"), ("frostbite", "Frostbite"), ("rupture", "Rupture"), ("insanity", "Insanity"),
    ]
    EDITABLE_CONDITION_KEYS = {"bleeding", "fracture", "burn", "rupture"}
    PLAYER_EDIT_KEYS = ["health", "energy", "hydration", "temperature", "mental"]
    WORLD_READONLY_KEYS = ["difficulty", "season", "day", "time", "weather", "weatherTime", "shelters"]
    BG_DARK = "#2f2d2a"
    PANEL = "#d9cfbf"
    PANEL_ALT = "#e7dfd1"
    FIELD = "#f4efe6"
    ACCENT = "#8e4436"
    ACCENT_HOVER = "#a55343"
    TEXT_DARK = "#241f1b"
    TEXT_MUTED = "#5f564d"

    def __init__(self, root):
        self.root = root
        self.root.title("RTV_ModTool Beta v0.4.14")
        self.root.geometry("1120x860")
        self.current_root_folder = None
        self.characters_root = None
        self.template_root = None
        self.live_root_folder = None
        self.current_profile_dir = None
        self.current_files = {}
        self.player_widgets = {}
        self.world_readonly_widgets = {}
        self.condition_vars = {}
        self.profile_records = []
        self.live_root_files = {}
        self.active_profile_name = None
        self.logo_image = None
        self.root_icon_image = None
        self.load_branding_assets()
        self.setup_styles()
        self.build_ui()
        self.log("RTV_ModTool Beta v0.4.14 initialized.")
        self.log("New Character auto-creates BaseCharacterTemplate on first use if it is missing.")

    def resource_path(self, relative_path):
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)

    def load_branding_assets(self):
        icon_path = self.resource_path(os.path.join("assets", "icon.ico"))
        logo_path = self.resource_path(os.path.join("assets", "logo.png"))
        try:
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except tk.TclError:
            pass
        try:
            if os.path.exists(logo_path):
                self.logo_image = tk.PhotoImage(file=logo_path)
                self.root_icon_image = self.logo_image
                self.root.iconphoto(True, self.root_icon_image)
        except tk.TclError:
            self.logo_image = None

    def setup_styles(self):
        self.root.configure(bg=self.BG_DARK)
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Big.TNotebook", background=self.PANEL, borderwidth=0, tabmargins=[10, 10, 10, 0])
        style.configure("Big.TNotebook.Tab", background=self.PANEL_ALT, foreground=self.TEXT_DARK, padding=[20, 10], font=("Segoe UI", 10, "bold"), borderwidth=0)
        style.map("Big.TNotebook.Tab", background=[("selected", self.ACCENT), ("active", self.ACCENT_HOVER)], foreground=[("selected", "white"), ("active", "white")])
        style.configure("Section.TLabelframe", background=self.PANEL_ALT, bordercolor=self.ACCENT, borderwidth=1, relief="solid", padding=12)
        style.configure("Section.TLabelframe.Label", background=self.PANEL_ALT, foreground=self.TEXT_DARK, font=("Segoe UI", 10, "bold"))

    def make_button(self, parent, text, command, width=None, accent=False):
        bg = self.ACCENT if accent else self.PANEL_ALT
        fg = "white" if accent else self.TEXT_DARK
        active_bg = self.ACCENT_HOVER if accent else self.PANEL
        btn = tk.Button(parent, text=text, command=command, width=width, bg=bg, fg=fg, activebackground=active_bg, activeforeground=fg, relief="flat", bd=0, padx=14, pady=8, font=("Segoe UI", 9, "bold"), cursor="hand2")
        return btn

    def build_ui(self):
        outer = tk.Frame(self.root, bg=self.BG_DARK, padx=14, pady=14)
        outer.pack(fill="both", expand=True)

        top = tk.Frame(outer, bg=self.BG_DARK)
        top.pack(fill="x", pady=(0, 12))
        self.make_button(top, "Select Save Root", self.select_root_folder, width=16).pack(side="left")
        self.make_button(top, "New Character", self.create_new_character, width=14).pack(side="left", padx=(8, 0))
        self.make_button(top, "Rename Character", self.rename_selected_profile, width=16).pack(side="left", padx=(8, 0))
        self.make_button(top, "Backup Manager", self.open_backup_manager, width=15).pack(side="left", padx=(8, 0))
        self.make_button(top, "Buy Me a Coffee", self.open_buy_me_a_coffee, width=16, accent=True).pack(side="right")

        body = tk.Frame(outer, bg=self.BG_DARK)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=self.PANEL, padx=12, pady=12, highlightthickness=1, highlightbackground=self.ACCENT)
        left.pack(side="left", fill="y", padx=(0, 12))
        tk.Label(left, text="Character Folders", font=("Segoe UI", 12, "bold"), bg=self.PANEL, fg=self.TEXT_DARK).pack(anchor="w")
        tk.Label(left, text="Active slot shows with an asterisk.", font=("Segoe UI", 9), bg=self.PANEL, fg=self.TEXT_MUTED).pack(anchor="w", pady=(2, 8))
        self.profile_list = tk.Listbox(left, height=22, bg=self.FIELD, fg=self.TEXT_DARK, selectbackground=self.ACCENT, selectforeground="white", relief="flat", bd=0, highlightthickness=0, font=("Segoe UI", 10), activestyle="none")
        self.profile_list.pack(fill="both", expand=True)
        self.profile_list.bind("<<ListboxSelect>>", self.on_select_profile)

        right = tk.Frame(body, bg=self.PANEL, padx=12, pady=12, highlightthickness=1, highlightbackground=self.ACCENT)
        right.pack(side="left", fill="both", expand=True)

        header = tk.Frame(right, bg=self.PANEL_ALT, padx=14, pady=14, highlightthickness=1, highlightbackground=self.ACCENT)
        header.pack(fill="x", pady=(0, 10))
        if self.logo_image is not None:
            logo = tk.Label(header, image=self.logo_image, bg=self.PANEL_ALT)
            logo.pack(side="left", padx=(0, 14))
        text_wrap = tk.Frame(header, bg=self.PANEL_ALT)
        text_wrap.pack(side="left", fill="x", expand=True)
        tk.Label(text_wrap, text="RTV_ModTool", font=("Segoe UI", 20, "bold"), bg=self.PANEL_ALT, fg=self.TEXT_DARK).pack(anchor="w")
        tk.Label(text_wrap, text="Beta v0.4.14", font=("Segoe UI", 10, "bold"), bg=self.PANEL_ALT, fg=self.ACCENT).pack(anchor="w", pady=(2, 2))
        tk.Label(text_wrap, text="Clean save management for Road to Vostok with active-profile sync and rolling backups.", font=("Segoe UI", 10), bg=self.PANEL_ALT, fg=self.TEXT_MUTED, wraplength=640, justify="left").pack(anchor="w")

        self.tabs = ttk.Notebook(right, style="Big.TNotebook")
        self.tabs.pack(fill="both", expand=True)
        self.player_tab = tk.Frame(self.tabs, padx=16, pady=16, bg=self.PANEL_ALT)
        self.world_tab = tk.Frame(self.tabs, padx=16, pady=16, bg=self.PANEL_ALT)
        self.summary_tab = tk.Frame(self.tabs, padx=16, pady=16, bg=self.PANEL_ALT)
        self.tabs.add(self.player_tab, text="Player")
        self.tabs.add(self.world_tab, text="World")
        self.tabs.add(self.summary_tab, text="Summary")
        self.build_player_tab()
        self.build_world_tab()
        self.build_summary_tab()

    def build_player_tab(self):
        tk.Label(self.player_tab, text="Player Editor", font=("Segoe UI", 15, "bold"), bg=self.PANEL_ALT, fg=self.TEXT_DARK).pack(anchor="w", pady=(0, 12))
        vitals = ttk.LabelFrame(self.player_tab, text="Vitals", style="Section.TLabelframe")
        vitals.pack(fill="x", pady=(0, 12))
        labels = {"health": "Health", "energy": "Energy", "hydration": "Hydration", "temperature": "Temperature", "mental": "Mental"}
        for row, key in enumerate(self.PLAYER_EDIT_KEYS):
            self.player_widgets[key] = self.add_entry_row(vitals, labels[key], row)
        #tk.Label(self.player_tab, text="Note: health appears capped by the game around 100 based on current testing.", anchor="w", fg=self.TEXT_MUTED, bg=self.PANEL_ALT).pack(fill="x", pady=(0, 12))
        conditions = ttk.LabelFrame(self.player_tab, text="Condition Status", style="Section.TLabelframe")
        conditions.pack(fill="x", pady=(0, 12))
        for idx, (key, label) in enumerate(self.CONDITION_KEYS):
            var = tk.BooleanVar(value=False)
            state = "normal" if key in self.EDITABLE_CONDITION_KEYS else "disabled"
            cb = tk.Checkbutton(conditions, text=label, variable=var, state=state, anchor="w", bg=self.PANEL_ALT, fg=self.TEXT_DARK, selectcolor=self.FIELD, activebackground=self.PANEL_ALT, activeforeground=self.TEXT_DARK, disabledforeground=self.TEXT_MUTED, highlightthickness=0)
            cb.grid(row=idx // 2, column=idx % 2, sticky="w", padx=(0, 22), pady=5)
            self.condition_vars[key] = var
        row = tk.Frame(self.player_tab, bg=self.PANEL_ALT)
        row.pack(fill="x", pady=(8, 0))
        self.make_button(row, "Clear Conditions", self.clear_conditions, width=15).pack(side="left")
        self.make_button(row, "Reload Player", self.reload_player, width=14).pack(side="left", padx=(8, 0))
        self.make_button(row, "Save Player", self.save_player, width=14, accent=True).pack(side="right")

    def build_world_tab(self):
        tk.Label(self.world_tab, text="World Reference", font=("Segoe UI", 15, "bold"), bg=self.PANEL_ALT, fg=self.TEXT_DARK).pack(anchor="w", pady=(0, 12))
        box = ttk.LabelFrame(self.world_tab, text="Read-Only World Values", style="Section.TLabelframe")
        box.pack(fill="x", pady=(0, 12))
        labels = {"difficulty": "Difficulty", "season": "Season", "day": "Day", "time": "Time", "weather": "Weather", "weatherTime": "Weather Timer", "shelters": "Shelters"}
        for row, key in enumerate(self.WORLD_READONLY_KEYS):
            self.world_readonly_widgets[key] = self.add_readonly_row(box, labels[key], row)
        tk.Label(self.world_tab, text="World values stay read-only because direct edits have been shown to break game state and desync the in-game clock.", anchor="w", fg=self.TEXT_MUTED, bg=self.PANEL_ALT, justify="left", wraplength=760).pack(fill="x")

    def build_summary_tab(self):
        tk.Label(self.summary_tab, text="Activity Log", font=("Segoe UI", 15, "bold"), bg=self.PANEL_ALT, fg=self.TEXT_DARK).pack(anchor="w", pady=(0, 8))
        tk.Label(self.summary_tab, text="Detected files, backup activity, and status messages are shown here.", anchor="w", fg=self.TEXT_MUTED, bg=self.PANEL_ALT).pack(fill="x", pady=(0, 10))
        self.summary_text = tk.Text(self.summary_tab, wrap="word", bg=self.FIELD, fg=self.TEXT_DARK, insertbackground=self.TEXT_DARK, relief="flat", bd=0, padx=10, pady=10, font=("Consolas", 10))
        self.summary_text.pack(fill="both", expand=True)

    def add_entry_row(self, parent, label_text, row):
        tk.Label(parent, text=label_text + ":", width=16, anchor="w", bg=self.PANEL_ALT, fg=self.TEXT_DARK).grid(row=row, column=0, sticky="w", pady=5)
        entry = tk.Entry(parent, bg=self.FIELD, fg=self.TEXT_DARK, relief="flat", bd=0, insertbackground=self.TEXT_DARK, font=("Segoe UI", 10))
        entry.grid(row=row, column=1, sticky="ew", pady=5, padx=(8, 0), ipady=6)
        parent.grid_columnconfigure(1, weight=1)
        return entry

    def add_readonly_row(self, parent, label_text, row):
        tk.Label(parent, text=label_text + ":", width=16, anchor="w", bg=self.PANEL_ALT, fg=self.TEXT_DARK).grid(row=row, column=0, sticky="w", pady=5)
        value = tk.Label(parent, text="—", anchor="w", bg=self.FIELD, fg=self.TEXT_DARK, width=28, padx=8, pady=6)
        value.grid(row=row, column=1, sticky="ew", pady=5, padx=(8, 0))
        parent.grid_columnconfigure(1, weight=1)
        return value

    def open_backup_manager(self):
        BackupManagerWindow(self)

    def open_buy_me_a_coffee(self):
        webbrowser.open("https://www.buymeacoffee.com/elderwhale")
        self.log("Opened Buy Me a Coffee link in the default browser.")

    def log(self, message):
        print(message)
        self.summary_text.insert(tk.END, message + "\n")
        self.summary_text.see(tk.END)

    def log_section(self, title, lines):
        self.log(f"[{title}]")
        if not lines:
            self.log("- none")
            return
        for line in lines:
            self.log(f"- {line}")

    def clear_outputs(self, clear_summary=False):
        if clear_summary:
            self.summary_text.delete("1.0", tk.END)
        for entry in self.player_widgets.values():
            entry.delete(0, tk.END)
        for label in self.world_readonly_widgets.values():
            label.config(text="—")
        for var in self.condition_vars.values():
            var.set(False)

    def refresh_profiles(self, startup_sync=False):
        self.active_profile_name = read_active_profile(self.live_root_folder, logger=self.log)
        if startup_sync and self.active_profile_name:
            active_dir = os.path.join(self.characters_root, self.active_profile_name)
            sync_live_root_to_profile(active_dir, self.live_root_folder, logger=self.log)
        self.live_root_files = find_root_save_files(self.live_root_folder, logger=self.log)
        character_records = find_character_profiles(self.characters_root, logger=self.log)
        self.profile_records = []
        if self.live_root_files:
            self.profile_records.append({
                "profile_dir": self.live_root_folder,
                "files": self.live_root_files,
                "is_live_root": True,
            })
        self.profile_records.extend(character_records)
        self.profile_list.delete(0, tk.END)
        self.clear_outputs(clear_summary=True)
        if not self.profile_records:
            return False
        for record in self.profile_records:
            self.profile_list.insert(tk.END, self.get_profile_display_name(record))
        live_count = 1 if self.live_root_files else 0
        self.log(f"Loaded {live_count} live root profile and {len(character_records)} character folder(s).")
        return True

    def select_root_folder(self):
        path = filedialog.askdirectory()
        if not path:
            return
        self.current_root_folder = path
        self.characters_root = os.path.join(path, "Characters")
        self.template_root = os.path.join(path, "BaseCharacterTemplate")
        self.live_root_folder = path
        os.makedirs(self.characters_root, exist_ok=True)
        ok = self.refresh_profiles(startup_sync=True)
        if ok:
            self.profile_list.selection_clear(0, tk.END)
            self.profile_list.selection_set(0)
            self.profile_list.activate(0)
            self.load_profile(self.profile_records[0])
            return
        created = bootstrap_initial_character_from_live_root(self.characters_root, self.live_root_folder, logger=self.log)
        if created:
            self.refresh_profiles()
            self.select_profile_by_folder(os.path.basename(created))
        else:
            messagebox.showwarning("No characters found", "No character folders were found, and no recognizable live save files were found in the selected root to seed an initial character.")

    def select_profile_by_folder(self, folder_name):
        for idx, record in enumerate(self.profile_records):
            if os.path.basename(record["profile_dir"]) == folder_name:
                self.profile_list.selection_clear(0, tk.END)
                self.profile_list.selection_set(idx)
                self.profile_list.activate(idx)
                self.load_profile(record)
                return

    def create_new_character(self):
        if not self.current_root_folder:
            messagebox.showwarning("No save root", "Select a save root first.")
            return
        folder_name = simpledialog.askstring("New Character", "Enter a new character folder name:", initialvalue=self.suggest_new_character_name(), parent=self.root)
        if folder_name is None:
            return
        folder_name = folder_name.strip()
        if not folder_name:
            messagebox.showerror("Invalid name", "Character folder name cannot be blank.")
            return
        try:
            created, source_used = create_new_character(self.characters_root, self.template_root, self.live_root_folder, folder_name, logger=self.log)
            self.log(f"Created new character folder: {created}")
            self.log(f"New character source: {source_used}")
            self.refresh_profiles()
            self.select_profile_by_folder(os.path.basename(created))
        except FileExistsError:
            messagebox.showerror("Already exists", "A character folder with that name already exists.")
        except FileNotFoundError as exc:
            messagebox.showerror("No template or live save found", str(exc))
        except Exception as exc:
            messagebox.showerror("Create failed", str(exc))

    def suggest_new_character_name(self):
        existing = {os.path.basename(record["profile_dir"]).lower() for record in self.profile_records}
        i = 1
        while True:
            candidate = f"Character_{i:03d}"
            if candidate.lower() not in existing:
                return candidate
            i += 1

    def get_profile_display_name(self, record):
        if record.get("is_live_root"):
            return "[ACTIVE ROOT SAVE]"
        folder_name = os.path.basename(record["profile_dir"])
        return f"{folder_name}*" if folder_name == getattr(self, "active_profile_name", None) else folder_name

    def on_select_profile(self, _event=None):
        if not self.profile_list.curselection():
            return
        self.load_profile(self.profile_records[self.profile_list.curselection()[0]])

    def load_profile(self, record):
        self.current_profile_dir = record["profile_dir"]
        self.current_files = record["files"]
        self.clear_outputs(clear_summary=True)
        backup_dir = create_backup_folder(self.current_files, logger=self.log)
        if record.get("is_live_root"):
            self.log("Loaded active live root save.")
        else:
            self.log(f"Loaded character folder: {self.current_profile_dir}")
        self.log_section("Detected Save Files", [f"{key}: {file_path}" for key, file_path in self.current_files.items()])
        self.log_section("Latest Backup", [backup_dir])
        self.load_current_files()

    def rename_selected_profile(self):
        if not self.current_root_folder or not self.profile_list.curselection():
            messagebox.showwarning("No character selected", "Select a save root and a character folder first.")
            return
        index = self.profile_list.curselection()[0]
        record = self.profile_records[index]
        if record.get("is_live_root"):
            messagebox.showwarning("Cannot rename active root", "The active root save is not a character folder and cannot be renamed.")
            return
        old_folder_name = os.path.basename(record["profile_dir"])
        new_folder_name = simpledialog.askstring("Rename Character", f"Enter a new folder name for {old_folder_name}:", initialvalue=old_folder_name, parent=self.root)
        if new_folder_name is None:
            return
        new_folder_name = new_folder_name.strip()
        if not new_folder_name:
            messagebox.showerror("Invalid name", "Character folder name cannot be blank.")
            return
        if new_folder_name == old_folder_name:
            return
        old_path = record["profile_dir"]
        new_path = os.path.join(self.characters_root, new_folder_name)
        if os.path.exists(new_path):
            messagebox.showerror("Already exists", "A character folder with that name already exists.")
            return
        try:
            os.rename(old_path, new_path)
            self.log(f"Renamed character folder: {old_folder_name} -> {new_folder_name}")
            if self.active_profile_name == old_folder_name:
                write_active_profile(self.live_root_folder, new_folder_name, logger=self.log)
                self.active_profile_name = new_folder_name
            self.refresh_profiles()
            self.select_profile_by_folder(new_folder_name)
        except Exception as exc:
            messagebox.showerror("Rename failed", str(exc))

    def load_current_files(self):
        if "Character" in self.current_files:
            player = parse_player_tres(self.current_files["Character"], logger=self.log)
            self.render_player(player)
            self.log("Player values loaded into the Player tab.")
        if "World" in self.current_files:
            world = parse_world_tres(self.current_files["World"], logger=self.log)
            self.render_world(world)
            self.log("World values loaded into the World tab.")

    def render_player(self, data):
        for key in self.PLAYER_EDIT_KEYS:
            entry = self.player_widgets[key]
            entry.delete(0, tk.END)
            if data.get(key) is not None:
                entry.insert(0, str(data.get(key)))
        for key, _ in self.CONDITION_KEYS:
            self.condition_vars[key].set(bool(data.get(key)))

    def render_world(self, data):
        for key in self.WORLD_READONLY_KEYS:
            self.world_readonly_widgets[key].config(text=format_value(data.get(key)))

    def clear_conditions(self):
        for key, _ in self.CONDITION_KEYS:
            self.condition_vars[key].set(False)

    def reload_player(self):
        if "Character" not in self.current_files:
            return
        player = parse_player_tres(self.current_files["Character"], logger=self.log)
        self.render_player(player)

    def save_player(self):
        if "Character" not in self.current_files:
            return
        path = self.current_files["Character"]
        updates = {}
        try:
            for key in self.PLAYER_EDIT_KEYS:
                raw = self.player_widgets[key].get().strip()
                if raw != "":
                    updates[key] = float(raw) if "." in raw else int(raw)
            for key, _ in self.CONDITION_KEYS:
                if key in self.EDITABLE_CONDITION_KEYS:
                    updates[key] = self.condition_vars[key].get()
            apply_updates_to_tres(path, updates, logger=self.log)
            is_live_root = os.path.abspath(self.current_profile_dir) == os.path.abspath(self.live_root_folder)
            if not is_live_root:
                publish_profile_to_live_root(self.current_profile_dir, self.live_root_folder, logger=self.log)
                write_active_profile(self.live_root_folder, os.path.basename(self.current_profile_dir), logger=self.log)
                self.active_profile_name = os.path.basename(self.current_profile_dir)
                saved_msg = "Player values were saved to the character folder and published as the active profile."
                self.refresh_profiles()
                self.select_profile_by_folder(os.path.basename(self.current_profile_dir))
            else:
                linked_profile = self.active_profile_name or read_active_profile(self.live_root_folder, logger=self.log)
                linked_dir = os.path.join(self.characters_root, linked_profile) if linked_profile else None
                if linked_profile and linked_dir and os.path.isdir(linked_dir):
                    sync_live_root_to_profile(linked_dir, self.live_root_folder, logger=self.log)
                    self.active_profile_name = linked_profile
                    self.refresh_profiles()
                    saved_msg = f"Player values were saved to the active root save and synced back to {linked_profile}."
                elif linked_profile:
                    saved_msg = f"Player values were saved to the active root save. Active profile link '{linked_profile}' was not found on disk."
                else:
                    saved_msg = "Player values were saved to the active root save. No active character folder link was set."
            player = parse_player_tres(path, logger=self.log)
            self.render_player(player)
            messagebox.showinfo("Saved", f"{saved_msg}\n\nCharacter file:\n{path}")
        except ValueError as exc:
            messagebox.showerror("Invalid input", f"One or more Player fields contain invalid values.\n\n{exc}")

        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))

def format_value(value):
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)

def format_dict(data):
    return "\n".join(f"{k}: {format_value(v)}" for k, v in data.items())

def format_backup_preview(preview):
    lines = ["Selected Backup:", preview.get("backup_path", "Unknown"), "", "[Player]"]
    for key, value in preview.get("player", {}).items():
        lines.append(f"{key}: {format_value(value)}")
    lines += ["", "[World]"]
    for key, value in preview.get("world", {}).items():
        lines.append(f"{key}: {format_value(value)}")
    missing = preview.get("missing_files", [])
    if missing:
        lines += ["", "Missing Files:"]
        for item in missing:
            lines.append(f"- {item}")
    return "\n".join(lines)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.geometry("1920x1080")
    root.mainloop()
