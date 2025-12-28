# Cross platform
# Drag and drop
# Single files and folders
# Cancel button added
# Added options menu CPu, GPU CPU and GPU
# Added super speed mode

import os
import subprocess
import threading
import time
import platform
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from moviepy import VideoFileClip
from tkinterdnd2 import DND_FILES, TkinterDnD
from concurrent.futures import ThreadPoolExecutor


class RTHConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("RonsTechHub Video Converter")
        self.root.geometry("600x620")
        self.root.minsize(550, 600)

        self.is_dark_mode = False
        self.target_extensions = ('.mkv', '.mov', '.webm', '.avi')
        self.stop_requested = False
        self.hw_mode = tk.IntVar(value=1)  # 1: Auto, 2: GPU, 3: CPU
        self.super_speed = tk.BooleanVar(value=False)

        try:
            icon_img = Image.open("RTH Logo.png")
            self.icon_photo = ImageTk.PhotoImage(icon_img)
            self.root.iconphoto(False, self.icon_photo)
        except:
            pass

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self.setup_ui()
        self.apply_theme()

        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_drop)

    def setup_ui(self):
        # --- HEADER ---
        self.header_frame = tk.Frame(self.root)
        self.header_frame.grid(row=0, column=0, sticky="nsew", pady=10, padx=20)
        self.header_frame.columnconfigure(1, weight=1)

        try:
            img = Image.open("RTH Logo.png").resize((50, 50), Image.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(img)
            self.logo_label = tk.Label(self.header_frame, image=self.logo_img)
            self.logo_label.grid(row=0, column=0, padx=10)
        except:
            self.logo_label = tk.Label(self.header_frame, text="[RTH]")
            self.logo_label.grid(row=0, column=0, padx=10)

        self.title_label = tk.Label(self.header_frame, text="RonsTechHub Video Converter", font=("Arial", 16, "bold"))
        self.title_label.grid(row=0, column=1, sticky="w")

        self.theme_btn = tk.Button(self.header_frame, text="🌙 Dark Mode", command=self.toggle_theme, relief="flat",
                                   padx=10)
        self.theme_btn.grid(row=0, column=2)

        # --- MAIN AREA ---
        self.main_frame = tk.Frame(self.root, relief="groove", borderwidth=2)
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.main_frame.columnconfigure(0, weight=1)

        self.status_label = tk.Label(self.main_frame, text="Drag & Drop Folder or Video Files Here", font=("Arial", 11))
        self.status_label.pack(pady=(15, 5))

        self.info_label = tk.Label(self.main_frame, text="Converts to MP4. Existing MP4s are ignored.",
                                   font=("Arial", 9), wraplength=450)
        self.info_label.pack()

        # Hardware Settings
        self.hw_frame = tk.LabelFrame(self.main_frame, text=" Hardware Acceleration ", padx=10, pady=10,
                                      font=("Arial", 9, "bold"))
        self.hw_frame.pack(pady=10, padx=20, fill="x")
        tk.Radiobutton(self.hw_frame, text="Auto", variable=self.hw_mode, value=1).pack(side="left", expand=True)
        tk.Radiobutton(self.hw_frame, text="GPU Only", variable=self.hw_mode, value=2).pack(side="left", expand=True)
        tk.Radiobutton(self.hw_frame, text="CPU Only", variable=self.hw_mode, value=3).pack(side="left", expand=True)

        # SUPER SPEED MODE SECTION
        self.speed_frame = tk.Frame(self.main_frame)
        self.speed_frame.pack(pady=5, fill="x", padx=20)
        self.speed_toggle = tk.Checkbutton(self.speed_frame, text="🚀 SUPER SPEED MODE", variable=self.super_speed,
                                           font=("Arial", 10, "bold"), fg="#e67e22")
        self.speed_toggle.pack(side="left")
        self.speed_warn = tk.Label(self.speed_frame, text="(Uses most power & produces most heat)",
                                   font=("Arial", 8, "italic"), fg="red")
        self.speed_warn.pack(side="left", padx=5)

        self.progress_label = tk.Label(self.main_frame, text="Ready", font=("Arial", 10, "bold"))
        self.progress_label.pack(pady=5)

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.progress_bar = ttk.Progressbar(self.main_frame, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill="x", padx=40, pady=10)

        # --- BUTTONS ---
        self.btn_frame = tk.Frame(self.root)
        self.btn_frame.grid(row=2, column=0, sticky="ew", padx=40, pady=20)
        self.btn_frame.columnconfigure(0, weight=1)
        self.btn_frame.columnconfigure(1, weight=1)
        self.btn_frame.columnconfigure(2, weight=1)

        self.file_btn = tk.Button(self.btn_frame, text="Files", command=lambda: self.start_thread("files"),
                                  bg="#00CED1", fg="white", font=("Arial", 11, "bold"), pady=10, relief="flat")
        self.file_btn.grid(row=0, column=0, padx=5, sticky="ew")

        self.folder_btn = tk.Button(self.btn_frame, text="Folder", command=lambda: self.start_thread("folder"),
                                    bg="#00CED1", fg="white", font=("Arial", 11, "bold"), pady=10, relief="flat")
        self.folder_btn.grid(row=0, column=1, padx=5, sticky="ew")

        self.cancel_btn = tk.Button(self.btn_frame, text="Cancel", command=self.request_cancel, bg="#b71c1c",
                                    fg="white", font=("Arial", 11, "bold"), pady=10, relief="flat", state="disabled")
        self.cancel_btn.grid(row=0, column=2, padx=5, sticky="ew")

    def apply_theme(self):
        colors = {
            True: {"bg": "#1e1e1e", "fg": "#ffffff", "w_bg": "#2d2d2d", "btn": "☀️ Light", "trough": "#333333",
                   "hw_fg": "#00CED1"},
            False: {"bg": "#f0f0f0", "fg": "#000000", "w_bg": "#ffffff", "btn": "🌙 Dark", "trough": "#dddddd",
                    "hw_fg": "#333333"}
        }[self.is_dark_mode]
        self.root.configure(bg=colors["bg"])
        self.header_frame.configure(bg=colors["bg"])
        self.main_frame.configure(bg=colors["w_bg"])
        self.hw_frame.configure(bg=colors["w_bg"], fg=colors["hw_fg"])
        self.speed_frame.configure(bg=colors["w_bg"])
        self.speed_toggle.configure(bg=colors["w_bg"], selectcolor=colors["w_bg"])
        self.speed_warn.configure(bg=colors["w_bg"])
        self.status_label.configure(bg=colors["w_bg"], fg=colors["fg"])
        self.info_label.configure(bg=colors["w_bg"], fg="#888888")
        self.progress_label.configure(bg=colors["w_bg"], fg=colors["fg"])
        self.title_label.configure(bg=colors["bg"], fg=colors["fg"])
        self.theme_btn.configure(text=colors["btn"], bg=colors["bg"], fg=colors["fg"])
        self.style.configure("TProgressbar", troughcolor=colors["trough"], background='#00CED1')

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()

    def get_best_codec(self):
        mode = self.hw_mode.get()
        if mode == 3: return "libx264"
        try:
            subprocess.check_output('nvidia-smi', shell=True)
            return "h264_nvenc"
        except:
            pass
        if platform.system() == "Darwin": return "h264_videotoolbox"
        if mode == 2: raise Exception("No GPU found.")
        return "libx264"

    def convert_single_file(self, f_path, codec, i, total):
        if self.stop_requested: return
        filename = os.path.basename(f_path)
        out_p = os.path.join(os.path.dirname(f_path), f"{os.path.splitext(filename)[0]}-converted.mp4")

        self.status_label.config(text=f"Converting: {filename}")
        self.progress_label.config(text=f"Processing {i + 1} of {total}")

        try:
            clip = VideoFileClip(f_path)
            bitrate = clip.reader.infos.get('video_bitrate', '5000k')
            b_str = f"{int(bitrate / 1000)}k" if isinstance(bitrate, (int, float)) else "5000k"

            # Apply Super Speed Presets
            preset = "ultrafast" if codec == "libx264" else None

            clip.write_videofile(out_p, codec=codec, audio_codec="aac", bitrate=b_str, fps=clip.fps, preset=preset,
                                 logger=None)
            clip.close()
        except:
            pass

        self.root.after(0, lambda: self.progress_bar.step(1))

    def start_thread(self, mode, paths=None):
        self.file_btn.config(state="disabled")
        self.folder_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.stop_requested = False
        threading.Thread(target=self.process_manager, args=(mode, paths), daemon=True).start()

    def process_manager(self, mode, paths):
        target_files = []
        if mode == "folder":
            folder = filedialog.askdirectory()
            if folder: target_files = [os.path.join(folder, f) for f in os.listdir(folder) if
                                       f.lower().endswith(self.target_extensions) and "-converted" not in f.lower()]
        elif mode == "files":
            target_files = list(filedialog.askopenfilenames(filetypes=[("Video Files", "*.mkv *.mov *.webm *.avi")]))
        elif mode == "drop":
            for p in paths:
                if os.path.isdir(p):
                    target_files.extend([os.path.join(p, f) for f in os.listdir(p) if
                                         f.lower().endswith(self.target_extensions) and "-converted" not in f.lower()])
                elif p.lower().endswith(self.target_extensions):
                    target_files.append(p)

        if not target_files:
            self.root.after(0, self.reset_buttons)
            return

        try:
            codec = self.get_best_codec()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.root.after(0, self.reset_buttons)
            return

        self.progress_bar["maximum"] = len(target_files)
        self.progress_bar["value"] = 0

        max_workers = 3 if self.super_speed.get() else 1

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i, f_path in enumerate(target_files):
                if self.stop_requested: break
                executor.submit(self.convert_single_file, f_path, codec, i, len(target_files))

        messagebox.showinfo("RonsTechHub", "Batch Complete!") if not self.stop_requested else messagebox.showwarning(
            "RonsTechHub", "Cancelled.")
        self.root.after(0, self.reset_buttons)

    def request_cancel(self):
        if messagebox.askyesno("Cancel", "Stop all conversions?"):
            self.stop_requested = True
            self.status_label.config(text="Stopping... please wait.")

    def handle_drop(self, event):
        self.start_thread("drop", list(self.root.tk.splitlist(event.data)))

    def reset_buttons(self):
        self.status_label.config(text="Status: Ready")
        self.progress_bar["value"] = 0
        self.file_btn.config(state="normal")
        self.folder_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = RTHConverter(root)
    root.mainloop()