# PDF Figure Extractor

A powerful desktop application for extracting high-quality figures and images from PDF documents with precision cropping and intelligent naming features.

## Features

- **Interactive PDF Viewer**: Navigate through PDF pages with intuitive controls
- **Precision Cropping**: Select and extract specific regions from PDF pages
- **Adaptive Naming System**: Automatically learns your naming patterns from the first renamed crop
- **High-Quality Output**: Extracts images at 300+ DPI for publication-ready quality
- **Flexible Export Options**: Save individual crops or batch export all selections
- **Multiple View Modes**: Single-page or continuous scrolling view
- **Auto-Highlighting**: Optionally highlight visualization keywords (figure, plot, diagram, etc.)
- **Smart Navigation**: Keyboard shortcuts and direct page jumping

## Quick Start

### Prerequisites

- Python 3.10 or later
- Windows, macOS, or Linux

### Installation & Running

1. **Download the project files** to your computer
2. **Install dependencies**:
   ```bash
   pip install fitz pillow pyinstaller pymupdf
   ```
3. **Run the application**:
   ```bash
   python main.py
   ```

That's it! The application window will open ready to use.

## How to Use

### Loading a PDF
- **File → Open PDF** or press `Ctrl+O`
- **File → Load from URL** or press `Ctrl+U` (for Google Drive links, etc.)

### Creating Crop Selections
1. Navigate to the page containing the figure you want
2. **Click and drag** on the PDF to select the area
3. The crop appears in the "Crop Selections" list with an automatic name
4. Repeat for additional crops

### Adaptive Naming (Key Feature)
1. Create your first crop (gets name like "document_Q0001")
2. **Rename it** to your preferred format (e.g., "study_fig_001" or "nima_Q0001")
3. **All future crops automatically follow your pattern!**
   - If you renamed to "study_fig_001", next crops become "study_fig_002", "study_fig_003", etc.
   - The system learns prefixes, suffixes, and number formats

### Exporting Images
- **Individual**: Select a crop → "Save Individual" → Choose location
- **Batch Export**: "Select Output Directory" → "Export All Crops"
- All images saved as high-quality PNG files

### Navigation & Controls

#### Keyboard Shortcuts
- `Ctrl+O` - Open PDF file
- `Ctrl+U` - Load PDF from URL
- `Ctrl+E` - Export all crops
- `Ctrl+Z` - Undo last crop
- `Delete/Backspace` - Remove selected crop
- `F2` - Rename selected crop
- `Arrow Keys` - Navigate pages
- `Page Up/Down` - Navigate pages
- `Home/End` - First/last page

#### Mouse Controls
- **Left click + drag** - Create crop selection
- **Double-click crop** - Rename crop (immediate, no delay)
- **Mouse wheel** - Scroll through interface

### View Options
- **Continuous Scroll**: View all pages in one scrollable view
- **Auto-highlight Keywords**: Highlight words like "figure", "plot", "diagram" in blue

## Troubleshooting

### Common Issues

**App won't start:**
- Ensure Python 3.10+ is installed
- Install all required packages: `pip install fitz pillow pyinstaller pymupdf`

**PDF won't load:**
- Check if the PDF file is corrupted
- Try a different PDF file
- For URLs, ensure the link is a direct PDF download

**Crops appear too small/large:**
- The zoom functionality has been disabled for stability
- Crops are extracted at optimal resolution automatically
- Use the scroll bars if the PDF appears too large for the window

**Exported images are low quality:**
- The app automatically uses high DPI (300+) for extraction
- Quality depends on the source PDF resolution

### Getting Help

If you encounter issues:
1. Check that all dependencies are installed correctly
2. Try restarting the application
3. Ensure your PDF files are not corrupted or password-protected

## Technical Details

### System Requirements
- **OS**: Windows 10+, macOS 10.14+, or Linux
- **Python**: 3.10 or later
- **Memory**: 2GB RAM minimum, 4GB recommended
- **Storage**: 100MB for application + space for exported images

### Supported Formats
- **Input**: PDF files (including password-protected with manual unlock)
- **Output**: PNG images (high-quality, 300+ DPI)

### Dependencies
- **PyMuPDF (fitz)**: PDF parsing and rendering
- **Pillow (PIL)**: Image processing and export
- **Tkinter**: User interface (included with Python)

## Project Structure

```
pdf-figure-extractor/
├── main.py              # Application entry point
├── pdf_viewer.py        # Main application logic and UI
├── ui_components.py     # Reusable UI components
├── image_extractor.py   # High-quality image extraction
├── utils.py             # Utility functions
└── README.md           # This file
```

## License

This project is open source. Feel free to use, modify, and distribute.

## Contributing

Contributions are welcome! The codebase is well-documented and modular for easy enhancement.