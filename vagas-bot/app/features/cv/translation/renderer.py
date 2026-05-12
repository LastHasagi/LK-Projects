from pathlib import Path

import markdown as md_lib
from weasyprint import HTML

_CSS = """
@page { size: A4; margin: 18mm 16mm; }
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
       font-size: 10.5pt; line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 20pt; margin: 0 0 4pt 0; }
h2 { font-size: 13pt; margin: 14pt 0 4pt 0; color: #0b3d91;
     border-bottom: 1px solid #0b3d91; padding-bottom: 2pt; }
h3 { font-size: 11pt; margin: 8pt 0 2pt 0; }
ul { margin: 2pt 0 6pt 18pt; padding: 0; }
li { margin: 2pt 0; }
p  { margin: 4pt 0; }
strong { color: #000; }
a  { color: #0b3d91; text-decoration: none; }
"""

_HTML_SHELL = """<!doctype html>
<html><head><meta charset="utf-8"><style>{css}</style></head>
<body>{body}</body></html>"""


def render_markdown_to_pdf(markdown_text: str, output_path: Path) -> None:
    html_body = md_lib.markdown(
        markdown_text,
        extensions=["extra", "sane_lists"],
        output_format="html5",
    )
    html_doc = _HTML_SHELL.format(css=_CSS, body=html_body)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_doc).write_pdf(str(output_path))
