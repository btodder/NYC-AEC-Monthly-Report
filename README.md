# NYC AEC Monthly Report

A news site that auto-updates from text reports.
https://btodder.github.io/NYC-AEC-Monthly-Report/

## Project Structure

- `index.html` & `style.css`: The frontend website.
- `update_site.py`: The automation script.
- `incoming_reports/`: Drop new `.txt` reports here.
- `archive/`: Processed reports are moved here automatically.

## formatting

Reports should follow this format:

```text
[FILINGS]
... content ...

[ABI]
... content ...

[RATES]
... content ...

[TAKEAWAYS]
... content ...
```

## How to Update

1. Place your text report (e.g., `feb_report.txt`) into the `incoming_reports/` folder.
2. Run the update script:
   ```bash
   python update_site.py
   ```
3. The script will:
   - Parse the text file.
   - Update `index.html` with the new content.
   - Update the "Last Updated" timestamp.
   - Commit and Push changes to GitHub.
   - Move the text file to `archive/`.

## Requirements

- Python 3.x
- Git (configured with credentials)
