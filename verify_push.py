import tkinter as tk
import sys

def verify_manual_push():
    """
    Simple binary verification popup for manual git push commands.
    Returns 0 if approved, 1 if rejected.
    """
    result = {'approved': False}
    
    root = tk.Tk()
    root.title("Manual Push Detected")
    
    # Center the window
    window_width = 350
    window_height = 120
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    tk.Label(root, text="Manual Push Detected", font=("Arial", 12, "bold")).pack(pady=(15, 5))
    tk.Label(root, text="Allow this push to proceed?", font=("Arial", 10)).pack(pady=5)
    
    def on_approve():
        result['approved'] = True
        root.destroy()
        
    def on_reject():
        result['approved'] = False
        root.destroy()
        
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=15)
    
    tk.Button(btn_frame, text="Yes", command=on_approve, bg="#4caf50", fg="white", width=10).pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text="No", command=on_reject, bg="#f44336", fg="white", width=10).pack(side=tk.LEFT, padx=10)
    
    # Bind keys
    root.bind('<Return>', lambda e: on_approve())
    root.bind('<Escape>', lambda e: on_reject())
    
    root.protocol("WM_DELETE_WINDOW", on_reject)
    root.mainloop()
    
    return 0 if result['approved'] else 1

if __name__ == "__main__":
    sys.exit(verify_manual_push())
