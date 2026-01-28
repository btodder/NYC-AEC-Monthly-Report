import customtkinter as ctk
import tkinter as tk
import sys
import subprocess
import os
import ctypes

# Enable DPI awareness for crisp rendering on high-res displays
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

def get_windows_theme():
    """Detect Windows theme (light/dark) via registry."""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                           r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return "light" if value == 1 else "dark"
    except:
        return "light"

def get_theme_colors(theme):
    """Return color scheme based on system theme."""
    if theme == "dark":
        return {
            'bg': '#1e1e1e',
            'surface': '#2d2d2d',
            'surface_dark': '#252525',
            'text': '#ffffff',
            'subtext': '#b4b4b4',
            'accent': '#0078d4',
            'accent_hover': '#1a86d9',
            'cancel': '#484848',
            'cancel_hover': '#c42b1c',  # Red on hover
            'border': '#3f3f3f'
        }
    else:
        return {
            'bg': '#f0f0f0',
            'surface': '#ffffff',
            'surface_dark': '#f5f5f5',
            'text': '#1f1f1f',
            'subtext': '#5f5f5f',
            'accent': '#0067c0',
            'accent_hover': '#005a9e',
            'cancel': '#6e6e6e',
            'cancel_hover': '#c42b1c',  # Red on hover
            'border': '#d0d0d0'
        }

