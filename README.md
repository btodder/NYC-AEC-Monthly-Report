# NYC AEC Monthly Report

A static news site summarizing the New York City architecture, engineering, and construction (AEC) market each month. A Python script turns a plain-text report into site content, updates the ABI trend chart, and publishes the result to GitHub Pages.

**Live:** https://btodder.github.io/NYC-AEC-Monthly-Report/

## Report sections

Each monthly report has four sections:

- **Filings & Permits**: new-building filings, proposed units, and completions
- **ABI (Northeast)**: the AIA Architecture Billings Index, tracked in `abi_history.json` and charted on the site. The script calculates the trend line itself.
- **Rates & Incentives**: financing rates and incentive programs
- **Key Takeaways**

## Report format

The first line of the file becomes the report title. Sections can use either bracket tags or bold headings:

```text
NYC AEC Monthly Activity Report — Feb 2026

[FILINGS]            (or **Filings & Permits**)
- bullet or paragraph text

[ABI]                (or **ABI (Northeast)**)
- ABI Northeast — 45.1

[RATES]              (or **Rates & Incentives**)
...

[TAKEAWAYS]          (or **Key Takeaways**)
...
```

Lines starting with `-` or `•` become bullet lists. A missing section shows "No data provided." Past reports in `archive/` are working examples.

## Publishing a new report

1. Create an `incoming_reports/` folder if it doesn't exist, and put the new `.txt` report in it.
2. Run:
   ```sh
   python update_site.py
   ```
3. The script:
   - picks the newest `.txt` in `incoming_reports/` and parses it
   - updates the matching sections in `index.html` and the "Last Updated" date
   - adds the ABI value to `abi_history.json` and redraws the chart with the last four readings and month-over-month change
   - opens an approval dialog where you can edit the commit message, then commits and pushes. **Cancel** aborts without pushing.
   - moves the report to `archive/`, but only if the push succeeded

`verify_push.py` shows the same approval dialog for a manual `git push`. It can be wired up as a pre-push hook.

## Project structure

```
index.html, style.css, abi_chart.css   The site
update_site.py                         Parse → update HTML → commit/push → archive
gui_utils.py                           Approval dialog (customtkinter, follows the Windows light/dark theme)
verify_push.py                         Push confirmation dialog
abi_history.json                       ABI readings by month
archive/                               Processed reports
```

## Requirements

- Python 3.10+
- `customtkinter` (`pip install customtkinter`) for the approval dialog. The dialog is tuned for Windows (DPI scaling, theme detection).
- Git with push access to this repo

> **Note:** If `tkinter`/`customtkinter` can't be imported (headless machines, Codespaces), the approval step **auto-approves** and pushes without asking.
