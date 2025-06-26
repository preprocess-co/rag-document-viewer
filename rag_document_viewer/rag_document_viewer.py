import json, re, shutil, warnings
from subprocess import run
from bs4 import BeautifulSoup, Comment
from pathlib import Path

# Define supported sheet formats for special handling
SHEET_FORMATS = [".xlsx", ".xls", ".ods"]

class RAG_Document_Viewer:
    """
    RAG Document Viewer - Document Processing and Preview Generation Tool
    =======================================================================

    Developed by the Preprocess Team (https://preprocess.co)

    This module provides a comprehensive solution for converting various document formats 
    (PDF, Office documents, spreadsheets) into interactive HTML previews with advanced 
    features like chunk navigation, page numbering, zooming capabilities, and customizable 
    styling. The tool is specifically designed for RAG (Retrieval-Augmented Generation) 
    applications where document visualization and navigation are essential.

    Key Features:
    - Multi-format support: PDF, DOCX, XLSX, XLS, ODS, and more
    - Interactive HTML preview generation with embedded navigation
    - Customizable color schemes and styling options
    - Chunk-based navigation for large documents
    - Tabbed interface for multi-sheet spreadsheets
    - Responsive zoom controls and scrollbar bookmarks
    - Clean asset organization and optimized file structure

    The RAG_Document_Viewer class handles the entire pipeline from document conversion
    to final HTML preview generation, including asset management and cleanup operations.
    """
    def __init__(self, filepath, distpath=None, boxes: list[list[dict]] = None, configs={}):
        """
        Initialize the document viewer converter.
        
        Args:
            filepath (str): Path to the input document file
            distpath (str, optional): Output directory path. Defaults to input file directory
            boxes (list[list[dict]]): List of bounding box information for chunk highlighting
            configs (dict): Configuration options for styling and features
        """
        # Convert string paths to Path objects
        self._path_in = Path(filepath)
        self._path = Path(distpath) if distpath is not None else None
        
        self._file_name_in = self._path_in.name
        self._configs = configs
        
        # Boxes are required for RAG functionality - they define chunk boundaries
        if boxes is None:
            raise Exception("Please pass a boxes info to build the previewer.")
        self._boxes = boxes
        
        self._ext = self._path_in.suffix
        
        # Validate input file exists
        if not self._path_in.exists():
            raise FileNotFoundError(f"There is no file exist with name {self._file_name_in} to be converted")
        
        # Set default output path to input file directory if not specified
        if self._path is None:
            self._path = self._path_in.parent


    def convert_document(self):
        """
        Main method to orchestrate the conversion process.
        Handles preparation, generation, and cleanup in sequence.
        """
        print("** Preparing the input file")
        self._setup_input_file()
        print("** Generating the main previewer")
        self._create_html_preview()
        print("** Cleaning the files")
        self._organize_output_files()


    def _create_html_preview(self):
        """
        Generate the HTML previewer from the prepared document.
        Validates that the conversion was successful.
        """
        self._execute_html_conversion()
        
        # Verify HTML conversion was successful
        path_out = self._path / self._file_name_in
        html_path = path_out.with_suffix('.html')
        if not html_path.exists():
            raise Exception(f"faild to convert file {self._file_name_in} to html previewer.")


    def _setup_input_file(self):
        """
        Prepare the input file for conversion.
        Creates output directory and converts non-PDF files to PDF if needed.
        """
        print("  |_ Making a main dir to put all files inside it.")
        # Create output directory if it doesn't exist
        if not self._path.exists():
            self._path.mkdir()
        else:
            # Check if PDF version already exists in the directory
            pdf_name = self._path_in.stem + ".pdf"
            pdf_path = self._path / pdf_name
            if pdf_path.exists():
                print("  |_ There is pdf version exist inside the path, will be used.")
                self._file_name_in = pdf_name
                return

        # Handle different file types
        if self._ext in SHEET_FORMATS:
            # Spreadsheet files get special handling - copy directly
            print("  |_ It's a sheet, loading sheet previewer generator.")
            shutil.copy2(self._path_in, self._path)
            return
            
        elif self._ext == ".pdf":
            # PDF files are copied as-is
            print("  |_ It's already pdf, copy it inside and load previewer generator.")
            shutil.copy2(self._path_in, self._path)
            return
            
        elif self._ext != ".pdf":
            # Convert other formats to PDF first using LibreOffice
            print("  |_ Converting the file to pdf.")
            self._execute_pdf_conversion()
            # Verify PDF conversion was successful
            pdf_name = self._path_in.stem + ".pdf"
            pdf_path = self._path / pdf_name
            if not pdf_path.exists():
                raise Exception(f"The converted pdf version from {self._file_name_in} not exist.")
            self._file_name_in = pdf_name


    def _execute_html_conversion(self):
        """
        Convert the document to HTML format.
        Uses pdf2htmlEX for PDFs and LibreOffice for spreadsheets.
        """
        if self._ext not in SHEET_FORMATS:
            # Use pdf2htmlEX for PDF to HTML conversion with specific options
            command_tool = [
                "pdf2htmlEX",
                "--embed",           # Embed all resources
                "cfijo",            # Embed CSS, fonts, images, JavaScript, outline
                "--decompose-ligature", "1",  # Decompose ligatures for better text extraction
                "--tounicode", "1",  # Generate ToUnicode mapping
                "--debug", "1",      # Enable debug output
                "--tmp-dir", str(self._path),     # Temporary directory
                "--dest-dir", str(self._path),    # Output directory
                str(self._path / self._file_name_in)
            ]
        else:
            # Use LibreOffice for spreadsheet to HTML conversion
            command_tool = [
                "libreoffice",
                "--headless",        # Run without GUI
                "--convert-to", "html",  # Convert to HTML format
                "--outdir", str(self._path),  # Output directory
                str(self._path_in)
            ]

        # Execute the conversion command with timeout
        run(command_tool, capture_output=True, timeout=600)


    def _execute_pdf_conversion(self):
        """
        Convert document to PDF format using LibreOffice.
        Used as an intermediate step for non-PDF documents.
        """
        command_tool = [
                "libreoffice",
                "--headless",            # Run without GUI
                "--convert-to", "pdf",   # Convert to PDF format
                "--outdir", str(self._path),  # Output directory
                str(self._path_in)
            ]
        run(command_tool, capture_output=True, timeout=600)


    def _organize_output_files(self):
        """
        Clean up and organize the generated files.
        Different cleanup processes for spreadsheets vs regular documents.
        """
        if self._ext in SHEET_FORMATS:
            # Special cleanup for spreadsheet files
            self._process_spreadsheet_layout()
            
            # Add custom styles and scripts for spreadsheet viewer
            styles_path = self._path / "assets" / "styles" / "preprocess-custom-styles.css"
            scripts_path = self._path / "assets" / "scripts" / "preprocess-custom-scripts.js"
            self._write_file_content(styles_path, self._generate_css_styles())
            self._write_file_content(scripts_path, self._generate_javascript_code())
        else:
            # Regular document cleanup
            css, html = self._get_output_file_paths()
            css_content = self._read_file_content(css)
            html_content = self._read_file_content(html)
            
            # Skip if files couldn't be read
            if css_content == "" or html_content == "":
                return
            
            # Clean and enhance HTML content
            html_content = self._remove_unwanted_elements(html_content)
            html_content = self._inject_ui_components(html_content)
            
            self._write_file_content(html, html_content)
            
            # Add custom styles and scripts
            custom_styles_path = self._path / "preprocess-custom-styles.css"
            custom_scripts_path = self._path / "preprocess-custom-scripts.js"
            self._write_file_content(custom_styles_path, self._generate_css_styles())
            self._write_file_content(custom_scripts_path, self._generate_javascript_code())

            # Remove pdf2htmlEX generated files that aren't needed
            (self._path / "pdf2htmlEX-64x64.png").unlink(missing_ok=True)
            (self._path / "pdf2htmlEX.min.js").unlink(missing_ok=True)
            
            # Reorganize file structure
            self._organize_assets_structure()


    def _read_file_content(self, file_path) -> str:
        """
        Safely read file contents.
        
        Args:
            file_path: Path to the file to read (str or Path)
            
        Returns:
            str: File contents or empty string if file doesn't exist
        """
        path = Path(file_path)
        if not path.exists():
            return ""
        
        contents = ""
        with path.open('r') as f:
            contents = f.read()
        
        return contents


    def _write_file_content(self, file_path, contents: str):
        """
        Save content to a file.
        
        Args:
            file_path: Path where to save the file (str or Path)
            contents (str): Content to write to the file
        """
        path = Path(file_path)
        with path.open("w") as file:
            file.write(contents)
        return
    

    def _remove_unwanted_elements(self,  content: str) -> str:
        """
        Remove unwanted elements from HTML content.
        Removes sidebar, loading indicators, and scripts while adding compatibility script.
        
        Args:
            content (str): Original HTML content
            
        Returns:
            str: Cleaned HTML content
        """
        bs = BeautifulSoup(content, "html.parser")
        
        # Remove unwanted UI elements
        for x in bs.find_all("div", {"id": "sidebar"}):
            x.decompose()
        for x in bs.find_all("div", {"class": "loading-indicator"}):
            x.decompose()
        for x in bs.find_all("script"):
            x.decompose()
        
        # Remove all HTML comments
        for x in bs.find_all(string=lambda text: isinstance(text, Comment)):
            x.decompose()
        
        # Remove unwanted meta tag with specific name
        meta_tag = bs.find('meta', attrs={'name': 'generator'})
        if meta_tag:
            meta_tag.decompose()

        # Add compatibility script for older browsers
        bs.find("head").append(bs.new_tag("script", src="compatibility.min.js"))

        # Update title with filename
        title_tag = bs.find('title')
        if title_tag:
            title_tag.string = Path(self._file_name_in).stem

        return str(bs)


    def _organize_assets_structure(self):
        """
        Reorganize files into a structured directory layout.
        Creates assets folder with subdirectories for different file types.
        """
        assets_dir = self._path / "assets"
        
        # Remove existing assets directory
        if assets_dir.exists():
            shutil.rmtree(assets_dir)

        # Create organized directory structure
        images_dir = assets_dir / "images"
        styles_dir = assets_dir / "styles"
        scripts_dir = assets_dir / "scripts"
        fonts_dir = assets_dir / "fonts"

        assets_dir.mkdir()
        images_dir.mkdir()
        styles_dir.mkdir()
        scripts_dir.mkdir()
        fonts_dir.mkdir()

        # Move files to appropriate directories based on file extension
        for file_path in sorted(self._path.iterdir()):
            if file_path.name in [".", "..", ".DS_Store", "assets"]: 
                continue
            
            ext = file_path.suffix
            
            if ext in [".css", ".outline"]:
                # Fix font paths in CSS files
                if file_path.name == f"{Path(self._file_name_in).stem}.css":
                    content = self._read_file_content(file_path)
                    content = content.replace("src:url(f", "src:url(../fonts/f")
                    self._write_file_content(file_path, content)
                shutil.move(str(file_path), str(styles_dir))
            elif ext == ".js":
                shutil.move(str(file_path), str(scripts_dir))
            elif ext == ".png":
                shutil.move(str(file_path), str(images_dir))
            elif ext == ".woff":
                shutil.move(str(file_path), str(fonts_dir))
            elif ext == ".html":
                # Rename main HTML file to index.html
                dist = self._path / "index.html"
                shutil.move(str(file_path), str(dist))
            else:
                # Remove unneeded files
                file_path.unlink()

        # Fix asset links in the main HTML file
        self._update_asset_links(self._path / "index.html")
        

    def _get_output_file_paths(self) -> tuple[Path, Path]:
        """
        Get the expected CSS and HTML file paths based on input filename.
        
        Returns:
            tuple[Path, Path]: Paths to CSS and HTML files
        """
        general = Path(self._file_name_in).stem
        css_file = self._path / f"{general}.css"
        html_file = self._path / f"{general}.html"
        return css_file, html_file


    def _update_asset_links(self, path):
        """
        Update asset links in HTML to use the new directory structure.
        
        Args:
            path: Path to the HTML file to fix (str or Path)
        """
        file_path = Path(path)
        bs = BeautifulSoup(self._read_file_content(file_path), "html.parser")
        
        # Fix script source paths (except jQuery CDN)
        for x in bs.find_all("script"):
            if x.get("src") and not "jquery" in x['src']:
                x['src'] = f"./assets/scripts/{x['src']}"
        
        # Fix image source paths
        for x in bs.find_all("img"):
            x['src'] = f"./assets/images/{x['src']}"

        # Fix CSS link paths
        for x in bs.find_all("link"):
            if x.get("href") and x['href'][-4:] == ".css":
                x['href'] = f"./assets/styles/{x['href']}"
        
        self._write_file_content(file_path, str(bs))


    def _inject_ui_components(self,  content: str) -> str:
        """
        Add custom UI elements and functionality to the HTML document.
        Includes scrollbar, navigation controls, page numbers, and zoom controls.
        
        Args:
            content (str): Original HTML content
            
        Returns:
            str: Enhanced HTML content with added UI elements
        """
        bs = BeautifulSoup(content, "html.parser")        
        
        # Add custom scrollbar
        elements = """<div id="scrollbar"><div id="scroller"></div></div>"""
        
        # Add chunk navigation controls if enabled
        if self._configs.get("chunks_navigator", True) and len(self._boxes) > 0:
            chunk_navigator_text = self._configs.get("chunk_navigator_text", "Chunks %d of %d")
            chunk_navigator_text = [x.strip() for x in chunk_navigator_text.split("%d") if len(x.strip()) > 0]
            if len(chunk_navigator_text) < 2:
                chunk_navigator_text = ["Chunks", "of"]
            elements += f"""<div id="navigator"><span id="prevS" class="btn btn-link" onclick="prev_chunk()"> < </span><span class="btn like-link"><span id="s-text">{chunk_navigator_text[0]} <span id="currentS"></span> {chunk_navigator_text[1]} <span id="totalS"></span></span></span><span id="nextS" class="btn btn-link" onclick="next_chunk()"> > </span></div>"""
        
        # Add page number display if enabled
        if self._configs.get("page_number", True):
            elements += """<div id="page-number"></div>"""
            
        # Add zoom controls (initially hidden)
        elements += """<div id="zoom-out" class="zoom" style="display: none;">-</div><div id="zoom-in" class="zoom" style="display: none;">+</div>"""

        # Insert new elements at the beginning of body
        new_elements = BeautifulSoup(elements, "html.parser")
        bs.find("body").insert(0, new_elements)
        
        # Add custom JavaScript
        bs.find("body").append(bs.new_tag("script", src="preprocess-custom-scripts.js", type="text/javascript"))

        # Add jQuery and custom CSS to head
        bs.find("head").append(bs.new_tag("script", src="https://code.jquery.com/jquery-3.7.1.min.js", type="text/javascript"))
        bs.find("head").append(bs.new_tag("link", href="preprocess-custom-styles.css", rel="stylesheet"))

        return str(bs)


    def _generate_css_styles(self) -> str:
        """
        Generate custom CSS styles based on configuration.
        Supports different templates for sheets vs normal documents.
        
        Returns:
            str: Generated CSS content with configured colors and styles
        """
        # Load appropriate CSS template
        current_dir = Path(__file__).parent
        if self._ext in SHEET_FORMATS:
            styles = self._read_file_content(current_dir / "preprocess-custom-styles_sheet.css")
        else:
            styles = self._read_file_content(current_dir / "preprocess-custom-styles_normal.css")
        
        # Get color configuration with defaults
        main_color = self._configs.get("main_color", "#ff8000")
        gray_color = self._configs.get("background_color", "#dddddd")
        
        # Generate color variations (tints and shades)
        tint_main, shade_main = self._create_color_palette(main_color, 12)
        tint_gray, shade_gray = self._create_color_palette(gray_color, 12)

        # Configure page shadow
        page_shadow = self._configs.get("page_shadow", shade_gray[1])
        if (page_shadow[0] == "#" and len(page_shadow) <= 9): 
            page_shadow = f"{page_shadow} 0 0 0.8rem 0.2rem"

        # Configure control colors with proper contrast
        cbgc = self._configs.get("controls_bg_color", f"{shade_gray[3]}cc")
        if cbgc[0] == "#":
            cbgc = self._convert_hex_to_rgb(cbgc)
        ctxc = "#000" if self._calculate_contrast_ratio(cbgc, (0, 0, 0)) >= 4.5 else "#fff"

        # Replace placeholders in CSS template with configured values
        styles = styles.replace("{#_text_selection_color_#}", self._configs.get("text_selection_color", tint_main[2]))
        styles = styles.replace("{#_controls_bg_color_#}", self._configs.get("controls_bg_color", shade_gray[3]))
        styles = styles.replace("{#_controls_text_color_#}", self._configs.get("controls_text_color",  ctxc))
        styles = styles.replace("{#_page_shadow_#}", page_shadow)
        styles = styles.replace("{#_background_#}", self._configs.get("background_color", gray_color))
        styles = styles.replace("{#_bookmark_#}", self._configs.get("bookmark_color", main_color))
        styles = styles.replace("{#_scrollbar_#}", self._configs.get("scrollbar_color", shade_gray[1]))
        styles = styles.replace("{#_scroller_#}", self._configs.get("scroller_color", shade_gray[2]))
        styles = styles.replace("{#_highlight_page_outline_#}", self._configs.get("highlight_page_outline", tint_main[1]))
        
        # Create gradient styles for highlighting
        highlight_chunk_color = f"linear-gradient(100deg, {tint_main[-2]}, {tint_main[-1]}, {tint_main[-2]})"
        highlight_page_color = f"linear-gradient(100deg, {tint_main[-2]}aa, {tint_main[-1]}aa, {tint_main[-2]}aa, {tint_main[-1]}aa, {tint_main[-2]}aa)"

        styles = styles.replace("{#_highlight_page_color_#}", self._configs.get("highlight_page_color", highlight_page_color))
        styles = styles.replace("{#_highlight_chunk_color_#}", self._configs.get("highlight_chunk_color", highlight_chunk_color))

        return styles


    def _generate_javascript_code(self) -> str:
        """
        Generate custom JavaScript with configuration and box data.
        
        Returns:
            str: JavaScript content with configuration values and box data embedded
        """
        # Load appropriate JavaScript template
        current_dir = Path(__file__).parent
        if self._ext in SHEET_FORMATS:
            scripts = self._read_file_content(current_dir / "preprocess-custom-scripts_sheet.js")
        else:
            scripts = self._read_file_content(current_dir / "preprocess-custom-scripts_normal.js")
        
        # Get feature configuration
        show_single_chunk = self._configs.get("show_chunks_if_single", False) and len(self._boxes) > 0
        chunks_navigator = self._configs.get("chunks_navigator", True) and len(self._boxes) > 0
        page_number = self._configs.get("page_number", True)
        scrollbar_bookmarks = self._configs.get("scrollbar_navigator", True) and len(self._boxes) > 0

        # Replace placeholders in JavaScript template with configuration values
        scripts = scripts.replace("{#_show_single_chunk_#}", str(show_single_chunk).lower())
        scripts = scripts.replace("{#_chunks_navigator_#}", str(chunks_navigator).lower())
        scripts = scripts.replace("{#_show_page_number_#}", str(page_number).lower())
        scripts = scripts.replace("{#_scrollbar_bookmarks_#}", str(scrollbar_bookmarks).lower())
        
        # Embed box data as JSON for chunk highlighting functionality
        scripts = scripts.replace("{#_boxes_data_#}", json.dumps(self._boxes))

        return scripts    


    def _calculate_color_luminance(self, rgb: tuple[int, int, int]) -> float:
        """
        Calculate relative luminance of an RGB color for contrast calculations.
        
        Args:
            rgb (tuple[int, int, int]): RGB color values (0-255)
            
        Returns:
            float: Relative luminance value (0-1)
        """
        def chan(c):
            c = c / 255
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        r, g, b = map(chan, rgb)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b


    def _calculate_contrast_ratio(self, rgb1, rgb2) -> float:
        """
        Calculate contrast ratio between two RGB colors.
        Used to ensure text readability on background colors.
        
        Args:
            rgb1: First RGB color
            rgb2: Second RGB color
            
        Returns:
            float: Contrast ratio (1-21, higher is better contrast)
        """
        l1, l2 = sorted([self._calculate_color_luminance(rgb1), self._calculate_color_luminance(rgb2)], reverse=True)
        return (l1 + 0.05) / (l2 + 0.05)


    def _convert_hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        """
        Convert hex color to RGB tuple.
        
        Args:
            hex_color (str): Hex color string (e.g., "#FF0000" or "#F00")
            
        Returns:
            tuple[int, int, int]: RGB values (0-255)
        """
        hex_color = hex_color.lstrip("#")
        # Handle 3-character hex codes
        if len(hex_color) == 3:
            hex_color = "".join(2 * ch for ch in hex_color)
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


    def _convert_rgb_to_hex(self, rgb: tuple[int, int, int]) -> str:
        """
        Convert RGB tuple to hex color string.
        
        Args:
            rgb (tuple[int, int, int]): RGB values (0-255)
            
        Returns:
            str: Hex color string (e.g., "#ff0000")
        """
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


    def _create_color_palette(self, base_color: str, count: int = 5) -> tuple[list[str], list[str]]:
        """
        Generate tints (lighter) and shades (darker) of a base color.
        Used to create color palettes for theming.
        
        Args:
            base_color (str): Base hex color
            count (int): Number of variations to generate
            
        Returns:
            tuple[list[str], list[str]]: Lists of tint and shade hex colors
        """
        r, g, b = self._convert_hex_to_rgb(base_color)
        colors_tint = []
        colors_shade = []
        
        for i in range(count):
            factor = i / (count - 1)  # 0 to 1
            
            if i < count // 2:
                # Tints (mix with white) - lighter colors
                new_r = int(r + (255 - r) * factor * 2)
                new_g = int(g + (255 - g) * factor * 2)
                new_b = int(b + (255 - b) * factor * 2)
                colors_tint.append(self._convert_rgb_to_hex((new_r, new_g, new_b)))
            else:
                # Shades (mix with black) - darker colors
                factor = (i - count // 2) / (count - count // 2)
                new_r = int(r * (1 - factor))
                new_g = int(g * (1 - factor))
                new_b = int(b * (1 - factor))
                colors_shade.append(self._convert_rgb_to_hex((new_r, new_g, new_b)))
        
        return colors_tint, colors_shade


    def _process_spreadsheet_layout(self):
        """
        Cleans and reorganizes HTML files generated from spreadsheet formats (xlsx, xls, ods).
        This method creates a structured layout with separate sheets displayed in tabs and iframes.
        Only processes files if they are in SHEET_FORMATS, otherwise returns early.
        """
        if self._ext not in SHEET_FORMATS: 
            return

        # Convert path to Path object for better path handling
        base_path = Path(self._path)
        
        # Remove existing assets directory if it exists to start fresh
        assets_dir = base_path / "assets"
        if assets_dir.exists():
            shutil.rmtree(assets_dir)

        # Create the directory structure for organizing different asset types
        images_dir = assets_dir / "images"      # For PNG, JPG images
        styles_dir = assets_dir / "styles"      # For CSS files
        scripts_dir = assets_dir / "scripts"    # For JavaScript files
        sheets_dir = assets_dir / "sheets"      # For individual sheet HTML files

        # Create all required directories
        assets_dir.mkdir()
        images_dir.mkdir()
        styles_dir.mkdir()
        scripts_dir.mkdir()
        sheets_dir.mkdir()

        # Load the HTML content generated from the spreadsheet file
        filepath = base_path / self._file_name_in.replace(self._ext, ".html")
        content = self._read_file_content(filepath)

        # Get color configuration for styling, with defaults
        main_color = self._configs.get("main_color", "#ff8000")        # Orange default
        gray_color = self._configs.get("background_color", "#dddddd")   # Light gray default
        
        # Extract sheet names from HTML anchors - these become tab labels
        # Looks for patterns like <a href="#table...>Sheet Name</a>
        sheet_names = re.findall(r"<a href=\"#table.*>(.*)</a>", content, re.MULTILINE|re.IGNORECASE)
        
        # Find the start positions of each table by locating anchor tags
        # Pattern matches <a name="table...></a> which marks table beginnings
        starts = re.finditer(r"<a name=\"table.*</a>", content, re.MULTILINE|re.IGNORECASE)
        
        # Find the end positions of each table by locating HTML comments
        # Tables typically end with <!-- comments in LibreOffice HTML output
        ends = re.finditer(r"<!--", content, re.MULTILINE|re.IGNORECASE)
        
        # Convert iterators to lists of positions for table extraction
        table_starts = [match.end() for matchNum, match in enumerate(starts, start=1)]
        table_ends = [match.start() for matchNum, match in enumerate(ends, start=1)]
        
        # Build the tabstrip HTML - this creates the navigation tabs at the bottom
        # Contains styling for the tab appearance and behavior
        tabs = """<html><head><meta http-equiv="content-type" content="text/html; charset=utf-8"/>
                    <style>
                        a {
                            text-decoration: none;
                            color: #000000;
                            font-size: 10pt;
                            margin: auto 10px;
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
                        }
                        body {
                            margin: 0;
                            padding: 0;
                            background-color: {#_bg_color_#};
                        }

                        td {
                            background-color: {#_td_bg_color_#};
                            color: {#_td_bg_color_#};
                        }
                        .bold {
                            font-weight: bold;
                        }

                        .highlight {
                            background-color: {#_bookmark_#} !important;
                        }
                    </style></head><body><table border="0" cellspacing="1"><tr>"""
        
        # Replace color placeholders with actual configured colors
        tabs = tabs.replace("{#_bookmark_#}", self._configs.get("bookmark_color", main_color))
        tabs = tabs.replace("{#_bg_color_#}", self._configs.get("background_color", gray_color))
        tabs = tabs.replace("{#_td_bg_color_#}", self._configs.get("td_background_color", "#fff"))
        tabs = tabs.replace("{#_td_color_#}", self._configs.get("td_color", "#000"))
        tabs = tabs.replace("{#_td_color_#}", self._configs.get("td_color", "#000"))
        
        # Track the first sheet name to set as default view
        _1st_sheet = ""
        
        # Process each sheet: extract table content and create individual HTML files
        for i, sheet_name in enumerate(sheet_names):
            # Extract the HTML content for this specific table using start/end positions
            table_content = content[table_starts[i]:table_ends[i]]
            
            # Add basic Arial font styling to the extracted table
            table_content = "<style>* {font-family: Arial;}</style>" + table_content
            
            # Parse the HTML and fix image source paths to point to assets/images/
            bs = BeautifulSoup(table_content, "html.parser")
            for x in bs.find_all("img"):
                x['src'] = f"../images/{x['src']}"
            
            # Create filename for this sheet (lowercase with .html extension)
            sheet = f"{sheet_name.lower()}.html"
            if _1st_sheet == "": 
                _1st_sheet = sheet  # Remember first sheet for default loading
            
            # Save the individual sheet HTML file
            table_filepath = sheets_dir / sheet
            self._write_file_content(table_filepath, bs.prettify())
            
            # Add a tab button to the tabstrip for this sheet
            tabs += f"""<td nowrap><a href="{sheet}" target="sheet_preview">{sheet_name.upper()}</a></td>"""

        # Close the tabstrip HTML structure
        tabs += """</tr></table></body></html>"""
        # Save the complete tabstrip file
        self._write_file_content(sheets_dir / "tabstrip.html", tabs)

        # Create the main index.html file that combines everything using iframes
        # This creates a two-pane layout: main sheet viewer on top, tabs on bottom
        content = f"""<html>
                        <head>
                            <meta content="text/html; charset=utf-8" http-equiv="content-type" />
                            <title>
                            {self._file_name_in.replace(self._ext, "")}
                            </title>
                            <script src="https://code.jquery.com/jquery-3.7.1.min.js" type="text/javascript"></script>
                            <link href="./assets/styles/preprocess-custom-styles.css" rel="stylesheet" />
                        </head>

                        <body style="padding: 0; margin: 0;">"""
        
        # Add chunk navigation controls if enabled in configuration
        # This provides previous/next buttons for navigating between chunks
        if self._configs.get("chunks_navigator", True) and len(self._boxes) > 0:
            # Parse the chunk navigator text template, splitting on %d placeholders
            chunk_navigator_text = self._configs.get("chunk_navigator_text", "Chunks %d of %d")
            chunk_navigator_text = [x.strip() for x in chunk_navigator_text.split("%d") if len(x.strip()) > 0]
            if len(chunk_navigator_text) < 2:
                chunk_navigator_text = ["Chunks", "of"]  # Fallback text
            
            # Build the navigation HTML with dynamic text
            content += f"""<div id="navigator">
                            <span class="btn btn-link" id="prevS" onclick="prev_chunk()"> &lt; </span>
                            <span class="btn like-link">
                                <span id="s-text">{chunk_navigator_text[0]} <span id="currentS"></span> {chunk_navigator_text[1]} <span id="totalS"></span></span>
                            </span>
                            <span class="btn btn-link" id="nextS" onclick="next_chunk()"> &gt;</span>
                        </div>"""
        
        # Create the main layout with two iframes:
        # 1. sheet_preview: displays the selected sheet content (flex: 1 = takes remaining space)
        # 2. tabs: displays the tabstrip navigation (fixed height: 45px)
        # Also includes zoom controls positioned absolutely
        content += f"""<div style="height: 100%; width: 100%; display: flex; flex-direction: column; margin: 0; padding: 0;">
                                <iframe id="sheet_preview" name="sheet_preview" src="./assets/sheets/{_1st_sheet}" style="flex: 1; border: none;"></iframe>
                                <iframe id="tabs" name="tabs" src="./assets/sheets/tabstrip.html" style="height: 45px; border: none;"></iframe>
                            </div>
                            <div onclick="zoom_out()" id="zoom-out" class="zoom"> - </div>
                            <div onclick="zoom_in()" id="zoom-in" class="zoom"> + </div>
                        </body>
                        <script src="./assets/scripts/preprocess-custom-scripts.js" type="text/javascript"></script>
                    </html>"""
        
        # Parse and prettify the final HTML, then save as index.html
        bs = BeautifulSoup(content, "html.parser")
        self._write_file_content(base_path / "index.html", bs.prettify())

        # Clean up: remove the original HTML and spreadsheet files as they're no longer needed
        filepath.unlink()  # Remove the LibreOffice-generated HTML
        Path(str(filepath).replace(".html", self._ext)).unlink()  # Remove the original spreadsheet file

        # Organize remaining files into appropriate asset directories
        for file_path in sorted(base_path.iterdir()):
            # Skip directories, system files, and the assets folder
            if file_path.is_dir() or file_path.name in [".", "..", ".DS_Store", "assets"]: 
                continue
            
            ext = file_path.suffix  # Get file extension using pathlib
            
            if ext in [".png", ".jpg"]:
                # Move image files to images directory
                shutil.move(str(file_path), images_dir)
            elif ext == ".html":
                # Skip HTML files (index.html should remain in root)
                continue
            else: 
                # Remove any other unexpected files
                file_path.unlink()

def RAG_DV(file_path:str=None, store_path:str=None, boxes:list=[], **kwargs):
    """
    RAG_DV function - Wrapper for RAG_Document_Viewer.

    This function initializes and runs the RAG_Document_Viewer class to convert various
    document formats into interactive HTML previews. It handles initial validation
    of file paths, sets up the output directory, and passes configuration options
    and bounding box information for chunk highlighting.

    Developed by the Preprocess Team (https://preprocess.co)

    Args:
        file_path (str, optional): The path to the input document file. Defaults to None.
        store_path (str, optional): The directory where the converted output files
                                    will be stored. Defaults to None, in which case
                                    it creates a new directory named after the input file's
                                    stem within the input file's parent directory.
        boxes (list, optional): A list of bounding box information (dictionaries).
                                This is essential for the RAG functionality, as these
                                boxes define the boundaries of document "chunks" that
                                can be highlighted in the preview. Defaults to an empty list.
        **kwargs: Additional keyword arguments that are passed as configuration
                  options to the RAG_Document_Viewer for customization (e.g.,
                  styling, feature toggles).

    Raises:
        FileNotFoundError: If the specified `file_path` does not exist.
        FileExistsError: If the `store_path` directory already exists, preventing
                         accidental overwriting.

    Warns:
        UserWarning: If the `boxes` list is empty, indicating that no chunks
                     will be highlighted in the generated preview.
    """
    # Check if a file path is provided; raise an error if not.
    if file_path is None:
        raise FileNotFoundError(f"[{file_path}] not exist, please check.")

    # Convert the file_path string to a Path object for easier manipulation.
    file_path = Path(file_path)
    # Check if the input file actually exists; raise an error if not.
    if not file_path.exists():
        raise FileNotFoundError(f"[{file_path}] not exist, please check.")

    # Determine the store_path (output directory).
    if store_path is None:
        # If no store_path is provided, create one named after the input file's stem
        # within the input file's parent directory.
        store_path = Path(file_path.parent / file_path.stem)
    else:
        # If a store_path is provided, convert it to a Path object.
        store_path = Path(store_path)

    # Check if the store_path directory already exists.
    if not store_path.exists():
        # If it doesn't exist, create the directory and any necessary parent directories.
        store_path.mkdir(parents=True)
    else:
        # If the directory already exists, raise an error to prevent overwriting.
        raise FileExistsError(f"[{store_path}] already exist, please check.")

    # Check if the boxes list is empty. If so, issue a warning as chunk highlighting
    # will not occur without this information.
    if len(boxes) == 0:
        warnings.warn("The boxes length is empty, so there is no chunks will be highlited.")

    # Initialize an empty dictionary to store configuration options.
    configs = {}
    # Populate the configs dictionary with any additional keyword arguments passed to the function.
    for key, value in kwargs.items():
        configs[key] = value

    # Create an instance of the RAG_Document_Viewer class with the gathered parameters.
    ragdv = RAG_Document_Viewer(file_path, store_path, boxes, configs)
    # Start the document conversion process.
    ragdv.convert_document()