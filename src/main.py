import sys
import os
import sqlite3
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QPlainTextEdit, QSplitter, QListWidget, QComboBox,
    QDialog, QMessageBox, QFileDialog, QFormLayout, QLineEdit, QDialogButtonBox,
    QFrame, QLabel, QSizePolicy, QStyledItemDelegate, QToolButton, QMenu, QInputDialog
)
from PySide6.QtCore import Qt, QUrl, QRegularExpression, QMarginsF, QSizeF, QSize
from PySide6.QtGui import (
    QFont, QKeySequence, QShortcut, QSyntaxHighlighter, QTextCharFormat, 
    QColor, QPageLayout, QPageSize, QIcon, QDesktopServices, QAction, QActionGroup
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage

# Import our new Markdown Engine
from markdown_pdf import MarkdownEngine 

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller onefile """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def build_tooltip(description, shortcut=None):
    if shortcut:
        return f"{description}\nShortcut: {shortcut}"
    return description

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

        self.btn_delete.setToolTip(build_tooltip("Delete the selected log entry permanently."))
        self.btn_cancel.setToolTip(build_tooltip("Close this editor without saving changes.", "Esc"))
        self.btn_update.setToolTip(build_tooltip("Save the edited log content.", "Ctrl+Enter"))
        
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
        
        self.html_content = r"""
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
            <p>This guide explains every major control in the app: how to create and open sessions, how logs work, how to use the editor and preview, what each button does, and which shortcuts are available.</p>

            <h2>1. First Time Use</h2>
            <div class="note"><strong>Core rule:</strong> your work is saved as a database file inside a visible <code>sessions</code> folder. You do not need hidden files.</div>
            <ul>
                <li><strong>New:</strong> create a project folder, then enter a session name. The app creates <code>sessions/&lt;name&gt;.db</code> inside that folder.</li>
                <li><strong>Open:</strong> choose your project folder, then select one of the existing <code>.db</code> files from the visible <code>sessions</code> folder.</li>
                <li><strong>Current session:</strong> the title bar shows the active session name.</li>
            </ul>

            <h2>2. Top Menu Buttons</h2>
            <div class="feature-box">
                <ul>
                    <li><strong>Logs:</strong> shows or hides the logs panel on the left side.</li>
                    <li><strong>New:</strong> creates a new session database in the visible <code>sessions</code> folder.</li>
                    <li><strong>Open:</strong> opens an existing session database from the visible <code>sessions</code> folder.</li>
                    <li><strong>Clear Logs:</strong> removes all saved logs from the current session.</li>
                    <li><strong>Layout:</strong> opens the PDF layout settings dialog.</li>
                </ul>
            </div>

            <h2>3. Left Sidebar Buttons</h2>
            <p>The left sidebar contains icon buttons for fast access to the most important actions.</p>
            <ul>
                <li><strong>Editor Theme:</strong> opens a popup list of UI themes and applies the selected theme immediately.</li>
                <li><strong>Preview Theme:</strong> opens a popup list of preview themes for the exported/previewed document.</li>
                <li><strong>Export:</strong> exports the current session as a PDF.</li>
                <li><strong>Help:</strong> opens this guide.</li>
                <li><strong>GitHub:</strong> opens the project repository in your browser.</li>
            </ul>

            <h2>4. Editor And Preview</h2>
            <p>The center of the app is split into two parts: the editor on the left and the live preview on the right.</p>
            <ul>
                <li><strong>Editor:</strong> type Markdown, LaTeX, code blocks, and normal text here.</li>
                <li><strong>Preview:</strong> shows the rendered result of the current editor text and all saved logs.</li>
                <li><strong>Zoom:</strong> use Ctrl with the mouse wheel inside the editor to zoom text in and out.</li>
            </ul>

            <h3>Supported Markdown And Content</h3>
            <ul>
                <li><strong>Headers:</strong> <code># H1</code>, <code>## H2</code>, <code>### H3</code>.</li>
                <li><strong>Lists:</strong> <code>- Item</code> or <code>1. Item</code>.</li>
                <li><strong>Code blocks:</strong> use triple backticks such as <code>```python</code>.</li>
                <li><strong>Inline math:</strong> <code>$E = mc^2$</code>.</li>
                <li><strong>Block math:</strong> <code>$$\lim_{x \to \infty} f(x)$$</code>.</li>
                <li><strong>Divider:</strong> use <code>line{---}</code>.</li>
                <li><strong>Images:</strong> standard markdown image syntax or raw HTML image tags.</li>
            </ul>

            <h2>5. Logs Workflow</h2>
            <p>Logs are the saved building blocks of your document.</p>
            <ul>
                <li><strong>Single click a log:</strong> scrolls the preview to that log and highlights it briefly.</li>
                <li><strong>Double click a log:</strong> opens the log editor dialog for updating or deleting that log.</li>
                <li><strong>Delete in log editor:</strong> removes that single log entry.</li>
                <li><strong>Clear Logs:</strong> removes all logs from the current session and resets the document history.</li>
            </ul>

            <h2>6. Layout Settings</h2>
            <p>The <strong>Layout</strong> dialog controls the PDF output, not the editor UI.</p>
            <ul>
                <li><strong>Title:</strong> shown on the PDF cover.</li>
                <li><strong>Author and Date:</strong> optional metadata fields for the PDF cover.</li>
                <li><strong>Scale:</strong> choose A4, A3, A5, Letter, LinkedIn Square (1:1), LinkedIn Portrait (4:5), or Custom.</li>
                <li><strong>Custom size:</strong> enter exact width and height when using Custom.</li>
                <li><strong>Theme:</strong> controls the document color palette in preview and export.</li>
                <li><strong>Code theme:</strong> controls syntax highlighting inside code blocks.</li>
                <li><strong>Heading colors:</strong> can inherit from the selected theme or use custom hex values.</li>
            </ul>

            <h2>7. Export</h2>
            <p>Export generates a PDF from all saved logs in the current session. The result uses the selected theme, code theme, and layout settings. Export overwrites the existing PDF for that session.</p>

            <h2>8. Shortcuts</h2>
            <div class="feature-box">
                <ul>
                    <li><span class="shortcut">Ctrl+S</span> preview the current editor text without saving it as a log.</li>
                    <li><span class="shortcut">Ctrl+Shift+S</span> save the current editor text as a log.</li>
                    <li><span class="shortcut">Ctrl+Shift+E</span> export the session to PDF.</li>
                    <li><span class="shortcut">Ctrl+N</span> create a new session.</li>
                    <li><span class="shortcut">Ctrl+O</span> open an existing session.</li>
                    <li><span class="shortcut">Ctrl+Shift+Delete</span> clear all logs.</li>
                    <li><span class="shortcut">Ctrl+,</span> open Layout settings.</li>
                    <li><span class="shortcut">Ctrl+L</span> toggle the Logs sidebar on or off.</li>
                    <li><span class="shortcut">Ctrl+Enter</span> save changes inside the log editor dialog.</li>
                    <li><span class="shortcut">Ctrl+Return</span> also saves changes inside the log editor dialog.</li>
                    <li><span class="shortcut">Esc</span> close the log editor dialog without saving.</li>
                    <li><span class="shortcut">Ctrl</span> + <strong>mouse wheel</strong> zoom the editor text.</li>
                </ul>
            </div>

            <h2>9. Suggested Workflow</h2>
            <ul>
                <li>Click <strong>New</strong> to create a fresh session.</li>
                <li>Type in the editor.</li>
                <li>Press <strong>Ctrl+S</strong> to preview a draft.</li>
                <li>Press <strong>Ctrl+Shift+S</strong> to save a log.</li>
                <li>Use the <strong>Logs</strong> sidebar to jump between saved sections.</li>
                <li>Adjust <strong>Layout</strong> and <strong>Preview Theme</strong> if needed.</li>
                <li>Click <strong>Export</strong> or press <strong>Ctrl+Shift+E</strong> when finished.</li>
            </ul>

            <h2>10. Troubleshooting</h2>
            <ul>
                <li>If Open does nothing, make sure the project folder contains a visible <code>sessions</code> folder and at least one <code>.db</code> file.</li>
                <li>If content appears twice, use <strong>Ctrl+S</strong> for preview and <strong>Ctrl+Shift+S</strong> only when you want to commit a log.</li>
                <li>If the preview looks different from the exported PDF, check the selected <strong>Layout</strong> scale and <strong>Preview Theme</strong>.</li>
                <li>If a log is wrong, double click it in the Logs sidebar and edit or delete it from the popup.</li>
            </ul>
        </body>
        </html>
        """
        self.browser.setHtml(self.html_content)
        layout.addWidget(self.browser)
        
        btn_layout = QHBoxLayout()
        self.btn_save_pdf = QPushButton("💾 Save Guide to Desktop")
        self.btn_close = QPushButton("Close")

        self.btn_save_pdf.setToolTip(build_tooltip("Export this user guide as a PDF file."))
        self.btn_close.setToolTip(build_tooltip("Close the user guide window."))
        
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
        self.parent_app = parent
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.inputs = {}
        for key, value in self.settings.items():
            if key in ["scale", "theme", "code_theme"]:
                combo = QComboBox()
                if key == "scale": combo.addItems(["A4", "A3", "A5", "Letter", "LinkedIn Square (1:1)", "LinkedIn Portrait (4:5)", "Custom"])
                elif key == "theme":
                    if self.parent_app:
                        combo.addItems(list(self.parent_app.themes.keys()))
                    else:
                        combo.addItems(["Standard", "Soft Paper", "Dracula"])
                elif key == "code_theme": 
                    combo.addItems([
                        "Atom One Dark", "Catppuccin Macchiato", "Catppuccin Frappe (Light)", 
                        "Dracula", "GitHub Dark", "GitHub Light", 
                        "Monokai", "Solarized Dark", "Solarized Light"
                    ])
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

        c_heading = QColor(theme_colors["accent"]) 
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

        self.conn = None
        self.cursor = None
        self.current_session_dir = None
        self.current_session_name = None
        self.is_preview_loaded = False 

        # --- UNIFIED PROFESSIONAL THEME PALETTES ---
        self.themes = {
            "Solarized Light": {"bg": "#fdf6e3", "text": "#586e75", "border": "#eee8d5", "button_bg": "#eee8d5", "button_hover": "#e8dfd6", "accent": "#268bd2", "is_dark": False},
            "Solarized Dark": {"bg": "#002b36", "text": "#839496", "border": "#073642", "button_bg": "#073642", "button_hover": "#586e75", "accent": "#268bd2", "is_dark": True},
            "GitHub Light": {"bg": "#ffffff", "text": "#24292e", "border": "#e1e4e8", "button_bg": "#f6f8fa", "button_hover": "#e1e4e8", "accent": "#0366d6", "is_dark": False},
            "GitHub Dark": {"bg": "#0d1117", "text": "#c9d1d9", "border": "#30363d", "button_bg": "#161b22", "button_hover": "#21262d", "accent": "#58a6ff", "is_dark": True},
            "Soft Paper": {"bg": "#F4F3EE", "text": "#3E3C38", "border": "#DCD8D0", "button_bg": "#EAE7E0", "button_hover": "#DCD8D0", "accent": "#4A90E2", "is_dark": False},
            "Monokai": {"bg": "#272822", "text": "#f8f8f2", "border": "#3e3d32", "button_bg": "#3e3d32", "button_hover": "#49483e", "accent": "#f92672", "is_dark": True},
            "Catppuccin Macchiato": {"bg": "#24273a", "text": "#cad3f4", "border": "#363a4f", "button_bg": "#1e2030", "button_hover": "#363a4f", "accent": "#8aadf4", "is_dark": True},
            "Catppuccin Frappe (Light)": {"bg": "#eff1f5", "text": "#4c4f69", "border": "#ccd0da", "button_bg": "#e6e9ef", "button_hover": "#dce0e8", "accent": "#1e66f5", "is_dark": False},
            "Atom One Dark": {"bg": "#282c34", "text": "#abb2bf", "border": "#3e4451", "button_bg": "#21252b", "button_hover": "#3e4451", "accent": "#61afef", "is_dark": True}
        }

        self.md_engine = MarkdownEngine()

        self.setup_ui()
        self.apply_theme()
        self.setup_shortcuts()
        self.render_document(preserve_scroll=False)

    def create_icon_button(self, icon_name, tooltip, handler):
        button = QToolButton()
        button.setCursor(Qt.PointingHandCursor)
        button.setToolTip(tooltip)
        button.setIcon(QIcon(resource_path(icon_name)))
        button.setIconSize(QSize(28, 28))
        button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        button.setAutoRaise(True)
        button.clicked.connect(handler)
        return button

    def open_theme_menu(self, target_combo, anchor_button):
        menu = QMenu(self)
        group = QActionGroup(menu)
        group.setExclusive(True)

        for theme_name in self.themes.keys():
            action = QAction(theme_name, menu)
            action.setCheckable(True)
            action.setChecked(theme_name == target_combo.currentText())
            action.triggered.connect(lambda checked=False, name=theme_name, combo=target_combo: combo.setCurrentText(name))
            group.addAction(action)
            menu.addAction(action)

        menu.exec(anchor_button.mapToGlobal(anchor_button.rect().bottomLeft()))

    def setup_shortcuts(self):
        self.shortcut_save = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        self.shortcut_save.activated.connect(self.save_log)

        self.shortcut_preview = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_preview.activated.connect(self.preview_only)

        self.shortcut_export = QShortcut(QKeySequence("Ctrl+Shift+E"), self)
        self.shortcut_export.activated.connect(self.export_pdf)

        self.shortcut_new = QShortcut(QKeySequence("Ctrl+N"), self)
        self.shortcut_new.activated.connect(self.new_session)

        self.shortcut_open = QShortcut(QKeySequence("Ctrl+O"), self)
        self.shortcut_open.activated.connect(self.open_session)

        self.shortcut_clear_logs = QShortcut(QKeySequence("Ctrl+Shift+Delete"), self)
        self.shortcut_clear_logs.activated.connect(self.clear_all_logs)

        self.shortcut_layout = QShortcut(QKeySequence("Ctrl+,"), self)
        self.shortcut_layout.activated.connect(self.open_layout_settings)

        self.shortcut_toggle_logs = QShortcut(QKeySequence("Ctrl+L"), self)
        self.shortcut_toggle_logs.activated.connect(self.toggle_sidebar)

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # --- THE POLISHED TOOLBAR ---
        self.toolbar_frame = QFrame()
        self.toolbar_frame.setObjectName("toolbar")
        self.toolbar_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.top_bar = QHBoxLayout(self.toolbar_frame)
        self.top_bar.setContentsMargins(8, 8, 8, 8)
        self.top_bar.setSpacing(8)

        # 1. Left Group: File & Navigation
        self.btn_toggle_logs = QPushButton("☰ Logs")
        self.btn_toggle_logs.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_logs.setToolTip(build_tooltip("Show or hide the logs sidebar."))
        self.btn_toggle_logs.clicked.connect(self.toggle_sidebar)

        self.btn_new = QPushButton("📝 New")
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.setToolTip(build_tooltip("Create a new project session."))
        self.btn_new.clicked.connect(self.new_session)
        
        self.btn_open = QPushButton("📂 Open")
        self.btn_open.setCursor(Qt.PointingHandCursor)
        self.btn_open.setToolTip(build_tooltip("Open an existing project session."))
        self.btn_open.clicked.connect(self.open_session)
        
        self.btn_clear_all = QPushButton("🗑️ Clear Logs")
        self.btn_clear_all.setCursor(Qt.PointingHandCursor)
        self.btn_clear_all.setToolTip(build_tooltip("Delete all logs in the current session."))
        self.btn_clear_all.clicked.connect(self.clear_all_logs)

        # 2. Middle Group: Theming & Settings
        self.combo_ui_theme = QComboBox()
        self.combo_ui_theme.setItemDelegate(QStyledItemDelegate()) # Force custom CSS on items
        self.combo_ui_theme.setCursor(Qt.PointingHandCursor)
        self.combo_ui_theme.addItems(list(self.themes.keys()))
        self.combo_ui_theme.setCurrentText("Atom One Dark")
        self.combo_ui_theme.currentTextChanged.connect(self.apply_theme) 

        self.combo_preview_theme = QComboBox()
        self.combo_preview_theme.setItemDelegate(QStyledItemDelegate()) # Force custom CSS on items
        self.combo_preview_theme.setCursor(Qt.PointingHandCursor)
        self.combo_preview_theme.addItems(list(self.themes.keys()))
        self.combo_preview_theme.setCurrentText("Soft Paper")
        self.combo_preview_theme.currentTextChanged.connect(self.on_preview_theme_changed) 

        self.btn_layout = QPushButton("⚙️ Layout")
        self.btn_layout.setCursor(Qt.PointingHandCursor)
        self.btn_layout.setToolTip(build_tooltip("Open PDF layout settings."))
        self.btn_layout.clicked.connect(self.open_layout_settings)

        # Add all to toolbar layout in a clean, professional grouping
        self.top_bar.addWidget(self.btn_toggle_logs)
        self.top_bar.addWidget(self.btn_new)
        self.top_bar.addWidget(self.btn_open)
        self.top_bar.addWidget(self.btn_clear_all)
        self.top_bar.addWidget(self.btn_layout)

        self.main_layout.addWidget(self.toolbar_frame)

        # --- MAIN CONTENT AREA ---
        self.content_layout = QHBoxLayout()
        self.main_layout.addLayout(self.content_layout)

        self.icon_sidebar = QFrame()
        self.icon_sidebar.setObjectName("iconSidebar")
        self.icon_sidebar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.icon_sidebar.setFixedWidth(76)

        sidebar_layout = QVBoxLayout(self.icon_sidebar)
        sidebar_layout.setContentsMargins(10, 12, 10, 12)
        sidebar_layout.setSpacing(10)

        self.btn_editor_theme = self.create_icon_button(
            "assets/editor_theme.svg",
            build_tooltip("Choose the editor theme."),
            lambda: self.open_theme_menu(self.combo_ui_theme, self.btn_editor_theme)
        )
        self.btn_preview_theme = self.create_icon_button(
            "assets/preview_theme.svg",
            build_tooltip("Choose the preview theme."),
            lambda: self.open_theme_menu(self.combo_preview_theme, self.btn_preview_theme)
        )
        self.btn_export = self.create_icon_button(
            "assets/export.svg",
            build_tooltip("Export the current document to PDF.", "Ctrl+Shift+E"),
            self.export_pdf
        )

        self.btn_help = self.create_icon_button(
            "assets/help.png",
            build_tooltip("Open the user guide."),
            self.open_help_guide
        )
        self.btn_github = self.create_icon_button(
            "assets/github.svg",
            build_tooltip("Open the project repository on GitHub."),
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/vasif-asadov1/report-generator"))
        )

        sidebar_layout.addWidget(self.btn_editor_theme)
        sidebar_layout.addWidget(self.btn_preview_theme)
        sidebar_layout.addWidget(self.btn_export)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(self.btn_help)
        sidebar_layout.addWidget(self.btn_github)

        self.content_layout.addWidget(self.icon_sidebar)

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
        
        self.editor = ZoomablePlainTextEdit()
        self.editor.setPlaceholderText("Write your markdown here...\nPress Ctrl+S to preview.\nPress Ctrl+Shift+S to save log.")

        self.preview = QWebEngineView()
        self.preview.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.preview.loadFinished.connect(self.on_preview_loaded)
        
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        self.splitter.setSizes([700, 700])
        self.content_layout.addWidget(self.splitter)

    # --- CORE WORKFLOW METHODS ---
    def on_preview_loaded(self, ok):
        if ok:
            self.is_preview_loaded = True

    def preview_only(self):
        current_text = self.editor.toPlainText().strip()
        if not current_text:
            return

        if self.conn:
            self.cursor.execute("SELECT content FROM logs ORDER BY id DESC LIMIT 1")
            row = self.cursor.fetchone()
            if row and row[0].strip() == current_text:
                self.render_document(preserve_scroll=True)
                return

        self.render_document(additional_text=current_text, preserve_scroll=True)

    def open_help_guide(self):
        dialog = HelpGuideDialog(self)
        dialog.setStyleSheet(self.styleSheet())
        dialog.exec()

    def new_session(self):
        project_dir = QFileDialog.getExistingDirectory(self, "Choose Project Folder", "")
        if not project_dir:
            return False

        base_name, ok = QInputDialog.getText(self, "Create New Session", "Session name:")
        if not ok:
            return False

        base_name = base_name.strip()
        if not base_name:
            QMessageBox.warning(self, "Warning", "Please enter a session name.")
            return False

        self.current_session_dir = project_dir
        self.current_session_name = base_name

        session_folder = os.path.join(project_dir, "sessions")
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
            
            # Sync the combo box to reflect Layout Settings changes
            self.combo_preview_theme.blockSignals(True)
            self.combo_preview_theme.setCurrentText(dialog.settings.get('theme', 'Soft Paper'))
            self.combo_preview_theme.blockSignals(False)
            
            # Rebuild full CSS blocks and layout rules natively
            self.render_document(preserve_scroll=False)

    def open_session(self):
        project_dir = self.current_session_dir
        if not project_dir or not os.path.isdir(project_dir):
            project_dir = QFileDialog.getExistingDirectory(self, "Choose Project Folder", "")
            if not project_dir:
                return

        session_folder = os.path.join(project_dir, "sessions")
        legacy_folder = os.path.join(project_dir, ".session")

        if os.path.isdir(session_folder):
            start_folder = session_folder
        elif os.path.isdir(legacy_folder):
            start_folder = legacy_folder
        else:
            QMessageBox.warning(
                self,
                "Warning",
                f"No sessions folder found in:\n{project_dir}\n\nExpected a visible 'sessions' folder."
            )
            return

        db_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Existing Session",
            start_folder,
            "Database Files (*.db)"
        )
        if not db_path:
            return

        base_name = os.path.splitext(os.path.basename(db_path))[0]
        self.current_session_dir = project_dir
        self.current_session_name = base_name
        self.connect_to_db(db_path, base_name)

    def connect_to_db(self, db_path, name):
        if self.conn: self.conn.close()
            
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")

        default_settings = {
            "title": name, "author": "", "date": "", "code_theme": "Atom One Dark",
            "scale": "A4", "custom_width": "1080", "custom_height": "1080",
            "theme": "Soft Paper", "font_size": "16px",
            "h1_size": "24px", "h2_size": "20px", "h3_size": "18px", "h4_size": "16px",
            "h1_color": "theme", "h2_color": "theme", "h3_color": "theme", "h4_color": "theme"
        }
        
        for k, v in default_settings.items():
            self.cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
            
        self.conn.commit()
        
        # Sync the combo box with the saved database theme
        self.cursor.execute("SELECT value FROM settings WHERE key='theme'")
        row = self.cursor.fetchone()
        if row:
            self.combo_preview_theme.blockSignals(True)
            self.combo_preview_theme.setCurrentText(row[0])
            self.combo_preview_theme.blockSignals(False)
            
        self.setWindowTitle(f"Report Generator Pro - {name}")
        self.refresh_sidebar()
        self.render_document(preserve_scroll=False)

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
            self.render_document(preserve_scroll=True)

    def save_log(self):
        text = self.editor.toPlainText().strip()
        if not text: return
            
        if not self.conn:
            success = self.new_session()
            if not success: return 

        self.cursor.execute("SELECT content FROM logs ORDER BY id DESC LIMIT 1")
        row = self.cursor.fetchone()
        if row and row[0].strip() == text:
            self.render_document(preserve_scroll=True)
            return
            
        self.cursor.execute("INSERT INTO logs (content) VALUES (?)", (text,))
        self.conn.commit()
        
        # We do NOT clear the editor so the user can continue logging manually.
        self.refresh_sidebar()
        self.render_document(preserve_scroll=True)
    
    def scroll_to_log(self, item):
        try:
            log_id_str = item.text().split(":")[0] 
            log_id = int(log_id_str.replace("Log ", ""))
            
            # Natively scrolls into the exact slice/slide since all logs are preserved structurally
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

    def on_preview_theme_changed(self, text):
        if self.conn:
            self.cursor.execute("UPDATE settings SET value = ? WHERE key = 'theme'", (text,))
            self.conn.commit()
        self.render_document(preserve_scroll=False)

    def get_code_theme_css(self, theme_name):
        themes = {
            "Monokai": { "bg": "#272822", "text": "#f8f8f2", "k": "#f92672", "s": "#e6db74", "c": "#75715e", "nf": "#a6e22e", "mi": "#ae81ff" },
            "Dracula": { "bg": "#282a36", "text": "#f8f8f2", "k": "#ff79c6", "s": "#f1fa8c", "c": "#6272a4", "nf": "#50fa7b", "mi": "#bd93f9" },
            "GitHub Light": { "bg": "#f6f8fa", "text": "#24292e", "k": "#d73a49", "s": "#032f62", "c": "#6a737d", "nf": "#6f42c1", "mi": "#005cc5" },
            "GitHub Dark": { "bg": "#0d1117", "text": "#c9d1d9", "k": "#ff7b72", "s": "#a5d6ff", "c": "#8b949e", "nf": "#d2a8ff", "mi": "#79c0ff" },
            "Solarized Light": { "bg": "#fdf6e3", "text": "#657b83", "k": "#859900", "s": "#2aa198", "c": "#93a1a1", "nf": "#268bd2", "mi": "#d33682" },
            "Solarized Dark": { "bg": "#002b36", "text": "#839496", "k": "#859900", "s": "#2aa198", "c": "#586e75", "nf": "#268bd2", "mi": "#d33682" },
            "Catppuccin Macchiato": { "bg": "#24273a", "text": "#cad3f4", "k": "#c6a0f6", "s": "#a6da95", "c": "#5b6078", "nf": "#8aadf4", "mi": "#f5a97f" },
            "Catppuccin Frappe (Light)": { "bg": "#eff1f5", "text": "#4c4f69", "k": "#ca9ee6", "s": "#a6d189", "c": "#9ca0b0", "nf": "#8caaee", "mi": "#ef9f76" },
            "Atom One Dark": { "bg": "#282c34", "text": "#abb2bf", "k": "#c678dd", "s": "#98c379", "c": "#5c6370", "nf": "#61afef", "mi": "#d19a66" }
        }
        c = themes.get(theme_name, themes["Atom One Dark"])
        
        return f"""
            pre, .codehilite {{ 
                background-color: {c['bg']} !important; 
                color: {c['text']} !important; 
                padding: 15px; 
                border-radius: 8px; 
                overflow-x: auto; 
                font-family: 'Cascadia Code', monospace;
                border: 1px solid rgba(128,128,128,0.2);
            }}
            code {{ 
                font-family: 'Cascadia Code', monospace; 
                background-color: rgba(128,128,128,0.15); 
                padding: 2px 4px; 
                border-radius: 4px; 
            }}
            pre code {{ 
                background-color: transparent; 
                padding: 0; 
                color: inherit;
            }}
            .codehilite .k, .codehilite .kd, .codehilite .kn, .codehilite .kp, .codehilite .kr, .codehilite .kt {{ color: {c['k']}; font-weight: bold; }}
            .codehilite .s, .codehilite .s1, .codehilite .s2, .codehilite .sb, .codehilite .sc, .codehilite .sd, .codehilite .si, .codehilite .se, .codehilite .sh, .codehilite .sx {{ color: {c['s']}; }}
            .codehilite .c, .codehilite .c1, .codehilite .ch, .codehilite .cm, .codehilite .cp, .codehilite .cpf, .codehilite .cs {{ color: {c['c']}; font-style: italic; }}
            .codehilite .nf, .codehilite .fm, .codehilite .nc, .codehilite .nd, .codehilite .ne, .codehilite .nn, .codehilite .nx {{ color: {c['nf']}; }}
            .codehilite .m, .codehilite .mb, .codehilite .mf, .codehilite .mh, .codehilite .mi, .codehilite .il, .codehilite .mo {{ color: {c['mi']}; }}
            .codehilite .o, .codehilite .ow, .codehilite .p, .codehilite .pi {{ color: {c['text']}; }}
        """

    def render_document(self, additional_text="", preserve_scroll=True):
        logs = []
        
        config = {
            "title": self.current_session_name or "Unsaved Document", 
            "author": "", "date": "", "scale": "A4",
            "custom_width": "1080", "custom_height": "1080",
            "font_size": "16px", "h1_size": "24px", "h2_size": "20px", 
            "h3_size": "18px", "h4_size": "16px",
            "h1_color": "theme", "h2_color": "theme", "h3_color": "theme", "h4_color": "theme"
        }
        
        if self.conn:
            self.cursor.execute("SELECT id, content FROM logs ORDER BY id ASC")
            for row in self.cursor.fetchall():
                logs.append(f'<div id="log-{row[0]}"></div>\n{row[1]}')
                
            self.cursor.execute("SELECT key, value FROM settings")
            for row in self.cursor.fetchall():
                config[row[0]] = row[1]
        
        if additional_text:
            logs.append(additional_text)
        
        if not logs:
            self.preview.setHtml("<h2 style='font-family: sans-serif; color: #888; text-align: center; margin-top: 50px;'>Write notes to see preview</h2>")
            return
            
        full_markdown = "\n\n".join(logs)
        theme_name = self.combo_preview_theme.currentText()
        colors = self.themes.get(theme_name, self.themes["Soft Paper"])
        
        raw_html = self.md_engine.convert_to_html(full_markdown, colors)
        
        # This isolated HTML string will be pushed to the JS DOM Engine instantly without reloading
        source_html = f"""
            <div class="cover-page">
                <div class="cover-title">{config['title']}</div>
                <div class="cover-meta">By: {config['author']} | Date: {config['date']}</div>
            </div>
            {raw_html}
        """

        if preserve_scroll and self.is_preview_loaded:
            # Silent zero-latency JS DOM Update
            js_code = f"if (typeof window.updateWorkspace === 'function') {{ window.updateWorkspace({json.dumps(source_html)}); }} else {{ 'NOT_READY'; }}"
            
            def js_callback(res):
                if res == 'NOT_READY':
                    self._apply_full_render(source_html, config, colors)
                    
            self.preview.page().runJavaScript(js_code, js_callback)
        else:
            # Full CSS/HTML rebuild for structural changes
            self._apply_full_render(source_html, config, colors)

    def _apply_full_render(self, source_html, config, colors):
        self.is_preview_loaded = False
        
        h1_color = colors['accent'] if config.get('h1_color', 'theme') == 'theme' else config['h1_color']
        h2_color = colors['text'] if config.get('h2_color', 'theme') == 'theme' else config['h2_color']
        h3_color = colors['text'] if config.get('h3_color', 'theme') == 'theme' else config['h3_color']
        h4_color = colors['text'] if config.get('h4_color', 'theme') == 'theme' else config['h4_color']
        
        scale = config.get("scale", "A4")
        if scale == "A3": 
            page_w, page_h = "1123px", "1587px"
        elif scale == "A5": 
            page_w, page_h = "559px", "794px"
        elif scale == "Letter": 
            page_w, page_h = "816px", "1056px"
        elif scale == "LinkedIn Square (1:1)": 
            page_w, page_h = "1080px", "1080px"
        elif scale == "LinkedIn Portrait (4:5)": 
            page_w, page_h = "1080px", "1350px"
        elif scale == "Custom":
            try:
                w = float(config.get('custom_width', 1080))
                h = float(config.get('custom_height', 1080))
            except ValueError:
                w, h = 1080, 1080
            page_w, page_h = f"{w}px", f"{h}px"
        else: 
            page_w, page_h = "794px", "1123px" 
            
        outer_bg = "radial-gradient(circle at 50% 50%, #4b5563 0%, #111827 100%)" if colors.get("is_dark", False) else "radial-gradient(circle at 50% 50%, #9ca3af 0%, #4b5563 100%)"
        
        try:
            usable_h = float(page_h.replace('px', '')) - 120 
        except:
            usable_h = 1003 

        code_theme_name = config.get("code_theme", "Atom One Dark")
        code_css = self.get_code_theme_css(code_theme_name)
        
        page_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    background: {outer_bg};
                    background-attachment: fixed;
                    margin: 0;
                    padding: 40px 0; 
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 40px; 
                }}
                .slide {{
                    background-color: {colors['bg']};
                    width: {page_w};
                    min-height: {page_h};
                    box-shadow: 0 15px 40px rgba(0,0,0,0.6); 
                    padding: 60px; 
                    box-sizing: border-box;
                    color: {colors['text']};
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: {config['font_size']};
                    position: relative; 
                }}
                .slide-content {{
                    width: 100%;
                    height: 100%;
                }}
                .slide h1 {{ font-size: {config['h1_size']}; color: {h1_color}; border-bottom: 2px solid {h1_color}; margin-top: 0; }}
                .slide h2 {{ font-size: {config['h2_size']}; color: {h2_color}; }}
                .slide h3 {{ font-size: {config['h3_size']}; color: {h3_color}; }}
                .slide h4 {{ font-size: {config['h4_size']}; color: {h4_color}; }}
                .cover-page {{ text-align: center; margin-bottom: 50px; padding-bottom: 20px; border-bottom: 1px solid #ccc; }}
                .cover-title {{ font-size: 32px; font-weight: bold; color: {h1_color}; }}
                .cover-meta {{ font-size: 18px; color: {colors['text']}; opacity: 0.7; margin-top: 10px; }}
                img {{ max-width: 100%; max-height: {usable_h}px; object-fit: contain; }} 
                {code_css}
            </style>
        </head>
        <body>
            <div id="source-content" style="display: none;">
                {source_html}
            </div>
            
            <div id="workspace" style="display: flex; flex-direction: column; gap: 40px; align-items: center;"></div>

            <script>
                function runPaginator() {{
                    const source = document.getElementById('source-content');
                    const workspace = document.getElementById('workspace');
                    workspace.innerHTML = '';
                    
                    const maxH = {usable_h};
                    const splitTags = ['UL', 'OL', 'LI', 'DIV', 'BLOCKQUOTE', 'TABLE', 'TBODY', 'THEAD', 'TR'];

                    function isMeaningful(n) {{
                        return !(n.nodeType === Node.TEXT_NODE && n.textContent.trim() === '');
                    }}

                    function hasContent(node) {{
                        if (node.nodeType === Node.TEXT_NODE && node.textContent.trim() !== '') return true;
                        if (node.nodeType === Node.ELEMENT_NODE) {{
                            if (['IMG', 'BR', 'HR', 'IFRAME'].includes(node.tagName)) return true;
                            let children = node.childNodes;
                            for (let i = 0; i < children.length; i++) {{
                                if (hasContent(children[i])) return true;
                            }}
                        }}
                        return false;
                    }}

                    function createSlide() {{
                        const slide = document.createElement('div');
                        slide.className = 'slide';
                        const content = document.createElement('div');
                        content.className = 'slide-content';
                        slide.appendChild(content);
                        workspace.appendChild(slide);
                        return content;
                    }}

                    let currentRoot = createSlide();

                    function processNode(node, currentParent, root) {{
                        if (!isMeaningful(node)) return {{ parent: currentParent, root: root }};
                        
                        currentParent.appendChild(node);
                        
                        if (root.scrollHeight > maxH) {{
                            currentParent.removeChild(node);
                            let isEmpty = !hasContent(root);
                            
                            if (node.nodeType === Node.ELEMENT_NODE && splitTags.includes(node.tagName) && node.childNodes.length > 0) {{
                                let splitContainer = node.cloneNode(false);
                                splitContainer.innerHTML = '';
                                currentParent.appendChild(splitContainer);
                                
                                let children = Array.from(node.childNodes);
                                let currentCont = splitContainer;
                                let curRoot = root;
                                
                                for (let child of children) {{
                                    let res = processNode(child, currentCont, curRoot);
                                    currentCont = res.parent;
                                    curRoot = res.root;
                                }}
                                
                                if (!hasContent(splitContainer) && splitContainer.parentNode) {{
                                    splitContainer.parentNode.removeChild(splitContainer);
                                }}
                                return {{ parent: currentCont.parentNode, root: curRoot }};
                            }} else {{
                                if (isEmpty) {{
                                    currentParent.appendChild(node);
                                    return {{ parent: currentParent, root: root }};
                                }} else {{
                                    let newRoot = createSlide();
                                    let path = [];
                                    let temp = currentParent;
                                    while(temp !== root && temp !== null) {{
                                        path.unshift(temp);
                                        temp = temp.parentNode;
                                    }}
                                    let newParent = newRoot;
                                    for (let p of path) {{
                                        let clone = p.cloneNode(false);
                                        clone.innerHTML = '';
                                        newParent.appendChild(clone);
                                        newParent = clone;
                                    }}
                                    newParent.appendChild(node);
                                    return {{ parent: newParent, root: newRoot }};
                                }}
                            }}
                        }}
                        return {{ parent: currentParent, root: root }};
                    }}

                    const nodes = Array.from(source.childNodes);
                    let curRoot = currentRoot;

                    for (let i = 0; i < nodes.length; i++) {{
                        let res = processNode(nodes[i], curRoot, curRoot);
                        curRoot = res.root;
                    }}
                }}

                window.onload = function() {{
                    runPaginator();
                }};

                // Secure JavaScript Morpher API invoked by Python securely
                window.updateWorkspace = function(newHtml) {{
                    let scrollY = window.scrollY; // Capture precise scroll immediately
                    document.getElementById('source-content').innerHTML = newHtml;
                    runPaginator();
                    window.scrollTo(0, scrollY); // Restore instantaneously so the view never moves
                    return 'OK';
                }};
            </script>
        </body>
        </html>
        """
        self.preview.setHtml(page_html, QUrl("file:///"))

    def export_pdf(self):
        if not self.conn:
            QMessageBox.warning(self, "Warning", "No active session to export.")
            return
            
        # Ensure the PDF path uses the base folder, correctly placing the file natively in your project folder
        pdf_path = os.path.join(self.current_session_dir, f"{self.current_session_name}.pdf")
        
        self.cursor.execute("SELECT key, value FROM settings")
        config = {row[0]: row[1] for row in self.cursor.fetchall()}
        
        self.cursor.execute("SELECT content FROM logs ORDER BY id ASC")
        logs = [row[0] for row in self.cursor.fetchall()]
        full_markdown = "\n\n".join(logs)
        
        # Match the exported PDF strictly to the active unified config theme!
        theme_name = self.combo_preview_theme.currentText()
        pdf_colors = self.themes.get(theme_name, self.themes["Soft Paper"])
        
        raw_html = self.md_engine.convert_to_html(full_markdown, pdf_colors)
        
        code_theme_name = config.get("code_theme", "Atom One Dark")
        code_css = self.get_code_theme_css(code_theme_name)
        
        h1_color = pdf_colors['accent'] if config.get('h1_color', 'theme') == 'theme' else config['h1_color']
        h2_color = pdf_colors['text'] if config.get('h2_color', 'theme') == 'theme' else config['h2_color']
        h3_color = pdf_colors['text'] if config.get('h3_color', 'theme') == 'theme' else config['h3_color']
        h4_color = pdf_colors['text'] if config.get('h4_color', 'theme') == 'theme' else config['h4_color']
        
        pdf_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{ margin: 0; }} /* Native Qt pagination requires zeroing the CSS page margin */
                body {{ 
                    margin: 0;
                    box-sizing: border-box;
                    font-family: 'Segoe UI', Arial, sans-serif; 
                    font-size: {config['font_size']}; 
                    color: {pdf_colors['text']}; 
                    background: {pdf_colors['bg']}; 
                }}
                h1 {{ font-size: {config['h1_size']}; color: {h1_color}; border-bottom: 2px solid {h1_color}; }}
                h2 {{ font-size: {config['h2_size']}; color: {h2_color}; }}
                h3 {{ font-size: {config['h3_size']}; color: {h3_color}; }}
                h4 {{ font-size: {config['h4_size']}; color: {h4_color}; }}
                .cover-page {{ text-align: center; margin-bottom: 50px; padding-bottom: 20px; border-bottom: 1px solid #ccc; }}
                .cover-title {{ font-size: 32px; font-weight: bold; color: {h1_color}; }}
                .cover-meta {{ font-size: 18px; color: {pdf_colors['text']}; opacity: 0.7; margin-top: 10px; }}
                img {{ max-width: 100%; }}
                {code_css}
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
                scale_val = config.get('scale', 'A4')
                page_size = QPageSize(QPageSize.A4) 
                
                # MATHEMATICALLY PERFECT PX TO POINT SCALING (pt = px * 0.75)
                if scale_val == "A3": 
                    page_size = QPageSize(QPageSize.A3)
                elif scale_val == "A5": 
                    page_size = QPageSize(QPageSize.A5)
                elif scale_val == "Letter": 
                    page_size = QPageSize(QPageSize.Letter)
                elif scale_val == "LinkedIn Square (1:1)":
                    page_size = QPageSize(QSizeF(810, 810), QPageSize.Unit.Point)
                elif scale_val == "LinkedIn Portrait (4:5)":
                    page_size = QPageSize(QSizeF(810, 1012.5), QPageSize.Unit.Point)
                elif scale_val == "Custom":
                    try:
                        w = float(config.get('custom_width', 1080))
                        h = float(config.get('custom_height', 1080))
                    except ValueError:
                        w, h = 1080, 1080
                    page_size = QPageSize(QSizeF(w * 0.75, h * 0.75), QPageSize.Unit.Point)
                
                # Enforce physical PDF margins (equivalent to the 60px WYSIWYG padding)
                layout = QPageLayout(page_size, QPageLayout.Portrait, QMarginsF(15, 15, 15, 15), QPageLayout.Millimeter)
                self.pdf_engine.printToPdf(pdf_path, layout)
                
        def on_pdf_exported(success):
            if success:
                QMessageBox.information(self, "Export Successful", f"Beautiful PDF created at:\n{pdf_path}")
            else:
                QMessageBox.critical(self, "Export Failed", "Failed to generate PDF.")
                
        self.pdf_engine.loadFinished.connect(on_load_finished)
        self.pdf_engine.pdfPrintingFinished.connect(on_pdf_exported)

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
            self.render_document(preserve_scroll=False)

    # --- UI & STYLING METHODS ---

    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def apply_theme(self):
        theme_name = self.combo_ui_theme.currentText()
        colors = self.themes[theme_name]

        if hasattr(self, 'editor'):
            self.highlighter = MarkdownHighlighter(self.editor.document(), colors, colors["is_dark"])

        stylesheet = f"""
            QWidget {{
                background-color: {colors["bg"]};
                color: {colors["text"]};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            
            QFrame#toolbar {{
                background-color: {colors["button_bg"]};
                border: 1px solid {colors["border"]};
                border-radius: 8px;
            }}
            QFrame#iconSidebar {{
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
                font-size: 14px;
            }}
            QFrame#iconSidebar QToolButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 8px;
                padding: 10px;
            }}
            QFrame#iconSidebar QToolButton:hover {{
                background-color: {colors["button_hover"]};
                border: 1px solid {colors["border"]};
            }}
            QFrame#iconSidebar QToolButton:pressed {{
                background-color: {colors["accent"]};
                color: white;
            }}
            QFrame#toolbar QPushButton:hover, QFrame#toolbar QComboBox:hover {{
                background-color: {colors["button_hover"]};
                border: 1px solid {colors["border"]};
            }}
            QComboBox::drop-down {{ border: none; }}
            
            /* --- Dropdown Menu List Styling Fix --- */
            QComboBox QAbstractItemView {{
                background-color: {colors["bg"]};
                color: {colors["text"]};
                selection-background-color: {colors["button_hover"]};
                selection-color: {colors["text"]};
                border: 1px solid {colors["border"]};
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                min-height: 28px;
                padding-left: 8px;
            }}
            QComboBox QAbstractItemView::item:hover, QComboBox QAbstractItemView::item:selected {{
                background-color: {colors["button_hover"]};
                color: {colors["text"]};
            }}
            
            QToolTip {{
                background-color: {colors["bg"]};
                color: {colors["text"]};
                border: 1px solid {colors["accent"]};
                padding: 6px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: normal;
            }}

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
                font-size: 14px;
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
            
            QDialog QPushButton {{
                background-color: {colors["button_bg"]};
                border: 1px solid {colors["border"]};
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
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