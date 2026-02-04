import customtkinter as ctk
import threading
import asyncio
import os
import json
from tkinter import filedialog
from logic import BotLogic

COLOR_BG = "#000000"
COLOR_PANEL = "#0A0A0A"
COLOR_FG = "#FFFFFF"
COLOR_LZ_GREEN = "#B8F244"
COLOR_LZ_PURPLE = "#A076F9"
COLOR_LZ_RED = "#FF4444"
COLOR_BORDER = "#333333"

FONT_MONO_BOLD = ("Courier New", 13, "bold") 
FONT_MONO_REG = ("Courier New", 12)
FONT_HEADER = ("Courier New", 24, "bold")

ctk.set_appearance_mode("Dark")

class LZButton(ctk.CTkButton):
    def __init__(self, master, theme_color=COLOR_FG, **kwargs):
        self.theme_color = theme_color
        super().__init__(master, **kwargs)
        
        self.configure(
            corner_radius=0, 
            border_width=1, 
            fg_color=COLOR_BG,
            border_color=self.theme_color, 
            text_color=self.theme_color,
            font=FONT_MONO_BOLD, 
            hover_color=self.theme_color
        )
        
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)

    def on_enter(self, event):
        if self._state != "disabled":
            self.configure(text_color=COLOR_BG, fg_color=self.theme_color)

    def on_leave(self, event):
        if self._state != "disabled":
            self.configure(text_color=self.theme_color, fg_color=COLOR_BG)
            
    def set_disabled(self, disabled: bool):
        if disabled:
            self.configure(state="disabled", border_color="#333333", text_color="#333333", fg_color=COLOR_BG)
        else:
            self.configure(state="normal", border_color=self.theme_color, text_color=self.theme_color, fg_color=COLOR_BG)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TREX")
        self.geometry("1200x700")
        self.configure(fg_color=COLOR_BG)
        
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(script_dir, "icon.ico")
            
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
            else:
                print(f"Warning: Icon not found at {icon_path}")
        except Exception as e:
            print(f"Icon load error: {e}")

        self.grid_columnconfigure(0, weight=0) 
        self.grid_columnconfigure(1, weight=1) 
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self.bot_logic = BotLogic(self.log_message)
        self.loop = asyncio.new_event_loop()
        
        self.profile_data = [] 
        self.is_sidebar_visible = True

        self._init_ui()
        self._load_db()

    def _init_ui(self):
        self.left_frame = ctk.CTkFrame(self, fg_color=COLOR_BG, width=280, corner_radius=0)
        self.left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.left_frame.grid_propagate(False)
        
        ctk.CTkLabel(self.left_frame, text="TREX_PROTOCOL", font=FONT_HEADER, text_color=COLOR_FG).pack(pady=(0, 30), anchor="w")

        ctk.CTkLabel(self.left_frame, text="// TARGET SYSTEM", font=FONT_MONO_BOLD, text_color=COLOR_FG, anchor="w").pack(fill="x", pady=(0, 5))
        
        self.browser_info = ctk.CTkLabel(self.left_frame, text="[ADS POWER]", font=FONT_MONO_REG, text_color=COLOR_LZ_GREEN, anchor="w")
        self.browser_info.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(self.left_frame, text="// CONCURRENCY", font=FONT_MONO_BOLD, text_color=COLOR_FG, anchor="w").pack(fill="x", pady=(0, 5))
        self.threads_slider = ctk.CTkSlider(self.left_frame, from_=1, to=10, number_of_steps=9, button_color=COLOR_FG, progress_color=COLOR_FG, button_hover_color=COLOR_LZ_GREEN, fg_color="#333333", command=self.update_slider)
        self.threads_slider.pack(fill="x", pady=(10, 5))
        self.threads_slider.set(1)
        self.threads_label = ctk.CTkLabel(self.left_frame, text="> THREADS: 1", font=FONT_MONO_REG, text_color=COLOR_FG, anchor="w")
        self.threads_label.pack(fill="x", pady=(0, 20))

        self.toggle_btn = LZButton(self.left_frame, text="HIDE_PROFILES [>>>]", theme_color=COLOR_FG, command=self.toggle_sidebar, height=35)
        self.toggle_btn.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(self.left_frame, text="").pack(expand=True)

        self.start_btn = LZButton(self.left_frame, text="INITIALIZE_SEQUENCE", theme_color=COLOR_LZ_GREEN, command=self.start_process, height=50)
        self.start_btn.pack(fill="x", pady=(0, 10), side="bottom")
        self.stop_btn = LZButton(self.left_frame, text="TERMINATE", theme_color=COLOR_LZ_RED, command=self.stop_process, height=40)
        self.stop_btn.set_disabled(True)
        self.stop_btn.pack(fill="x", pady=(10, 20), side="bottom")

        self.center_frame = ctk.CTkFrame(self, fg_color=COLOR_BG, corner_radius=0, border_width=1, border_color=COLOR_BORDER)
        self.center_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        self.center_frame.grid_rowconfigure(1, weight=1)
        self.center_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.center_frame, text="> SYSTEM_LOGS", font=FONT_MONO_BOLD, text_color=COLOR_FG, anchor="w").grid(row=0, column=0, padx=15, pady=15, sticky="w")
        self.textbox = ctk.CTkTextbox(self.center_frame, fg_color="transparent", text_color=COLOR_LZ_GREEN, font=FONT_MONO_REG, corner_radius=0, activate_scrollbars=True)
        self.textbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.textbox.tag_config("error", foreground=COLOR_LZ_RED)
        self.textbox.tag_config("warn", foreground="yellow")

        self.right_frame = ctk.CTkFrame(self, fg_color=COLOR_BG, width=300, corner_radius=0, border_width=0)
        self.right_frame.grid(row=0, column=2, padx=(0, 20), pady=20, sticky="nsew")
        self.right_frame.grid_propagate(False)
        self.right_frame.grid_rowconfigure(2, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.right_frame, text="// DATABASE", font=FONT_MONO_BOLD, text_color=COLOR_FG, anchor="w").grid(row=0, column=0, pady=(0, 10), sticky="w")
        
        tools_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        tools_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        self.load_btn = LZButton(tools_frame, text="IMPORT", theme_color=COLOR_FG, command=self.import_profiles, height=30, width=80)
        self.load_btn.pack(side="left", padx=(0, 5))
        
        self.clear_btn = LZButton(tools_frame, text="CLEAR", theme_color=COLOR_LZ_PURPLE, command=self.clear_database, height=30, width=80)
        self.clear_btn.pack(side="left")
        
        self.count_label = ctk.CTkLabel(tools_frame, text="[0]", font=FONT_MONO_REG, text_color=COLOR_LZ_GREEN)
        self.count_label.pack(side="right")

        self.scroll_frame = ctk.CTkScrollableFrame(self.right_frame, fg_color=COLOR_PANEL, corner_radius=0, border_width=1, border_color=COLOR_BORDER)
        self.scroll_frame.grid(row=2, column=0, sticky="nsew")

        self.select_all_var = ctk.BooleanVar(value=True)
        self.select_all_chk = ctk.CTkCheckBox(self.right_frame, text="SELECT ALL", variable=self.select_all_var, command=self.toggle_all, 
                    fg_color=COLOR_LZ_GREEN, hover_color=COLOR_LZ_GREEN, checkmark_color=COLOR_BG,
                    font=FONT_MONO_REG, text_color=COLOR_FG, border_color=COLOR_FG, corner_radius=0)
        self.select_all_chk.grid(row=3, column=0, pady=10, sticky="w")

    def toggle_sidebar(self):
        if self.is_sidebar_visible:
            self.right_frame.grid_remove()
            self.toggle_btn.configure(text="SHOW_PROFILES [<<<]")
            self.is_sidebar_visible = False
        else:
            self.right_frame.grid()
            self.toggle_btn.configure(text="HIDE_PROFILES [>>>]")
            self.is_sidebar_visible = True

    def update_slider(self, value):
        self.threads_label.configure(text=f"> THREADS: {int(value)}")

    def log_message(self, message, tag=None):
        self.after(0, self._update_textbox, message, tag)

    def _update_textbox(self, message, tag):
        self.textbox.insert("end", f"> {message}\n", tag)
        self.textbox.see("end")

    def parse_line(self, line):
        line = line.strip().replace('"', '').replace("'", "")
        if not line: return None, None
        
        parts = line.split(':')
        pid = parts[0].strip()
        
        if len(pid) < 4 or len(pid) > 20 or not pid.isalnum(): return None, None
        
        name = parts[1].strip() if len(parts) > 1 else f"Account_{pid[-4:]}"
        
        return pid, name

    def import_profiles(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if not file_path: return

        new_count = 0
        dup_count = 0
        existing_ids = {p['id'] for p in self.profile_data}

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                pid, name = self.parse_line(line)
                if pid:
                    if pid not in existing_ids:
                        self.profile_data.append({
                            'id': pid,
                            'name': name,
                            'active': ctk.BooleanVar(value=True)
                        })
                        existing_ids.add(pid)
                        new_count += 1
                    else:
                        dup_count += 1
        
        self._refresh_list()
        self._save_db()
        msg = f"Imported: {new_count}. Duplicates: {dup_count}."
        self.log_message(msg, "warn" if dup_count > 0 else None)

    def _refresh_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        for item in self.profile_data:
            if not isinstance(item.get('active'), ctk.BooleanVar):
                item['active'] = ctk.BooleanVar(value=item.get('active_bool', True))

            row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            display_text = f"{item['name']} ({item['id']})"
            
            chk = ctk.CTkCheckBox(row, text=display_text, variable=item['active'],
                    fg_color=COLOR_LZ_GREEN, hover_color=COLOR_LZ_GREEN, checkmark_color=COLOR_BG,
                    font=FONT_MONO_REG, text_color=COLOR_FG, border_color=COLOR_FG, corner_radius=0)
            chk.pack(side="left", padx=5)
            
        
        self.count_label.configure(text=f"[{len(self.profile_data)}]")

    def toggle_all(self):
        val = self.select_all_var.get()
        for item in self.profile_data:
            item['active'].set(val)

    def clear_database(self):
        self.profile_data = []
        self._refresh_list()
        self._save_db()
        self.log_message("Database cleared.", "error")

    def _save_db(self):
        data_to_save = [{'id': p['id'], 'name': p['name'], 'active_bool': p['active'].get()} for p in self.profile_data]
        try:
            with open("profiles.json", "w") as f:
                json.dump(data_to_save, f)
        except Exception as e:
            self.log_message(f"Save error: {e}", "error")

    def _load_db(self):
        if not os.path.exists("profiles.json"): return
        try:
            with open("profiles.json", "r") as f:
                loaded = json.load(f)
                self.profile_data = []
                for item in loaded:
                    self.profile_data.append({
                        'id': item['id'],
                        'name': item.get('name', f"Account_{item['id']}"),
                        'active': ctk.BooleanVar(value=item['active_bool'])
                    })
            self._refresh_list()
            self.log_message(f"Database loaded. {len(self.profile_data)} profiles.")
        except Exception as e:
            self.log_message(f"Load error: {e}", "error")

    def start_process(self):
        selected_items = []
        
        for p in self.profile_data:
            if p['active'].get():
                selected_items.append({'id': p['id']})

        if not selected_items:
            self.log_message("ERROR: No profiles selected.", "error")
            return

        self.start_btn.set_disabled(True)
        self.start_btn.configure(text="RUNNING...")
        self.stop_btn.set_disabled(False)
        self.load_btn.set_disabled(True)
        self.clear_btn.set_disabled(True)
        
        self._save_db()
        
        threads = int(self.threads_slider.get())
        
        self.log_message(f"Starting sequence. Targets: {len(selected_items)}. Threads: {threads}")
        threading.Thread(target=self._run_async_loop, args=(selected_items, threads), daemon=True).start()

    def _run_async_loop(self, items, threads):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.bot_logic.run_batch(items, threads))
        self.after(0, self._reset_buttons)

    def stop_process(self):
        self.log_message("!!! INTERRUPT SIGNAL !!!", "error")
        self.stop_btn.set_disabled(True)
        asyncio.run_coroutine_threadsafe(self.bot_logic.emergency_stop(), self.loop)

    def _reset_buttons(self):
        self.start_btn.set_disabled(False)
        self.start_btn.configure(text="INITIALIZE_SEQUENCE", fg_color=COLOR_BG, text_color=COLOR_LZ_GREEN)
        self.stop_btn.set_disabled(True)
        self.stop_btn.configure(fg_color=COLOR_BG)
        self.load_btn.set_disabled(False)
        self.clear_btn.set_disabled(False)

if __name__ == "__main__":
    app = App()
    app.mainloop()