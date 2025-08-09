# PDF Figure Extractor

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

A powerful desktop application for extracting high-quality figures and images from PDF documents with precision cropping and intelligent naming features.

![PDF Figure Extractor Demo](https://via.placeholder.com/800x400/f0f0f0/333333?text=PDF+Figure+Extractor+Screenshot)

## 🚀 Features

- **🎯 Precision Cropping**: Click and drag to select exactly what you need
- **🧠 Smart Naming**: Learns your naming patterns automatically
- **📊 High-Quality Output**: 300+ DPI extraction for publication-ready images
- **⚡ Batch Processing**: Export multiple crops at once
- **🔍 Multi-View Support**: Single-page or continuous scrolling
- **🎨 Auto-Highlighting**: Finds visualization keywords automatically
- **⌨️ Keyboard Shortcuts**: Efficient workflow with hotkeys

## 📦 Quick Start

### Prerequisites
- Python 3.10+
- Windows, macOS, or Linux

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/pdf-figure-extractor.git
cd pdf-figure-extractor

# Install dependencies
pip install fitz pillow pyinstaller pymupdf

# Run the application
python main.py
```

## 🎮 Usage

### Basic Workflow
1. **Load PDF**: `Ctrl+O` to open a file or `Ctrl+U` for URLs
2. **Create Crops**: Click and drag on areas you want to extract
3. **Smart Naming**: Rename your first crop - the app learns your pattern!
4. **Export**: Individual saves or batch export all crops

### 🔥 Key Feature: Adaptive Naming
The app learns from your first rename:
- Create crop (gets name like `document_Q0001`)
- Rename to `study_fig_001` 
- **All future crops automatically become `study_fig_002`, `study_fig_003`, etc.**

### Keyboard Shortcuts
| Action | Shortcut |
|--------|----------|
| Open PDF | `Ctrl+O` |
| Load from URL | `Ctrl+U` |
| Export All | `Ctrl+E` |
| Undo Last Crop | `Ctrl+Z` |
| Delete Crop | `Delete` |
| Rename Crop | `F2` |
| Navigate Pages | `Arrow Keys` |

## 🛠️ Technical Details

### Built With
- **Python 3.10+** - Core application
- **PyMuPDF (fitz)** - PDF processing
- **Pillow (PIL)** - Image handling
- **Tkinter** - GUI framework

### System Requirements
- **OS**: Windows 10+, macOS 10.14+, or Linux
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 100MB + space for exports

### Project Structure
```
pdf-figure-extractor/
├── main.py              # Application entry point
├── pdf_viewer.py        # Main application logic
├── ui_components.py     # UI components
├── image_extractor.py   # Image processing
├── utils.py             # Utilities
└── README.md           # Documentation
```

## 🔧 Troubleshooting

<details>
<summary>Common Issues</summary>

**App won't start**
- Verify Python 3.10+ is installed
- Install all dependencies: `pip install fitz pillow pyinstaller pymupdf`

**PDF won't load**
- Check if PDF is corrupted
- For URLs, ensure direct PDF download link

**Low quality exports**
- App automatically uses high DPI (300+)
- Quality depends on source PDF resolution

</details>

## 🤝 Contributing

Contributions welcome! The codebase is modular and well-documented.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for researchers, students, and professionals
- Optimized for academic paper figure extraction
- Designed with workflow efficiency in mind

## 📈 Roadmap

- [ ] Batch PDF processing
- [ ] Cloud storage integration
- [ ] Advanced image filtering
- [ ] Custom export formats
- [ ] OCR text extraction

---

⭐ **Star this repo if it helps your research workflow!**