import sys
import os
import sqlite3
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QPlainTextEdit, QSplitter, QListWidget, QComboBox,
    QDialog, QMessageBox, QFileDialog, QFormLayout, QLineEdit, QDialogButtonBox,
    QFrame, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, QUrl, QRegularExpression, QMarginsF, QSizeF
from PySide6.QtGui import (
    QFont, QKeySequence, QShortcut, QSyntaxHighlighter, QTextCharFormat, 
    QColor, QPageLayout, QPageSize, QIcon, QDesktopServices
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage

# Import our new Markdown Engine
from markdown_pdf import MarkdownEngine 

class ZoomablePlainTextEdit(QPlainTextEdit):
    """Custom PlainTextEdit that natively supports zooming via mouse wheel and shortcuts."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_font_size = 15 # Starting size (~20px visually)
        self.update_font()
        
        # Keyboard shortcuts for zooming (Restricted to Widget focus to prevent conflicts)
        self.shortcut_zoom_in_1 = QShortcut(QKeySequence("Ctrl+="), self)
        self.shortcut_zoom_in_1.setContext(Qt.WidgetShortcut)
        self.shortcut_zoom_in_1.activated.connect(self.zoom_in)
        
        self.shortcut_zoom_in_2 = QShortcut(QKeySequence("Ctrl++"), self)
        self.shortcut_zoom_in_2.setContext(Qt.WidgetShortcut)
        self.shortcut_zoom_in_2.activated.connect(self.zoom_in)
        
        self.shortcut_zoom_out = QShortcut(QKeySequence("Ctrl+-"), self)
        self.shortcut_zoom_out.setContext(Qt.WidgetShortcut)
        self.shortcut_zoom_out.activated.connect(self.zoom_out)

    def update_font(self):
        font = QFont("Cascadia Code", self.current_font_size)
        self.setFont(font)
        # Force the font size dynamically so it bypasses global QSS overriding
        self.setStyleSheet(f"font-size: {self.current_font_size}pt; font-family: 'Cascadia Code';")

    def zoom_in(self):
        if self.current_font_size < 40:
            self.current_font_size += 1
            self.update_font()

    def zoom_out(self):
        if self.current_font_size > 8:
            self.current_font_size -= 1
            self.update_font()

    def wheelEvent(self, event):
        # Bitwise AND catches Ctrl even if NumLock or other modifiers are active
        if event.modifiers() & Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            # Normal scrolling behavior
            super().wheelEvent(event)

class EditLogDialog(QDialog):
    def __init__(self, log_id, current_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Editing Log {log_id}")
        self.resize(700, 500)
        self.log_id = log_id
        self.action = None  
        self.new_text = current_text
        
        layout = QVBoxLayout(self)
        
        # Use our new Zoomable editor
        self.editor = ZoomablePlainTextEdit()
        self.editor.setPlainText(current_text)
        layout.addWidget(self.editor)
        
        btn_layout = QHBoxLayout()
        self.btn_delete = QPushButton("🗑️ Delete Log")
        self.btn_cancel = QPushButton("Cancel (Esc)")
        self.btn_update = QPushButton("💾 Update (Ctrl+Enter)")
        
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch() 
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_update)
        
        layout.addLayout(btn_layout)
        
        self.btn_update.clicked.connect(self.accept_update)
        self.btn_delete.clicked.connect(self.accept_delete)
        self.btn_cancel.clicked.connect(self.reject)
        
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self.accept_update)
        QShortcut(QKeySequence("Ctrl+Enter"), self).activated.connect(self.accept_update)

    def accept_update(self):
        self.new_text = self.editor.toPlainText().strip()
        self.action = 'update'
        self.accept() 
        
    def accept_delete(self):
        reply = QMessageBox.question(self, 'Confirm Delete', 
                                     f'Are you sure you want to delete Log {self.log_id}?\nThis cannot be undone.',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.action = 'delete'
            self.accept()

class HelpGuideDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Report Generator Pro - User Guide")
        self.resize(900, 700)
        
        layout = QVBoxLayout(self)
        self.browser = QWebEngineView()
        
        self.html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #3E3C38; padding: 30px; background: #F4F3EE; }
                h1 { color: #4A90E2; border-bottom: 2px solid #4A90E2; padding-bottom: 10px; }
                h2 { color: #d33682; margin-top: 30px; }
                h3 { color: #859900; }
                code { background: #EAE7E0; padding: 2px 6px; border-radius: 4px; font-family: 'Cascadia Code', monospace; color: #b58900; }
                pre { background: #282a36; padding: 15px; border-radius: 8px; overflow-x: auto; }
                pre code { background: transparent; color: #f8f8f2; }
                .shortcut { font-weight: bold; background: #2aa198; color: white; padding: 2px 6px; border-radius: 4px; }
                .note { background: #E0DCD3; border-left: 4px solid #4A90E2; padding: 10px; margin: 15px 0; }
                ul { margin-bottom: 20px; }
                li { margin-bottom: 8px; }
                .feature-box { border: 1px solid #E0DCD3; padding: 15px; border-radius: 8px; background: white; margin-bottom: 15px;}
            </style>
        </head>
        <body>
            <h1>Report Generator Pro - Official User Guide</h1>
            <p>Welcome to the ultimate offline, zero-latency Markdown and LaTeX note-taking environment designed specifically for Data Analysts and Data Scientists.</p>

            <h2>1. The Core Philosophy (File Management)</h2>
            <div class="note"><strong>Golden Rule:</strong> 1 Session = 1 Database = 1 PDF Document.</div>
            <p>To eliminate file spaghetti, everything revolves around your selected project directory:</p>
            <ul>
                <li><strong>📝 New:</strong> Creates a new project. You choose a folder and specify a name (e.g., <code>EDA_Report</code>). The app generates a <code>.session/EDA_Report.db</code> file. This single file tracks your entire history for that specific document.</li>
                <li><strong>📂 Open:</strong> Resumes an existing project. Navigate into the <code>.session</code> folder and select your database file.</li>
            </ul>

            <h2>2. Writing and Previewing (The Editor)</h2>
            <p>The editor supports extended Markdown, Code Blocks, and LaTeX equations. It relies on a two-step rendering process:</p>
            <div class="feature-box">
                <h3>Keyboard Shortcuts</h3>
                <ul>
                    <li><span class="shortcut">Ctrl+S</span> <strong>(Live Draft):</strong> Instantly renders your current editor text into the preview window alongside your saved logs. <em>It does not save to the database.</em> Use this to test your math syntax or code formatting.</li>
                    <li><span class="shortcut">Ctrl+Shift+S</span> <strong>(Commit Log):</strong> Saves your current text into the database as a new discrete log, adding it to the history sidebar. Your text remains in the editor so you can continue writing seamlessly.</li>
                    <li><span class="shortcut">Ctrl+Shift+E</span> <strong>(Export):</strong> Generates the final PDF.</li>
                    <li><span class="shortcut">Ctrl</span> + <strong>Mouse Wheel Up/Down:</strong> Zoom in and out of the editor text dynamically. <span class="shortcut">Ctrl++</span> and <span class="shortcut">Ctrl+-</span> also work.</li>
                </ul>
            </div>

            <h2>3. Supported Syntax Elements</h2>
            <ul>
                <li><strong>Headers:</strong> Use <code># Header 1</code>, <code>## Header 2</code>.</li>
                <li><strong>Lists:</strong> Use <code>- Item</code> or <code>1. Item</code>.</li>
                <li><strong>Code Blocks:</strong> Use triple backticks (e.g., <code>```python</code>) for syntax-highlighted code.</li>
                <li><strong>Inline Math:</strong> Wrap your LaTeX in single dollar signs: <code>$E = mc^2$</code>.</li>
                <li><strong>Block Math:</strong> Wrap your LaTeX in double dollar signs: <code>$$\lim_{x \to \infty} f(x)$$</code>.</li>
                <li><strong>Dividers:</strong> Use <code>line{---}</code> to render a visual separation line.</li>
            </ul>

            <h2>4. Managing Logs (The Sidebar)</h2>
            <p>Your document is constructed block by block (logs). Open the <strong>☰ Logs</strong> sidebar to manage your document's structure:</p>
            <ul>
                <li><strong>Single Click:</strong> Smoothly scrolls the preview window to that exact section and temporarily highlights it with a gray pulse.</li>
                <li><strong>Double Click:</strong> Opens a dedicated Popup Editor. Here, you can fix typos or update code in that specific log. Press <span class="shortcut">Ctrl+Enter</span> to save changes, or click the Delete button to remove the log entirely.</li>
                <li><strong>🗑️ Clear Logs:</strong> Completely wipes the current database session, resetting your document to a blank state.</li>
            </ul>

            <h2>5. Custom Layouts & Page Sizes</h2>
            <p>Click the <strong>⚙️ Layout</strong> button to adjust the final PDF output. <em>Note: These settings strictly control the exported PDF document, not your application UI theme.</em></p>
            <ul>
                <li><strong>Title, Author & Date:</strong> Automatically generates a beautiful, standardized cover block at the very top of your PDF.</li>
                <li><strong>Scale (Dimensions):</strong> Choose standard paper formats (A4, A3, A5, Letter).</li>
                <li><strong>LinkedIn Carousel Formats:</strong> Select <strong>LinkedIn Square (1:1)</strong> or <strong>LinkedIn Portrait (4:5)</strong> to easily export beautifully proportioned slides for social media.</li>
                <li><strong>Custom Dimensions:</strong> Select "Custom" scale and define exact Width and Height dimensions in Points at the bottom of the form (1 pt = 1 pixel).</li>
                <li><strong>Theme Overrides:</strong> Configure Header font sizes (e.g., 24px) and hex colors precisely to match your brand or presentation style.</li>
            </ul>

            <h2>6. PDF Export Engine</h2>
            <p>Once your document looks perfect in the preview, press <span class="shortcut">Ctrl+Shift+E</span> or click <strong>📄 Export</strong>. The app silently compiles your layout settings and your entire log history, generating a flawless PDF directly next to your <code>.session</code> folder. If you edit your notes and export again, it cleanly overwrites the exact same file to prevent duplicates.</p>
        </body>
        </html>
        """
        self.browser.setHtml(self.html_content)
        layout.addWidget(self.browser)
        
        btn_layout = QHBoxLayout()
        self.btn_save_pdf = QPushButton("💾 Save Guide to Desktop")
        self.btn_close = QPushButton("Close")
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save_pdf)
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)
        
        self.btn_close.clicked.connect(self.reject)
        self.btn_save_pdf.clicked.connect(self.export_guide_pdf)
        
    def export_guide_pdf(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save User Guide", "Report_Generator_Pro_Guide.pdf", "PDF Files (*.pdf)")
        if not file_path: return
            
        def on_pdf_exported(success):
            if success:
                QMessageBox.information(self, "Success", f"User Guide saved to:\n{file_path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to save the User Guide.")
                
        layout = QPageLayout(QPageSize(QPageSize.A4), QPageLayout.Portrait, QMarginsF(15, 15, 15, 15))
        self.browser.page().printToPdf(file_path, layout)
        self.browser.page().pdfPrintingFinished.connect(on_pdf_exported)

class LayoutSettingsDialog(QDialog):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PDF Layout Settings")
        self.resize(400, 500)
        self.settings = current_settings.copy()
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.inputs = {}
        for key, value in self.settings.items():
            if key in ["scale", "theme", "code_theme"]:
                combo = QComboBox()
                if key == "scale": combo.addItems(["A4", "A3", "A5", "Letter", "LinkedIn Square (1:1)", "LinkedIn Portrait (4:5)", "Custom"])
                elif key == "theme": combo.addItems(["Standard", "Soft Paper", "Dracula"])
                elif key == "code_theme": combo.addItems(["Monokai", "Dracula", "GitHub"])
                combo.setCurrentText(value)
                self.inputs[key] = combo
            else:
                line_edit = QLineEdit(str(value))
                self.inputs[key] = line_edit
                
            label_text = key.replace("_", " ").title()
            form_layout.addRow(label_text + ":", self.inputs[key])
            
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def accept_settings(self):
        for key, widget in self.inputs.items():
            if isinstance(widget, QComboBox):
                self.settings[key] = widget.currentText()
            else:
                self.settings[key] = widget.text()
        self.accept()

class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, document, theme_colors, is_dark):
        super().__init__(document)
        self.rules = []

        c_heading = QColor("#bd93f9") if is_dark else QColor("#268bd2")
        c_list = QColor("#50fa7b") if is_dark else QColor("#859900")
        c_math = QColor("#ff79c6") if is_dark else QColor("#d33682")
        c_code = QColor("#8be9fd") if is_dark else QColor("#2aa198")
        c_bold = QColor(theme_colors["text"])

        fmt_heading = QTextCharFormat()
        fmt_heading.setForeground(c_heading)
        fmt_heading.setFontWeight(QFont.Bold)
        self.rules.append((QRegularExpression(r"^#+\s.*"), fmt_heading))

        fmt_list = QTextCharFormat()
        fmt_list.setForeground(c_list)
        fmt_list.setFontWeight(QFont.Bold)
        self.rules.append((QRegularExpression(r"^\s*[-*+]\s+"), fmt_list))
        self.rules.append((QRegularExpression(r"^\s*\d+\.\s+"), fmt_list))

        fmt_bold = QTextCharFormat()
        fmt_bold.setFontWeight(QFont.Bold)
        fmt_bold.setForeground(c_bold)
        self.rules.append((QRegularExpression(r"\*\*[^*]+\*\*"), fmt_bold))

        fmt_math_inline = QTextCharFormat()
        fmt_math_inline.setForeground(c_math)
        self.rules.append((QRegularExpression(r"\$[^$]+\$"), fmt_math_inline))

        fmt_code_inline = QTextCharFormat()
        fmt_code_inline.setForeground(c_code)
        self.rules.append((QRegularExpression(r"`[^`]+`"), fmt_code_inline))

        self.fmt_code_block = QTextCharFormat()
        self.fmt_code_block.setForeground(c_code)
        
        self.fmt_math_block = QTextCharFormat()
        self.fmt_math_block.setForeground(c_math)

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

        self.setCurrentBlockState(0)
        
        if text.strip().startswith("```"):
            self.setFormat(0, len(text), self.fmt_code_block)
            self.setCurrentBlockState(1 if self.previousBlockState() != 1 else 0)
        elif self.previousBlockState() == 1:
            self.setFormat(0, len(text), self.fmt_code_block)
            self.setCurrentBlockState(1)

        if self.currentBlockState() != 1:
            if text.strip() == "$$":
                self.setFormat(0, len(text), self.fmt_math_block)
                self.setCurrentBlockState(2 if self.previousBlockState() != 2 else 0)
            elif self.previousBlockState() == 2:
                self.setFormat(0, len(text), self.fmt_math_block)
                self.setCurrentBlockState(2)

class ReportGeneratorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Report Generator Pro - Unsaved Session")
        self.resize(1400, 800)
        self.is_dark_theme = True

        self.conn = None
        self.cursor = None
        self.current_session_dir = None
        self.current_session_name = None

        self.themes = {
            "light": {
                "bg": "#F4F3EE", "text": "#3E3C38", "border": "#E0DCD3",
                "button_bg": "#EAE7E0", "button_hover": "#DCD8D0", "accent": "#4A90E2"
            },
            "dark": {
                "bg": "#282a36", "text": "#f8f8f2", "border": "#44475a",
                "button_bg": "#44475a", "button_hover": "#6272a4", "accent": "#bd93f9"
            }
        }
        
        self.preview_themes = {
            "Standard": {"bg": "#ffffff", "text": "#000000"},
            "Soft Paper": {"bg": "#F4F3EE", "text": "#3E3C38"},
            "Dracula Soft": {"bg": "#282a36", "text": "#f8f8f2"},
            "Atom One Dark": {"bg": "#282c34", "text": "#abb2bf"}
        }

        self.md_engine = MarkdownEngine()

        self.setup_ui()
        self.apply_theme()
        self.setup_shortcuts()
        self.render_document()

    def setup_shortcuts(self):
        shortcut_save = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        shortcut_save.activated.connect(self.save_log)

        shortcut_preview = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut_preview.activated.connect(self.preview_only)

        shortcut_export = QShortcut(QKeySequence("Ctrl+Shift+E"), self)
        shortcut_export.activated.connect(self.export_pdf)

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # --- THE POLISHED TOOLBAR ---
        self.toolbar_frame = QFrame()
        self.toolbar_frame.setObjectName("toolbar")
        
        # FIX: Force the toolbar to stay compact and not expand vertically!
        self.toolbar_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.top_bar = QHBoxLayout(self.toolbar_frame)
        self.top_bar.setContentsMargins(8, 8, 8, 8)
        self.top_bar.setSpacing(8)

        # 1. Left Group: File & Navigation
        self.btn_toggle_logs = QPushButton("☰ Logs")
        self.btn_toggle_logs.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_logs.setToolTip("Toggle the logs sidebar history")
        self.btn_toggle_logs.clicked.connect(self.toggle_sidebar)

        self.btn_new = QPushButton("📝 New")
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.setToolTip("Create a new project session folder")
        self.btn_new.clicked.connect(self.new_session)
        
        self.btn_open = QPushButton("📂 Open")
        self.btn_open.setCursor(Qt.PointingHandCursor)
        self.btn_open.setToolTip("Open an existing project session")
        self.btn_open.clicked.connect(self.open_session)
        
        self.btn_clear_all = QPushButton("🗑️ Clear Logs")
        self.btn_clear_all.setCursor(Qt.PointingHandCursor)
        self.btn_clear_all.setToolTip("Purge all logs in the current session")
        self.btn_clear_all.clicked.connect(self.clear_all_logs)

        # 2. Middle Group: Theming & Settings
        self.btn_theme = QPushButton("☀️ Editor Theme")
        self.btn_theme.setCursor(Qt.PointingHandCursor)
        self.btn_theme.setToolTip("Toggle UI between Light and Dark mode")
        self.btn_theme.clicked.connect(self.toggle_theme)

        self.lbl_preview = QLabel("👁️ Preview:")
        self.lbl_preview.setObjectName("preview_label")
        
        self.combo_preview_theme = QComboBox()
        self.combo_preview_theme.setCursor(Qt.PointingHandCursor)
        self.combo_preview_theme.setToolTip("Change the color theme of the right preview pane")
        self.combo_preview_theme.addItems(["Standard", "Soft Paper", "Dracula Soft", "Atom One Dark"])
        self.combo_preview_theme.currentTextChanged.connect(self.render_document) 

        self.btn_layout = QPushButton("⚙️ Layout")
        self.btn_layout.setCursor(Qt.PointingHandCursor)
        self.btn_layout.setToolTip("Configure PDF page size, fonts, and colors")
        self.btn_layout.clicked.connect(self.open_layout_settings)

        self.btn_export = QPushButton("📄 Export")
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setToolTip("Export the current document to PDF (Ctrl+Shift+E)")
        self.btn_export.clicked.connect(self.export_pdf)
        
        # 3. Right Group: Actions & Help
        self.btn_github = QPushButton(" GitHub")
        self.btn_github.setCursor(Qt.PointingHandCursor)
        self.btn_github.setToolTip("Visit the open-source repository")
        self.btn_github.setIcon(QIcon("assets/github.svg"))
        # FIX: Actually link the GitHub button without markdown brackets
        self.btn_github.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/vasif-asadov1/report-generator")))
        
        self.btn_help = QPushButton("❓ Help")
        self.btn_help.setCursor(Qt.PointingHandCursor)
        self.btn_help.setToolTip("Open the User Guide and Manual")
        self.btn_help.clicked.connect(self.open_help_guide)

        # Add all to toolbar layout in a clean, professional grouping
        self.top_bar.addWidget(self.btn_toggle_logs)
        self.top_bar.addWidget(self.btn_new)
        self.top_bar.addWidget(self.btn_open)
        self.top_bar.addWidget(self.btn_clear_all)
        
        self.top_bar.addSpacing(20) # Add a clean gap before the middle tools
        
        self.top_bar.addWidget(self.btn_theme)
        self.top_bar.addWidget(self.lbl_preview)
        self.top_bar.addWidget(self.combo_preview_theme)
        self.top_bar.addWidget(self.btn_layout)
        self.top_bar.addWidget(self.btn_export)
        
        self.top_bar.addStretch() # Pushes GitHub and Help cleanly to the far right edge
        
        self.top_bar.addWidget(self.btn_github)
        self.top_bar.addWidget(self.btn_help)

        # Add Toolbar to main layout
        self.main_layout.addWidget(self.toolbar_frame)

        # --- MAIN CONTENT AREA ---
        self.content_layout = QHBoxLayout()
        self.main_layout.addLayout(self.content_layout)

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(250)
        self.sidebar.setVisible(False)
        self.sidebar.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
        self.sidebar.setSpacing(6) 
        self.sidebar.itemClicked.connect(self.scroll_to_log)
        self.sidebar.itemDoubleClicked.connect(self.open_edit_dialog)
        self.content_layout.addWidget(self.sidebar)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(8)
        
        # Use our new Zoomable editor
        self.editor = ZoomablePlainTextEdit()
        self.editor.setPlaceholderText("Write your markdown here...\nPress Ctrl+S to preview.\nPress Ctrl+Shift+S to save log.")

        colors = self.themes["light"] if not self.is_dark_theme else self.themes["dark"]
        self.highlighter = MarkdownHighlighter(self.editor.document(), colors, self.is_dark_theme)
        
        self.preview = QWebEngineView()
        self.preview.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.preview.loadFinished.connect(self.scroll_to_bottom)
        
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        self.splitter.setSizes([700, 700])
        self.content_layout.addWidget(self.splitter)

    # --- CORE WORKFLOW METHODS ---

    def preview_only(self):
        current_text = self.editor.toPlainText().strip()
        self.render_document(additional_text=current_text)

    def open_help_guide(self):
        dialog = HelpGuideDialog(self)
        dialog.setStyleSheet(self.styleSheet())
        dialog.exec()

    def new_session(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Create New Session", "", "Database Name (*.db)")
        if not file_path: return False
        
        dir_path = os.path.dirname(file_path)
        base_name = os.path.basename(file_path)
        if base_name.endswith('.db'): base_name = base_name[:-3]
            
        self.current_session_dir = dir_path
        self.current_session_name = base_name
        
        session_folder = os.path.join(dir_path, ".session")
        os.makedirs(session_folder, exist_ok=True)
        db_path = os.path.join(session_folder, f"{base_name}.db")
        
        self.connect_to_db(db_path, base_name)
        return True
    
    def open_layout_settings(self):
        if not self.conn:
            QMessageBox.warning(self, "Warning", "Please create or open a session first.")
            return
            
        self.cursor.execute("SELECT key, value FROM settings")
        current_settings = {row[0]: row[1] for row in self.cursor.fetchall()}
        
        dialog = LayoutSettingsDialog(current_settings, self)
        dialog.setStyleSheet(self.styleSheet())
        
        if dialog.exec():
            for k, v in dialog.settings.items():
                self.cursor.execute("UPDATE settings SET value = ? WHERE key = ?", (v, k))
            self.conn.commit()

    def open_session(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Existing Session", "", "Database Files (*.db)")
        if not file_path: return
        
        session_folder = os.path.dirname(file_path)
        self.current_session_dir = os.path.dirname(session_folder) 
        base_name = os.path.basename(file_path)
        if base_name.endswith('.db'): base_name = base_name[:-3]
            
        self.current_session_name = base_name
        self.connect_to_db(file_path, base_name)

    def connect_to_db(self, db_path, name):
        if self.conn: self.conn.close()
            
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")

        default_settings = {
            "title": name, "author": "", "date": "", "code_theme": "Monokai",
            "scale": "A4", "custom_width": "1080", "custom_height": "1080",
            "theme": "Standard", "font_size": "16px",
            "h1_size": "24px", "h2_size": "20px", "h3_size": "18px", "h4_size": "16px",
            "h1_color": "pink", "h2_color": "#FF4324", "h3_color": "cyan", "h4_color": "black"
        }
        
        for k, v in default_settings.items():
            self.cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
            
        self.conn.commit()
        
        self.setWindowTitle(f"Report Generator Pro - {name}")
        self.refresh_sidebar()
        self.render_document()

    def open_edit_dialog(self, item):
        log_id_str = item.text().split(":")[0] 
        log_id = int(log_id_str.replace("Log ", ""))
        
        self.cursor.execute("SELECT content FROM logs WHERE id = ?", (log_id,))
        row = self.cursor.fetchone()
        if not row: return
            
        dialog = EditLogDialog(log_id, row[0], self)
        dialog.setStyleSheet(self.styleSheet())
        
        if dialog.exec():
            if dialog.action == 'update':
                if dialog.new_text:
                    self.cursor.execute("UPDATE logs SET content = ? WHERE id = ?", (dialog.new_text, log_id))
                else:
                    self.cursor.execute("DELETE FROM logs WHERE id = ?", (log_id,))
            elif dialog.action == 'delete':
                self.cursor.execute("DELETE FROM logs WHERE id = ?", (log_id,))
                
            self.conn.commit()
            self.refresh_sidebar()
            self.render_document()

    def save_log(self):
        text = self.editor.toPlainText().strip()
        if not text: return
            
        if not self.conn:
            success = self.new_session()
            if not success: return 
            
        self.cursor.execute("INSERT INTO logs (content) VALUES (?)", (text,))
        self.conn.commit()
        
        self.refresh_sidebar()
        self.render_document()
    
    def scroll_to_log(self, item):
        try:
            log_id_str = item.text().split(":")[0] 
            log_id = int(log_id_str.replace("Log ", ""))
            
            js_code = f"""
            (function() {{
                document.querySelectorAll('.highlight-flash').forEach(el => {{
                    el.style.backgroundColor = '';
                    el.style.borderLeft = '';
                    el.classList.remove('highlight-flash');
                }});

                let startNode = document.getElementById('log-{log_id}');
                if (startNode) {{
                    startNode.scrollIntoView({{behavior: 'smooth', block: 'start'}});
                    
                    let curr = startNode.nextElementSibling;
                    while(curr && (!curr.id || !curr.id.startsWith('log-'))) {{
                        curr.classList.add('highlight-flash');
                        curr.style.transition = 'none'; 
                        
                        if (!curr.classList.contains('codehilite')) {{
                            curr.style.backgroundColor = 'rgba(136, 136, 136, 0.25)';
                            curr.style.borderRadius = '4px';
                        }}
                        
                        curr.style.borderLeft = '4px solid #888';
                        curr.style.paddingLeft = '10px';
                        
                        void curr.offsetWidth; 
                        
                        curr.style.transition = 'all 1.5s ease-out';
                        curr = curr.nextElementSibling;
                    }}
                    
                    setTimeout(() => {{
                        document.querySelectorAll('.highlight-flash').forEach(el => {{
                            el.style.backgroundColor = '';
                            el.style.borderLeftColor = 'transparent';
                        }});
                    }}, 600);
                }}
            }})();
            """
            self.preview.page().runJavaScript(js_code)
        except Exception:
            pass

    def refresh_sidebar(self):
        self.sidebar.clear()
        self.cursor.execute("SELECT id, content FROM logs ORDER BY id ASC")
        for row in self.cursor.fetchall():
            log_id = row[0]
            content = row[1].strip()
            
            if not content:
                preview = "Empty log"
            else:
                first_line = content.split('\n')[0].strip()
                
                if first_line.startswith('```'):
                    preview = "[Code Block]"
                elif first_line.startswith('$$'):
                    preview = "[Math Block]"
                elif first_line.startswith('line{---}'):
                    preview = "--- Divider ---"
                else:
                    preview = first_line.replace('#', '').strip()
                    if len(preview) > 22:
                        preview = preview[:19] + "..."
                    elif not preview.endswith('.') and len(preview) > 5:
                        preview += "."
                    
            self.sidebar.addItem(f"Log {log_id}: {preview}")

    def render_document(self, additional_text=""):
        logs = []
        if self.conn:
            self.cursor.execute("SELECT id, content FROM logs ORDER BY id ASC")
            for row in self.cursor.fetchall():
                logs.append(f'<div id="log-{row[0]}"></div>\n{row[1]}')
        
        if additional_text:
            logs.append(additional_text)
        
        if not logs:
            self.preview.setHtml("<h2 style='font-family: sans-serif; color: #888; text-align: center; margin-top: 50px;'>Write notes to see preview</h2>")
            return
            
        full_markdown = "\n\n".join(logs)
        theme_name = self.combo_preview_theme.currentText()
        colors = self.preview_themes.get(theme_name, self.preview_themes["Standard"])
        
        html = self.md_engine.convert_to_html(full_markdown, colors)
        self.preview.setHtml(html, QUrl("file:///"))

    def export_pdf(self):
        if not self.conn:
            QMessageBox.warning(self, "Warning", "No active session to export.")
            return
            
        pdf_path = os.path.join(self.current_session_dir, f"{self.current_session_name}.pdf")
        
        self.cursor.execute("SELECT key, value FROM settings")
        config = {row[0]: row[1] for row in self.cursor.fetchall()}
        
        self.cursor.execute("SELECT content FROM logs ORDER BY id ASC")
        logs = [row[0] for row in self.cursor.fetchall()]
        full_markdown = "\n\n".join(logs)
        
        pdf_colors = {"bg": "#ffffff", "text": "#000000"} 
        raw_html = self.md_engine.convert_to_html(full_markdown, pdf_colors)
        
        pdf_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: {config['font_size']}; color: black; background: white; padding: 40px; }}
                h1 {{ font-size: {config['h1_size']}; color: {config['h1_color']}; border-bottom: 2px solid {config['h1_color']}; }}
                h2 {{ font-size: {config['h2_size']}; color: {config['h2_color']}; }}
                h3 {{ font-size: {config['h3_size']}; color: {config['h3_color']}; }}
                h4 {{ font-size: {config['h4_size']}; color: {config['h4_color']}; }}
                .cover-page {{ text-align: center; margin-bottom: 50px; padding-bottom: 20px; border-bottom: 1px solid #ccc; }}
                .cover-title {{ font-size: 32px; font-weight: bold; color: {config['h1_color']}; }}
                .cover-meta {{ font-size: 18px; color: #555; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="cover-page">
                <div class="cover-title">{config['title']}</div>
                <div class="cover-meta">By: {config['author']} | Date: {config['date']}</div>
            </div>
            {raw_html}
        </body>
        </html>
        """
        
        self.pdf_engine = QWebEnginePage()
        self.pdf_engine.setHtml(pdf_html, QUrl("file:///"))
        
        def on_load_finished(ok):
            if ok:
                page_size = QPageSize(QPageSize.A4)
                
                if config['scale'] == "A3": 
                    page_size = QPageSize(QPageSize.A3)
                elif config['scale'] == "A5": 
                    page_size = QPageSize(QPageSize.A5)
                elif config['scale'] == "Letter": 
                    page_size = QPageSize(QPageSize.Letter)
                elif config['scale'] == "LinkedIn Square (1:1)":
                    page_size = QPageSize(QSizeF(1080, 1080), QPageSize.Unit.Point)
                elif config['scale'] == "LinkedIn Portrait (4:5)":
                    page_size = QPageSize(QSizeF(1080, 1350), QPageSize.Unit.Point)
                elif config['scale'] == "Custom":
                    try:
                        w = float(config.get('custom_width', 1080))
                        h = float(config.get('custom_height', 1080))
                    except ValueError:
                        w, h = 1080, 1080
                    page_size = QPageSize(QSizeF(w, h), QPageSize.Unit.Point)
                
                layout = QPageLayout(page_size, QPageLayout.Portrait, QMarginsF(15, 15, 15, 15))
                self.pdf_engine.printToPdf(pdf_path, layout)
                
        def on_pdf_exported(success):
            if success:
                QMessageBox.information(self, "Export Successful", f"Beautiful PDF created at:\n{pdf_path}")
            else:
                QMessageBox.critical(self, "Export Failed", "Failed to generate PDF.")
                
        self.pdf_engine.loadFinished.connect(on_load_finished)
        self.pdf_engine.pdfPrintingFinished.connect(on_pdf_exported)

    def scroll_to_bottom(self, ok):
        if ok:
            self.preview.page().runJavaScript("window.scrollTo(0, document.body.scrollHeight);")

    def clear_all_logs(self):
        reply = QMessageBox.question(self, 'Confirm Purge', 
                                     'Are you sure you want to delete ALL logs?\nThis will completely wipe your current database session.',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.cursor.execute("DELETE FROM logs")
            self.cursor.execute("DELETE FROM sqlite_sequence WHERE name='logs'")
            self.conn.commit()
            
            self.editor.clear()
            self.refresh_sidebar()
            self.render_document()

    # --- UI & STYLING METHODS ---

    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        self.apply_theme()

    def apply_theme(self):
        theme_name = "dark" if self.is_dark_theme else "light"
        colors = self.themes[theme_name]

        if hasattr(self, 'editor'):
            self.highlighter = MarkdownHighlighter(self.editor.document(), colors, self.is_dark_theme)

        # Polished, premium CSS
        stylesheet = f"""
            QWidget {{
                background-color: {colors["bg"]};
                color: {colors["text"]};
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
            }}
            
            /* --- POLISHED TOOLBAR STYLING --- */
            QFrame#toolbar {{
                background-color: {colors["button_bg"]};
                border: 1px solid {colors["border"]};
                border-radius: 8px;
            }}
            QFrame#toolbar QPushButton, QFrame#toolbar QComboBox {{
                background-color: transparent;
                border: 1px solid transparent;
                padding: 6px 14px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QFrame#toolbar QPushButton:hover, QFrame#toolbar QComboBox:hover {{
                background-color: {colors["button_hover"]};
                border: 1px solid {colors["border"]};
            }}
            QFrame#toolbar QLabel#preview_label {{
                font-weight: bold;
                padding-left: 10px;
                background: transparent;
            }}
            QComboBox::drop-down {{ border: none; }}
            
            /* --- TOOLTIPS STYLING --- */
            QToolTip {{
                background-color: {colors["bg"]};
                color: {colors["text"]};
                border: 1px solid {colors["accent"]};
                padding: 6px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: normal;
            }}

            /* --- GENERAL INPUT & LIST STYLING --- */
            QPlainTextEdit, QDialog QLineEdit {{
                background-color: {colors["bg"]};
                border: 2px solid {colors["border"]};
                border-radius: 8px;
                padding: 10px;
            }}
            QPlainTextEdit:focus, QDialog QLineEdit:focus {{
                border: 2px solid {colors["accent"]};
            }}
            
            QListWidget {{
                background-color: {colors["bg"]};
                border: 2px solid {colors["border"]};
                border-radius: 8px;
                padding: 8px;
                outline: 0; 
            }}
            QListWidget::item {{
                background-color: {colors["button_bg"]};
                border: 1px solid {colors["border"]};
                border-radius: 6px;
                padding: 12px 8px;
                color: {colors["text"]};
                margin-bottom: 4px;
            }}
            QListWidget::item:hover {{
                background-color: {colors["button_hover"]};
                border: 1px solid {colors["accent"]};
            }}
            QListWidget::item:selected {{
                background-color: {colors["button_hover"]};
                border-left: 4px solid {colors["accent"]};
                color: {colors["text"]};
            }}
            
            QSplitter::handle {{
                background-color: {colors["border"]};
                border-radius: 4px;
            }}
            
            /* Dialog Buttons Fallback */
            QDialog QPushButton {{
                background-color: {colors["button_bg"]};
                border: 1px solid {colors["border"]};
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QDialog QPushButton:hover {{
                background-color: {colors["button_hover"]};
            }}
        """
        self.setStyleSheet(stylesheet)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ReportGeneratorApp()
    window.show()
    sys.exit(app.exec())