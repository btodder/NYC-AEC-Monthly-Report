import tkinter as tk
import sys
import subprocess
import os

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
        return "light"  # Fallback to light theme

def get_theme_colors(theme):
    """Return color scheme based on system theme."""
    if theme == "dark":
        return {
            'bg': '#202020',
            'surface': '#2d2d2d',
            'text': '#ffffff',
            'subtext': '#b4b4b4',
            'accent': '#60cdff',
            'accent_hover': '#4cb8eb',
            'cancel': '#5a5a5a',
            'cancel_hover': '#6e6e6e',
            'border': '#3f3f3f'
        }
    else:
        return {
            'bg': '#f3f3f3',
            'surface': '#ffffff',
            'text': '#1f1f1f',
            'subtext': '#5f5f5f',
            'accent': '#0067c0',
            'accent_hover': '#005a9e',
            'cancel': '#8a8a8a',
            'cancel_hover': '#737373',
            'border': '#e5e5e5'
        }

def apply_dark_title_bar(root):
    """Apply dark title bar on Windows 10/11."""
    try:
        import ctypes
        root.update()  # Force window to be realized
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 20, ctypes.byref(value), ctypes.sizeof(value)
        )
        # Force redraw
        root.withdraw()
        root.deiconify()
    except:
        pass

def verify_manual_push():
    """
    Verification popup for manual git push commands with commit message editing.
    Returns 0 if approved, 1 if rejected.
    """
    # Get the repository directory
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
    
    root = tk.Tk()
    root.title("Git Push")
    root.configure(bg=colors['bg'])
    
    # Center the window - LARGER HEIGHT for bigger buttons
    window_width = 540
    window_height = 240
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Apply dark title bar AFTER window setup
    if theme == "dark":
        apply_dark_title_bar(root)
    
    # Main container
    container = tk.Frame(root, bg=colors['surface'], relief=tk.FLAT, bd=0)
    container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
    
    # Header with icon
    header_frame = tk.Frame(container, bg=colors['surface'])
    header_frame.pack(pady=(25, 8))
    
    header = tk.Label(
        header_frame,
        text="📤  Manual Push Detected",
        font=("Segoe UI", 14, "bold"),
        bg=colors['surface'],
        fg=colors['text']
    )
    header.pack()
    
    # Subheader
    subheader = tk.Label(
        container,
        text="Review and edit the commit message before pushing:",
        font=("Segoe UI", 10),
        bg=colors['surface'],
        fg=colors['subtext']
    )
    subheader.pack(pady=(0, 15))
    
    # Entry field with subtle border
    entry_frame = tk.Frame(container, bg=colors['border'], relief=tk.FLAT, bd=0)
    entry_frame.pack(padx=40, pady=(0, 20), fill=tk.X)
    
    entry = tk.Entry(
        entry_frame,
        font=("Segoe UI", 11),
        bg=colors['surface'],
        fg=colors['text'],
        relief=tk.FLAT,
        insertbackground=colors['accent'],
        bd=0,
        highlightthickness=0
    )
    entry.pack(padx=2, pady=2, fill=tk.X, ipady=10)
    entry.insert(0, original_message)
    entry.focus_set()
    entry.select_range(0, tk.END)
    
    def on_approve():
        result_dict['approved'] = True
        result_dict['message'] = entry.get()
        root.destroy()
        
    def on_reject():
        result_dict['approved'] = False
        root.destroy()
    
    # Button frame
    btn_frame = tk.Frame(container, bg=colors['surface'])
    btn_frame.pack(pady=(5, 25))
    
    # Create buttons with explicit width and height
    def create_button(parent, text, command, bg, hover_bg):
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 11, "bold"),
            bg=bg,
            fg="white",
            activebackground=hover_bg,
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            bd=0,
            width=12,
            height=2
        )
        
        # Bind hover events
        btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg))
        
        return btn
    
    # Push button
    push_btn = create_button(btn_frame, "Push", on_approve, colors['accent'], colors['accent_hover'])
    push_btn.pack(side=tk.LEFT, padx=8)
    
    # Cancel button
    cancel_btn = create_button(btn_frame, "Cancel", on_reject, colors['cancel'], colors['cancel_hover'])
    cancel_btn.pack(side=tk.LEFT, padx=8)
    
    # Bind keys
    root.bind('<Return>', lambda e: on_approve())
    root.bind('<Escape>', lambda e: on_reject())
    
    root.protocol("WM_DELETE_WINDOW", on_reject)
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
