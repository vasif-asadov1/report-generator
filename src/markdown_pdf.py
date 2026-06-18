import markdown
from pygments.formatters import HtmlFormatter

class MarkdownEngine:
    def __init__(self):
        # standard extensions + fenced_code (for ```python) + codehilite (for colors)
        self.extensions = ['fenced_code', 'codehilite', 'tables', 'sane_lists']
        
    def convert_to_html(self, md_text, theme_colors):
        # 1. Convert Markdown to raw HTML
        raw_html = markdown.markdown(md_text, extensions=self.extensions)
        
        # 2. Generate Syntax Highlighting CSS (Using 'monokai' for a great dark code look)
        code_css = HtmlFormatter(style='monokai').get_style_defs('.codehilite')
        
        # 3. MathJax configuration for $..$ and $$..$$
        # 3. MathJax configuration for $..$ and $$..$$
        mathjax_script = """
        <script>
        MathJax = {
          tex: {
            inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
            displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']]
          }
        };
        </script>
        <script id="MathJax-script" src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
        """
        
        # 4. Construct the final HTML document with injected theme colors
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    background-color: {theme_colors['bg']};
                    color: {theme_colors['text']};
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 16px;
                    line-height: 1.6;
                    padding: 40px;
                    margin: 0;
                    transition: background-color 0.3s;
                }}
                .codehilite {{
                    background-color: #272822; /* Monokai background */
                    border-radius: 6px;
                    padding: 10px;
                    overflow-x: auto;
                    margin-bottom: 16px;
                }}
                code {{
                    font-family: 'Cascadia Code', 'Courier New', monospace;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin-bottom: 20px;
                }}
                th, td {{
                    border: 1px solid {theme_colors['text']};
                    padding: 8px;
                    text-align: left;
                }}
                {code_css}
            </style>
            {mathjax_script}
        </head>
        <body>
            {raw_html}
        </body>
        </html>
        """
        return full_html