import os
import glob
import re
import shutil
import subprocess
from datetime import datetime

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INCOMING_DIR = os.path.join(BASE_DIR, 'incoming_reports')
ARCHIVE_DIR = os.path.join(BASE_DIR, 'archive')
INDEX_FILE = os.path.join(BASE_DIR, 'index.html')

def get_latest_report():
    files = glob.glob(os.path.join(INCOMING_DIR, '*.txt'))
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def parse_report(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = {}
    
    # Headers regex patterns
    # Support both [HEADER] and **Header** formats
    h_filings = r'(?:\[FILINGS\]|\*\*Filings & Permits\*\*)'
    h_abi = r'(?:\[ABI\]|\*\*ABI \(Northeast\)\*\*)'
    h_rates = r'(?:\[RATES\]|\*\*Rates & Incentives\*\*)'
    h_takeaways = r'(?:\[TAKEAWAYS\]|\*\*Key Takeaways\*\*)'
    
    # Lookahead for any header or end of string
    any_header = f'(?:{h_filings}|{h_abi}|{h_rates}|{h_takeaways}|$)'

    filings_match = re.search(rf'{h_filings}\s*(.*?)\s*(?={any_header})', content, re.DOTALL | re.IGNORECASE)
    abi_match = re.search(rf'{h_abi}\s*(.*?)\s*(?={any_header})', content, re.DOTALL | re.IGNORECASE)
    rates_match = re.search(rf'{h_rates}\s*(.*?)\s*(?={any_header})', content, re.DOTALL | re.IGNORECASE)
    takeaways_match = re.search(rf'{h_takeaways}\s*(.*?)\s*(?={any_header})', content, re.DOTALL | re.IGNORECASE)

    sections['filings'] = filings_match.group(1).strip() if filings_match else "No data provided."
    sections['abi'] = abi_match.group(1).strip() if abi_match else "No data provided."
    sections['rates'] = rates_match.group(1).strip() if rates_match else "No data provided."
    sections['takeaways'] = takeaways_match.group(1).strip() if takeaways_match else "No data provided."
    
    return sections

def format_content_to_html(text):
    """Converts raw text into HTML, turning bullet points into lists."""
    lines = text.split('\n')
    html_output = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        # Check if line is a bullet point
        if stripped.startswith('•') or stripped.startswith('-') or stripped.startswith('*'):
            if not in_list:
                html_output.append('<ul>')
                in_list = True
            # Remove bullet char and wrap in li
            content = re.sub(r'^[•\-\*]\s*', '', stripped)
            html_output.append(f'<li>{content}</li>')
        else:
            if in_list:
                html_output.append('</ul>')
                in_list = False
            html_output.append(f'<p>{stripped}</p>')
    
    if in_list:
        html_output.append('</ul>')
        
    return "".join(html_output)

# ABI Chart Logic
import json

ABI_HISTORY_FILE = os.path.join(BASE_DIR, 'abi_history.json')

def update_abi_history(report_date_str, abi_section_text):
    # Extract ABI value from text like "ABI Northeast - 45.1"
    match = re.search(r'ABI Northeast\s*[—\-]\s*(\d+\.?\d*)', abi_section_text, re.IGNORECASE)
    if not match:
        print("Could not extract ABI value.")
        return load_abi_history()

    new_value = float(match.group(1))
    
    # Load existing history
    history = load_abi_history()
    
    # Append new entry
    # Append new entry
    # Extract short month and year: "JAN<br>2026" -> "JAN", "2026"
    parts = report_date_str.split('<br>')
    month_label = parts[0]
    year_label = parts[1] if len(parts) > 1 else str(datetime.now().year)
    
    # Check if duplicate date (matches both month and year)
    if history:
        last = history[-1]
        if last.get('month') == month_label and last.get('year') == year_label:
            return history # Don't duplicate

    history.append({
        'month': month_label,
        'year': year_label,
        'value': new_value
    })
    
    # Save full history (Long-term database)
    with open(ABI_HISTORY_FILE, 'w') as f:
        json.dump(history, f)
        
    return history

def load_abi_history():
    if not os.path.exists(ABI_HISTORY_FILE):
        return []
    with open(ABI_HISTORY_FILE, 'r') as f:
        return json.load(f)

def generate_abi_chart_html(history):
    if not history:
        return ""

    # Chart Configuration
    min_y = 40
    max_y = 60
    range_y = max_y - min_y
    baseline_y = 50
    # Calculate baseline position percentage (from bottom)
    baseline_pct = ((baseline_y - min_y) / range_y) * 100

    html_parts = ['<div class="abi-chart-container">']
    html_parts.append(f'<div class="chart-baseline" style="bottom: {baseline_pct}%;"></div>')

    for entry in history:
        val = entry['value']
        # Use 'month' for the chart label,fallback to 'date' for backward compatibility if needed (though we migrated)
        label = entry.get('month', entry.get('date', ''))
        
        # Calculate height and position
        is_positive = val >= baseline_y
        
        # Distance from baseline
        diff = abs(val - baseline_y)
        height_pct = (diff / range_y) * 100
        
        # If positive, bottom is baseline. If negative, top is baseline (bottom is baseline - height)
        # Actually easier: use bottom position relative to scale
        
        if is_positive:
            bottom_pos = baseline_pct
            bar_class = "hatch-green"
            val_pos_style = f"bottom: {height_pct + 5}%;"
        else:
            bottom_pos = baseline_pct - height_pct
            bar_class = "hatch-red"
            val_pos_style = f"top: {height_pct + 5}%;" # Inside/below bar? 
            # For negative bars growing down, let's position:
            # bottom = (val - min_y) / range * 100
            
        # Simplified positioning:
        bar_bottom_pct = ((val - min_y) / range_y) * 100
        bar_height_pct = height_pct
        
        # Correct logic for absolute bars:
        # If val > 50: bottom = 50%, height = (val-50)%
        # If val < 50: top = 50% (from bottom), or bottom = val%, height = (50-val)%
        
        if is_positive:
            style = f"bottom: {baseline_pct}%; height: {height_pct}%;"
            val_html = f'<div class="chart-value" style="bottom: 100%; margin-bottom: 5px;">{val}</div>'
        else:
             # For negative, bar starts at val and goes up to baseline
             style = f"bottom: {((val - min_y)/range_y)*100}%; height: {height_pct}%;"
             val_html = f'<div class="chart-value" style="top: 100%; margin-top: 5px;">{val}</div>'

        col_html = f'''
        <div class="chart-column">
            <div class="chart-bar {bar_class}" style="{style}">
                {val_html}
            </div>
            <div class="chart-label">{label}</div>
        </div>
        '''
        html_parts.append(col_html)

    html_parts.append('</div>')
    return "".join(html_parts)

def update_html(sections, report_date_str=None):
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        html = f.read()

    # ABI Chart Injection
    abi_history = []
    if report_date_str:
        abi_history = update_abi_history(report_date_str, sections['abi'])
    
    # Visualize only the last 4 months from the full history
    chart_history_window = abi_history[-4:] if len(abi_history) > 4 else abi_history
    chart_html = generate_abi_chart_html(chart_history_window)
    
    # Clean ABI text - Remove the specific data line that is now in the chart
    # Matches any line containing "ABI Northeast" and a number
    cleaned_abi_text = re.sub(r'(?m)^.*?ABI Northeast.*?\d+.*(?:\r?\n)?', '', sections['abi'], flags=re.IGNORECASE)
    
    # Remove existing manual Trend line to replace with verified calculation
    cleaned_abi_text = re.sub(r'(?m)^.*?Trend.*(?:\r?\n)?', '', cleaned_abi_text, flags=re.IGNORECASE)
    
    # Generate Verified Trend Bullet
    trend_bullet = ""
    if len(abi_history) >= 2:
        curr = abi_history[-1]
        prev = abi_history[-2]
        diff = curr['value'] - prev['value']
        
        direction = "STABLE"
        if diff > 0.05: direction = "UP"
        elif diff < -0.05: direction = "DOWN"
        
        trend_bullet = f"Trend — {direction} ({diff:+.1f} pts from {prev['month']} {prev['year']})"
        
        # Prepend verified trend to text
        cleaned_abi_text = f"• {trend_bullet}\n" + cleaned_abi_text.strip()
    
    # Prepend chart to ABI content if it exists
    full_abi_content = chart_html + format_content_to_html(cleaned_abi_text)
    
    # Construct Full ABI Section HTML
    abi_section_html = f'''
        <!-- Section 2: ABI (Northeast) -->
        <section class="abi">
            <h2>02. ABI (Northeast)</h2>
            <div id="abi-content" class="content-block">{full_abi_content}</div>
        </section>
        '''

    # Function to replace content inside a div with specific ID
    def replace_section(html_content, section_id, new_html):
        pattern = f'(<div id="{section_id}"[^>]*>)(.*?)(</div>)'
        replacement = f'\\1{new_html}\\3'
        return re.sub(pattern, replacement, html_content, flags=re.DOTALL)

    html = replace_section(html, 'filings-content', format_content_to_html(sections['filings']))
    
    # Robust Replacement for ABI Section
    # Matches everything from <!-- Section 2: ... --> to just before <!-- Section 3: ... -->
    # This ensures we replace the ENTIRE block structure, avoiding nested div issues
    abi_pattern = r'(<!-- Section 2: ABI \(Northeast\) -->.*?)(?=<!-- Section 3:)'
    html = re.sub(abi_pattern, abi_section_html.strip() + '\n\n        ', html, flags=re.DOTALL)
    
    html = replace_section(html, 'rates-content', format_content_to_html(sections['rates']))
    html = replace_section(html, 'takeaways-content', format_content_to_html(sections['takeaways']))
    
    html = replace_section(html, 'rates-content', format_content_to_html(sections['rates']))
    html = replace_section(html, 'takeaways-content', format_content_to_html(sections['takeaways']))

    # Update Timestamp
    timestamp = datetime.now().strftime("%m-%d-%y")
    html = re.sub(r'(<div id="last-updated">).*?(</div>)', f'\\1Last Updated {timestamp}\\2', html, flags=re.DOTALL)

    # Update Report Month if provided
    if report_date_str:
         html = re.sub(r'(<div id="report-month">).*?(</div>)', f'\\1{report_date_str}\\2', html, flags=re.DOTALL)

    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Updated index.html with new content at {timestamp}")

# GUI Imports and Logic - Wrapped in Try/Except for headless environments (Streamlit Cloud)
HAS_GUI = False
try:
    import tkinter as tk
    from tkinter import messagebox
    HAS_GUI = True
except (ImportError, RuntimeError):
    # RuntimeError can happen in headless Linux if DISPLAY is not set
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

def get_user_approval(default_message):
    """
    Opens a Tkinter popup to get user approval and optional edit of the commit message.
    Automatically approves if GUI is not available (e.g. Streamlit Cloud).
    """
    if not HAS_GUI:
        print("Headless environment detected. Auto-approving deployment.")
        return True, default_message

    result = {'approved': False, 'message': None}
    
    # Detect theme and get colors
    theme = get_windows_theme()
    colors = get_theme_colors(theme)
    
    root = tk.Tk()
    root.title("Deploy Report")
    root.configure(bg=colors['bg'])
    
    # Center the window
    window_width = 520
    window_height = 200
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Apply dark title bar on Windows 10/11
    if theme == "dark":
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
            value = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
        except:
            pass
    
    # Main container
    container = tk.Frame(root, bg=colors['surface'], relief=tk.FLAT, bd=0)
    container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
    
    # Header with icon
    header_frame = tk.Frame(container, bg=colors['surface'])
    header_frame.pack(pady=(25, 5))
    
    header = tk.Label(
        header_frame,
        text="🚀  Confirm Deployment",
        font=("Segoe UI", 13, "bold"),
        bg=colors['surface'],
        fg=colors['text']
    )
    header.pack()
    
    # Subheader
    subheader = tk.Label(
        container,
        text="Review and edit the commit message before deploying:",
        font=("Segoe UI", 9),
        bg=colors['surface'],
        fg=colors['subtext']
    )
    subheader.pack(pady=(0, 20))
    
    # Entry field with subtle border
    entry_frame = tk.Frame(container, bg=colors['border'], relief=tk.FLAT, bd=0)
    entry_frame.pack(padx=35, pady=(0, 25), fill=tk.X)
    
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
    entry.insert(0, default_message)
    entry.focus_set()
    entry.select_range(0, tk.END)
    
    def on_confirm():
        result['approved'] = True
        result['message'] = entry.get()
        root.destroy()
        
    def on_cancel():
        result['approved'] = False
        root.destroy()
    
    # Button frame
    btn_frame = tk.Frame(container, bg=colors['surface'])
    btn_frame.pack(pady=(0, 25))
    
    # Create buttons with hover effect and MUCH larger padding
    def create_button(parent, text, command, bg, hover_bg):
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 10, "bold"),
            bg=bg,
            fg="white",
            activebackground=hover_bg,
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            bd=0,
            padx=50,
            pady=12
        )
        
        # Bind hover events
        btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg))
        
        return btn
    
    # Deploy button
    deploy_btn = create_button(btn_frame, "Deploy", on_confirm, colors['accent'], colors['accent_hover'])
    deploy_btn.pack(side=tk.LEFT, padx=6)
    
    # Cancel button
    cancel_btn = create_button(btn_frame, "Cancel", on_cancel, colors['cancel'], colors['cancel_hover'])
    cancel_btn.pack(side=tk.LEFT, padx=6)
    
    # Bind Enter and Escape keys
    root.bind('<Return>', lambda e: on_confirm())
    root.bind('<Escape>', lambda e: on_cancel())
    
    root.protocol("WM_DELETE_WINDOW", on_cancel)
    root.mainloop()
    
    return result['approved'], result['message']

