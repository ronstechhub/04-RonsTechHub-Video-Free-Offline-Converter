import os
import subprocess
import threading
import time
import platform
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
from PIL import Image, ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD
from concurrent.futures import ThreadPoolExecutor


class RTHConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("RonsTechHub Video Converter")
        self.root.geometry("600x780")
        self.root.minsize(550, 750)

        self.is_dark_mode = False
        self.target_extensions = ('.mkv', '.mov', '.webm', '.avi')
        self.stop_requested = False
        self.queued_files = []

        # Settings Variables
        self.hw_mode = tk.IntVar(value=1)  # 1: Auto, 2: GPU, 3: CPU
        self.super_speed = tk.BooleanVar(value=False)
        self.output_type = tk.IntVar(value=1)  # 1: Source, 2: Custom
        self.custom_output_path = tk.StringVar(value="No folder selected")

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
        # Header, Output Settings, Hardware Settings, and Buttons UI code (identical to requested features)
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

        self.main_frame = tk.Frame(self.root, relief="groove", borderwidth=2)
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.main_frame.columnconfigure(0, weight=1)

        self.status_label = tk.Label(self.main_frame, text="Queue: 0 files", font=("Arial", 11, "bold"), fg="#00CED1")
        self.status_label.pack(pady=(10, 5))

        self.out_frame = tk.LabelFrame(self.main_frame, text=" 1. Output Destination Settings ", padx=10, pady=10,
                                       font=("Arial", 9, "bold"))
        self.out_frame.pack(pady=10, padx=20, fill="x")
        tk.Radiobutton(self.out_frame, text="Save in Original Source Folder", variable=self.output_type, value=1).pack(
            anchor="w")

        custom_row = tk.Frame(self.out_frame)
        custom_row.pack(fill="x", pady=5)
        tk.Radiobutton(custom_row, text="Save in Custom Folder:", variable=self.output_type, value=2).pack(side="left")
        self.path_label = tk.Label(custom_row, textvariable=self.custom_output_path, font=("Arial", 8), fg="blue",
                                   wraplength=300)
        self.path_label.pack(side="left", padx=5)

        self.browse_out_btn = tk.Button(self.out_frame, text="Browse / Create & Rename Folder",
                                        command=self.pick_output_folder, font=("Arial", 8))
        self.browse_out_btn.pack(anchor="w", padx=20)

        self.hw_frame = tk.LabelFrame(self.main_frame, text=" 2. Hardware Acceleration ", padx=10, pady=10,
                                      font=("Arial", 9, "bold"))
        self.hw_frame.pack(pady=10, padx=20, fill="x")
        tk.Radiobutton(self.hw_frame, text="Auto", variable=self.hw_mode, value=1).pack(side="left", expand=True)
        tk.Radiobutton(self.hw_frame, text="GPU Only", variable=self.hw_mode, value=2).pack(side="left", expand=True)
        tk.Radiobutton(self.hw_frame, text="CPU Only", variable=self.hw_mode, value=3).pack(side="left", expand=True)

        self.speed_frame = tk.Frame(self.main_frame)
        self.speed_frame.pack(pady=5, fill="x", padx=20)
        self.speed_toggle = tk.Checkbutton(self.speed_frame, text="🚀 SUPER SPEED MODE", variable=self.super_speed,
                                           font=("Arial", 10, "bold"), fg="#e67e22")
        self.speed_toggle.pack(side="left")
        self.speed_warn = tk.Label(self.speed_frame, text="(Uses most power & heat)", font=("Arial", 8, "italic"),
                                   fg="red")
        self.speed_warn.pack(side="left", padx=5)

        self.progress_bar = ttk.Progressbar(self.main_frame, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill="x", padx=40, pady=20)

        self.action_frame = tk.Frame(self.root)
        self.action_frame.grid(row=2, column=0, sticky="ew", padx=40, pady=(10, 10))
        self.action_frame.columnconfigure(0, weight=1);
        self.action_frame.columnconfigure(1, weight=1);
        self.action_frame.columnconfigure(2, weight=1)

        self.file_btn = tk.Button(self.action_frame, text="Select Files", command=lambda: self.add_to_queue("files"),
                                  bg="#00CED1", fg="white", font=("Arial", 10, "bold"), pady=8, relief="flat")
        self.file_btn.grid(row=0, column=0, padx=5, sticky="ew")
        self.folder_btn = tk.Button(self.action_frame, text="Select Folder",
                                    command=lambda: self.add_to_queue("folder"), bg="#00CED1", fg="white",
                                    font=("Arial", 10, "bold"), pady=8, relief="flat")
        self.folder_btn.grid(row=0, column=1, padx=5, sticky="ew")
        self.clear_btn = tk.Button(self.action_frame, text="Clear Queue", command=self.clear_queue, bg="#808080",
                                   fg="white", font=("Arial", 10, "bold"), pady=8, relief="flat")
        self.clear_btn.grid(row=0, column=2, padx=5, sticky="ew")

        self.start_btn = tk.Button(self.root, text="START CONVERSION", command=self.begin_conversion, bg="#4CAF50",
                                   fg="white", font=("Arial", 12, "bold"), pady=15, relief="flat")
        self.start_btn.grid(row=3, column=0, sticky="ew", padx=45, pady=(5, 10))
        self.cancel_btn = tk.Button(self.root, text="CANCEL PROCESS", command=self.request_cancel, bg="#b71c1c",
                                    fg="white", font=("Arial", 10, "bold"), pady=10, relief="flat", state="disabled")
        self.cancel_btn.grid(row=4, column=0, sticky="ew", padx=45, pady=(0, 20))

    def convert_single_file(self, f_path, codec, i, total):
        """Direct FFmpeg call for maximum efficiency and compatibility."""
        if self.stop_requested: return
        abs_src = os.path.abspath(f_path)
        dest_dir = os.path.dirname(abs_src) if self.output_type.get() == 1 else os.path.abspath(
            self.custom_output_path.get())
        if not os.path.exists(dest_dir): os.makedirs(dest_dir, exist_ok=True)
        out_p = os.path.join(dest_dir, f"{os.path.splitext(os.path.basename(abs_src))[0]}-converted.mp4")

        # Standard Compatibility Command
        cmd = [
            'ffmpeg', '-y', '-i', abs_src,
            '-c:v', codec,
            '-pix_fmt', 'yuv420p',  # FIX: Ensures video playback on all players
            '-c:a', 'aac', '-b:a', '192k',
            '-movflags', '+faststart'  # Optimizes for web/social media
        ]

        # Add Speed/Quality Tuning
        if codec == "libx264":
            cmd.extend(['-preset', 'ultrafast' if self.super_speed.get() else 'medium'])
            cmd.extend(['-crf', '22'])
        elif codec == "h264_nvenc":
            cmd.extend(['-preset', 'p1' if self.super_speed.get() else 'p4'])

        cmd.append(out_p)

        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except Exception as e:
            print(f"FFmpeg Error on {os.path.basename(abs_src)}: {e}")

        self.root.after(0, lambda: self.progress_bar.step(1))

    # (Helper functions for Queueing, Theme, Explorer remain optimized as requested)
    def add_to_queue(self, mode, paths=None):
        new_files = []
        if mode == "folder":
            folder = filedialog.askdirectory()
            if folder: new_files = [os.path.abspath(os.path.join(folder, f)) for f in os.listdir(folder) if
                                    f.lower().endswith(self.target_extensions) and "-converted" not in f.lower()]
        elif mode == "files":
            new_files = [os.path.abspath(f) for f in
                         filedialog.askopenfilenames(filetypes=[("Video Files", "*.mkv *.mov *.webm *.avi")])]
        elif mode == "drop":
            for p in paths:
                p = os.path.abspath(p.strip('{}'))
                if os.path.isdir(p):
                    new_files.extend([os.path.abspath(os.path.join(p, f)) for f in os.listdir(p) if
                                      f.lower().endswith(self.target_extensions) and "-converted" not in f.lower()])
                elif p.lower().endswith(self.target_extensions):
                    new_files.append(p)
        if new_files:
            self.queued_files.extend(new_files)
            self.status_label.config(text=f"Queue: {len(self.queued_files)} files ready")

    def pick_output_folder(self):
        base_dir = filedialog.askdirectory(title="Select Output Destination")
        if not base_dir: return
        if messagebox.askyesno("New Folder", "Create and rename a new sub-folder here?"):
            new_name = simpledialog.askstring("Rename Folder", "Enter folder name:", initialvalue="Converted Videos")
            if new_name:
                full_path = os.path.abspath(os.path.join(base_dir, new_name))
                os.makedirs(full_path, exist_ok=True)
                base_dir = full_path
        self.custom_output_path.set(os.path.abspath(base_dir))
        self.output_type.set(2)

    def begin_conversion(self):
        if not self.queued_files: return messagebox.showwarning("Empty Queue", "Please select files or a folder first.")
        self.start_btn.config(state="disabled", text="CONVERTING...")
        self.cancel_btn.config(state="normal")
        self.stop_requested = False
        threading.Thread(target=self.process_manager, daemon=True).start()

    def process_manager(self):
        try:
            codec = self.get_best_codec()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return self.root.after(0, self.reset_ui)

        self.progress_bar["maximum"] = len(self.queued_files);
        self.progress_bar["value"] = 0
        workers = 3 if self.super_speed.get() else 1
        with ThreadPoolExecutor(max_workers=workers) as executor:
            for i, f_path in enumerate(self.queued_files):
                if self.stop_requested: break
                executor.submit(self.convert_single_file, f_path, codec, i, len(self.queued_files))

        if not self.stop_requested:
            messagebox.showinfo("RonsTechHub", "Batch Complete!")
            self.open_explorer(
                self.custom_output_path.get() if self.output_type.get() == 2 else os.path.dirname(self.queued_files[0]))
        self.queued_files = [];
        self.root.after(0, self.reset_ui)

    def get_best_codec(self):
        mode = self.hw_mode.get()
        if mode == 3: return "libx264"
        try:
            subprocess.check_output('nvidia-smi', shell=True)
            return "h264_nvenc"
        except:
            pass
        if platform.system() == "Darwin": return "h264_videotoolbox"
        return "libx264"

    def open_explorer(self, path):
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def handle_drop(self, event):
        self.add_to_queue("drop", list(self.root.tk.splitlist(event.data)))

    def request_cancel(self):
        self.stop_requested = True

    def clear_queue(self):
        self.queued_files = []; self.status_label.config(text="Queue: 0 files")

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode; self.apply_theme()

    def apply_theme(self):
        colors = {True: {"bg": "#1e1e1e", "fg": "#ffffff", "w_bg": "#2d2d2d"},
                  False: {"bg": "#f0f0f0", "fg": "#000000", "w_bg": "#ffffff"}}[self.is_dark_mode]
        self.root.configure(bg=colors["bg"]);
        self.header_frame.configure(bg=colors["bg"]);
        self.main_frame.configure(bg=colors["w_bg"])
        self.out_frame.configure(bg=colors["w_bg"], fg="#00CED1");
        self.hw_frame.configure(bg=colors["w_bg"], fg="#00CED1")
        self.speed_frame.configure(bg=colors["w_bg"]);
        self.status_label.configure(bg=colors["w_bg"]);
        self.title_label.configure(bg=colors["bg"], fg=colors["fg"])

    def reset_ui(self):
        self.status_label.config(text="Queue: 0 files");
        self.start_btn.config(state="normal", text="START CONVERSION")
        self.cancel_btn.config(state="disabled");
        self.progress_bar["value"] = 0


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = RTHConverter(root)
    root.mainloop()