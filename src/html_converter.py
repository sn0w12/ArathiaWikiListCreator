import os
import re

# Module-level cache for head content
_HEAD_CONTENT_CACHE = None


def parse_wiki_attributes(attr_str):
    """Parse MediaWiki style attributes into HTML attributes."""
    if not attr_str:
        return ""

    # Remove any trailing | character and clean whitespace
    attr_str = attr_str.rstrip("|").strip()

    # Early return if just whitespace
    if not attr_str:
        return ""

    # Handle class and style attributes separately
    attrs = {}

    # Match different attribute patterns:
    # 1. key="value"
    # 2. key=value
    # 3. class="value"
    # 4. style="value"
    pattern = r'([\w-]+)\s*=\s*(?:"([^"]*)"|([^\s"|][^|]*?)(?=\s|\||$))'
    matches = re.finditer(pattern, attr_str)

    for match in matches:
        key = match.group(1)
        # Take the quoted value if it exists, otherwise take the unquoted value
        value = match.group(2) if match.group(2) is not None else match.group(3)
        if value is not None:
            attrs[key] = value.strip()

    return " ".join(f'{k}="{v}"' for k, v in attrs.items())


def parse_wiki_cell(cell):
    """Parse a wiki cell into attributes and content."""
    if "|" in cell:
        attrs, content = cell.split("|", 1)
        return parse_wiki_attributes(attrs), content.strip()
    return "", cell.strip()


def wiki_to_html_table(wiki_text):
    """Convert MediaWiki table syntax to HTML."""
    if not wiki_text:
        return '<div class="citizen-table-wrapper"><table></table></div>'

    html = ['<div class="citizen-table-wrapper">']
    lines = wiki_text.strip().split("\n")
    in_table = False
    needs_row_close = False

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("{|"):  # Table start
            attrs = parse_wiki_attributes(line[2:])
            html.append(f"<table {attrs}>")
            html.append("<tbody>")
            in_table = True

        elif line.startswith("|}"):  # Table end
            if needs_row_close:
                html.append("</tr>")
                needs_row_close = False
            html.append("</tbody>")
            html.append("</table>")
            in_table = False

        elif line.startswith("|-"):  # Row separator
            if needs_row_close:
                html.append("</tr>")
            html.append("<tr>")
            needs_row_close = True

        elif line.startswith("!") or line.startswith("|"):  # Header or regular cell
            if not needs_row_close:
                html.append("<tr>")
                needs_row_close = True

            is_header = line.startswith("!")
            tag = "th" if is_header else "td"
            cells = line[1:].split("||" if not is_header else "!!")

            for cell in cells:
                if cell.strip():
                    attrs, content = parse_wiki_cell(cell)
                    html.append(f"<{tag} {attrs}>{content}\n</{tag}>")

        i += 1

    if needs_row_close:
        html.append("</tr>")
    if in_table:
        html.append("</tbody>")
        html.append("</table>")

    html.append("</div>")
    return "\n".join(html)


def load_head_content(force_reload=False):
    """Loads the head content from head.html file with caching support."""
    global _HEAD_CONTENT_CACHE

    # Return cached content unless force_reload is True
    if _HEAD_CONTENT_CACHE is not None and not force_reload:
        return _HEAD_CONTENT_CACHE

    possible_paths = [
        "./html/head.html",
        "html/head.html",
        "../html/head.html",
        os.path.join(os.path.dirname(__file__), "html/head.html"),
        os.path.join(os.path.dirname(__file__), "../html/head.html"),
    ]

    for path in possible_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                _HEAD_CONTENT_CACHE = f.read()
                return _HEAD_CONTENT_CACHE
        except FileNotFoundError:
            continue

    # If no file is found, use default head content
    print("Head.html not found in any location. Using default head content.")
    _HEAD_CONTENT_CACHE = """<head>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="https://arathia.net/w/load.php?lang=en&amp;modules=site.styles&amp;only=styles&amp;skin=citizen">
    <title>Arathia Wiki Table</title>
</head>"""
    return _HEAD_CONTENT_CACHE


def create_html_page(table_html):
    """Creates a complete HTML page with the required stylesheet and table content."""
    head_content = load_head_content()
    html = f"""<!DOCTYPE html>
<html>
{head_content}
<body>
    {table_html}
</body>
</html>"""
    return html