def git_deploy():
    try:
        print("Starting Git deployment...")
        
        # Human Approval Step
        default_msg = "Weekly Update via Automation Script"
        approved, final_msg = get_user_approval(default_msg)
        
        if not approved:
            print("Deployment ABORTED by user.")
            print("File preserved in incoming_reports for later processing.")
            return False # Signal abort
            
        subprocess.run(["git", "add", "."], cwd=BASE_DIR, check=True)
        subprocess.run(["git", "commit", "-m", final_msg], cwd=BASE_DIR, check=True)
        
        # Set bypass flag to avoid double popup from pre-push hook
        env = os.environ.copy()
        env['BYPASS_HOOK'] = '1'
        subprocess.run(["git", "push"], cwd=BASE_DIR, check=True, env=env)
        print("Git push successful.")
        return True # Signal success
        
    except Exception as e:
        print(f"Git operation failed: {e}")
        # Even if git fails, we might want to continue or stop. 
        # Typically if git fails we might NOT want to archive the file? 
        # Let's assume we proceed to archive only if success or handled elsewhere.
        # But per original logic, it continued. Let's return False to prevent archiving if that was the intent,
        # but to match previous behavior (continue with archive), we can return True or handle differently.
        # The user said "If Cancel, abort immediately and NOT push or archive".
        return False


def main():
    print("Checking for new reports...")
    latest_file = get_latest_report()
    
    if not latest_file:
        print("No new reports found in incoming_reports/.")
        return

    print(f"Processing report: {latest_file}")
    try:
        sections = parse_report(latest_file)
        
        # Extract date from filename
        basename = os.path.basename(latest_file)
        report_date_str = None
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', basename)
        if date_match:
            try:
                dt = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                report_date_str = f"{dt.strftime('%b').upper()}<br>{dt.strftime('%Y')}"
            except ValueError:
                pass

        update_html(sections, report_date_str)
        
        # Git operations
        if git_deploy():
            # Archive file ONLY if deployment succeeded
            filename = os.path.basename(latest_file)
            shutil.move(latest_file, os.path.join(ARCHIVE_DIR, filename))
            print(f"Moved {filename} to archive/.")
        else:
            print("Skipping archive step due to deployment abort/failure.")
        
    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
