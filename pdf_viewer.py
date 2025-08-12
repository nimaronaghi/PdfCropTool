"""
PDF Viewer Component - Main UI and PDF Display Logic
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import os
import io
import threading
import urllib.request
import urllib.parse
import tempfile
import shutil
from pathlib import Path

from ui_components import CropFrame, NamingFrame, ControlFrame
from image_extractor import ImageExtractor
from utils import format_file_size, get_pdf_info, get_unique_filename

class PDFViewerApp:
    def __init__(self, root):
        self.root = root
        self.pdf_document = None
        self.current_page = 0
        self.zoom_level = 1.0
        self.pdf_images = []  # Cache for rendered pages
        self.crop_selections = []  # List of crop selections
        self.output_directory = ""
        self.naming_pattern = "Q{:02d}"
        self.use_sequential_naming = False
        
        # Adaptive naming system
        self.learned_naming_prefix = ""  # Learned prefix from user renaming (e.g., "nima_")
        self.learned_naming_pattern = ""  # Full learned pattern (e.g., "nima_Q{:02d}")
        self.naming_learning_enabled = True
        
        # Continuous scrolling system
        self.continuous_mode = False  # Disable continuous scrolling by default
        self.page_positions = []  # Y positions of each page in continuous view
        self.page_heights = []   # Height of each page
        self.total_height = 0    # Total height of all pages
        self.page_gap = 20       # Gap between pages in continuous mode
        
        # Search system removed - only keeping visualization highlighting
        
        # Visualization keywords for auto-highlighting
        self.viz_keywords = ['fig', 'Fig', 'figure', 'Figure', 'plot', 'Plot', 
                           'diagram', 'Diagram', 'chart', 'Chart', 'graph', 'Graph',
                           'image', 'Image', 'illustration', 'Illustration',
                           'table', 'Table', 'equation', 'Equation', 'formula', 'Formula',
                           'schema', 'Schema', 'flowchart', 'Flowchart', 'map', 'Map',
                           'screenshot', 'Screenshot', 'photo', 'Photo', 'visual', 'Visual']
        self.viz_highlights = []  # List of visualization highlight rectangles
        self.show_viz_highlights = False  # Control viz highlighting with checkbox (OFF by default)
        
        self.setup_ui()
        self.setup_bindings()
        
        # Initialize crop history for undo functionality
        self.crop_history = []
        
    def setup_ui(self):
        """Initialize the user interface"""
        # Create main menu
        self.create_menu()
        
        # Create main frames
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel with scrollbar for controls
        self.left_scroll_frame = ttk.Frame(self.main_frame, width=270)
        self.left_scroll_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        self.left_scroll_frame.pack_propagate(False)
        
        # Create canvas and scrollbar for left panel
        self.left_canvas = tk.Canvas(self.left_scroll_frame, width=250, highlightthickness=0, bg="white")
        self.left_scrollbar = ttk.Scrollbar(self.left_scroll_frame, orient="vertical", command=self.left_canvas.yview)
        self.left_panel = ttk.Frame(self.left_canvas)
        
        # Pack scrollbar first (on the right)
        self.left_scrollbar.pack(side="right", fill="y")
        # Then pack canvas (fills remaining space)
        self.left_canvas.pack(side="left", fill="both", expand=True)
        
        # Create window in canvas for the panel
        self.left_canvas_frame = self.left_canvas.create_window((0, 0), window=self.left_panel, anchor="nw")
        
        # Configure scrolling
        self.left_canvas.configure(yscrollcommand=self.left_scrollbar.set)
        
        def _configure_scroll_region(event=None):
            self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))
            # Also update the canvas window width to match the canvas
            canvas_width = self.left_canvas.winfo_width()
            self.left_canvas.itemconfig(self.left_canvas_frame, width=canvas_width)
        
        self.left_panel.bind("<Configure>", _configure_scroll_region)
        self.left_canvas.bind("<Configure>", _configure_scroll_region)
        
        # Enhanced mouse wheel scrolling for left panel
        def _on_left_mousewheel(event):
            try:
                # Handle different platforms (Windows uses event.delta, Linux uses event.num)
                if event.delta:
                    delta = int(-1 * (event.delta / 120))
                elif event.num == 4:
                    delta = -1
                elif event.num == 5:
                    delta = 1
                else:
                    return
                
                # Scroll the left canvas
                self.left_canvas.yview_scroll(delta, "units")
                return "break"
            except Exception:
                pass
        
        # Bind mousewheel to all left panel components recursively
        def bind_mousewheel_recursive(widget):
            widget.bind("<MouseWheel>", _on_left_mousewheel)  # Windows
            widget.bind("<Button-4>", _on_left_mousewheel)    # Linux scroll up
            widget.bind("<Button-5>", _on_left_mousewheel)    # Linux scroll down
            
            # Bind to all children
            for child in widget.winfo_children():
                try:
                    bind_mousewheel_recursive(child)
                except:
                    pass
        
        # Initially bind to frame, then refresh after components are created
        bind_mousewheel_recursive(self.left_scroll_frame)
        
        # Store the binding function for later use
        self._bind_mousewheel_recursive = bind_mousewheel_recursive
        
        # Right panel for PDF display
        self.right_panel = ttk.Frame(self.main_frame)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Setup control panels
        self.setup_control_panels()
        
        # Setup PDF viewer
        self.setup_pdf_viewer()
        
        # Setup visualization highlighting controls
        self.setup_highlighting_controls()
        
        # Status bar
        self.setup_status_bar()
        
        # Initial state - show welcome message
        self.show_welcome_message()
        
    def create_menu(self):
        """Create the application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open PDF...", command=self.open_pdf, accelerator="Ctrl+O")
        file_menu.add_command(label="Load PDF from URL...", command=self.load_pdf_from_url, accelerator="Ctrl+U")
        file_menu.add_separator()
        file_menu.add_command(label="Export Crops", command=self.export_all_crops, accelerator="Ctrl+E")

        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        # Zoom commands removed - functionality disabled to fix display issues
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Undo Last Crop", command=self.undo_last_crop, accelerator="Ctrl+Z")
        tools_menu.add_command(label="Delete Selected Crop", command=self.delete_selected_crop, accelerator="Delete")
        tools_menu.add_separator()
        tools_menu.add_command(label="Clear All Crops", command=self.clear_all_crops)
        tools_menu.add_command(label="Export All Crops", command=self.export_all_crops)
        
    def setup_control_panels(self):
        """Setup the left control panels"""
        # File operations frame
        file_frame = ttk.LabelFrame(self.left_panel, text="File Operations", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(file_frame, text="Open PDF", command=self.open_pdf).pack(fill=tk.X, pady=2)
        ttk.Button(file_frame, text="Load from URL", command=self.load_pdf_from_url).pack(fill=tk.X, pady=2)
        
        # PDF info frame
        self.info_frame = ttk.LabelFrame(self.left_panel, text="PDF Information", padding=10)
        self.info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.info_text = tk.Text(self.info_frame, height=6, wrap=tk.WORD, state=tk.DISABLED)
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        # Navigation frame
        nav_frame = ttk.LabelFrame(self.left_panel, text="Navigation", padding=10)
        nav_frame.pack(fill=tk.X, pady=(0, 10))
        
        # First row - Quick navigation buttons
        quick_nav = ttk.Frame(nav_frame)
        quick_nav.pack(fill=tk.X, pady=(0, 5))
        
        self.first_btn = ttk.Button(quick_nav, text="⏮", command=self.first_page, width=4)
        self.first_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.prev_btn = ttk.Button(quick_nav, text="◀", command=self.previous_page, width=4)
        self.prev_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.next_btn = ttk.Button(quick_nav, text="▶", command=self.next_page, width=4)
        self.next_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.last_btn = ttk.Button(quick_nav, text="⏭", command=self.last_page, width=4)
        self.last_btn.pack(side=tk.RIGHT, padx=(2, 0))
        
        # Second row - Direct page input
        page_input_frame = ttk.Frame(nav_frame)
        page_input_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(page_input_frame, text="Page:").pack(side=tk.LEFT)
        
        # Page input with validation
        self.page_var = tk.StringVar()
        self.page_var.trace('w', self.on_page_input_change)
        self.page_entry = ttk.Entry(page_input_frame, textvariable=self.page_var, width=8, justify=tk.CENTER)
        self.page_entry.pack(side=tk.LEFT, padx=(5, 5))
        
        # Bind Enter key to go to page
        self.page_entry.bind('<Return>', self.go_to_page_from_entry)
        self.page_entry.bind('<FocusOut>', self.on_page_entry_focus_out)
        
        self.total_pages_label = ttk.Label(page_input_frame, text="of 0")
        self.total_pages_label.pack(side=tk.LEFT)
        
        ttk.Button(page_input_frame, text="Go", command=self.go_to_page_from_entry, width=4).pack(side=tk.RIGHT)
        
        # Third row - Page status and thumbnails button
        status_frame = ttk.Frame(nav_frame)
        status_frame.pack(fill=tk.X)
        
        self.page_status_label = ttk.Label(status_frame, text="No PDF loaded", font=("Arial", 9))
        self.page_status_label.pack(side=tk.LEFT)
        
        # Future: Add thumbnails view button
        # ttk.Button(status_frame, text="Thumbnails", command=self.show_thumbnails).pack(side=tk.RIGHT)
        
        # Zoom frame removed - functionality disabled to fix display issues
        
        # Crop frame
        self.crop_frame = CropFrame(self.left_panel, self)
        self.crop_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Naming frame
        self.naming_frame = NamingFrame(self.left_panel, self)
        self.naming_frame.pack(fill=tk.X, pady=(0, 10))
        

        
        # Export frame
        export_frame = ttk.LabelFrame(self.left_panel, text="Export", padding=10)
        export_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(export_frame, text="Select Output Directory", 
                  command=self.select_output_directory).pack(fill=tk.X, pady=2)
        
        self.output_label = ttk.Label(export_frame, text="No directory selected", 
                                     wraplength=200, foreground="gray")
        self.output_label.pack(fill=tk.X, pady=2)
        
        ttk.Button(export_frame, text="Export All Crops", 
                  command=self.export_all_crops, style="Accent.TButton").pack(fill=tk.X, pady=(10, 2))
        
        # Refresh mouse wheel bindings after all components are created
        if hasattr(self, '_bind_mousewheel_recursive'):
            self._bind_mousewheel_recursive(self.left_scroll_frame)
    
    def setup_highlighting_controls(self):
        """Setup the highlighting and view controls in the right panel"""
        # Control frame at the top of the right panel
        control_frame = ttk.Frame(self.right_panel)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        # View mode toggle
        self.continuous_var = tk.BooleanVar(value=False)
        continuous_check = ttk.Checkbutton(control_frame, text="Continuous Scroll", 
                                         variable=self.continuous_var, 
                                         command=self.toggle_view_mode)
        continuous_check.pack(side=tk.LEFT, padx=(5, 20))
        
        # Visualization highlighting toggle
        self.viz_highlight_var = tk.BooleanVar(value=False)
        viz_check = ttk.Checkbutton(control_frame, text="Auto-highlight Keywords", 
                                   variable=self.viz_highlight_var, 
                                   command=self.toggle_viz_highlighting)
        viz_check.pack(side=tk.LEFT)
        
    def setup_pdf_viewer(self):
        """Setup the PDF viewer canvas"""
        # Create scrollable canvas
        canvas_frame = ttk.Frame(self.right_panel)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas with scrollbars
        self.canvas = tk.Canvas(canvas_frame, bg="white")
        
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout for canvas and scrollbars
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Bind mouse events for cropping
        self.canvas.bind("<Button-1>", self.start_crop)
        self.canvas.bind("<B1-Motion>", self.update_crop)
        self.canvas.bind("<ButtonRelease-1>", self.finish_crop)
        
        # Bind mouse motion for crosshair guides
        self.canvas.bind("<Motion>", self.show_crosshair)
        self.canvas.bind("<Leave>", self.hide_crosshair)
        
        # Enhanced mouse wheel scrolling for PDF canvas
        def _on_canvas_mousewheel(event):
            try:
                # Handle different platforms
                if event.delta:
                    delta = int(-1 * (event.delta / 120))
                elif event.num == 4:
                    delta = -1
                elif event.num == 5:
                    delta = 1
                else:
                    return
                
                # Scroll vertically by default, horizontally with Shift
                if event.state & 0x1:  # Shift key pressed
                    self.canvas.xview_scroll(delta, "units")
                else:
                    self.canvas.yview_scroll(delta, "units")
                return "break"
            except Exception:
                pass
        
        # Bind mouse wheel to PDF canvas
        self.canvas.bind("<MouseWheel>", _on_canvas_mousewheel)  # Windows
        self.canvas.bind("<Button-4>", _on_canvas_mousewheel)    # Linux scroll up  
        self.canvas.bind("<Button-5>", _on_canvas_mousewheel)    # Linux scroll down
        
        # Variables for crop selection
        self.crop_start = None
        self.crop_rect = None
        self.cropping = False
        
    def setup_status_bar(self):
        """Setup the status bar"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0, 5))
        
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(self.status_bar, mode='indeterminate')
        # Initially hidden
        

        
    def show_welcome_message(self):
        """Show welcome message when no PDF is loaded"""
        self.canvas.delete("all")
        welcome_text = "Use File → Open PDF to load a document"
        self.canvas.create_text(
            300, 200, text=welcome_text, 
            font=("Arial", 16), fill="gray", 
            justify=tk.CENTER, tags="welcome"
        )
        
    def open_pdf(self):
        """Open a PDF file"""
        file_path = filedialog.askopenfilename(
            title="Select PDF file",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if file_path:
            self.load_pdf(file_path)
            
    def load_pdf(self, file_path):
        """Load a PDF document"""
        try:
            self.status_label.config(text="Loading PDF...")
            self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))
            self.progress_bar.start()
            
            # Load PDF in a separate thread to prevent UI freezing
            threading.Thread(target=self._load_pdf_thread, args=(file_path,), daemon=True).start()
            
        except Exception as e:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.status_label.config(text="Ready")
            messagebox.showerror("Error", f"Failed to load PDF: {str(e)}")
            
    def _load_pdf_thread(self, file_path):
        """Load PDF in background thread"""
        try:
            # Open PDF document
            pdf_doc = fitz.open(file_path)
            
            # Update UI in main thread
            self.root.after(0, self._pdf_loaded_callback, pdf_doc, file_path)
            
        except Exception as e:
            self.root.after(0, self._pdf_load_error_callback, str(e))
            
    def _pdf_loaded_callback(self, pdf_doc, file_path):
        """Callback when PDF is successfully loaded"""
        self.pdf_document = pdf_doc
        self.current_file_path = file_path  # Store for default naming
        self.current_page = 0
        self.pdf_images = []
        self.crop_selections = []  # Clear previous crops
        self.crop_history = []
        
        # Update the crop list UI to reflect cleared selections
        self.crop_frame.update_crop_list(self.crop_selections)
        
        # Update UI
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.status_label.config(text=f"Loaded: {os.path.basename(file_path)}")
        
        # Update PDF info
        self.update_pdf_info(file_path)
        
        # Initialize view mode
        if self.continuous_mode:
            self.render_continuous_pages()
        else:
            self.render_current_page()
        
        # Update navigation
        self.update_navigation()
        
        # Auto-highlight visualization keywords
        if hasattr(self, 'viz_highlight_var'):
            self.highlight_visualization_keywords()
        
    def _pdf_load_error_callback(self, error_msg):
        """Callback when PDF loading fails"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.status_label.config(text="Ready")
        messagebox.showerror("Error", f"Failed to load PDF: {error_msg}")
        
    def update_pdf_info(self, file_path):
        """Update the PDF information display"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        
        try:
            info = get_pdf_info(self.pdf_document, file_path)
            self.info_text.insert(tk.END, info)
        except Exception as e:
            self.info_text.insert(tk.END, f"Error reading PDF info: {str(e)}")
            
        self.info_text.config(state=tk.DISABLED)
        
    def render_current_page(self):
        """Render the current PDF page (single page mode)"""
        if not self.pdf_document:
            return
            
        try:
            page = self.pdf_document[self.current_page]
            
            # Calculate render matrix for high DPI
            matrix = fitz.Matrix(self.zoom_level * 2, self.zoom_level * 2)  # 2x for high DPI
            
            # Render page to pixmap
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            
            # Convert to PIL Image
            img_data = pix.tobytes("ppm")
            pil_image = Image.open(io.BytesIO(img_data))
            
            # Resize for display (while keeping original for extraction)
            display_width = int(pil_image.width * self.zoom_level)
            display_height = int(pil_image.height * self.zoom_level)
            display_image = pil_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.current_image = ImageTk.PhotoImage(display_image)
            
            # Store original high-res image for extraction
            self.original_image = pil_image
            self.page_dpi = 72 * 2  # Base DPI * matrix scale
            
            # Clear canvas and display image
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_image, tags="page")
            
            # Update scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            # Reset scroll position to top-left when changing pages
            self.canvas.xview_moveto(0)
            self.canvas.yview_moveto(0)
            
            # Redraw existing crop rectangles
            self.redraw_crop_rectangles()
            
            # Update visualization highlighting for current page
            if hasattr(self, 'viz_highlight_var') and self.viz_highlight_var.get():
                self.highlight_visualization_keywords()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to render page: {str(e)}")
    
    def render_continuous_pages(self):
        """Render all pages continuously in a single scrollable view"""
        if not self.pdf_document:
            return
            
        try:
            # Clear canvas
            self.canvas.delete("all")
            
            # Reset position tracking
            self.page_positions = []
            self.page_heights = []
            current_y = 0
            
            # Store page images to prevent garbage collection
            self.page_images = []
            
            # Render each page
            for page_num in range(len(self.pdf_document)):
                page = self.pdf_document[page_num]
                
                # Calculate render matrix
                matrix = fitz.Matrix(self.zoom_level * 2, self.zoom_level * 2)
                
                # Render page to pixmap
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                
                # Convert to PIL Image
                img_data = pix.tobytes("ppm")
                pil_image = Image.open(io.BytesIO(img_data))
                
                # Resize for display
                display_width = int(pil_image.width * self.zoom_level)
                display_height = int(pil_image.height * self.zoom_level)
                display_image = pil_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage and store
                page_photo = ImageTk.PhotoImage(display_image)
                self.page_images.append(page_photo)
                
                # Store page position
                self.page_positions.append(current_y)
                self.page_heights.append(display_height)
                
                # Create image on canvas
                self.canvas.create_image(0, current_y, anchor=tk.NW, image=page_photo, 
                                       tags=f"page_{page_num}")
                
                # Add page number label
                self.canvas.create_text(10, current_y + 10, text=f"Page {page_num + 1}", 
                                      anchor=tk.NW, fill="red", font=("Arial", 12, "bold"),
                                      tags=f"page_label_{page_num}")
                
                # Move to next page position
                current_y += display_height + self.page_gap
            
            # Store total height
            self.total_height = current_y
            
            # Update scroll region
            max_width = max(img.width() for img in self.page_images) if self.page_images else 800
            self.canvas.configure(scrollregion=(0, 0, max_width, self.total_height))
            
            # Redraw crop rectangles
            self.redraw_crop_rectangles()
            
            # Update visualization highlighting for continuous mode
            if hasattr(self, 'viz_highlight_var') and self.viz_highlight_var.get():
                self.highlight_visualization_keywords()
            
            # Store current page DPI for extraction
            self.page_dpi = 72 * 2
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to render continuous pages: {str(e)}")
    
    def toggle_view_mode(self):
        """Toggle between continuous and single page view"""
        self.continuous_mode = self.continuous_var.get()
        
        if not self.pdf_document:
            return
        
        # Clear any existing search highlights
        self.canvas.delete("search_highlight")
        
        # Re-render in new mode
        if self.continuous_mode:
            self.render_continuous_pages()
        else:
            self.render_current_page()
        
        # Reapply highlights
        self.highlight_visualization_keywords()
    

    
    def toggle_viz_highlighting(self):
        """Toggle visualization keyword highlighting"""
        self.show_viz_highlights = self.viz_highlight_var.get()
        
        if self.show_viz_highlights:
            self.highlight_visualization_keywords()
        else:
            self.canvas.delete("viz_highlight")
            self.viz_highlights = []

    def highlight_visualization_keywords(self):
        """Auto-highlight visualization keywords"""
        if not self.pdf_document or not self.show_viz_highlights:
            return
        
        # Clear previous viz highlights
        self.canvas.delete("viz_highlight")
        self.viz_highlights = []
        
        # Search for each visualization keyword
        for keyword in self.viz_keywords:
            for page_num in range(len(self.pdf_document)):
                page = self.pdf_document[page_num]
                
                # Search for keyword instances
                text_instances = page.search_for(keyword)
                
                for inst in text_instances:
                    # Convert PDF coordinates to display coordinates
                    if self.continuous_mode:
                        display_coords = self.pdf_to_continuous_coords(inst, page_num)
                    else:
                        if page_num == self.current_page:
                            display_coords = self.pdf_to_display_coords(inst)
                        else:
                            continue
                    
                    if display_coords:
                        self.viz_highlights.append({
                            'coords': display_coords,
                            'page': page_num,
                            'keyword': keyword
                        })
                        
                        # Create highlight rectangle
                        self.canvas.create_rectangle(
                            display_coords[0], display_coords[1], 
                            display_coords[2], display_coords[3],
                            outline="blue", fill="lightblue", width=1, stipple="gray25",
                            tags="viz_highlight"
                        )
    
    def pdf_to_display_coords(self, pdf_rect):
        """Convert PDF coordinates to display coordinates (single page mode)"""
        if not hasattr(self, 'current_image') and not hasattr(self, 'page_images'):
            return None
        
        # Scale factor from PDF to display  
        scale_factor = self.zoom_level * 2
        
        return (
            pdf_rect[0] * scale_factor,  # left
            pdf_rect[1] * scale_factor,  # top
            pdf_rect[2] * scale_factor,  # right
            pdf_rect[3] * scale_factor   # bottom
        )
    
    def pdf_to_continuous_coords(self, pdf_rect, page_num):
        """Convert PDF coordinates to display coordinates (continuous mode)"""
        if not hasattr(self, 'page_positions') or page_num >= len(self.page_positions):
            return None
        
        # Scale factor from PDF to display  
        scale_factor = self.zoom_level * 2
        
        # Get page position offset
        page_y_offset = self.page_positions[page_num]
        
        return (
            pdf_rect[0] * scale_factor,  # left
            pdf_rect[1] * scale_factor + page_y_offset,  # top (with page offset)
            pdf_rect[2] * scale_factor,  # right
            pdf_rect[3] * scale_factor + page_y_offset   # bottom (with page offset)
        )
    
    def find_page_from_y_coord(self, y_coord):
        """Find which page a Y coordinate belongs to in continuous mode"""
        if not hasattr(self, 'page_positions') or not self.page_positions:
            return 0  # Default to first page if no positions available
        
        # Find the page that contains this Y coordinate
        for page_num in range(len(self.page_positions)):
            page_start_y = self.page_positions[page_num]
            
            # Get page end Y coordinate
            if page_num < len(self.page_heights):
                page_height = self.page_heights[page_num]
                page_end_y = page_start_y + page_height
            else:
                page_end_y = page_start_y + 500  # Default height if not available
            
            # Check if Y coordinate falls within this page
            if page_start_y <= y_coord <= page_end_y:
                return page_num
        
        # If not found, return the last page
        return len(self.page_positions) - 1 if self.page_positions else 0
    

            
    def update_navigation(self):
        """Update navigation controls"""
        if not self.pdf_document:
            self.page_status_label.config(text="No PDF loaded")
            self.total_pages_label.config(text="of 0")
            self.first_btn.config(state=tk.DISABLED)
            self.prev_btn.config(state=tk.DISABLED)
            self.next_btn.config(state=tk.DISABLED)
            self.last_btn.config(state=tk.DISABLED)
            self.page_entry.config(state=tk.DISABLED)
            self.page_var.set("")
            return
            
        total_pages = len(self.pdf_document)
        current_display = self.current_page + 1
        
        # Update page display
        self.page_status_label.config(text=f"Page {current_display} of {total_pages}")
        self.total_pages_label.config(text=f"of {total_pages}")
        
        # Update page entry if not currently being edited
        if self.page_entry != self.root.focus_get():
            self.page_var.set(str(current_display))
        
        # Enable/disable navigation buttons
        self.page_entry.config(state=tk.NORMAL)
        self.first_btn.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        self.prev_btn.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if self.current_page < total_pages - 1 else tk.DISABLED)
        self.last_btn.config(state=tk.NORMAL if self.current_page < total_pages - 1 else tk.DISABLED)
        
        # Zoom label removed with zoom functionality
        
    def previous_page(self):
        """Go to previous page"""
        if self.pdf_document and self.current_page > 0:
            self.current_page -= 1
            if not self.continuous_mode:
                self.render_current_page()
            self.update_navigation()
            
    def next_page(self):
        """Go to next page"""
        if self.pdf_document and self.current_page < len(self.pdf_document) - 1:
            self.current_page += 1
            if not self.continuous_mode:
                self.render_current_page()
            self.update_navigation()
            
    def first_page(self):
        """Go to first page"""
        if self.pdf_document and self.current_page > 0:
            self.current_page = 0
            if not self.continuous_mode:
                self.render_current_page()
            self.update_navigation()
            
    def last_page(self):
        """Go to last page"""
        if self.pdf_document:
            last_page = len(self.pdf_document) - 1
            if self.current_page != last_page:
                self.current_page = last_page
                if not self.continuous_mode:
                    self.render_current_page()
                self.update_navigation()
                
    def go_to_page(self, page_number):
        """Go to specific page (1-based)"""
        if not self.pdf_document:
            return False
            
        # Convert to 0-based index
        page_index = page_number - 1
        total_pages = len(self.pdf_document)
        
        if 0 <= page_index < total_pages:
            self.current_page = page_index
            if not self.continuous_mode:
                self.render_current_page()
            self.update_navigation()
            return True
        return False
        
    def go_to_page_from_entry(self, event=None):
        """Handle page navigation from entry widget"""
        try:
            page_text = self.page_var.get().strip()
            if not page_text:
                return
                
            page_number = int(page_text)
            if self.go_to_page(page_number):
                # Clear focus from entry
                self.root.focus()
            else:
                # Invalid page number - show error and reset
                total_pages = len(self.pdf_document) if self.pdf_document else 0
                messagebox.showerror("Invalid Page", 
                                   f"Please enter a page number between 1 and {total_pages}")
                # Reset to current page
                self.page_var.set(str(self.current_page + 1))
                
        except ValueError:
            # Invalid input - reset to current page
            if self.pdf_document:
                self.page_var.set(str(self.current_page + 1))
            else:
                self.page_var.set("")
                
    def on_page_input_change(self, *args):
        """Handle real-time validation of page input"""
        if not self.pdf_document:
            return
            
        try:
            page_text = self.page_var.get().strip()
            if not page_text:
                return
                
            page_number = int(page_text)
            total_pages = len(self.pdf_document)
            
            # Visual feedback for valid/invalid page numbers
            if 1 <= page_number <= total_pages:
                self.page_entry.config(foreground="black")
            else:
                self.page_entry.config(foreground="red")
                
        except ValueError:
            # Invalid input - show red text
            self.page_entry.config(foreground="red")
            
    def on_page_entry_focus_out(self, event=None):
        """Handle when page entry loses focus"""
        if self.pdf_document:
            # Reset to current page if invalid input
            try:
                page_text = self.page_var.get().strip()
                if not page_text:
                    self.page_var.set(str(self.current_page + 1))
                    return
                    
                page_number = int(page_text)
                total_pages = len(self.pdf_document)
                
                if not (1 <= page_number <= total_pages):
                    self.page_var.set(str(self.current_page + 1))
                    
            except ValueError:
                self.page_var.set(str(self.current_page + 1))
                
        # Reset text color
        self.page_entry.config(foreground="black")
        
    def focus_page_entry(self):
        """Focus on page entry for direct navigation"""
        if self.pdf_document:
            self.page_entry.focus()
            self.page_entry.select_range(0, tk.END)
            
    # Zoom functionality removed - was causing display issues
    # Cropping system now works at fixed 1.0 zoom level for reliability
            
    def show_crosshair(self, event):
        """Show crosshair guides at cursor position"""
        if not self.pdf_document:
            return
            
        # Delete existing crosshair
        self.canvas.delete("crosshair")
        
        # Get canvas coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Get scroll region to determine actual content size
        scroll_region = self.canvas.cget('scrollregion')
        if scroll_region:
            scroll_bounds = [float(x) for x in scroll_region.split()]
            max_x = scroll_bounds[2]
            max_y = scroll_bounds[3]
        else:
            max_x = canvas_width
            max_y = canvas_height
        
        # Draw vertical line
        self.canvas.create_line(canvas_x, 0, canvas_x, max_y, 
                               fill="#808080", dash=(5, 5), width=1, tags="crosshair")
        
        # Draw horizontal line
        self.canvas.create_line(0, canvas_y, max_x, canvas_y, 
                               fill="#808080", dash=(5, 5), width=1, tags="crosshair")
                               
    def hide_crosshair(self, event):
        """Hide crosshair guides when cursor leaves canvas"""
        self.canvas.delete("crosshair")
        
    def start_crop(self, event):
        """Start crop selection"""
        if not self.pdf_document:
            return
            
        # Hide crosshair during cropping
        self.canvas.delete("crosshair")
        
        # Convert canvas coordinates to image coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        self.crop_start = (canvas_x, canvas_y)
        self.cropping = True
        
        # Delete any existing crop rectangle
        self.canvas.delete("crop_rect")
        
    def update_crop(self, event):
        """Update crop selection rectangle"""
        if not self.cropping or not self.crop_start:
            return
            
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Delete previous rectangle
        self.canvas.delete("crop_rect")
        
        # Draw new rectangle
        self.crop_rect = self.canvas.create_rectangle(
            self.crop_start[0], self.crop_start[1], canvas_x, canvas_y,
            outline="red", width=2, tags="crop_rect"
        )
        
    def finish_crop(self, event):
        """Finish crop selection"""
        if not self.cropping or not self.crop_start:
            return
            
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Re-enable crosshair after cropping
        self.show_crosshair(event)
        
        # Calculate crop rectangle
        x1, y1 = self.crop_start
        x2, y2 = canvas_x, canvas_y
        
        # Ensure valid rectangle
        if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
            # Normalize coordinates
            left = min(x1, x2)
            top = min(y1, y2)
            right = max(x1, x2)
            bottom = max(y1, y2)
            
            # Convert display coordinates to PDF coordinates for storage
            display_scale = max(self.zoom_level * 2.0, 0.1)  # Ensure positive scale, minimum 0.1
            
            # Convert to PDF coordinates (normalized, zoom-independent)
            if self.continuous_mode:
                # Find which page this crop belongs to
                crop_page = self.find_page_from_y_coord(top)
                if crop_page is not None and crop_page < len(self.page_positions):
                    page_y_offset = self.page_positions[crop_page]
                    pdf_left = left / display_scale
                    pdf_top = (top - page_y_offset) / display_scale
                    pdf_right = right / display_scale
                    pdf_bottom = (bottom - page_y_offset) / display_scale
                else:
                    crop_page = self.current_page
                    pdf_left = left / display_scale
                    pdf_top = top / display_scale
                    pdf_right = right / display_scale
                    pdf_bottom = bottom / display_scale
            else:
                crop_page = self.current_page
                pdf_left = left / display_scale
                pdf_top = top / display_scale
                pdf_right = right / display_scale
                pdf_bottom = bottom / display_scale
            
            # Generate adaptive default name based on learned patterns
            default_name = self.get_adaptive_crop_name()
            
            # Store crops with PDF coordinates and display coordinates for drawing
            crop_data = {
                'page': crop_page if self.continuous_mode else self.current_page,
                'coords': (left, top, right, bottom),  # Display coords for drawing rectangles
                'pdf_coords': (pdf_left, pdf_top, pdf_right, pdf_bottom),  # PDF coords for extraction
                'zoom': self.zoom_level,  # Zoom level when created (for display only)
                'custom_name': default_name  # Default naming format
            }
            self.crop_selections.append(crop_data)
            
            # Add to history for undo functionality
            self.crop_history.append(len(self.crop_selections) - 1)
            
            # Update crop list and scroll to bottom
            self.crop_frame.update_crop_list(self.crop_selections, scroll_to_end=True)
            
            # Auto-popup naming dialog unless sequential naming is enabled
            if not self.use_sequential_naming:
                # Schedule the naming dialog to appear after the UI updates
                self.root.after(10, lambda: self.crop_frame.show_rename_dialog(len(self.crop_selections) - 1))
            
            # Redraw all crop rectangles to ensure proper display
            self.redraw_crop_rectangles()
            
        self.cropping = False
        self.crop_start = None
        
    def redraw_crop_rectangles(self):
        """Redraw all crop rectangles for current page"""
        self.canvas.delete("saved_crop")
        
        for i, crop in enumerate(self.crop_selections):
            # Convert PDF coordinates back to current display coordinates for drawing
            if 'pdf_coords' in crop:
                pdf_coords = crop['pdf_coords']
                current_scale = self.zoom_level * 2.0
                crop_page = crop['page']
                
                # Calculate display coordinates based on view mode
                if self.continuous_mode:
                    # Continuous mode: use page offset if available
                    if hasattr(self, 'page_positions') and crop_page < len(self.page_positions):
                        page_y_offset = self.page_positions[crop_page]
                        left = pdf_coords[0] * current_scale
                        top = pdf_coords[1] * current_scale + page_y_offset
                        right = pdf_coords[2] * current_scale
                        bottom = pdf_coords[3] * current_scale + page_y_offset
                    else:
                        # Fallback: skip this crop if page positions aren't available
                        continue
                else:
                    # Single page mode: only show crops for current page
                    if crop_page != self.current_page:
                        continue
                    left = pdf_coords[0] * current_scale
                    top = pdf_coords[1] * current_scale
                    right = pdf_coords[2] * current_scale
                    bottom = pdf_coords[3] * current_scale
            else:
                # Legacy format - use stored display coordinates (may be inaccurate after zoom changes)
                if not self.continuous_mode and crop['page'] != self.current_page:
                    continue
                coords = crop['coords']
                left, top, right, bottom = coords
            
            # Ensure we have valid coordinates
            width = abs(right - left)
            height = abs(bottom - top)
            
            # Normalize coordinates to handle negative dimensions
            left = min(left, right)
            right = max(left + width, left)
            top = min(top, bottom)  
            bottom = max(top + height, top)
            
            if width > 5 and height > 5:  # Valid minimum size
                rect = self.canvas.create_rectangle(
                    left, top, right, bottom,
                    outline="red", width=3, tags="saved_crop", fill=""
                )
                
                # Add crop number label
                center_x = (left + right) / 2
                center_y = top + 15
                self.canvas.create_text(
                    center_x, center_y, text=f"#{i+1}",
                    fill="red", font=("Arial", 12, "bold"), tags="saved_crop"
                )
            else:
                print(f"CROP TOO SMALL: width={width}, height={height}, coords=({left}, {top}, {right}, {bottom})")
                
    def select_output_directory(self):
        """Select output directory for exported images"""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_directory = directory
            self.output_label.config(
                text=f"Output: {os.path.basename(directory)}", 
                foreground="black"
            )
            
    def clear_all_crops(self):
        """Clear all crop selections"""
        if self.crop_selections:
            result = messagebox.askyesno("Confirm", "Clear all crop selections?")
            if result:
                self.crop_selections = []
                self.crop_history = []
                self.crop_frame.update_crop_list([])
                self.redraw_crop_rectangles()
                
    def export_all_crops(self):
        """Export all crop selections"""
        if not self.crop_selections:
            messagebox.showwarning("No Crops", "No crop selections to export")
            return
            
        if not self.output_directory:
            # Automatically prompt for output directory
            self.select_output_directory()
            if not self.output_directory:
                return
            
        try:
            extractor = ImageExtractor(self.pdf_document)
            
            self.status_label.config(text="Exporting crops...")
            self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))
            self.progress_bar.start()
            
            # Export in background thread
            threading.Thread(
                target=self._export_crops_thread, 
                args=(extractor,), 
                daemon=True
            ).start()
            
        except Exception as e:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.status_label.config(text="Ready")
            messagebox.showerror("Export Error", f"Failed to export crops: {str(e)}")
            
    def _export_crops_thread(self, extractor):
        """Export crops in background thread"""
        try:
            # First pass: collect all conflicts
            conflicts = []
            export_queue = []
            
            for i, crop in enumerate(self.crop_selections):
                # Generate filename based on naming mode
                if self.use_sequential_naming:
                    filename = self.naming_pattern.format(i + 1)
                    if not filename.endswith('.png'):
                        filename += '.png'
                else:
                    # Use custom name if available, otherwise use crop number
                    if 'custom_name' in crop and crop['custom_name']:
                        filename = crop['custom_name']
                    else:
                        filename = f"crop_{i + 1:02d}"
                    if not filename.endswith('.png'):
                        filename += '.png'
                    
                output_path = os.path.join(self.output_directory, filename)
                
                if os.path.exists(output_path):
                    unique_path = get_unique_filename(output_path)
                    conflicts.append({
                        'crop_index': i,
                        'crop': crop,
                        'original_path': output_path,
                        'suggested_path': unique_path,
                        'original_name': os.path.basename(output_path),
                        'suggested_name': os.path.basename(unique_path)
                    })
                else:
                    export_queue.append({'crop_index': i, 'crop': crop, 'path': output_path})
            
            # Handle conflicts if any
            if conflicts:
                # Ask user about conflicts in main thread and wait for response
                self.root.after(0, self._handle_batch_conflicts, conflicts, export_queue, extractor)
            else:
                # No conflicts, proceed with export
                self._process_export_queue(export_queue, extractor)
            
        except Exception as e:
            self.root.after(0, self._export_error_callback, str(e))
            
    def _handle_batch_conflicts(self, conflicts, export_queue, extractor):
        """Handle file conflicts during batch export"""
        if not conflicts:
            self._process_export_queue(export_queue, extractor)
            return
        
        # Create dialog to show all conflicts
        conflict_dialog = tk.Toplevel(self.root)
        conflict_dialog.title("File Conflicts")
        conflict_dialog.geometry("600x400")
        conflict_dialog.resizable(True, True)
        conflict_dialog.transient(self.root)
        conflict_dialog.grab_set()
        
        # Center the dialog
        conflict_dialog.update_idletasks()
        x = (conflict_dialog.winfo_screenwidth() // 2) - (conflict_dialog.winfo_width() // 2)
        y = (conflict_dialog.winfo_screenheight() // 2) - (conflict_dialog.winfo_height() // 2)
        conflict_dialog.geometry(f"+{x}+{y}")
        
        main_frame = ttk.Frame(conflict_dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text=f"Found {len(conflicts)} file conflicts. Choose how to handle them:", 
                 font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # Scrollable list of conflicts
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Create treeview for conflicts with rename capability
        columns = ('crop', 'existing', 'new_name')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        tree.heading('crop', text='Crop')
        tree.heading('existing', text='Existing File')
        tree.heading('new_name', text='New Name')
        
        tree.column('crop', width=100)
        tree.column('existing', width=200)
        tree.column('new_name', width=200)
        
        # Store conflict data with rename capability
        conflict_data = {}
        for i, conflict in enumerate(conflicts):
            item_id = tree.insert('', 'end', values=(
                f"Crop #{conflict['crop_index'] + 1}",
                conflict['original_name'],
                conflict['suggested_name']
            ))
            conflict_data[item_id] = {
                'conflict': conflict,
                'new_name': conflict['suggested_name']
            }
        
        # Double-click to rename
        def on_double_click(event):
            item = tree.selection()[0] if tree.selection() else None
            if item and item in conflict_data:
                current_name = conflict_data[item]['new_name']
                # Remove .png extension for editing
                base_name = current_name[:-4] if current_name.endswith('.png') else current_name
                
                new_name = simpledialog.askstring("Rename File", 
                    f"Enter new name for {conflict_data[item]['conflict']['original_name']}:",
                    initialvalue=base_name)
                
                if new_name:
                    # Ensure .png extension
                    if not new_name.endswith('.png'):
                        new_name += '.png'
                    
                    # Update the display and stored data
                    conflict_data[item]['new_name'] = new_name
                    tree.item(item, values=(
                        tree.item(item, 'values')[0],  # Keep crop number
                        tree.item(item, 'values')[1],  # Keep existing name
                        new_name
                    ))
        
        tree.bind('<Double-1>', on_double_click)
        
        # Scrollbar for tree
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Instructions
        instructions = ttk.Label(main_frame, text="Double-click on 'New Name' column to rename files", 
                                font=("TkDefaultFont", 9), foreground="gray")
        instructions.pack(anchor=tk.W, pady=(5, 10))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        result = {'action': None, 'conflict_data': conflict_data}
        
        def use_new_names():
            result['action'] = 'rename'
            conflict_dialog.destroy()
            
        def skip_conflicts():
            result['action'] = 'skip'
            conflict_dialog.destroy()
            
        def cancel_export():
            result['action'] = 'cancel'
            conflict_dialog.destroy()
        
        ttk.Button(button_frame, text="Use New Names", 
                  command=use_new_names).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Skip Conflicting Files", 
                  command=skip_conflicts).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel Export", 
                  command=cancel_export).pack(side=tk.RIGHT)
        
        # Wait for user decision
        conflict_dialog.wait_window()
        
        # Process based on user choice
        if result['action'] == 'rename':
            # Add conflicts with user-specified names to export queue
            for item_id, data in result['conflict_data'].items():
                conflict = data['conflict']
                new_filename = data['new_name']
                new_path = os.path.join(self.output_directory, new_filename)
                
                export_queue.append({
                    'crop_index': conflict['crop_index'],
                    'crop': conflict['crop'],
                    'path': new_path
                })
        elif result['action'] == 'skip':
            # Don't add conflicts to export queue
            pass
        else:  # cancel
            self._export_cancelled_callback()
            return
        
        # Continue with export
        threading.Thread(target=self._process_export_queue, args=(export_queue, extractor), daemon=True).start()
    
    def _process_export_queue(self, export_queue, extractor):
        """Process the export queue"""
        try:
            exported_count = 0
            
            for item in export_queue:
                crop = item['crop']
                output_path = item['path']
                
                # Extract and save crop
                metadata = extractor.extract_crop(crop, output_path)
                if metadata:
                    exported_count += 1
                    
            # Update UI in main thread
            self.root.after(0, self._export_complete_callback, exported_count, len(self.crop_selections))
            
        except Exception as e:
            self.root.after(0, self._export_error_callback, str(e))
    
    def _export_complete_callback(self, exported_count, total_count):
        """Callback when export is complete"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.status_label.config(text="Ready")
        
        if exported_count == total_count:
            messagebox.showinfo("Export Complete", 
                               f"Successfully exported {exported_count} images to:\n{self.output_directory}")
        else:
            messagebox.showwarning("Export Partial", 
                                 f"Exported {exported_count} of {total_count} images.\n"
                                 f"Some exports may have failed or were skipped.")
            
    def _export_error_callback(self, error_msg):
        """Callback when export fails"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.status_label.config(text="Ready")
        messagebox.showerror("Export Error", f"Export failed: {error_msg}")
        
    def _export_cancelled_callback(self):
        """Callback when export is cancelled"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.status_label.config(text="Ready")
        
    def update_naming_pattern(self, pattern):
        """Update the naming pattern for exported files"""
        self.naming_pattern = pattern
        
    def update_sequential_naming(self, use_sequential):
        """Update whether to use sequential naming or individual crop names"""
        self.use_sequential_naming = use_sequential
        
    def remove_crop(self, index):
        """Remove a specific crop selection"""
        if 0 <= index < len(self.crop_selections):
            self.crop_selections.pop(index)
            self.crop_frame.update_crop_list(self.crop_selections)
            self.redraw_crop_rectangles()
            
    def save_individual_crop(self, crop_index):
        """Save an individual crop with custom filename and location"""
        if crop_index >= len(self.crop_selections):
            return
            
        crop = self.crop_selections[crop_index]
        
        # Generate default filename - use custom name if available
        page_num = crop['page'] + 1
        if 'custom_name' in crop and crop['custom_name']:
            default_filename = f"{crop['custom_name']}.png"
        else:
            default_filename = f"crop_{crop_index + 1:03d}_page_{page_num:03d}.png"
        
        # Let user choose save location and filename
        file_path = filedialog.asksaveasfilename(
            title="Save Crop As...",
            defaultextension=".png",
            initialfile=default_filename,
            filetypes=[
                ("PNG files", "*.png"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return  # User cancelled
            
        try:
            self.status_label.config(text="Saving crop...")
            self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))
            self.progress_bar.start()
            
            # Save in background thread
            threading.Thread(
                target=self._save_individual_crop_thread,
                args=(crop, file_path, crop_index + 1),
                daemon=True
            ).start()
            
        except Exception as e:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.status_label.config(text="Ready")
            messagebox.showerror("Save Error", f"Failed to save crop: {str(e)}")
            
    def _save_individual_crop_thread(self, crop, file_path, crop_number):
        """Save individual crop in background thread"""
        try:
            # Check if file already exists and ask user
            if os.path.exists(file_path):
                unique_path = get_unique_filename(file_path)
                suggested_name = os.path.basename(unique_path)
                original_name = os.path.basename(file_path)
                
                response = messagebox.askyesno("File Exists", 
                    f"File '{original_name}' already exists.\n\nUse suggested name '{suggested_name}' instead?")
                
                if not response:
                    # User declined, don't save
                    self.root.after(0, self._individual_save_cancelled_callback)
                    return
                    
                final_path = unique_path
            else:
                final_path = file_path
            
            extractor = ImageExtractor(self.pdf_document)
            metadata = extractor.extract_crop(crop, final_path)
            
            # Update UI in main thread with the actual path used
            self.root.after(0, self._individual_save_complete_callback, metadata, final_path, crop_number)
            
        except Exception as e:
            self.root.after(0, self._individual_save_error_callback, str(e), crop_number)
            
    def _individual_save_complete_callback(self, metadata, file_path, crop_number):
        """Callback when individual crop save is complete"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.status_label.config(text="Ready")
        
        if metadata:
            filename = os.path.basename(file_path)
            # Show detailed save information
            details = (f"Crop #{crop_number} saved successfully!\n\n"
                      f"File: {filename}\n"
                      f"Resolution: {metadata['extraction_dpi']} DPI (Native Scale: {metadata['native_scale']:.1f}x)\n"
                      f"Dimensions: {metadata['width_pixels']}×{metadata['height_pixels']} pixels\n"
                      f"Physical Size: {metadata['width_inches']}×{metadata['height_inches']} inches\n"
                      f"Source: {metadata['source_quality']}\n"
                      f"Quality: {self._get_quality_rating(metadata['extraction_dpi'])}")
            
            messagebox.showinfo("Save Complete", details)
        else:
            messagebox.showerror("Save Failed", 
                               f"Failed to save crop #{crop_number}")
                               
    def _get_quality_rating(self, dpi):
        """Get quality rating based on DPI"""
        if dpi >= 600:
            return "Excellent (Print Ready)"
        elif dpi >= 300:
            return "Very Good (Print Quality)"
        elif dpi >= 200:
            return "Good (Web/Screen)"
        elif dpi >= 150:
            return "Fair (Low Print)"
        else:
            return "Poor (Screen Only)"
            
    def _individual_save_error_callback(self, error_msg, crop_number):
        """Callback when individual crop save fails"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.status_label.config(text="Ready")
        messagebox.showerror("Save Error", 
                           f"Failed to save crop #{crop_number}: {error_msg}")
                           
    def _individual_save_cancelled_callback(self):
        """Callback when individual crop save is cancelled by user"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.status_label.config(text="Ready")
    
    def load_pdf_from_url(self):
        """Load PDF from URL with streamlined interface"""
        # Create a custom dialog for better UX
        dialog = tk.Toplevel(self.root)
        dialog.title("Load PDF from URL")
        dialog.geometry("500x150")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Dialog content
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Enter PDF URL:").pack(anchor=tk.W, pady=(0, 5))
        
        url_var = tk.StringVar()
        url_entry = ttk.Entry(main_frame, textvariable=url_var, width=60)
        url_entry.pack(fill=tk.X, pady=(0, 10))
        url_entry.focus()
        
        # Try to get URL from clipboard
        try:
            clipboard_text = dialog.clipboard_get()
            if clipboard_text and ("http" in clipboard_text or "drive.google.com" in clipboard_text):
                url_var.set(clipboard_text)
                url_entry.select_range(0, tk.END)
        except:
            pass
        
        result = {'url': None}
        
        def load_url():
            result_url = url_var.get().strip()
            if result_url:
                result['url'] = result_url
            dialog.destroy()
            
        def cancel():
            dialog.destroy()
            
        # Handle Enter key
        def on_enter(event):
            load_url()
            
        url_entry.bind('<Return>', on_enter)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Load", command=load_url).pack(side=tk.RIGHT)
        
        # Wait for dialog to close
        dialog.wait_window()
        
        url = result['url']
        if not url:
            return
            
        # Convert Google Drive share links to direct download links automatically (silent)
        if "drive.google.com" in url and "/file/d/" in url:
            # Extract file ID from various Google Drive URL formats
            file_id = url.split("/file/d/")[1].split("/")[0]
            url = f"https://drive.google.com/uc?export=download&id={file_id}"
        elif "drive.google.com" in url:
            # Handle other Google Drive formats
            if "/view" in url:
                url = url.replace("/view?usp=sharing", "/export?format=pdf")
                url = url.replace("/view?usp=drivesdk", "/export?format=pdf")  
                url = url.replace("/view", "/export?format=pdf")
        
        self.status_label.config(text="Downloading PDF...")
        self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))
        self.progress_bar.start()
        
        # Download in background thread
        threading.Thread(target=self._download_pdf_thread, args=(url,), daemon=True).start()
        
    def _download_pdf_thread(self, url):
        """Download PDF from URL in background thread"""
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_path = temp_file.name
            temp_file.close()
            
            # Download file
            with urllib.request.urlopen(url) as response:
                with open(temp_path, 'wb') as f:
                    shutil.copyfileobj(response, f)
            
            # Load the downloaded PDF
            self.root.after(0, self._pdf_download_complete_callback, temp_path, url)
            
        except Exception as e:
            self.root.after(0, self._pdf_download_error_callback, str(e))
            
    def _pdf_download_complete_callback(self, temp_path, url):
        """Callback when PDF download is complete"""
        try:
            # Load the PDF
            self.pdf_document = fitz.open(temp_path)
            self.current_file_path = temp_path  # Store temp path for default naming
            self.current_page = 0
            self.pdf_images = []
            self.crop_selections = []
            self.crop_history = []
            
            # Update UI
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            
            # Extract filename from URL for display
            parsed_url = urllib.parse.urlparse(url)
            filename = os.path.basename(parsed_url.path) or "downloaded_pdf.pdf"
            if not filename.endswith('.pdf'):
                filename += '.pdf'
                
            self.status_label.config(text=f"Loaded: {filename}")
            
            # Update PDF info
            self.update_pdf_info_from_url(url, temp_path)
            
            # Clear and update crop list UI
            self.crop_frame.update_crop_list([])
            
            # Initialize view mode
            if self.continuous_mode:
                self.render_continuous_pages()
            else:
                self.render_current_page()
            
            # Update navigation
            self.update_navigation()
            
            # Auto-highlight visualization keywords
            if hasattr(self, 'viz_highlight_var'):
                self.highlight_visualization_keywords()
            
        except Exception as e:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.status_label.config(text="Ready")
            messagebox.showerror("Error", f"Failed to load downloaded PDF: {str(e)}")
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
                
    def _pdf_download_error_callback(self, error_msg):
        """Callback when PDF download fails"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.status_label.config(text="Ready")
        messagebox.showerror("Download Error", f"Failed to download PDF: {error_msg}")
        
    def update_pdf_info_from_url(self, url, file_path):
        """Update PDF info display for URL-loaded PDF"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        
        try:
            # Get basic file info
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            
            info = f"Source: URL\n"
            info += f"URL: {url[:50]}{'...' if len(url) > 50 else ''}\n"
            info += f"Pages: {self.pdf_document.page_count if self.pdf_document else 0}\n"
            info += f"Size: {size_mb:.1f} MB\n"
            
            # Get PDF metadata if available
            if self.pdf_document:
                metadata = self.pdf_document.metadata
                if metadata and metadata.get('title'):
                    info += f"Title: {metadata['title']}\n"
                if metadata and metadata.get('author'):
                    info += f"Author: {metadata['author']}\n"
                
            self.info_text.insert(tk.END, info)
        except Exception as e:
            self.info_text.insert(tk.END, f"Error reading PDF info: {str(e)}")
            
        self.info_text.config(state=tk.DISABLED)
        

        
    def undo_last_crop(self):
        """Undo the last crop selection"""
        if not self.crop_history:
            return
            
        # Remove the last crop
        last_crop_index = self.crop_history.pop()
        if last_crop_index < len(self.crop_selections):
            self.crop_selections.pop(last_crop_index)
            
            # Update crop list and redraw
            self.crop_frame.update_crop_list(self.crop_selections)
            self.redraw_crop_rectangles()
            
    def delete_selected_crop(self):
        """Delete the currently selected crop"""
        # Get selected crop from crop frame
        selection = self.crop_frame.crop_listbox.curselection()
        if selection:
            crop_index = selection[0]
            self.remove_crop(crop_index)
            
    def setup_bindings(self):
        """Setup keyboard bindings"""
        # File operations
        self.root.bind('<Control-o>', lambda e: self.open_pdf())
        self.root.bind('<Control-u>', lambda e: self.load_pdf_from_url())
        self.root.bind('<Control-e>', lambda e: self.export_all_crops())

        self.root.bind('<Control-q>', lambda e: self.root.quit())
        
        # View operations - zoom shortcuts removed
        
        # Crop operations
        self.root.bind('<Control-z>', lambda e: self.undo_last_crop())
        self.root.bind('<Delete>', lambda e: self.delete_selected_crop())
        self.root.bind('<BackSpace>', lambda e: self.delete_selected_crop())
        
        # Remove search keyboard bindings (search feature removed)
        
        # Navigation shortcuts
        self.root.bind("<Left>", lambda e: self.previous_page())
        self.root.bind("<Right>", lambda e: self.next_page())
        self.root.bind("<Home>", lambda e: self.first_page())
        self.root.bind("<End>", lambda e: self.last_page())
        self.root.bind("<Page_Up>", lambda e: self.previous_page())
        self.root.bind("<Page_Down>", lambda e: self.next_page())
        
    def get_default_crop_name(self):
        """Generate default crop name: [PDF filename without .pdf] + [_Q0001]"""
        # Get PDF filename without extension
        if hasattr(self, 'current_file_path') and self.current_file_path:
            # Handle both string paths and Path objects
            file_path = str(self.current_file_path)
            pdf_name = os.path.splitext(os.path.basename(file_path))[0]
        else:
            pdf_name = "pdf"
            
        # Count existing crops to get next number
        crop_count = len(self.crop_selections) + 1
        
        return f"{pdf_name}_Q{crop_count:02d}"
    
    def get_adaptive_crop_name(self):
        """Generate adaptive crop name based on learned patterns from user renames"""
        if not self.naming_learning_enabled:
            return self.get_default_crop_name()
        
        # Count existing crops to get next number
        crop_count = len(self.crop_selections) + 1
        
        # If we have a learned pattern, use it
        if self.learned_naming_pattern:
            try:
                return self.learned_naming_pattern.format(crop_count)
            except:
                # Fallback if format string is invalid
                pass
        
        # If we have a learned prefix, use it with Q pattern
        if self.learned_naming_prefix:
            return f"{self.learned_naming_prefix}Q{crop_count:02d}"
        
        # Fallback to default naming
        return self.get_default_crop_name()
    
    def learn_from_rename(self, crop_index, old_name, new_name):
        """Learn naming patterns from user renames"""
        if not self.naming_learning_enabled or not new_name or not old_name:
            return
        
        # Extract patterns from the rename
        pattern = self._extract_naming_pattern(crop_index, old_name, new_name)
        if pattern:
            self.learned_naming_prefix = pattern['prefix']
            self.learned_naming_pattern = pattern['full_pattern']
            print(f"DEBUG: Learned naming pattern: '{self.learned_naming_pattern}' from '{old_name}' -> '{new_name}'")
            
            # Update subsequent crops that haven't been manually renamed
            self._update_subsequent_crop_names(crop_index)
        else:
            print(f"DEBUG: Could not extract pattern from '{old_name}' -> '{new_name}'")
    
    def _extract_naming_pattern(self, crop_index, old_name, new_name):
        """Extract naming pattern from user rename"""
        import re
        
        # Look for number patterns in both names
        old_numbers = re.findall(r'\d+', old_name)
        new_numbers = re.findall(r'\d+', new_name)
        
        if not old_numbers or not new_numbers:
            # If no numbers, just use the new name as a prefix pattern
            if new_name:
                return {
                    'prefix': new_name + "_Q",
                    'suffix': "",
                    'full_pattern': new_name + "_Q{:02d}"
                }
            return None
        
        # Find the number that represents the crop sequence
        old_sequence = None
        new_sequence = None
        
        # Check if the last number in both names could be sequence numbers
        if old_numbers and new_numbers:
            old_last_num = int(old_numbers[-1])
            new_last_num = int(new_numbers[-1])
            
            # More flexible matching - check if either number matches expected crop number
            expected_old = crop_index + 1
            if old_last_num == expected_old or new_last_num == expected_old:
                old_sequence = old_last_num
                new_sequence = new_last_num
        
        if old_sequence is None:
            # Try to extract pattern without exact sequence matching
            # Use the last number from each name as the sequence number
            if old_numbers and new_numbers:
                old_sequence = int(old_numbers[-1])
                new_sequence = int(new_numbers[-1])
        
        if old_sequence is None:
            return None
        
        # Extract prefix (everything before the sequence number)
        old_str_before_num = old_name[:old_name.rfind(str(old_sequence))]
        new_str_before_num = new_name[:new_name.rfind(str(new_sequence))]
        
        # Extract suffix (everything after the sequence number)
        old_str_after_num = old_name[old_name.rfind(str(old_sequence)) + len(str(old_sequence)):]
        new_str_after_num = new_name[new_name.rfind(str(new_sequence)) + len(str(new_sequence)):]
        
        # Determine the number format by looking at the original formatting
        # Find how the number was formatted in the new name
        new_num_in_name = new_name[new_name.rfind(str(new_sequence)):new_name.rfind(str(new_sequence)) + len(str(new_sequence))]
        
        # Check if it has leading zeros
        if new_num_in_name.startswith('0') and len(new_num_in_name) > 1:
            # Preserve zero-padding format
            num_format = f"{{:0{len(new_num_in_name)}d}}"
        else:
            # Use 4-digit zero padding as default
            num_format = "{:02d}"
        
        return {
            'prefix': new_str_before_num,
            'suffix': new_str_after_num,
            'full_pattern': f"{new_str_before_num}{num_format}{new_str_after_num}"
        }
    
    def _update_subsequent_crop_names(self, changed_crop_index):
        """Update subsequent crop names that haven't been manually renamed"""
        if not self.learned_naming_pattern:
            return
        
        updated = False
        for i in range(changed_crop_index + 1, len(self.crop_selections)):
            crop = self.crop_selections[i]
            current_name = crop.get('custom_name', '')
            
            # Check if this crop still has a default-style name (not manually renamed by user)
            if self._is_default_style_name(current_name, i):
                try:
                    new_name = self.learned_naming_pattern.format(i + 1)
                    crop['custom_name'] = new_name
                    updated = True
                except:
                    break
        
        if updated:
            # Update the crop list display
            self.crop_frame.update_crop_list(self.crop_selections)
    
    def _is_default_style_name(self, name, crop_index):
        """Check if a name appears to be a default-generated name"""
        if not name:
            return True
        
        # Check if it matches the default pattern
        default_name = self.get_default_crop_name()
        expected_number = crop_index + 1
        
        # Simple heuristic: if it contains Q followed by the expected number, it's likely default
        import re
        pattern = f"Q{expected_number:02d}"
        return pattern in name
