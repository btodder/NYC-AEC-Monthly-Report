# GUI Utilities Shared Module
# --------------------------------------------------------------------------------
# CRITICAL: DO NOT MODIFY THE DESIGN OF THIS POPUP WITHOUT EXPLICIT USER APPROVAL.
# This file serves as the single source of truth for the deployment verification UI.
# It is used by both 'update_site.py' (automation) and 'verify_push.py' (git hook).
# --------------------------------------------------------------------------------

import sys
import os
import ctypes

# GUI Imports - Wrapped in Try/Except for headless environments
HAS_GUI = False
try:
    import tkinter as tk
    import customtkinter as ctk
    HAS_GUI = True
except (ImportError, RuntimeError):
    pass

def enable_dpi_awareness():
    """Enable DPI awareness for crisp rendering on high-res displays."""
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
            'bg': '#202020',
            'surface': '#2d2d2d',       # Title bar
            'surface_dark': '#252525',  # Content area
            'text': '#ffffff',
            'subtext': '#b4b4b4',
            'accent': '#0078d4',        # Blue
            'accent_hover': '#1a86d9',
            'cancel': '#5a5a5a',
            'cancel_hover': '#c42b1c',  # Red hover for cancel
            'border': '#3f3f3f'
        }
    else:
        return {
            'bg': '#f3f3f3',
            'surface': '#ffffff',       # Title bar
            'surface_dark': '#f5f5f5',  # Content area
            'text': '#1f1f1f',
            'subtext': '#5f5f5f',
            'accent': '#0067c0',
            'accent_hover': '#005a9e',
            'cancel': '#8a8a8a',
            'cancel_hover': '#c42b1c',  # Red hover for cancel
            'border': '#e5e5e5'
        }