def verify_manual_push():
    """
    Verification popup for manual git push commands with commit message editing.
    Returns 0 if approved, 1 if rejected.
    """
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Read the last commit message
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=%B"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=True
        )
        original_message = result.stdout.strip()
    except subprocess.CalledProcessError:
        original_message = "Unable to read commit message"
    
    result_dict = {'approved': False, 'message': original_message}
    
    # Detect theme and get colors
    theme = get_windows_theme()
    colors = get_theme_colors(theme)
    
    # Set customtkinter appearance
    ctk.set_appearance_mode("dark" if theme == "dark" else "light")
    ctk.set_default_color_theme("blue")
    ctk.set_widget_scaling(1.0)
    
    # Create window
    root = ctk.CTk()
    root.overrideredirect(True)
    root.configure(fg_color=colors['border'])
    
    # Spacing and sizing (scaled to 2/3, text unchanged)
    PADDING = 20
    ELEMENT_HEIGHT = 57
    TITLE_HEIGHT = 36
    BORDER_WIDTH = 2
    CORNER_RADIUS = 3
    
    # Fixed window size (scaled to 2/3)
    window_width = 467
    window_height = 250 + TITLE_HEIGHT
    
    # Center the window
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Apply rounded corners on Windows 11
    root.update()
    try:
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        if hwnd == 0:
            hwnd = root.winfo_id()
        preference = ctypes.c_int(2)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(preference), ctypes.sizeof(preference))
    except:
        pass
    
    # Main wrapper with border
    main_frame = ctk.CTkFrame(root, fg_color=colors['surface'], corner_radius=0)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=BORDER_WIDTH, pady=BORDER_WIDTH)
    
    # Custom title bar
    title_bar = ctk.CTkFrame(main_frame, fg_color=colors['surface'], height=TITLE_HEIGHT - BORDER_WIDTH, corner_radius=0)
    title_bar.pack(fill=tk.X, side=tk.TOP)
    title_bar.pack_propagate(False)
    
    # Title text - centered
    title_label = ctk.CTkLabel(
        title_bar,
        text="Git Push Detected, Review Commit Message:",
        font=("Segoe UI", 13),
        text_color=colors['text']
    )
    title_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    
    # Minimize button
    def minimize_window():
        root.overrideredirect(False)
        root.iconify()
        root.after(100, lambda: root.overrideredirect(True))
    
    min_btn = ctk.CTkButton(
        title_bar,
        text="─",
        command=minimize_window,
        font=("Segoe UI", 14),
        fg_color=colors['surface'],
        text_color=colors['text'],
        hover_color=colors['border'],
        width=50,
        height=TITLE_HEIGHT - BORDER_WIDTH,
        corner_radius=0
    )
    min_btn.pack(side=tk.RIGHT)
    
    # Make title bar draggable
    def start_drag(event):
        root._drag_x = event.x
        root._drag_y = event.y
    
    def do_drag(event):
        x = root.winfo_x() + event.x - root._drag_x
        y = root.winfo_y() + event.y - root._drag_y
        root.geometry(f"+{x}+{y}")
    
    title_bar.bind("<Button-1>", start_drag)
    title_bar.bind("<B1-Motion>", do_drag)
    title_label.bind("<Button-1>", start_drag)
    title_label.bind("<B1-Motion>", do_drag)
    
    # Main container - darker background
    container = ctk.CTkFrame(main_frame, fg_color=colors['surface_dark'], corner_radius=0)
    container.pack(fill=tk.BOTH, expand=True)
    
    # Configure grid for vertical centering
    container.grid_rowconfigure(0, weight=1)
    container.grid_rowconfigure(1, weight=0)
    container.grid_rowconfigure(2, weight=0)
    container.grid_rowconfigure(3, weight=1)
    container.grid_columnconfigure(0, weight=1)
    
    # Entry with rounded corners
    entry = ctk.CTkEntry(
        container,
        font=("Segoe UI", 13),
        fg_color=colors['surface'],
        text_color=colors['text'],
        border_color=colors['border'],
        border_width=2,
        height=ELEMENT_HEIGHT,
        corner_radius=CORNER_RADIUS,
        justify="center"
    )
    entry.grid(row=1, column=0, sticky="ew", padx=PADDING, pady=(0, PADDING))
    entry.insert(0, original_message)
    entry.focus_set()
    entry.select_range(0, tk.END)
    
    def on_confirm():
        result_dict['approved'] = True
        result_dict['message'] = entry.get()
        root.destroy()
        
    def on_cancel():
        result_dict['approved'] = False
        root.destroy()
    
    # Button frame
    btn_frame = ctk.CTkFrame(container, fg_color=colors['surface_dark'], height=ELEMENT_HEIGHT, corner_radius=0)
    btn_frame.grid(row=2, column=0, sticky="ew", padx=PADDING)
    btn_frame.grid_propagate(False)
    btn_frame.grid_columnconfigure(0, weight=1)
    btn_frame.grid_columnconfigure(1, weight=0, minsize=PADDING)
    btn_frame.grid_columnconfigure(2, weight=1)
    btn_frame.grid_rowconfigure(0, weight=1)
    
    # Confirm button with rounded corners
    confirm_btn = ctk.CTkButton(
        btn_frame,
        text="Confirm",
        command=on_confirm,
        font=("Segoe UI", 13),
        fg_color=colors['accent'],
        hover_color=colors['accent_hover'],
        text_color="white",
        corner_radius=CORNER_RADIUS
    )
    confirm_btn.grid(row=0, column=0, sticky="nsew")
    
    # Cancel button with rounded corners
    cancel_btn = ctk.CTkButton(
        btn_frame,
        text="Cancel",
        command=on_cancel,
        font=("Segoe UI", 13),
        fg_color=colors['cancel'],
        hover_color=colors['cancel_hover'],
        text_color="white",
        corner_radius=CORNER_RADIUS
    )
    cancel_btn.grid(row=0, column=2, sticky="nsew")
    
    # Bind keys
    root.bind('<Return>', lambda e: on_confirm())
    root.bind('<Escape>', lambda e: on_cancel())
    
    root.protocol("WM_DELETE_WINDOW", on_cancel)
    root.mainloop()
    
    if not result_dict['approved']:
        return 1
    
    # If message was changed, amend the commit
    new_message = result_dict['message']
    if new_message != original_message and new_message.strip():
        try:
            subprocess.run(
                ["git", "commit", "--amend", "-m", new_message],
                cwd=repo_dir,
                check=True
            )
            print(f"Commit message updated to: {new_message}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to amend commit: {e}")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(verify_manual_push())
