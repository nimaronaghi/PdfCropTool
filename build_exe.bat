@echo off
echo Building PDF Figure Extractor executable...
echo.

REM Install PyInstaller if not already installed
pip install pyinstaller

REM Remove old build files
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del "*.spec"

REM Build the executable
pyinstaller --onefile --windowed --name="PDF-Figure-Extractor" --icon=app_icon.ico main.py

REM Check if build was successful
if exist "dist\PDF-Figure-Extractor.exe" (
    echo.
    echo Build successful! 
    echo Executable created: dist\PDF-Figure-Extractor.exe
    echo.
    echo You can now copy the .exe file to any Windows computer and run it.
    pause
) else (
    echo.
    echo Build failed! Please check the error messages above.
    pause
)