def get_user_approval(default_message):
    """
    Opens a Modern CustomTkinter popup to get user approval.
    Returns: (approved: bool, message: str)
    """
    if not HAS_GUI:
        print("Headless environment detected. Auto-approving deployment.")
        return True, default_message

    enable_dpi_awareness()

    result = {'approved': False, 'message': None}
    
    # Detect theme
    theme = get_windows_theme()
    colors = get_theme_colors(theme)
    
    # Configure CustomTkinter
    try:
        ctk.set_appearance_mode("Dark" if theme == "dark" else "Light")
        ctk.set_default_color_theme("blue")
        ctk.set_widget_scaling(1.0)
    except Exception:
        pass # In case of any ctk init errors
    
    root = ctk.CTk()
    root.title("Deploy Report")
    root.overrideredirect(True)
    root.configure(fg_color=colors['border'])
    
    # Spacing and sizing (Verified Logic)
    PADDING = 20
    ELEMENT_HEIGHT = 57
    TITLE_HEIGHT = 48
    BORDER_WIDTH = 1
    CORNER_RADIUS = 3
    
    # Dimensions
    window_width = 467
    window_height = 340
    
    # Center Window
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Apply dark title bar on Windows 10/11
    if theme == "dark":
        try:
            hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
            value = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
        except:
            pass
            
    # Main wrapper with border (simulates 1px border via padding)
    main_frame = ctk.CTkFrame(root, fg_color=colors['surface'], corner_radius=0)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=BORDER_WIDTH, pady=BORDER_WIDTH)

    # Title bar
    title_bar = ctk.CTkFrame(main_frame, fg_color=colors['surface'], height=TITLE_HEIGHT - BORDER_WIDTH, corner_radius=0)
    title_bar.pack(fill=tk.X, side=tk.TOP)
    title_bar.pack_propagate(False)

    title_label = ctk.CTkLabel(title_bar, text="🚀  Confirm Deployment", font=("Segoe UI", 13, "bold"), text_color=colors['text'])
    title_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    
    # Minimize button
    def minimize_window():
        root.overrideredirect(False)
        root.iconify()
        def restore_window(event=None):
            if root.state() == 'iconic': return
            root.overrideredirect(True)
            root.unbind('<Map>')
        root.bind('<Map>', restore_window)
    
    min_btn = ctk.CTkButton(
        title_bar, text="─", command=minimize_window,
        font=("Segoe UI", 14), fg_color=colors['surface'], text_color=colors['text'],
        hover_color=colors['border'], width=50, height=TITLE_HEIGHT - BORDER_WIDTH, corner_radius=0
    )
    min_btn.pack(side=tk.RIGHT)
    
    # Make title bar draggable
    def start_drag(event): root._drag_x = event.x; root._drag_y = event.y
    def do_drag(event):
        x = root.winfo_x() + event.x - root._drag_x
        y = root.winfo_y() + event.y - root._drag_y
        root.geometry(f"+{x}+{y}")
    
    title_bar.bind("<Button-1>", start_drag)
    title_bar.bind("<B1-Motion>", do_drag)
    title_label.bind("<Button-1>", start_drag)
    title_label.bind("<B1-Motion>", do_drag)
    
    # Main container
    container = ctk.CTkFrame(main_frame, fg_color=colors['surface_dark'], corner_radius=0)
    container.pack(fill=tk.BOTH, expand=True)

    # Configure grid for vertical centering
    container.grid_rowconfigure(0, weight=1)
    container.grid_rowconfigure(1, weight=0)
    container.grid_rowconfigure(2, weight=0)
    container.grid_rowconfigure(3, weight=1)
    container.grid_columnconfigure(0, weight=1)
    
    # Subheader
    subheader = ctk.CTkLabel(
        container,
        text="Review and edit the commit message before deploying:",
        font=("Segoe UI", 12),
        text_color=colors['subtext']
    )
    subheader.grid(row=0, column=0, pady=(20, 10), sticky="s")
    
    # Entry
    entry = ctk.CTkEntry(
        container,
        font=("Segoe UI", 13),
        fg_color=colors['surface'],
        text_color=colors['text'],
        border_color=colors['border'],
        border_width=1,
        height=ELEMENT_HEIGHT,
        corner_radius=CORNER_RADIUS,
        justify="center"
    )
    entry.grid(row=1, column=0, padx=PADDING, pady=(0, PADDING), sticky="ew")
    entry.insert(0, default_message)
    entry.focus_set()
    entry.select_range(0, tk.END)
    
    # Buttons
    btn_frame = ctk.CTkFrame(container, fg_color=colors['surface_dark'], height=ELEMENT_HEIGHT, corner_radius=0)
    btn_frame.grid(row=2, column=0, padx=PADDING, sticky="ew")
    btn_frame.grid_propagate(False)
    btn_frame.grid_columnconfigure(0, weight=1)
    btn_frame.grid_columnconfigure(1, weight=0, minsize=PADDING) # Spacing
    btn_frame.grid_columnconfigure(2, weight=1)
    btn_frame.grid_rowconfigure(0, weight=1)
    
    def on_confirm():
        result['approved'] = True
        result['message'] = entry.get()
        root.destroy()
        
    def on_cancel():
        result['approved'] = False
        root.destroy()

    confirm_btn = ctk.CTkButton(
        btn_frame, text="Deploy", command=on_confirm,
        font=("Segoe UI", 13, "bold"), fg_color=colors['accent'], text_color="white",
        hover_color=colors['accent_hover'], height=ELEMENT_HEIGHT, corner_radius=CORNER_RADIUS
    )
    confirm_btn.grid(row=0, column=0, sticky="nsew")
    
    cancel_btn = ctk.CTkButton(
        btn_frame, text="Cancel", command=on_cancel,
        font=("Segoe UI", 13, "bold"), fg_color=colors['cancel'], text_color="white",
        hover_color=colors['cancel_hover'], height=ELEMENT_HEIGHT, corner_radius=CORNER_RADIUS
    )
    cancel_btn.grid(row=0, column=2, sticky="nsew")
    
    # Key Bindings
    root.bind('<Return>', lambda e: on_confirm())
    root.bind('<Escape>', lambda e: on_cancel())
    root.protocol("WM_DELETE_WINDOW", on_cancel)
    
    root.mainloop()
    
    return result['approved'], result['message']
