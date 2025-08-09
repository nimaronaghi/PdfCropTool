#!/bin/bash
echo "Building PDF Figure Extractor executable..."
echo

# Install PyInstaller if not already installed
pip install pyinstaller

# Remove old build files
rm -rf dist build *.spec

# Build the executable
pyinstaller --onefile --windowed --name="PDF-Figure-Extractor" main.py

# Check if build was successful
if [ -f "dist/PDF-Figure-Extractor" ]; then
    echo
    echo "Build successful!"
    echo "Executable created: dist/PDF-Figure-Extractor"
    echo
    echo "You can now copy the executable to any Linux computer and run it."
else
    echo
    echo "Build failed! Please check the error messages above."
fi