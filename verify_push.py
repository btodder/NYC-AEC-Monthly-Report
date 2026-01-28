import tkinter as tk
import sys
import subprocess
import os
import ctypes

# Enable DPI awareness for crisp rendering on high-res displays
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()  # Fallback
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
            'text': '#ffffff',
            'subtext': '#b4b4b4',
            'accent': '#0078d4',
            'accent_hover': '#1a86d9',
            'cancel': '#484848',
            'cancel_hover': '#5a5a5a',
            'border': '#3f3f3f'
        }
    else:
        return {
            'bg': '#f0f0f0',
            'surface': '#ffffff',
            'text': '#1f1f1f',
            'subtext': '#5f5f5f',
            'accent': '#0067c0',
            'accent_hover': '#005a9e',
            'cancel': '#6e6e6e',
            'cancel_hover': '#5a5a5a',
            'border': '#d0d0d0'
        }

def apply_dark_title_bar(root):
    """Apply dark title bar on Windows 10/11."""
    try:
        root.update()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
        root.withdraw()
        root.deiconify()
    except:
        pass

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
    
    root = tk.Tk()
    root.title("Git Push Detected, Review Commit Message:")  # Title bar text
    root.configure(bg=colors['bg'])
    
    # Fixed window size - not resizable
    window_width = 800
    window_height = 495
    root.resizable(False, False)
    
    # Center the window
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Apply dark title bar
    if theme == "dark":
        apply_dark_title_bar(root)
    
    # Main container
    container = tk.Frame(root, bg=colors['surface'], relief=tk.FLAT, bd=0)
    container.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
    
    # Entry field with border
    entry_frame = tk.Frame(container, bg=colors['border'], relief=tk.FLAT, bd=0)
    entry_frame.pack(padx=30, pady=(25, 0), fill=tk.X)
    
    entry = tk.Entry(
        entry_frame,
        font=("Segoe UI", 10),
        bg=colors['surface'],
        fg=colors['text'],
        relief=tk.FLAT,
        insertbackground=colors['accent'],
        bd=0,
        highlightthickness=0
    )
    entry.pack(padx=1, pady=1, fill=tk.X, ipady=8)
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
    
    # Button frame - same padding as entry field
    btn_frame = tk.Frame(container, bg=colors['surface'])
    btn_frame.pack(padx=30, pady=(15, 25), fill=tk.X)
    
    # Buttons that fill the frame width equally
    confirm_btn = tk.Button(
        btn_frame,
        text="Confirm",
        command=on_confirm,
        font=("Segoe UI", 10, "bold"),
        bg=colors['accent'],
        fg="white",
        activebackground=colors['accent_hover'],
        activeforeground="white",
        relief=tk.FLAT,
        cursor="hand2",
        bd=0,
        pady=10
    )
    confirm_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
    confirm_btn.bind("<Enter>", lambda e: confirm_btn.config(bg=colors['accent_hover']))
    confirm_btn.bind("<Leave>", lambda e: confirm_btn.config(bg=colors['accent']))
    
    cancel_btn = tk.Button(
        btn_frame,
        text="Cancel",
        command=on_cancel,
        font=("Segoe UI", 10, "bold"),
        bg=colors['cancel'],
        fg="white",
        activebackground=colors['cancel_hover'],
        activeforeground="white",
        relief=tk.FLAT,
        cursor="hand2",
        bd=0,
        pady=10
    )
    cancel_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
    cancel_btn.bind("<Enter>", lambda e: cancel_btn.config(bg=colors['cancel_hover']))
    cancel_btn.bind("<Leave>", lambda e: cancel_btn.config(bg=colors['cancel']))
    
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
