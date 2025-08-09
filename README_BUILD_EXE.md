# Building PDF Figure Extractor as .exe

## Quick Instructions

### For Windows Users:
1. **Download all Python files** from this project to your Windows computer
2. **Install Python** (if not already installed): https://python.org
3. **Open Command Prompt** in the project folder
4. **Run the build script**: `build_exe.bat`
5. **Find your .exe** in the `dist` folder

### Manual Build (Windows):
```cmd
pip install pyinstaller
pyinstaller --onefile --windowed --name="PDF-Figure-Extractor" main.py
```

### Manual Build (Alternative):
```cmd
pip install auto-py-to-exe
auto-py-to-exe
```
Then use the GUI to select `main.py` and configure options.

## What You'll Get:
- **Single .exe file** (~50-100MB)
- **No Python installation required** on target computers
- **Runs on any Windows computer** (Windows 7/10/11)
- **All features included** (PDF loading, cropping, export)

## Distribution:
Once built, you can copy the .exe file to any Windows computer and double-click to run it - no installation needed!

## Troubleshooting:
- If build fails, try running: `pip install --upgrade pyinstaller`
- For antivirus warnings, the .exe is safe - it's just a packaged Python app
- Large file size is normal - it includes the Python runtime and all libraries

## Alternative: Portable Python Setup
If .exe build doesn't work, you can create a portable setup:
1. Install Python and dependencies on a USB drive
2. Create a batch file that runs: `python main.py`
3. Share the entire folder with the batch file as the launcher