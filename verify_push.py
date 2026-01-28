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
    root.title("Manual Push Detected")
    
    # Center the window
    window_width = 400
    window_height = 150
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    tk.Label(root, text="Commit Message:", font=("Arial", 10)).pack(pady=(10, 5))
    
    entry = tk.Entry(root, width=50)
    entry.insert(0, original_message)
    entry.pack(pady=5)
    entry.focus_set()
    
    def on_approve():
        result_dict['approved'] = True
        result_dict['message'] = entry.get()
        root.destroy()
        
    def on_reject():
        result_dict['approved'] = False
        root.destroy()
        
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)
    
    tk.Button(btn_frame, text="Push", command=on_approve, bg="#4caf50", fg="white", width=10).pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text="Cancel", command=on_reject, bg="#f44336", fg="white", width=10).pack(side=tk.LEFT, padx=10)
    
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
