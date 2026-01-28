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
    # Extract short month for label: "JAN<br>2026" -> "JAN"
    month_label = report_date_str.split('<br>')[0] 
    
    # Check if duplicate date
    if history and history[-1]['date'] == month_label:
        return history # Don't duplicate

    history.append({
        'date': month_label,
        'value': new_value
    })
    
    # Keep last 4
    if len(history) > 4:
        history = history[-4:]
        
    # Save
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
        label = entry['date']
        
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
    
    chart_html = generate_abi_chart_html(abi_history)
    
    # Clean ABI text - Remove the specific data line that is now in the chart
    # Matches any line containing "ABI Northeast" and a number
    cleaned_abi_text = re.sub(r'(?m)^.*?ABI Northeast.*?\d+.*(?:\r?\n)?', '', sections['abi'], flags=re.IGNORECASE)
    
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

def git_deploy():
    try:
        print("Starting Git deployment...")
        subprocess.run(["git", "add", "."], cwd=BASE_DIR, check=True)
        subprocess.run(["git", "commit", "-m", "Weekly Update via Automation Script"], cwd=BASE_DIR, check=True)
        subprocess.run(["git", "push"], cwd=BASE_DIR, check=True)
        print("Git push successful.")
    except Exception as e:
        print(f"Git operation failed: {e}")
        print("Continuing with archive step...")

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
        git_deploy()
        
        # Archive file
        filename = os.path.basename(latest_file)
        shutil.move(latest_file, os.path.join(ARCHIVE_DIR, filename))
        print(f"Moved {filename} to archive/.")
        
    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
