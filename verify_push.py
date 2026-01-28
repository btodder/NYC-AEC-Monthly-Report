import tkinter as tk
import sys
import subprocess
import os

def verify_manual_push():
    """
    Verification popup for manual git push commands with commit message editing.
    Returns 0 if approved, 1 if rejected.
    """
    # Get the repository directory (verify_push.py is in the repo root)
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
    
    root = tk.Tk()
    root.title("Git Push")
    
    # Windows 11 color scheme
    BG_COLOR = "#f3f3f3"
    SURFACE_COLOR = "#ffffff"
    TEXT_COLOR = "#1f1f1f"
    ACCENT_COLOR = "#0067c0"
    BUTTON_HOVER = "#005a9e"
    CANCEL_COLOR = "#8a8a8a"
    CANCEL_HOVER = "#737373"
    
    root.configure(bg=BG_COLOR)
    
    # Center the window
    window_width = 500
    window_height = 180
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Main container with padding
    container = tk.Frame(root, bg=SURFACE_COLOR, relief=tk.FLAT)
    container.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
    
    # Header
    header = tk.Label(
        container,
        text="Manual Push Detected",
        font=("Segoe UI", 12, "bold"),
        bg=SURFACE_COLOR,
        fg=TEXT_COLOR
    )
    header.pack(pady=(20, 5))
    
    # Subheader
    subheader = tk.Label(
        container,
        text="Review and edit the commit message before pushing:",
        font=("Segoe UI", 9),
        bg=SURFACE_COLOR,
        fg="#5f5f5f"
    )
    subheader.pack(pady=(0, 15))
    
    # Entry field with border
    entry_frame = tk.Frame(container, bg="#e5e5e5", relief=tk.FLAT)
    entry_frame.pack(padx=30, pady=(0, 20), fill=tk.X)
    
    entry = tk.Entry(
        entry_frame,
        font=("Segoe UI", 10),
        bg=SURFACE_COLOR,
        fg=TEXT_COLOR,
        relief=tk.FLAT,
        insertbackground=TEXT_COLOR,
        bd=0
    )
    entry.pack(padx=1, pady=1, fill=tk.X, ipady=6)
    entry.insert(0, original_message)
    entry.focus_set()
    
    def on_approve():
        result_dict['approved'] = True
        result_dict['message'] = entry.get()
        root.destroy()
        
    def on_reject():
        result_dict['approved'] = False
        root.destroy()
    
    # Button frame
    btn_frame = tk.Frame(container, bg=SURFACE_COLOR)
    btn_frame.pack(pady=(0, 20))
    
    # Push button
    push_btn = tk.Button(
        btn_frame,
        text="Push",
        command=on_approve,
        font=("Segoe UI", 9),
        bg=ACCENT_COLOR,
        fg="white",
        activebackground=BUTTON_HOVER,
        activeforeground="white",
        relief=tk.FLAT,
        cursor="hand2",
        bd=0,
        padx=30,
        pady=8
    )
    push_btn.pack(side=tk.LEFT, padx=5)
    
    # Cancel button
    cancel_btn = tk.Button(
        btn_frame,
        text="Cancel",
        command=on_reject,
        font=("Segoe UI", 9),
        bg=CANCEL_COLOR,
        fg="white",
        activebackground=CANCEL_HOVER,
        activeforeground="white",
        relief=tk.FLAT,
        cursor="hand2",
        bd=0,
        padx=30,
        pady=8
    )
    cancel_btn.pack(side=tk.LEFT, padx=5)
    
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
