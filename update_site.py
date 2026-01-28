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
    
    # Simple parsing logic
    # Expected format:
    # [FILINGS]
    # content...
    # [RATES]
    # content...
    # [TAKEAWAYS]
    # content...

    # Updated regex to handle [ABI] section
    # Order: FILINGS -> ABI -> RATES -> TAKEAWAYS
    filings_match = re.search(r'\[FILINGS\]\s*(.*?)\s*(?=\[ABI\]|\[RATES\]|\[TAKEAWAYS\]|$)', content, re.DOTALL | re.IGNORECASE)
    abi_match = re.search(r'\[ABI\]\s*(.*?)\s*(?=\[FILINGS\]|\[RATES\]|\[TAKEAWAYS\]|$)', content, re.DOTALL | re.IGNORECASE)
    rates_match = re.search(r'\[RATES\]\s*(.*?)\s*(?=\[FILINGS\]|\[ABI\]|\[TAKEAWAYS\]|$)', content, re.DOTALL | re.IGNORECASE)
    takeaways_match = re.search(r'\[TAKEAWAYS\]\s*(.*?)\s*(?=\[FILINGS\]|\[ABI\]|\[RATES\]|$)', content, re.DOTALL | re.IGNORECASE)

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

def update_html(sections):
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        html = f.read()

    # Function to replace content inside a div with specific ID
    def replace_section(html_content, section_id, new_text):
        formatted_html = format_content_to_html(new_text)
        pattern = f'(<div id="{section_id}"[^>]*>)(.*?)(</div>)'
        replacement = f'\\1{formatted_html}\\3'
        return re.sub(pattern, replacement, html_content, flags=re.DOTALL)

    html = replace_section(html, 'filings-content', sections['filings'])
    html = replace_section(html, 'abi-content', sections['abi'])
    html = replace_section(html, 'rates-content', sections['rates'])
    html = replace_section(html, 'takeaways-content', sections['takeaways'])

    # Update Timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = re.sub(r'(<div id="last-updated">).*?(</div>)', f'\\1Last Updated: {timestamp}\\2', html, flags=re.DOTALL)

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
        update_html(sections)
        
        # Git operations
        git_deploy()
        
        # Archive file
        filename = os.path.basename(latest_file)
        shutil.move(latest_file, os.path.join(ARCHIVE_DIR, filename))
        print(f"Moved {filename} to archive/.")
        
    except Exception as e:
        print(f"Error processing file: {e}")

if __name__ == "__main__":
    main()
