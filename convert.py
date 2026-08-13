#!/usr/bin/env python3
"""
LaTeX to HTML converter for Mandelbulber manual.
Converts .tex source files to a single-page HTML document with collapsible sidebar TOC.
"""

import os
import re
import shutil
import argparse
from pathlib import Path
from html import escape

# Heading ID counter
_heading_counter = [0]

# Section numbering counters
_section_counter = [0]   # section number
_subsection_counter = [0]  # subsection number
_subsubsection_counter = [0]  # subsubsection number
_paragraph_counter = [0]  # paragraph number
_subparagraph_counter = [0]  # subparagraph number
_figure_counter = [0]     # figure number


def parse_args():
    parser = argparse.ArgumentParser(description="Convert Mandelbulber LaTeX manual to HTML")
    parser.add_argument("source", help="Path to mandelbulber2/manual directory")
    parser.add_argument("output", help="Output directory for HTML files")
    parser.add_argument("--index", action="store_true", help="Generate single-page HTML with TOC")
    return parser.parse_args()


def resolve_input(path, base_dir, repo_root=None):
    """Resolve \input{path} to actual file content, recursively processing \input{} directives."""
    # Skip makro.tex and preamble.tex — they contain \def macro definitions and
    # LaTeX package declarations, not content
    basename = path.replace("\\", "/").split("/")[-1]
    if basename in ("makro", "makro.tex", "preamble", "preamble.tex"):
        return ""
    # Always resolve \input{} paths relative to repo root (LaTeX source uses absolute paths from repo)
    if repo_root is not None:
        target = Path(repo_root) / path
    else:
        target = Path(base_dir) / path
    if not target.exists():
        # Try with .tex extension
        target_tex = Path(target).parent / (Path(target).stem + '.tex')
        if target_tex.exists():
            target = target_tex
        else:
            return f'<p class="error">File not found: {path}</p>'
    with open(target, "r", encoding="utf-8") as f:
        content = f.read()
    # Strip % comment lines from .tex files (lines that begin with %)
    # Only strip lines where % is the first non-whitespace character
    content = '\n'.join(
        line for line in content.split('\n')
        if not line.lstrip().startswith('%')
    )
    # Recursively process \input{} directives in the included file
    input_pattern = r'\\input\{([^}]+)\}'
    def replace_input(m):
        sub_path = m.group(1)
        return resolve_input(sub_path, base_dir, repo_root=repo_root)
    content = re.sub(input_pattern, replace_input, content)
    # Also process \include{} directives
    include_pattern = r'\\include\{([^}]+)\}'
    def replace_include(m):
        sub_path = m.group(1) + '.tex'
        return resolve_input(sub_path, base_dir, repo_root=repo_root)
    content = re.sub(include_pattern, replace_include, content)
    # Fix: restore &amp; that lost its & prefix (e.g. in editors table)
    
    # Restore verbatim content AFTER paragraph wrapping

    return content


def _strip_latex_for_slug(text):
    """Strip LaTeX commands from heading text for generating clean URL slugs."""
    # Remove \emph{...}, \textbf{...}, \textit{...}, \texttt{...} etc.
    # Use single backslash patterns to match LaTeX source text
    text = re.sub(r'\\emph\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\textbf\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\textit\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\texttt\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\text\{[^}]*\}', r'', text)
    # Remove any remaining \command{...} patterns
    text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', text)
    # Remove any remaining bare \commands, converting LaTeX escapes to their characters
    def strip_bare_cmd(m):
        name = m.group(1)
        esc = {'_': '_', '#': '#', '$': '$', '%': '%', '!': '!', '&': '&', '\\': '\\', '/': '/'}
        if name in esc:
            return esc[name]
        return ''
    # First handle bare backslash + non-alphabetic (e.g. \_ \# \$)
    text = re.sub(r'\\([^a-zA-Z])', lambda m: m.group(1), text)
    # Then handle bare \commands (alphabetic)
    text = re.sub(r'\\([a-zA-Z]+)', strip_bare_cmd, text)
    # Strip HTML tags that were already processed by the command loop
    text = re.sub(r'<[^>]*>', '', text)
    # Strip quotes and newlines to avoid breaking HTML attribute matching
    text = text.replace('"', '').replace("'", '').replace('{', '').replace('}', '')
    text = text.replace('\n', ' ').replace('\t', ' ')
    # Strip invalid HTML ID characters: &, ?, %, #, space, ., etc.
    text = re.sub(r'[&?#%,;:!\'\.\-]', '', text)
    # Remove leading/trailing dashes
    text = text.strip('-')
    return text


def _make_heading_id(text, level):
    """Generate a clean heading ID from raw LaTeX text."""
    clean = _strip_latex_for_slug(text)
    slug = clean.strip().lower().replace(' ', '-')
    slug = re.sub(r'-+', '-', slug)
    _heading_counter[0] += 1
    return f"sec-{_heading_counter[0]}-{slug}"


def _process_heading_text(raw):
    """Process raw LaTeX text in a heading tag for display.
    Converts \_, \&, \% etc. to their character equivalents.
    Strips \emph{}, \textbf{}, \texttt{} etc. wrapping."""
    text = raw
    # Strip wrapping commands like \emph{...}, \textbf{...}, \textit{...}, \texttt{...}
    for cmd in ['emph', 'textbf', 'textit', 'texttt', 'textsf', 'textup', 'textrm', 'bf', 'it', 'tt', 'rm', 'sf', 'large', 'Large', 'huge', 'scriptsize', 'footnotesize', 'tiny']:
        text = re.sub(r'\\' + cmd + r'\{([^}]*)\}', r'\1', text)
    # Process bare LaTeX escapes: \_ \& \% etc.
    def unescape_cmd(m):
        name = m.group(1)
        esc = {'_': '_', '#': '#', '$': '$', '%': '%', '!': '!', '&': '&', '\\': '\\', '/': '/'}
        if name in esc:
            return esc[name]
        return ''
    text = re.sub(r'\\([^a-zA-Z])', lambda m: m.group(1), text)
    text = re.sub(r'\\([a-zA-Z]+)', unescape_cmd, text)
    return text


def process_command(cmd_match):
    """Process a LaTeX command and return HTML."""
    cmd = cmd_match.group(1)
    args = cmd_match.group(2) or ""
    parts = [p.strip() for p in args.split(",") if p.strip()]

    if cmd == "textbf":
        return f"<strong>{parts[0]}</strong>" if parts else ""
    elif cmd == "textit":
        return f"<em>{parts[0]}</em>" if parts else ""
    elif cmd == "emph":
        # Handle nested content (e.g., from \textbf{\emph{text}})
        inner = parts[0] if parts else ""
        # Strip any HTML tags that leaked in
        inner = re.sub(r'<[^>]+>', '', inner)
        return f"<em>{inner}</em>" if inner else ""
    elif cmd == "verb":
        return f"<code>{parts[0]}</code>" if parts else ""
    elif cmd == "code":
        return f"<code>{parts[0]}</code>" if parts else ""
    elif cmd == "file":
        return f"<code>{parts[0]}</code>" if parts else ""
    elif cmd == "option":
        return f"<code>{parts[0]}</code>" if parts else ""
    elif cmd == "url":
        return f'<a href="{parts[0]}">{parts[0]}</a>' if parts else ""
    elif cmd == "email":
        return f'<a href="mailto:{parts[0]}">{parts[0].replace("mailto:", "")}</a>' if parts else ""
    elif cmd == "href":
        # \href{url}{text} - parts[0] is url, parts[1] is text
        if len(parts) >= 2:
            display = parts[1].replace("mailto:", "")
            return f'<a href="{parts[0]}">{display}</a>'
        elif parts:
            display = parts[0].replace("mailto:", "")
            return f'<a href="{parts[0]}">{display}</a>'
        return ""
    elif cmd == "index":
        return f'<span class="index-marker" data-index="{parts[0]}"></span>' if parts else ""
    elif cmd == "ref":
        return f'<a class="ref-link" href="#{parts[0]}">{parts[0]}</a>' if parts else ""
    elif cmd == "pageref":
        return f'<a class="ref-link" href="#{parts[0]}">page {parts[0]}</a>' if parts else ""
    elif cmd == "label":
        return f'<span id="{parts[0]}"></span>' if parts else ""
    elif cmd == "newlabel":
        return ""
    elif cmd == "vspace":
        return f'<div style="height: {parts[0]};"></div>' if parts else ""
    elif cmd == "hspace":
        return f'<span style="width: {parts[0]}; display: inline-block;"></span>' if parts else ""
    elif cmd == "specialrule":
        # \specialrule{thickness}{above}{below} - horizontal rule
        if len(parts) >= 1:
            thickness = parts[0]
            return f'<hr style="height:{thickness}; margin:0.5em 0;"/>'
        return ""
    elif cmd == "section":
        if not parts:
            return ""
        _section_counter[0] += 1
        _subsection_counter[0] = 0
        _subsubsection_counter[0] = 0
        _figure_counter[0] = 0  # Reset figure counter for new section
        sec_num = f"{_section_counter[0]}"
        rid = sec_num.replace('.', '-')
        return f"<h1 id='{rid}'>{sec_num}. {_process_heading_text(args)}</h1>"
    elif cmd == "subsection":
        if not parts:
            return ""
        _subsection_counter[0] += 1
        _subsubsection_counter[0] = 0
        sec_num = f"{_section_counter[0]}.{_subsection_counter[0]}"
        rid = sec_num.replace('.', '-')
        return f"<h2 id='{rid}'>{sec_num}. {_process_heading_text(args)}</h2>"
    elif cmd == "subsubsection":
        if not parts:
            return ""
        _subsubsection_counter[0] += 1
        sec_num = f"{_section_counter[0]}.{_subsection_counter[0]}.{_subsubsection_counter[0]}"
        rid = sec_num.replace('.', '-')
        return f"<h3 id='{rid}'>{sec_num}. {_process_heading_text(args)}</h3>"
    elif cmd == "paragraph":
        if not parts:
            return ""
        sec_num = f"{_section_counter[0]}.{_subsection_counter[0]}.{_subsubsection_counter[0]}.{_paragraph_counter[0]}"
        _paragraph_counter[0] += 1
        rid = sec_num.replace('.', '-')
        # Strip \emph{} even when inner content has HTML tags from prior iterations
        text = re.sub(r'\\emph\{([^}]*(?:\{[^}]*\})?[^}]*)\}', lambda m: re.sub(r'<[^>]+>', '', m.group(1)), parts[0])
        return f"<h4 id='{rid}'>{_process_heading_text(text)}</h4>"
    elif cmd == "subparagraph":
        if not parts:
            return ""
        sec_num = f"{_section_counter[0]}.{_subsection_counter[0]}.{_subsubsection_counter[0]}.{_paragraph_counter[0]}.{_subparagraph_counter[0]}"
        _subparagraph_counter[0] += 1
        rid = sec_num.replace('.', '-')
        return f"<h5 id='{rid}'>{_process_heading_text(parts[0])}</h5>"
    elif cmd == "textcolor":
        # \textcolor{color}{text} - parts[0] is color, parts[1] is text
        if len(parts) >= 2:
            return f'<span style="color:{parts[0]}">{parts[1]}</span>'
        elif parts:
            return f'<span style="color:{parts[0]}">{parts[0]}</span>'
        return ""
    elif cmd == "color":
        if parts:
            return f'<span style="color:{parts[0]}">'
        return ""
    elif cmd == "textsc":
        return f"<span style='font-variant:small-caps'>{parts[0]}</span>" if parts else ""
    elif cmd == "texttt":
        return f"<code>{parts[0]}</code>" if parts else ""
    elif cmd == "tt":
        return f"<code>{parts[0]}</code>" if parts else ""
    elif cmd == "bf":
        return f"<strong>{parts[0]}</strong>" if parts else ""
    elif cmd == "it":
        return f"<em>{parts[0]}</em>" if parts else ""
    elif cmd == "text":
        # \text{...} in math mode - just return the content
        return parts[0] if parts else ""
    elif cmd == "mathrm":
        # \mathrm{...} in math mode - just return the content
        return parts[0] if parts else ""
    elif cmd == "mathbf":
        return f"<strong>{parts[0]}</strong>" if parts else ""
    elif cmd == "mathit":
        return f"<em>{parts[0]}</em>" if parts else ""
    elif cmd == "textsuperscript":
        return f"<sup>{parts[0]}</sup>" if parts else ""
    elif cmd == "textsubscript":
        return f"<sub>{parts[0]}</sub>" if parts else ""
    elif cmd == "smallcaps":
        return f"<span style='font-variant:small-caps'>{parts[0]}</span>" if parts else ""
    elif cmd == "underline":
        return f"<u>{parts[0]}</u>" if parts else ""
    elif cmd == "sout":
        return f"<s>{parts[0]}</s>" if parts else ""
    elif cmd == "textrm":
        return parts[0] if parts else ""
    elif cmd == "large":
        return f"<span style='font-size:1.2em'>{parts[0]}</span>" if parts else ""
    elif cmd == "Large":
        return f"<span style='font-size:1.5em'>{parts[0]}</span>" if parts else ""
    elif cmd == "huge":
        return f"<span style='font-size:1.8em'>{parts[0]}</span>" if parts else ""
    elif cmd == "scriptsize":
        return f"<span style='font-size:0.8em'>{parts[0]}</span>" if parts else ""
    elif cmd == "footnotesize":
        return f"<span style='font-size:0.9em'>{parts[0]}</span>" if parts else ""
    elif cmd == "tiny":
        return f"<span style='font-size:0.7em'>{parts[0]}</span>" if parts else ""
    elif cmd == "rm":
        return parts[0] if parts else ""
    elif cmd == "sf":
        return f"<span style='font-family:sans-serif'>{parts[0]}</span>" if parts else ""
    elif cmd == "textsf":
        return f"<span style='font-family:sans-serif'>{parts[0]}</span>" if parts else ""
    elif cmd == "textup":
        return parts[0] if parts else ""
    elif cmd == "frac":
        if len(parts) >= 2:
            return f"<sup>{parts[0]}</sup>/<sub>{parts[1]}</sub>"
        return parts[0] if parts else ""
    elif cmd == "sqrt":
        return f"<sup>&radic;({parts[0]})</sup>" if parts else ""
    elif cmd == "begin":
        return f"<span class='begin-{parts[0]}'>" if parts else ""
    elif cmd == "end":
        return "</span>" if parts else ""
    elif cmd == "textgreater":
        return "&gt;"
    elif cmd == "textless":
        return "\\"
    elif cmd == "textperiodcentered":
        return "&middot;"
    elif cmd == "textvisiblespace":
        return "&#x2423;"
    elif cmd == "textasciicircum":
        return "&#x2038;"
    elif cmd == "textbackslash":
        return "\\\\"
    elif cmd == "textasciitilde":
        return "&#x007E;"
    elif cmd == "textem":
        return "&#x0153;"
    elif cmd == "textonehalf":
        return "1.5"
    elif cmd == "textonequarter":
        return "0.25"
    elif cmd == "textthreequarters":
        return "0.75"
    elif cmd == "textfractionsolidus":
        return "/"
    elif cmd == "texttrademark":
        return "&#x2122;"
    elif cmd == "textregistered":
        return "&#x00AE;"
    elif cmd == "textcopyright":
        return "&#x00A9;"
    elif cmd == "textbar":
        return "&#x00A6;"
    elif cmd == "textbraceleft":
        return "{"
    elif cmd == "textbraceright":
        return "}"


def process_image_macro(content, repo_root=None):
    """Process \\includegraphics[opts]{path} and custom \\simpleImageWithCaption{Type}{path}."""

    # Map custom macro suffixes to width percentages
    width_map = {
        'FullWidth': '',
        '75Width': '75%',
        'HalfWidth': '50%',
        'ThirdWidth': '33%',
        'SmallWidth': '200px',
    }

    # Process custom \simpleImageWithCaption{Type}{path} macros
    custom_pattern = r'\\simpleImageWithCaption(75Width|FullWidth|HalfWidth|SmallWidth|ThirdWidth)\{([^}]+)\}\s*\{([^}]+)\}'
    def replace_custom_image(m):
        suffix = m.group(1)
        path = m.group(2)
        caption = m.group(3) if m.group(3) else ""
        width = width_map.get(suffix, '')
        # Images are at img/manual/media/ relative to repo root (same as LaTeX source)
        html_path = path.replace("\\", "/")
        img_style = f"max-width:{width}; height:auto; display:block; margin:1em auto;" if width else "max-width:100%; height:auto; display:block; margin:1em auto;"
        img_html = f'<img src="{html_path}" alt="{path}" style="{img_style}" />'
        if caption:
            return f'<figure class="manual-figure">{img_html}<figcaption class="figcaption">__FIGNUM__ {caption}</figcaption></figure>'
        return img_html

    content = re.sub(custom_pattern, replace_custom_image, content)

    # Process \\twoImagesWithTwoCaptionsFullWidth{path1}{cap1}{lbl1}{path2}{cap2}{lbl2}{opts}
    twoimg_pattern = r'\\twoImagesWithTwoCaptionsFullWidth\s*\{([^}]+)\}\s*\{([^}]+)\}\s*\{[^}]*\}\s*\{([^}]+)\}\s*\{([^}]+)\}\s*\{[^}]*\}\s*\{[^}]*\}'
    def replace_two_images(m):
        path1, cap1, path2, cap2 = m.group(1), m.group(2), m.group(3), m.group(4)
        h1 = path1.replace("\\", "/")
        h2 = path2.replace("\\", "/")
        fig1 = f'<figure class="manual-figure" style="display:flex; flex-direction:column; flex:1; align-items:center;"><img src="{h1}" alt="{path1}" style="max-width:100%; height:auto; display:block; margin:0.5em 0; " /><figcaption class="figcaption">__FIGNUM__ {cap1}</figcaption></figure>'
        fig2 = f'<figure class="manual-figure" style="display:flex; flex-direction:column; flex:1; align-items:center;"><img src="{h2}" alt="{path2}" style="max-width:100%; height:auto; display:block; margin:0.5em 0; " /><figcaption class="figcaption">__FIGNUM__ {cap2}</figcaption></figure>'
        return f'<div style="display:flex; flex-direction:row; gap:0.5em; justify-content:center;">{fig1}{fig2}</div>'
    content = re.sub(twoimg_pattern, replace_two_images, content, flags=re.DOTALL)

    # Process \\threeImagesWithTwoCaptionsFullWidth{path1}{cap1}{lbl1}{path2}{cap2}{lbl2}{path3}{cap3}{lbl3}
    threeimg_pattern = r'\\threeImagesWithTwoCaptionsFullWidth\s*\{([^}]+)\}\s*\{([^}]+)\}\s*\{[^}]*\}\s*\{([^}]+)\}\s*\{([^}]+)\}\s*\{[^}]*\}\s*\{([^}]+)\}\s*\{([^}]+)\}\s*\{[^}]*\}'
    def replace_three_images(m):
        path1, cap1 = m.group(1), m.group(2)
        path2, cap2 = m.group(3), m.group(4)
        path3, cap3 = m.group(5), m.group(6)
        h1 = path1.replace("\\", "/")
        h2 = path2.replace("\\", "/")
        h3 = path3.replace("\\", "/")
        fig1 = f'<figure class="manual-figure" style="display:flex; flex-direction:column; flex:1; align-items:center;"><img src="{h1}" alt="{path1}" style="max-width:100%; height:auto; display:block; margin:0.5em 0; " /><figcaption class="figcaption">__FIGNUM__ {cap1}</figcaption></figure>'
        fig2 = f'<figure class="manual-figure" style="display:flex; flex-direction:column; flex:1; align-items:center;"><img src="{h2}" alt="{path2}" style="max-width:100%; height:auto; display:block; margin:0.5em 0; " /><figcaption class="figcaption">__FIGNUM__ {cap2}</figcaption></figure>'
        fig3 = f'<figure class="manual-figure" style="display:flex; flex-direction:column; flex:1; align-items:center;"><img src="{h3}" alt="{path3}" style="max-width:100%; height:auto; display:block; margin:0.5em 0; " /><figcaption class="figcaption">__FIGNUM__ {cap3}</figcaption></figure>'
        return f'<div style="display:flex; flex-direction:row; gap:0.5em; justify-content:center;">{fig1}{fig2}{fig3}</div>'
    content = re.sub(threeimg_pattern, replace_three_images, content, flags=re.DOTALL)



    # Process standard \includegraphics[opts]{path}
    pattern = r'\\includegraphics(\[[^\]]*\])?\{([^}]+)\}'
    def replace_image(m):
        opts = m.group(1) or ""
        path = m.group(2)
        width = ""
        height = ""
        # Handle width=0.3\linewidth style
        width_match = re.search(r"width=([\d.]+)(\\?linewidth|in|pt|px)?", opts)
        if width_match:
            val = float(width_match.group(1))
            unit = width_match.group(2) or 'linewidth'
            if 'linewidth' in unit:
                # \linewidth = 100% of line width
                width = '100%'
            elif 'in' in unit:
                # Convert inches to pixels (96 DPI)
                width = str(int(val * 96))
            else:
                width = str(int(val))
        height_match = re.search(r"height=([\d.]+)(in|pt|px)?", opts)
        if height_match:
            val = float(height_match.group(1))
            unit = height_match.group(2) or 'pt'
            if 'in' in unit:
                # Convert inches to pixels (96 DPI)
                height = str(int(val * 96))
            elif 'pt' in unit:
                # Convert points to pixels (1pt = 1.333px at 96 DPI)
                height = str(int(val * 4 / 3))
            else:
                height = str(int(val))
        # Images are at img/manual/media/ relative to repo root (same as LaTeX source)
        html_path = path.replace("\\", "/")
        # Auto-detect file extension if path has no extension
        if repo_root and '.' not in html_path.split('/')[-1]:
            for ext in ['.png', '.jpg', '.jpeg', '.svg', '.gif', '.pdf']:
                candidate = html_path + ext
                full = Path(repo_root) / candidate
                if full.exists():
                    html_path = candidate
                    break
        # Use style-based sizing (consistent with \simpleImageWithCaption)
        style_parts = ['height:auto', 'display:block', 'margin:1em auto']
        # Sound images use 50% width; other images use pixel width if available
        if 'sound' in path.lower():
            style_parts.insert(0, 'max-width:50%')
        elif width:
            # Avoid double suffix (e.g., '100%px')
            if isinstance(width, str) and '%' in width:
                style_parts.insert(0, f'max-width:{width}')
            else:
                style_parts.insert(0, f'max-width:{width}px')
        else:
            style_parts.insert(0, 'max-width:100%')
        style = '; '.join(style_parts)
        return '<img src="{}" alt="{}" style="{}" />'.format(html_path, path, style)
    content = re.sub(pattern, replace_image, content)
    return content


def process_content(content, base_dir, repo_root=None):
    """Main content processing function."""
    # Math protection registry - populated after file inclusion
    _math_registry = {}
    _math_counter = [0]
    
    # Process \input{} commands first
    input_pattern = r'\\input\{([^}]+)\}'
    def replace_input(m):
        path = m.group(1)
        return resolve_input(path, base_dir, repo_root=repo_root)
    content = re.sub(input_pattern, replace_input, content)

    # Process \include{} commands
    include_pattern = r'\\include\{([^}]+)\}'
    def replace_include(m):
        path = m.group(1) + ".tex"
        return resolve_input(path, base_dir, repo_root=repo_root)
    content = re.sub(include_pattern, replace_include, content)

    # Strip LaTeX grouping parens around $ math like ($ ... $)
    # These are common in mandelbulber source and cause ($ artifacts
    content = re.sub(r'\(\$', '$', content)
    content = re.sub(r'\$\)', '$', content)
    
    # =====================================================================
    # PROTECT MATH CONTENT - extract \[...\], \(...\), and $...$ before processing
    # Must run AFTER file inclusion so math from included files is captured
    # =====================================================================
    BS = chr(92)  # backslash character
    def extract_display_math(text):
        result = []
        i = 0
        while i < len(text):
            if text[i] == BS and i + 1 < len(text) and text[i+1] == '[':
                j = i + 2
                depth = 1
                while j < len(text) and depth > 0:
                    if text[j] == BS and j + 1 < len(text) and text[j+1] == '[':
                        depth += 1
                        j += 1
                    elif text[j] == BS and j + 1 < len(text) and text[j+1] == ']':
                        depth -= 1
                        j += 1
                    j += 1
                if depth == 0:
                    math_content = text[i+2:j-2]
                    _math_counter[0] += 1
                    key = f"__MATH_PLACEHOLDER_{_math_counter[0]}__"
                    _math_registry[key] = ("display", math_content)
                    result.append(key)
                    i = j
                    continue
            result.append(text[i])
            i += 1
        return ''.join(result)
    
    def extract_inline_math(text):
        result = []
        i = 0
        while i < len(text):
            if text[i] == BS and i + 1 < len(text) and text[i+1] == '(':
                j = i + 2
                depth = 1
                while j < len(text) and depth > 0:
                    if text[j] == BS and j + 1 < len(text) and text[j+1] == '(':
                        depth += 1
                        j += 1
                    elif text[j] == BS and j + 1 < len(text) and text[j+1] == ')':
                        depth -= 1
                        j += 1
                    j += 1
                if depth == 0:
                    math_content = text[i+2:j-2]
                    _math_counter[0] += 1
                    key = f"__MATH_PLACEHOLDER_{_math_counter[0]}__"
                    _math_registry[key] = ("inline", math_content)
                    result.append(key)
                    i = j
                    continue
            result.append(text[i])
            i += 1
        return ''.join(result)
    
    def extract_dollar_math(text):
        # Conservative: $ delimiters should only capture short inline math
        # Allow at most 1 newline and content < 200 chars to avoid capturing paragraphs
        result = []
        i = 0
        while i < len(text):
            if text[i] == '$' and (i + 1 >= len(text) or text[i+1] != '$'):
                j = i + 1
                newline_count = 0
                while j < len(text):
                    if text[j] == '\n':
                        newline_count += 1
                        if newline_count > 1:
                            break
                    if text[j] == '$' and (j + 1 >= len(text) or text[j+1] != '$'):
                        break
                    j += 1
                if j < len(text) and text[j] == '$':
                    math_content = text[i+1:j]
                    # Only protect if content is short (inline math)
                    if len(math_content) < 200:
                        _math_counter[0] += 1
                        key = f"__MATH_PLACEHOLDER_{_math_counter[0]}__"
                        _math_registry[key] = ("inline", math_content)
                        result.append(key)
                        i = j + 1
                        continue
            result.append(text[i])
            i += 1
        return ''.join(result)
    
    content = extract_display_math(content)
    content = extract_inline_math(content)
    content = extract_dollar_math(content)
    
    # Extract \newcommand definitions to a dict, then replace bare \mX refs
    metadata = {}
    
    def extract_command_value(content, start_pos, cmd_name):
        """Find the value after \\newcommand{\\cmd_name}{ by counting braces.
        
        start_pos is already past the opening { of the value, so depth starts at 1.
        """
        depth = 1
        i = start_pos
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    value = content[start_pos:i]
                    value = value.strip()
                    if value.startswith('{') and value.endswith('}'):
                        value = value[1:-1]
                    return value
            i += 1
        return None
    
    # Extract \newcommand{\mX}{value} for metadata commands (m*)
    pos = 0
    while pos < len(content):
        m = re.search(r'\\newcommand{\\(m[a-zA-Z]+)}{', content[pos:])
        if not m:
            break
        cmd_name = m.group(1)
        value_start = pos + m.end()
        value = extract_command_value(content, value_start, cmd_name)
        if value is not None:
            metadata[cmd_name] = value
            # Remove this definition from content
            # Find the end of the full \newcommand{\cmd_name}{value}
            end_pos = value_start
            depth = 1  # The opening { of the value was already consumed by the regex
            for j in range(value_start, len(content)):
                if content[j] == '{':
                    depth += 1
                elif content[j] == '}':
                    depth -= 1
                    if depth == 0:
                        end_pos = j + 1
                        break
            match_start = pos + m.start()
            content = content[:match_start] + content[end_pos:]
        pos = pos + m.start() + 1
    
    # Also extract \renewcommand for things like \baselinestretch
    pos = 0
    while pos < len(content):
        m = re.search(r'\\renewcommand{\\([a-zA-Z]+)}{', content[pos:])
        if not m:
            break
        cmd_name = m.group(1)
        value_start = pos + m.end()
        value = extract_command_value(content, value_start, cmd_name)
        if value is not None:
            metadata[cmd_name] = value
            # Find the end of the full \renewcommand{\cmd_name}{value}
            end_pos = value_start
            depth = 1  # The opening { of the value was already consumed by the regex
            for j in range(value_start, len(content)):
                if content[j] == '{':
                    depth += 1
                elif content[j] == '}':
                    depth -= 1
                    if depth == 0:
                        end_pos = j + 1
                        break
            # Use match start position, not search start position
            match_start = pos + m.start()
            content = content[:match_start] + content[end_pos:]
        pos = pos + m.start() + 1
    
    # After extracting renewcommand values, strip any leftover baselinestretch
    # (it's a formatting command, not content)
    content = re.sub(r'\\baselinestretch(\\)?\s*', '', content)
    
    # Extract verbatim environments BEFORE macro replacement to protect their content
    _verbatim_registry = {}
    _verbatim_counter = [0]
    verbatim_pattern = r'\\begin\{verbatim\}(?:\[[^\]]*\])?(.*?)\\end\{verbatim\}'
    def protect_verbatim(m):
        _verbatim_counter[0] += 1
        key = f'__VERBATIM_{_verbatim_counter[0]}__'
        _verbatim_registry[key] = m.group(1)
        return key
    content = re.sub(verbatim_pattern, protect_verbatim, content, flags=re.DOTALL)
    
    # Replace bare \\mX commands with extracted values
    for key, value in metadata.items():
        # Escape backslashes in value for use in re.sub replacement string
        escaped_value = value.replace('\\', '\\\\')
        # Also unescape & in value to prevent double-escaping
        escaped_value = escaped_value.replace('&amp;', '&').replace('&', '&amp;')
        # Replace \\mX{...} first (with arguments), then bare \\mX
        # Use brace-aware matching for \\mX{...}
        pattern_x = r'\\' + re.escape(key) + r'\{'
        def replace_mx_braced(m):
            return escaped_value
        content = re.sub(pattern_x, replace_mx_braced, content)
        content = re.sub(r'\\' + re.escape(key) + r'\s*', escaped_value, content)

    # Restore protected verbatim environments
            # Debug: check verbatim HTML newlines
    # Pre-process \item commands inside description environments
    # This runs BEFORE env_pattern to handle nested descriptions
    # Pre-process \item commands inside description environments
    # This runs BEFORE env_pattern to handle nested descriptions and itemize
    # Pre-process \item commands inside description environments
    # This runs BEFORE env_pattern to handle nested descriptions and itemize
    def process_description_items(m):
        body = m.group(1)
        items = []
        current_item = None
        depth = 0
        nested_buf = []
        itemize_depth = 0
        itemize_buf = []
        for line in body.split("\n"):
            stripped = line.strip()
            if stripped.startswith("\begin{description}"):
                if depth == 0:
                    nested_buf = []
                depth += 1
                continue
            if stripped.startswith("\end{description}"):
                depth -= 1
                if depth == 0:
                    if current_item is not None:
                        items.append(f"<li>{current_item}</li>")
                        current_item = None
                    nested_body = "\n".join(nested_buf)
                    nested_items = []
                    nested_current = None
                    for nline in nested_body.split("\n"):
                        nstripped = nline.strip()
                        if nstripped.startswith("\item"):
                            if nested_current is not None:
                                nested_items.append(f"<li>{nested_current}</li>")
                            nrest = nstripped[5:]
                            if nrest.startswith(" "):
                                nrest = nrest[1:]
                            if nrest.startswith("["):
                                nbe = nrest.find("]")
                                if nbe != -1:
                                    nlabel = nrest[1:nbe]
                                    ndesc = nrest[nbe+1:].strip()
                                    nested_current = f"<strong>{nlabel}</strong> {ndesc}"
                                    continue
                            nested_current = nrest.strip()
                        elif nested_current is not None and nstripped:
                            nested_current += f" {nstripped}"
                    if nested_current is not None:
                        nested_items.append(f"<li>{nested_current}</li>")
                    items.append(f"<ul>{chr(10).join(nested_items)}</ul>")
                    nested_buf = []
                continue
            if depth > 0:
                nested_buf.append(stripped)
                continue
            # Handle nested itemize inside description items
            if stripped.startswith("\begin{itemize}"):
                itemize_depth += 1
                itemize_buf = []
                continue
            if stripped.startswith("\end{itemize}"):
                itemize_depth -= 1
                if itemize_depth == 0:
                    ul_items = []
                    for iline in itemize_buf:
                        istripped = iline.strip()
                        if istripped.startswith("\item"):
                            item_text = istripped[5:].strip()
                            ul_items.append(f"<li>{item_text}</li>")
                    if ul_items:
                        ul_html = "\n".join(ul_items)
                        if current_item is not None:
                            current_item += f" <ul>{ul_html}</ul>"
                        else:
                            items.append(f"<ul>{ul_html}</ul>")
                    itemize_buf = []
                continue
            if itemize_depth > 0:
                itemize_buf.append(stripped)
                continue
            if stripped.startswith("\item"):
                if current_item is not None:
                    items.append(f"<li>{current_item}</li>")
                rest = stripped[5:]
                if rest.startswith(" "):
                    rest = rest[1:]
                if rest.startswith("["):
                    bracket_end = rest.find("]")
                    if bracket_end != -1:
                        label = rest[1:bracket_end]
                        desc_text = rest[bracket_end+1:].strip()
                        current_item = f"<strong>{label}</strong> {desc_text}"
                        continue
                current_item = rest.strip()
            elif current_item is not None and stripped:
                current_item += f" {stripped}"
        if current_item is not None:
            items.append(f"<li>{current_item}</li>")
        return "\n".join(items)
    
#!/usr/bin/env python3
"""
LaTeX to HTML converter for Mandelbulber manual.
Converts .tex source files to a single-page HTML document with collapsible sidebar TOC.
"""

import os
import re
import shutil
import argparse
from pathlib import Path
from html import escape

# Heading ID counter
_heading_counter = [0]

# Section numbering counters
_section_counter = [0]   # section number
_subsection_counter = [0]  # subsection number
_subsubsection_counter = [0]  # subsubsection number
_paragraph_counter = [0]  # paragraph number
_subparagraph_counter = [0]  # subparagraph number
_figure_counter = [0]     # figure number


def parse_args():
    parser = argparse.ArgumentParser(description="Convert Mandelbulber LaTeX manual to HTML")
    parser.add_argument("source", help="Path to mandelbulber2/manual directory")
    parser.add_argument("output", help="Output directory for HTML files")
    parser.add_argument("--index", action="store_true", help="Generate single-page HTML with TOC")
    return parser.parse_args()


def resolve_input(path, base_dir, repo_root=None):
    """Resolve \input{path} to actual file content, recursively processing \input{} directives."""
    # Skip makro.tex and preamble.tex — they contain \def macro definitions and
    # LaTeX package declarations, not content
    basename = path.replace("\\", "/").split("/")[-1]
    if basename in ("makro", "makro.tex", "preamble", "preamble.tex"):
        return ""
    # Always resolve \input{} paths relative to repo root (LaTeX source uses absolute paths from repo)
    if repo_root is not None:
        target = Path(repo_root) / path
    else:
        target = Path(base_dir) / path
    if not target.exists():
        # Try with .tex extension
        target_tex = Path(target).parent / (Path(target).stem + '.tex')
        if target_tex.exists():
            target = target_tex
        else:
            return f'<p class="error">File not found: {path}</p>'
    with open(target, "r", encoding="utf-8") as f:
        content = f.read()
    # Strip % comment lines from .tex files (lines that begin with %)
    # Only strip lines where % is the first non-whitespace character
    content = '\n'.join(
        line for line in content.split('\n')
        if not line.lstrip().startswith('%')
    )
    # Recursively process \input{} directives in the included file
    input_pattern = r'\\input\{([^}]+)\}'
    def replace_input(m):
        sub_path = m.group(1)
        return resolve_input(sub_path, base_dir, repo_root=repo_root)
    content = re.sub(input_pattern, replace_input, content)
    # Also process \include{} directives
    include_pattern = r'\\include\{([^}]+)\}'
    def replace_include(m):
        sub_path = m.group(1) + '.tex'
        return resolve_input(sub_path, base_dir, repo_root=repo_root)
    content = re.sub(include_pattern, replace_include, content)
    # Fix: restore &amp; that lost its & prefix (e.g. in editors table)
    
    # Restore verbatim content AFTER paragraph wrapping

    return content


def _strip_latex_for_slug(text):
    """Strip LaTeX commands from heading text for generating clean URL slugs."""
    # Remove \emph{...}, \textbf{...}, \textit{...}, \texttt{...} etc.
    # Use single backslash patterns to match LaTeX source text
    text = re.sub(r'\\emph\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\textbf\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\textit\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\texttt\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\text\{[^}]*\}', r'', text)
    # Remove any remaining \command{...} patterns
    text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', text)
    # Remove any remaining bare \commands, converting LaTeX escapes to their characters
    def strip_bare_cmd(m):
        name = m.group(1)
        esc = {'_': '_', '#': '#', '$': '$', '%': '%', '!': '!', '&': '&', '\\': '\\', '/': '/'}
        if name in esc:
            return esc[name]
        return ''
    # First handle bare backslash + non-alphabetic (e.g. \_ \# \$)
    text = re.sub(r'\\([^a-zA-Z])', lambda m: m.group(1), text)
    # Then handle bare \commands (alphabetic)
    text = re.sub(r'\\([a-zA-Z]+)', strip_bare_cmd, text)
    # Strip HTML tags that were already processed by the command loop
    text = re.sub(r'<[^>]*>', '', text)
    # Strip quotes and newlines to avoid breaking HTML attribute matching
    text = text.replace('"', '').replace("'", '').replace('{', '').replace('}', '')
    text = text.replace('\n', ' ').replace('\t', ' ')
    # Strip invalid HTML ID characters: &, ?, %, #, space, ., etc.
    text = re.sub(r'[&?#%,;:!\'\.\-]', '', text)
    # Remove leading/trailing dashes
    text = text.strip('-')
    return text


def _make_heading_id(text, level):
    """Generate a clean heading ID from raw LaTeX text."""
    clean = _strip_latex_for_slug(text)
    slug = clean.strip().lower().replace(' ', '-')
    slug = re.sub(r'-+', '-', slug)
    _heading_counter[0] += 1
    return f"sec-{_heading_counter[0]}-{slug}"


def _process_heading_text(raw):
    """Process raw LaTeX text in a heading tag for display.
    Converts \_, \&, \% etc. to their character equivalents.
    Strips \emph{}, \textbf{}, \texttt{} etc. wrapping."""
    text = raw
    # Strip wrapping commands like \emph{...}, \textbf{...}, \textit{...}, \texttt{...}
    for cmd in ['emph', 'textbf', 'textit', 'texttt', 'textsf', 'textup', 'textrm', 'bf', 'it', 'tt', 'rm', 'sf', 'large', 'Large', 'huge', 'scriptsize', 'footnotesize', 'tiny']:
        text = re.sub(r'\\' + cmd + r'\{([^}]*)\}', r'\1', text)
    # Process bare LaTeX escapes: \_ \& \% etc.
    def unescape_cmd(m):
        name = m.group(1)
        esc = {'_': '_', '#': '#', '$': '$', '%': '%', '!': '!', '&': '&', '\\': '\\', '/': '/'}
        if name in esc:
            return esc[name]
        return ''
    text = re.sub(r'\\([^a-zA-Z])', lambda m: m.group(1), text)
    text = re.sub(r'\\([a-zA-Z]+)', unescape_cmd, text)
    return text


def process_command(cmd_match):
    """Process a LaTeX command and return HTML."""
    cmd = cmd_match.group(1)
    args = cmd_match.group(2) or ""
    parts = [p.strip() for p in args.split(",") if p.strip()]

    if cmd == "textbf":
        return f"<strong>{parts[0]}</strong>" if parts else ""
    elif cmd == "textit":
        return f"<em>{parts[0]}</em>" if parts else ""
    elif cmd == "emph":
        # Handle nested content (e.g., from \textbf{\emph{text}})
        inner = parts[0] if parts else ""
        # Strip any HTML tags that leaked in
        inner = re.sub(r'<[^>]+>', '', inner)
        return f"<em>{inner}</em>" if inner else ""
    elif cmd == "verb":
        return f"<code>{parts[0]}</code>" if parts else ""
    elif cmd == "code":
        return f"<code>{parts[0]}</code>" if parts else ""
    elif cmd == "file":
        return f"<code>{parts[0]}</code>" if parts else ""
    elif cmd == "option":
        return f"<code>{parts[0]}</code>" if parts else ""
    elif cmd == "url":
        return f'<a href="{parts[0]}">{parts[0]}</a>' if parts else ""
    elif cmd == "email":
        return f'<a href="mailto:{parts[0]}">{parts[0].replace("mailto:", "")}</a>' if parts else ""
    elif cmd == "href":
        # \href{url}{text} - parts[0] is url, parts[1] is text
        if len(parts) >= 2:
            display = parts[1].replace("mailto:", "")
            return f'<a href="{parts[0]}">{display}</a>'
        elif parts:
            display = parts[0].replace("mailto:", "")
            return f'<a href="{parts[0]}">{display}</a>'
        return ""
    elif cmd == "index":
        return f'<span class="index-marker" data-index="{parts[0]}"></span>' if parts else ""
    elif cmd == "ref":
        return f'<a class="ref-link" href="#{parts[0]}">{parts[0]}</a>' if parts else ""
    elif cmd == "pageref":
        return f'<a class="ref-link" href="#{parts[0]}">page {parts[0]}</a>' if parts else ""
    elif cmd == "label":
        return f'<span id="{parts[0]}"></span>' if parts else ""
    elif cmd == "newlabel":
        return ""
    elif cmd == "vspace":
        return f'<div style="height: {parts[0]};"></div>' if parts else ""
    elif cmd == "hspace":
        return f'<span style="width: {parts[0]}; display: inline-block;"></span>' if parts else ""
    elif cmd == "specialrule":
        # \specialrule{thickness}{above}{below} - horizontal rule
        if len(parts) >= 1:
            thickness = parts[0]
            return f'<hr style="height:{thickness}; margin:0.5em 0;"/>'
        return ""
    elif cmd == "section":
        if not parts:
            return ""
        _section_counter[0] += 1
        _subsection_counter[0] = 0
        _subsubsection_counter[0] = 0
        _figure_counter[0] = 0  # Reset figure counter for new section
        sec_num = f"{_section_counter[0]}"
        rid = sec_num.replace('.', '-')
        return f"<h1 id='{rid}'>{sec_num}. {_process_heading_text(args)}</h1>"
    elif cmd == "subsection":
        if not parts:
            return ""
        _subsection_counter[0] += 1
        _subsubsection_counter[0] = 0
        sec_num = f"{_section_counter[0]}.{_subsection_counter[0]}"
        rid = sec_num.replace('.', '-')
        return f"<h2 id='{rid}'>{sec_num}. {_process_heading_text(args)}</h2>"
    elif cmd == "subsubsection":
        if not parts:
            return ""
        _subsubsection_counter[0] += 1
        sec_num = f"{_section_counter[0]}.{_subsection_counter[0]}.{_subsubsection_counter[0]}"
        rid = sec_num.replace('.', '-')
        return f"<h3 id='{rid}'>{sec_num}. {_process_heading_text(args)}</h3>"
    elif cmd == "paragraph":
        if not parts:
            return ""
        sec_num = f"{_section_counter[0]}.{_subsection_counter[0]}.{_subsubsection_counter[0]}.{_paragraph_counter[0]}"
        _paragraph_counter[0] += 1
        rid = sec_num.replace('.', '-')
        # Strip \emph{} even when inner content has HTML tags from prior iterations
        text = re.sub(r'\\emph\{([^}]*(?:\{[^}]*\})?[^}]*)\}', lambda m: re.sub(r'<[^>]+>', '', m.group(1)), parts[0])
        return f"<h4 id='{rid}'>{_process_heading_text(text)}</h4>"
    elif cmd == "subparagraph":
        if not parts:
            return ""
        sec_num = f"{_section_counter[0]}.{_subsection_counter[0]}.{_subsubsection_counter[0]}.{_paragraph_counter[0]}.{_subparagraph_counter[0]}"
        _subparagraph_counter[0] += 1
        rid = sec_num.replace('.', '-')
        return f"<h5 id='{rid}'>{_process_heading_text(parts[0])}</h5>"
    elif cmd == "textcolor":
        # \textcolor{color}{text} - parts[0] is color, parts[1] is text
        if len(parts) >= 2:
            return f'<span style="color:{parts[0]}">{parts[1]}</span>'
        elif parts:
            return f'<span style="color:{parts[0]}">{parts[0]}</span>'
        return ""
    elif cmd == "color":
        if parts:
            return f'<span style="color:{parts[0]}">'
        return ""
    elif cmd == "textsc":
        return f"<span style='font-variant:small-caps'>{parts[0]}</span>" if parts else ""
    elif cmd == "texttt":
        return f"<code>{parts[0]}</code>" if parts else ""
    elif cmd == "tt":
        return f"<code>{parts[0]}</code>" if parts else ""
    elif cmd == "bf":
        return f"<strong>{parts[0]}</strong>" if parts else ""
    elif cmd == "it":
        return f"<em>{parts[0]}</em>" if parts else ""
    elif cmd == "text":
        # \text{...} in math mode - just return the content
        return parts[0] if parts else ""
    elif cmd == "mathrm":
        # \mathrm{...} in math mode - just return the content
        return parts[0] if parts else ""
    elif cmd == "mathbf":
        return f"<strong>{parts[0]}</strong>" if parts else ""
    elif cmd == "mathit":
        return f"<em>{parts[0]}</em>" if parts else ""
    elif cmd == "textsuperscript":
        return f"<sup>{parts[0]}</sup>" if parts else ""
    elif cmd == "textsubscript":
        return f"<sub>{parts[0]}</sub>" if parts else ""
    elif cmd == "smallcaps":
        return f"<span style='font-variant:small-caps'>{parts[0]}</span>" if parts else ""
    elif cmd == "underline":
        return f"<u>{parts[0]}</u>" if parts else ""
    elif cmd == "sout":
        return f"<s>{parts[0]}</s>" if parts else ""
    elif cmd == "textrm":
        return parts[0] if parts else ""
    elif cmd == "large":
        return f"<span style='font-size:1.2em'>{parts[0]}</span>" if parts else ""
    elif cmd == "Large":
        return f"<span style='font-size:1.5em'>{parts[0]}</span>" if parts else ""
    elif cmd == "huge":
        return f"<span style='font-size:1.8em'>{parts[0]}</span>" if parts else ""
    elif cmd == "scriptsize":
        return f"<span style='font-size:0.8em'>{parts[0]}</span>" if parts else ""
    elif cmd == "footnotesize":
        return f"<span style='font-size:0.9em'>{parts[0]}</span>" if parts else ""
    elif cmd == "tiny":
        return f"<span style='font-size:0.7em'>{parts[0]}</span>" if parts else ""
    elif cmd == "rm":
        return parts[0] if parts else ""
    elif cmd == "sf":
        return f"<span style='font-family:sans-serif'>{parts[0]}</span>" if parts else ""
    elif cmd == "textsf":
        return f"<span style='font-family:sans-serif'>{parts[0]}</span>" if parts else ""
    elif cmd == "textup":
        return parts[0] if parts else ""
    elif cmd == "frac":
        if len(parts) >= 2:
            return f"<sup>{parts[0]}</sup>/<sub>{parts[1]}</sub>"
        return parts[0] if parts else ""
    elif cmd == "sqrt":
        return f"<sup>&radic;({parts[0]})</sup>" if parts else ""
    elif cmd == "begin":
        return f"<span class='begin-{parts[0]}'>" if parts else ""
    elif cmd == "end":
        return "</span>" if parts else ""
    elif cmd == "textgreater":
        return "&gt;"
    elif cmd == "textless":
        return "\\"
    elif cmd == "textperiodcentered":
        return "&middot;"
    elif cmd == "textvisiblespace":
        return "&#x2423;"
    elif cmd == "textasciicircum":
        return "&#x2038;"
    elif cmd == "textbackslash":
        return "\\\\"
    elif cmd == "textasciitilde":
        return "&#x007E;"
    elif cmd == "textem":
        return "&#x0153;"
    elif cmd == "textonehalf":
        return "1.5"
    elif cmd == "textonequarter":
        return "0.25"
    elif cmd == "textthreequarters":
        return "0.75"
    elif cmd == "textfractionsolidus":
        return "/"
    elif cmd == "texttrademark":
        return "&#x2122;"
    elif cmd == "textregistered":
        return "&#x00AE;"
    elif cmd == "textcopyright":
        return "&#x00A9;"
    elif cmd == "textbar":
        return "&#x00A6;"
    elif cmd == "textbraceleft":
        return "{"
    elif cmd == "textbraceright":
        return "}"


def process_image_macro(content, repo_root=None):
    """Process \\includegraphics[opts]{path} and custom \\simpleImageWithCaption{Type}{path}."""

    # Map custom macro suffixes to width percentages
    width_map = {
        'FullWidth': '',
        '75Width': '75%',
        'HalfWidth': '50%',
        'ThirdWidth': '33%',
        'SmallWidth': '200px',
    }

    # Process custom \simpleImageWithCaption{Type}{path} macros
    custom_pattern = r'\\simpleImageWithCaption(75Width|FullWidth|HalfWidth|SmallWidth|ThirdWidth)\{([^}]+)\}\s*\{([^}]+)\}'
    def replace_custom_image(m):
        suffix = m.group(1)
        path = m.group(2)
        caption = m.group(3) if m.group(3) else ""
        width = width_map.get(suffix, '')
        # Images are at img/manual/media/ relative to repo root (same as LaTeX source)
        html_path = path.replace("\\", "/")
        img_style = f"max-width:{width}; height:auto; display:block; margin:1em auto;" if width else "max-width:100%; height:auto; display:block; margin:1em auto;"
        img_html = f'<img src="{html_path}" alt="{path}" style="{img_style}" />'
        if caption:
            return f'<figure class="manual-figure">{img_html}<figcaption class="figcaption">__FIGNUM__ {caption}</figcaption></figure>'
        return img_html

    content = re.sub(custom_pattern, replace_custom_image, content)

    # Process \\twoImagesWithTwoCaptionsFullWidth{path1}{cap1}{lbl1}{path2}{cap2}{lbl2}{opts}
    twoimg_pattern = r'\\twoImagesWithTwoCaptionsFullWidth\s*\{([^}]+)\}\s*\{([^}]+)\}\s*\{[^}]*\}\s*\{([^}]+)\}\s*\{([^}]+)\}\s*\{[^}]*\}\s*\{[^}]*\}'
    def replace_two_images(m):
        path1, cap1, path2, cap2 = m.group(1), m.group(2), m.group(3), m.group(4)
        h1 = path1.replace("\\", "/")
        h2 = path2.replace("\\", "/")
        fig1 = f'<figure class="manual-figure" style="display:flex; flex-direction:column; flex:1; align-items:center;"><img src="{h1}" alt="{path1}" style="max-width:100%; height:auto; display:block; margin:0.5em 0; " /><figcaption class="figcaption">__FIGNUM__ {cap1}</figcaption></figure>'
        fig2 = f'<figure class="manual-figure" style="display:flex; flex-direction:column; flex:1; align-items:center;"><img src="{h2}" alt="{path2}" style="max-width:100%; height:auto; display:block; margin:0.5em 0; " /><figcaption class="figcaption">__FIGNUM__ {cap2}</figcaption></figure>'
        return f'<div style="display:flex; flex-direction:row; gap:0.5em; justify-content:center;">{fig1}{fig2}</div>'
    content = re.sub(twoimg_pattern, replace_two_images, content, flags=re.DOTALL)

    # Process \\threeImagesWithTwoCaptionsFullWidth{path1}{cap1}{lbl1}{path2}{cap2}{lbl2}{path3}{cap3}{lbl3}
    threeimg_pattern = r'\\threeImagesWithTwoCaptionsFullWidth\s*\{([^}]+)\}\s*\{([^}]+)\}\s*\{[^}]*\}\s*\{([^}]+)\}\s*\{([^}]+)\}\s*\{[^}]*\}\s*\{([^}]+)\}\s*\{([^}]+)\}\s*\{[^}]*\}'
    def replace_three_images(m):
        path1, cap1 = m.group(1), m.group(2)
        path2, cap2 = m.group(3), m.group(4)
        path3, cap3 = m.group(5), m.group(6)
        h1 = path1.replace("\\", "/")
        h2 = path2.replace("\\", "/")
        h3 = path3.replace("\\", "/")
        fig1 = f'<figure class="manual-figure" style="display:flex; flex-direction:column; flex:1; align-items:center;"><img src="{h1}" alt="{path1}" style="max-width:100%; height:auto; display:block; margin:0.5em 0; " /><figcaption class="figcaption">__FIGNUM__ {cap1}</figcaption></figure>'
        fig2 = f'<figure class="manual-figure" style="display:flex; flex-direction:column; flex:1; align-items:center;"><img src="{h2}" alt="{path2}" style="max-width:100%; height:auto; display:block; margin:0.5em 0; " /><figcaption class="figcaption">__FIGNUM__ {cap2}</figcaption></figure>'
        fig3 = f'<figure class="manual-figure" style="display:flex; flex-direction:column; flex:1; align-items:center;"><img src="{h3}" alt="{path3}" style="max-width:100%; height:auto; display:block; margin:0.5em 0; " /><figcaption class="figcaption">__FIGNUM__ {cap3}</figcaption></figure>'
        return f'<div style="display:flex; flex-direction:row; gap:0.5em; justify-content:center;">{fig1}{fig2}{fig3}</div>'
    content = re.sub(threeimg_pattern, replace_three_images, content, flags=re.DOTALL)



    # Process standard \includegraphics[opts]{path}
    pattern = r'\\includegraphics(\[[^\]]*\])?\{([^}]+)\}'
    def replace_image(m):
        opts = m.group(1) or ""
        path = m.group(2)
        width = ""
        height = ""
        # Handle width=0.3\linewidth style
        width_match = re.search(r"width=([\d.]+)(\\?linewidth|in|pt|px)?", opts)
        if width_match:
            val = float(width_match.group(1))
            unit = width_match.group(2) or 'linewidth'
            if 'linewidth' in unit:
                # \linewidth = 100% of line width
                width = '100%'
            elif 'in' in unit:
                # Convert inches to pixels (96 DPI)
                width = str(int(val * 96))
            else:
                width = str(int(val))
        height_match = re.search(r"height=([\d.]+)(in|pt|px)?", opts)
        if height_match:
            val = float(height_match.group(1))
            unit = height_match.group(2) or 'pt'
            if 'in' in unit:
                # Convert inches to pixels (96 DPI)
                height = str(int(val * 96))
            elif 'pt' in unit:
                # Convert points to pixels (1pt = 1.333px at 96 DPI)
                height = str(int(val * 4 / 3))
            else:
                height = str(int(val))
        # Images are at img/manual/media/ relative to repo root (same as LaTeX source)
        html_path = path.replace("\\", "/")
        # Auto-detect file extension if path has no extension
        if repo_root and '.' not in html_path.split('/')[-1]:
            for ext in ['.png', '.jpg', '.jpeg', '.svg', '.gif', '.pdf']:
                candidate = html_path + ext
                full = Path(repo_root) / candidate
                if full.exists():
                    html_path = candidate
                    break
        # Use style-based sizing (consistent with \simpleImageWithCaption)
        style_parts = ['height:auto', 'display:block', 'margin:1em auto']
        # Sound images use 50% width; other images use pixel width if available
        if 'sound' in path.lower():
            style_parts.insert(0, 'max-width:50%')
        elif width:
            # Avoid double suffix (e.g., '100%px')
            if isinstance(width, str) and '%' in width:
                style_parts.insert(0, f'max-width:{width}')
            else:
                style_parts.insert(0, f'max-width:{width}px')
        else:
            style_parts.insert(0, 'max-width:100%')
        style = '; '.join(style_parts)
        return '<img src="{}" alt="{}" style="{}" />'.format(html_path, path, style)
    content = re.sub(pattern, replace_image, content)
    return content


def process_content(content, base_dir, repo_root=None):
    """Main content processing function."""
    # Math protection registry - populated after file inclusion
    _math_registry = {}
    _math_counter = [0]
    
    # Process \input{} commands first
    input_pattern = r'\\input\{([^}]+)\}'
    def replace_input(m):
        path = m.group(1)
        return resolve_input(path, base_dir, repo_root=repo_root)
    content = re.sub(input_pattern, replace_input, content)

    # Process \include{} commands
    include_pattern = r'\\include\{([^}]+)\}'
    def replace_include(m):
        path = m.group(1) + ".tex"
        return resolve_input(path, base_dir, repo_root=repo_root)
    content = re.sub(include_pattern, replace_include, content)

    # Strip LaTeX grouping parens around $ math like ($ ... $)
    # These are common in mandelbulber source and cause ($ artifacts
    content = re.sub(r'\(\$', '$', content)
    content = re.sub(r'\$\)', '$', content)
    
    # =====================================================================
    # PROTECT MATH CONTENT - extract \[...\], \(...\), and $...$ before processing
    # Must run AFTER file inclusion so math from included files is captured
    # =====================================================================
    BS = chr(92)  # backslash character
    def extract_display_math(text):
        result = []
        i = 0
        while i < len(text):
            if text[i] == BS and i + 1 < len(text) and text[i+1] == '[':
                j = i + 2
                depth = 1
                while j < len(text) and depth > 0:
                    if text[j] == BS and j + 1 < len(text) and text[j+1] == '[':
                        depth += 1
                        j += 1
                    elif text[j] == BS and j + 1 < len(text) and text[j+1] == ']':
                        depth -= 1
                        j += 1
                    j += 1
                if depth == 0:
                    math_content = text[i+2:j-2]
                    _math_counter[0] += 1
                    key = f"__MATH_PLACEHOLDER_{_math_counter[0]}__"
                    _math_registry[key] = ("display", math_content)
                    result.append(key)
                    i = j
                    continue
            result.append(text[i])
            i += 1
        return ''.join(result)
    
    def extract_inline_math(text):
        result = []
        i = 0
        while i < len(text):
            if text[i] == BS and i + 1 < len(text) and text[i+1] == '(':
                j = i + 2
                depth = 1
                while j < len(text) and depth > 0:
                    if text[j] == BS and j + 1 < len(text) and text[j+1] == '(':
                        depth += 1
                        j += 1
                    elif text[j] == BS and j + 1 < len(text) and text[j+1] == ')':
                        depth -= 1
                        j += 1
                    j += 1
                if depth == 0:
                    math_content = text[i+2:j-2]
                    _math_counter[0] += 1
                    key = f"__MATH_PLACEHOLDER_{_math_counter[0]}__"
                    _math_registry[key] = ("inline", math_content)
                    result.append(key)
                    i = j
                    continue
            result.append(text[i])
            i += 1
        return ''.join(result)
    
    def extract_dollar_math(text):
        # Conservative: $ delimiters should only capture short inline math
        # Allow at most 1 newline and content < 200 chars to avoid capturing paragraphs
        result = []
        i = 0
        while i < len(text):
            if text[i] == '$' and (i + 1 >= len(text) or text[i+1] != '$'):
                j = i + 1
                newline_count = 0
                while j < len(text):
                    if text[j] == '\n':
                        newline_count += 1
                        if newline_count > 1:
                            break
                    if text[j] == '$' and (j + 1 >= len(text) or text[j+1] != '$'):
                        break
                    j += 1
                if j < len(text) and text[j] == '$':
                    math_content = text[i+1:j]
                    # Only protect if content is short (inline math)
                    if len(math_content) < 200:
                        _math_counter[0] += 1
                        key = f"__MATH_PLACEHOLDER_{_math_counter[0]}__"
                        _math_registry[key] = ("inline", math_content)
                        result.append(key)
                        i = j + 1
                        continue
            result.append(text[i])
            i += 1
        return ''.join(result)
    
    content = extract_display_math(content)
    content = extract_inline_math(content)
    content = extract_dollar_math(content)
    
    # Extract \newcommand definitions to a dict, then replace bare \mX refs
    metadata = {}
    
    def extract_command_value(content, start_pos, cmd_name):
        """Find the value after \\newcommand{\\cmd_name}{ by counting braces.
        
        start_pos is already past the opening { of the value, so depth starts at 1.
        """
        depth = 1
        i = start_pos
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    value = content[start_pos:i]
                    value = value.strip()
                    if value.startswith('{') and value.endswith('}'):
                        value = value[1:-1]
                    return value
            i += 1
        return None
    
    # Extract \newcommand{\mX}{value} for metadata commands (m*)
    pos = 0
    while pos < len(content):
        m = re.search(r'\\newcommand{\\(m[a-zA-Z]+)}{', content[pos:])
        if not m:
            break
        cmd_name = m.group(1)
        value_start = pos + m.end()
        value = extract_command_value(content, value_start, cmd_name)
        if value is not None:
            metadata[cmd_name] = value
            # Remove this definition from content
            # Find the end of the full \newcommand{\cmd_name}{value}
            end_pos = value_start
            depth = 1  # The opening { of the value was already consumed by the regex
            for j in range(value_start, len(content)):
                if content[j] == '{':
                    depth += 1
                elif content[j] == '}':
                    depth -= 1
                    if depth == 0:
                        end_pos = j + 1
                        break
            match_start = pos + m.start()
            content = content[:match_start] + content[end_pos:]
        pos = pos + m.start() + 1
    
    # Also extract \renewcommand for things like \baselinestretch
    pos = 0
    while pos < len(content):
        m = re.search(r'\\renewcommand{\\([a-zA-Z]+)}{', content[pos:])
        if not m:
            break
        cmd_name = m.group(1)
        value_start = pos + m.end()
        value = extract_command_value(content, value_start, cmd_name)
        if value is not None:
            metadata[cmd_name] = value
            # Find the end of the full \renewcommand{\cmd_name}{value}
            end_pos = value_start
            depth = 1  # The opening { of the value was already consumed by the regex
            for j in range(value_start, len(content)):
                if content[j] == '{':
                    depth += 1
                elif content[j] == '}':
                    depth -= 1
                    if depth == 0:
                        end_pos = j + 1
                        break
            # Use match start position, not search start position
            match_start = pos + m.start()
            content = content[:match_start] + content[end_pos:]
        pos = pos + m.start() + 1
    
    # After extracting renewcommand values, strip any leftover baselinestretch
    # (it's a formatting command, not content)
    content = re.sub(r'\\baselinestretch(\\)?\s*', '', content)
    
    # Extract verbatim environments BEFORE macro replacement to protect their content
    _verbatim_registry = {}
    _verbatim_counter = [0]
    verbatim_pattern = r'\\begin\{verbatim\}(?:\[[^\]]*\])?(.*?)\\end\{verbatim\}'
    def protect_verbatim(m):
        _verbatim_counter[0] += 1
        key = f'__VERBATIM_{_verbatim_counter[0]}__'
        _verbatim_registry[key] = m.group(1)
        return key
    content = re.sub(verbatim_pattern, protect_verbatim, content, flags=re.DOTALL)
    
    # Replace bare \\mX commands with extracted values
    for key, value in metadata.items():
        # Escape backslashes in value for use in re.sub replacement string
        escaped_value = value.replace('\\', '\\\\')
        # Also unescape & in value to prevent double-escaping
        escaped_value = escaped_value.replace('&amp;', '&').replace('&', '&amp;')
        # Replace \\mX{...} first (with arguments), then bare \\mX
        # Use brace-aware matching for \\mX{...}
        pattern_x = r'\\' + re.escape(key) + r'\{'
        def replace_mx_braced(m):
            return escaped_value
        content = re.sub(pattern_x, replace_mx_braced, content)
        content = re.sub(r'\\' + re.escape(key) + r'\s*', escaped_value, content)

    # Restore protected verbatim environments
            # Debug: check verbatim HTML newlines
    # Pre-process \item commands inside description environments
    # This runs BEFORE env_pattern to handle nested descriptions
    # Pre-process \item commands inside description environments
    # This runs BEFORE env_pattern to handle nested descriptions and itemize
    def process_description_items(m):
        body = m.group(1)
        items = []
        current_item = None
        depth = 0
        nested_buf = []
        itemize_depth = 0
        itemize_buf = []
        for line in body.split("\n"):
            stripped = line.strip()
            if stripped.startswith("\begin{description}"):
                if depth == 0:
                    nested_buf = []
                depth += 1
                continue
            if stripped.startswith("\end{description}"):
                depth -= 1
                if depth == 0:
                    if current_item is not None:
                        items.append(f"<li>{current_item}</li>")
                        current_item = None
                    nested_body = "\n".join(nested_buf)
                    nested_items = []
                    nested_current = None
                    for nline in nested_body.split("\n"):
                        nstripped = nline.strip()
                        if nstripped.startswith("\item"):
                            if nested_current is not None:
                                nested_items.append(f"<li>{nested_current}</li>")
                            nrest = nstripped[5:]
                            if nrest.startswith(' '):
                                nrest = nrest[1:]
                            if nrest.startswith('['):
                                nbe = nrest.find(']')
                                if nbe != -1:
                                    nlabel = nrest[1:nbe]
                                    ndesc = nrest[nbe+1:].strip()
                                    nested_current = f"<strong>{nlabel}</strong> {ndesc}"
                                    continue
                            nested_current = nrest.strip()
                        elif nested_current is not None and nstripped:
                            nested_current += f" {nstripped}"
                    if nested_current is not None:
                        nested_items.append(f"<li>{nested_current}</li>")
                    items.append(f"<ul>{chr(10).join(nested_items)}</ul>")
                    nested_buf = []
                continue
            if depth > 0:
                nested_buf.append(stripped)
                continue
            # Handle nested itemize inside description items
            if stripped.startswith("\begin{itemize}"):
                itemize_depth += 1
                itemize_buf = []
                continue
            if stripped.startswith("\end{itemize}"):
                itemize_depth -= 1
                if itemize_depth == 0:
                    # Convert buffered itemize items to <ul><li>
                    ul_items = []
                    for iline in itemize_buf:
                        istripped = iline.strip()
                        if istripped.startswith("\item"):
                            item_text = istripped[5:].strip()
                            ul_items.append(f"<li>{item_text}</li>")
                    if ul_items:
                        ul_html = "\n".join(ul_items)
                        if current_item is not None:
                            current_item += f" <ul>{ul_html}</ul>"
                        else:
                            items.append(f"<ul>{ul_html}</ul>")
                    itemize_buf = []
                continue
            if itemize_depth > 0:
                itemize_buf.append(stripped)
                continue
            if stripped.startswith("\item"):
                if current_item is not None:
                    items.append(f"<li>{current_item}</li>")
                rest = stripped[5:]
                if rest.startswith(' '):
                    rest = rest[1:]
                if rest.startswith('['):
                    bracket_end = rest.find(']')
                    if bracket_end != -1:
                        label = rest[1:bracket_end]
                        desc_text = rest[bracket_end+1:].strip()
                        current_item = f"<strong>{label}</strong> {desc_text}"
                        continue
                current_item = rest.strip()
            elif current_item is not None and stripped:
                current_item += f" {stripped}"
        if current_item is not None:
            items.append(f"<li>{current_item}</li>")
        return "\n".join(items)
        # Process description environments with nested support
        # Scan for matching begin/end pairs to handle nesting
        desc_blocks = []
        desc_depth = 0
        desc_start = None
        for dm in re.finditer(r"\\\\begin\{description\}|\\\\end\{description\}", content):
            if dm.group().startswith("\\\\begin"):
                if desc_depth == 0:
                    desc_start = dm.end()
                desc_depth += 1
            else:
                desc_depth -= 1
                if desc_depth == 0 and desc_start is not None:
                    desc_blocks.append((desc_start, dm.start()))
                    desc_start = None
        # Process from end to preserve positions
        for s, e in reversed(desc_blocks):
            body = content[s:e]
            result = process_description_items(type("m", (), {"group": lambda i: body})())
            content = content[:s - len("\\\\begin{description}")] + result + content[e + len("\\\\end{description}"):]  



    env_pattern = r'\\begin\{([^}]+)\}(?:\[[^\]]*\])?(?:\{(?:(?:[^{}]*\{[^{}]*\})*[^{}]*)\})?(.*?)\\end\{\1\}'
    def replace_env(m):
        env_name = m.group(1)
        body = m.group(2)
        if env_name == "verbatim":
            cleaned = escape(body)
            cleaned = re.sub(r'\[fontsize=\]', '', cleaned)
            return f'<pre class="verbatim">{cleaned}</pre>'
        elif env_name == "figure":
            # Process figure environments (basic)
            # Strip caption from figure body - processed globally
            # Preserve \caption{} for global caption processing
            # Extract \caption{} and place inside figure properly
            if caption_match:
                # Remove caption from body to prevent double-processing
                clean_body = re.sub(r'\\\\caption\{[^}]*\}', '', body)
                # Caption will be processed by global handler - just return figure with clean body
                return f'<figure class="figure">{clean_body}</figure>'
            else:
                return f'<figure class="figure">{body}</figure>'
            # Convert tabular content: & -> cell delimiter, \\ -> row delimiter
            # Only process if content actually has & cell delimiters
            if '&' not in body:
                return body
            lines = re.split(r'\\\\(?=\s*$|\s)', body)
            rows = []
            for line in lines:
                line = line.strip()
                # Skip column spec lines (first line usually has {l|c|c} etc.)
                if re.match(r'^\s*\{[^}]*\}\s*$', line):
                    continue
                # Also match unbraced column specs like l|c|c or r|p{11cm}
                # Use brace counting for specs with nested braces (e.g. r|p{11cm})
                stripped = line.strip()
                if stripped:
                    depth = 0
                    is_col_spec = True
                    for ch in stripped:
                        if ch == '{':
                            depth += 1
                        elif ch == '}':
                            depth -= 1
                        elif ch not in 'lrcLRCpP|.1234567890 ':
                            is_col_spec = False
                            break
                    if depth == 0 and is_col_spec:
                        continue
                # Match braced column specs with nested braces (e.g. {r|p{11cm}})
                # Use brace counting since regex can't handle nested braces
                if line.strip().startswith('{'):
                    depth = 0
                    valid_col_spec = True
                    for ch in line.strip():
                        if ch == '{':
                            depth += 1
                        elif ch == '}':
                            depth -= 1
                        elif ch not in 'lrcLRCpP|.1234567890 ':
                            valid_col_spec = False
                            break
                    if depth == 0 and valid_col_spec:
                        continue
                cells = line.split('&')
                row_cells = []
                for cell in cells:
                    cell = cell.strip()
                    # Strip leading/trailing { and } from cell content
                    while cell.startswith('{') and cell.endswith('}'):
                        cell = cell[1:-1]
                    # Strip leading &amp; that leaked from cell separator
                    while cell.startswith('&amp;'):
                        cell = cell[5:]
                    while cell.startswith('&'):
                        cell = cell[1:]
                    cell = cell.strip()
                    # Preserve & as &amp; in cell content (handle both \& and &)
                    cell = cell.replace('\&', '&amp;')
                    cell = cell.replace('&', '&amp;')
                    row_cells.append(f'<td>{cell}</td>')
                rows.append(f'<tr>{"".join(row_cells)}</tr>')
            table_html = f'<table class="table"><tbody>{"".join(rows)}</tbody></table>'
            # Strip leading &amp; from cells (leaked cell separator)
            table_html = re.sub(r'<td>\\s*&amp;\\s*', '<td>', table_html)
            return table_html
        elif env_name == "itemize":
            items = []
            current_item = None
            for line in body.split("\n"):
                stripped = line.strip()
                if stripped.startswith("\\item"):
                    if current_item is not None:
                        items.append(f"<li>{current_item}</li>")
                    rest = stripped[5:]
                    if rest.startswith('['):
                        bracket_end = rest.find(']')
                        if bracket_end != -1:
                            desc = rest[:bracket_end+1].strip()
                            content_text = rest[bracket_end+1:].strip()
                            current_item = f"{desc} {content_text}"
                            continue
                    current_item = rest.strip()
                elif current_item is not None and stripped:
                    current_item += f" {stripped}"
            if current_item is not None:
                items.append(f"<li>{current_item}</li>")
            return f"<ul>{chr(10).join(items)}</ul>"
        elif env_name == "enumerate":
            items = []
            current_item = None
            counter = 0
            for line in body.split("\n"):
                stripped = line.strip()
                if stripped.startswith("\\item"):
                    counter += 1
                    if current_item is not None:
                        items.append(f"<li>{current_item}</li>")
                    rest = stripped[5:]
                    current_item = rest.strip()
                elif current_item is not None and stripped:
                    current_item += f" {stripped}"
            if current_item is not None:
                items.append(f"<li>{current_item}</li>")
            return f"<ol>{chr(10).join(items)}</ol>"
        elif env_name == "quote":
            return f"<blockquote>{body}</blockquote>"
        elif env_name == "quotation":
            return f"<blockquote>{body}</blockquote>"
        elif env_name in ("bmatrix", "pmatrix", "array", "matrix"):
            # Convert \\\\ row separators to <br> and & to cell separators
            body = body.replace("\\", "<br>")
            body = body.replace("&", " & ")
            return f'<span class="math-matrix">{body}</span>'
        elif env_name == "center":
            # Just a wrapper, return body so nested envs (tabular) get processed
            return body
        elif env_name == "minipage":
            # \begin{minipage}[b]{0.5\linewidth} — strip optional [arg] and {arg}
            return body
        elif env_name == "description":
            return body
        elif env_name == "tabular":
            # Convert tabular content: & -> cell delimiter, \\ -> row delimiter
            # Only process if content actually has & cell delimiters
            if '&' not in body:
                return f'<div class="tabular">{body}</div>'
            lines = body.split('\\\\')
            rows = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # Skip column spec lines (first line usually has {l|c|c} etc.)
                if re.match(r'^\s*\{[^}]*\}\s*$', line):
                    continue
                # Also match unbraced column specs like l|c|c or r|p{11cm}
                stripped = line.strip()
                if stripped:
                    depth = 0
                    is_col_spec = True
                    for ch in stripped:
                        if ch == '{':
                            depth += 1
                        elif ch == '}':
                            depth -= 1
                        elif ch not in 'lrcLRCpP|.1234567890 ':
                            is_col_spec = False
                            break
                    if depth == 0 and is_col_spec:
                        continue
                # Match braced column specs with nested braces
                if line.strip().startswith('{'):
                    depth = 0
                    valid_col_spec = True
                    for ch in line.strip():
                        if ch == '{':
                            depth += 1
                        elif ch == '}':
                            depth -= 1
                        elif ch not in 'lrcLRCpP|.1234567890 ':
                            valid_col_spec = False
                            break
                    if depth == 0 and valid_col_spec:
                        continue
                cells = line.split('&')
                row_cells = []
                for cell in cells:
                    cell = cell.strip()
                    # Strip leading/trailing { and } from cell content
                    while cell.startswith('{') and cell.endswith('}'):
                        cell = cell[1:-1]
                    # Strip leading &amp; that leaked from cell separator
                    while cell.startswith('&amp;'):
                        cell = cell[5:]
                    while cell.startswith('&'):
                        cell = cell[1:]
                    cell = cell.strip()
                    # Preserve & as &amp; in cell content
                    cell = cell.replace('\&', '&amp;')
                    cell = cell.replace('&', '&amp;')
                    row_cells.append(f'<td>{cell}</td>')
                rows.append(f'<tr>{"".join(row_cells)}</tr>')
            if rows:
                return f'<table class="table"><tbody>{"".join(rows)}</tbody></table>'
            return f'<div class="tabular">{body}</div>'

        else:
            return f'<div class="{env_name}">{body}</div>'
    # Process environments iteratively to handle nesting (center > tabular)
    prev = None
    env_iter = 0
    while prev != content and env_iter < 10:
        prev = content
        content = re.sub(env_pattern, replace_env, content, flags=re.DOTALL)
        env_iter += 1

    # Process \lstinputlisting[caption={...}]{code/path} — code file references
    def replace_lstinputlisting(m):
        opts = m.group(1) or ""
        path = m.group(2)
        # Extract caption if present: caption={Formula > Mandelbulb constructor}
        caption_match = re.search(r'caption=\{([^}]*)\}', opts)
        caption = caption_match.group(1) if caption_match else path
        # Try to read the source file; fall back to placeholder
        file_path = Path(repo_root) / path if repo_root else None
        code_content = ""
        if file_path and file_path.exists():
            try:
                code_content = file_path.read_text(encoding="utf-8")
            except Exception:
                code_content = f"/* Source file '{path}' not available */"
        else:
            code_content = f"/* Source file '{path}' not available in repository */"
        escaped = escape(code_content)
        return f'<pre class="code-block"><code class="language-cpp">{escaped}</code></pre><p class="code-caption">{caption}</p>'
    content = re.sub(r'\\lstinputlisting\[([^\]]*)\]\{([^}]+)\}', replace_lstinputlisting, content)

    # Process images BEFORE other commands (to avoid double-processing)
    content = process_image_macro(content, repo_root=repo_root)

    # Pre-process \frac{num}{den} and \sqrt{expr} before the main loop
    # These have two separate brace arguments that the general regex can't handle
    def replace_frac(m):
        num = m.group(1)
        den = m.group(2)
        return f"<sup>{num}</sup>/<sub>{den}</sub>"
    content = re.sub(r'\\frac\{([^}]*)\}\{([^}]*)\}', replace_frac, content)

    def replace_sqrt(m):
        expr = m.group(1)
        return f"<sup>&radic;({expr})</sup>"
    content = re.sub(r'\\sqrt\{([^}]*)\}', replace_sqrt, content)

    # Strip multi-line makro.tex image macro calls (images don't exist in repo)
    # threeImagesWithTwoCaptionsFullWidth — variable args on separate lines
    # twoImagesWithTwoCaptionsFullWidth — variable args, optional newline before first arg
    # simpleImageWithCaption + suffix — first arg on same line, H/h marker at end
    # All must run BEFORE the general cmd_pattern loop
    
    # threeImages: macro on own line, 9 args total (3x {img},{caption},{ref_id})
    # First arg may be on same line or next line (with/without tab)
    content = re.sub(
        r'\\threeImagesWithTwoCaptionsFullWidth\s*\{[^}]*\}(?:\s*\{[^}]*\}){6,}\s*\{[^}]*\}\s*\{[^}]*\}',
        '', content, flags=re.DOTALL
    )
    # twoImages: variable args (3-11+), first arg may be on same line, {H}/{h} may be on same line as last arg
    content = re.sub(
        r'\\twoImagesWithTwoCaptionsFullWidth\s*(?:\s*\{[^}]*\})+',
        '', content, flags=re.DOTALL
    )
    # simpleImageWithCaption + suffix — variable args (1+), may be single-line or multi-line
    content = re.sub(
        r'\\simpleImageWithCaption(75Width|FullWidth|HalfWidth|SmallWidth|ThirdWidth)\s*(?:\s*\{[^}]*\})+',
        '', content, flags=re.DOTALL
    )
    

    # Strip \specialrule{thickness}{above}{below} - multi-arg command
    content = re.sub(r'\\specialrule(?:\s*\{[^}]*\}){1,4}', '', content)

    # Strip \break (page break) and \vfill (vertical filler)
    content = re.sub(r'\\break\s*', '', content)
    content = re.sub(r'\\vfill\s*', '', content)
    # Process commands iteratively until stable (handles nested \textbf{\emph{text}})
    # Use brace-aware regex that handles one level of nesting



    # Pre-process \\textcolor with nested braces (process from inside out)
    # This handles cases like \\textcolor{yellow}{\\textcolor{black}{Yellow}}
    # which the generic cmd_pattern cannot handle due to nested braces
    def process_textcolor(content):
        max_iter = 50
        while max_iter > 0:
            max_iter -= 1
            m = re.search(r'\\textcolor\{([^{}]+)\}\{([^{}]*)\}', content)
            if not m:
                break
            color = m.group(1)
            text = m.group(2)
            replacement = f'<span style="color:{color}">{text}</span>'
            content = content[:m.start()] + replacement + content[m.end():]
        return content
    content = process_textcolor(content)

    cmd_pattern = r'\\([a-zA-Z]+)\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
    prev = None
    iteration = 0
    while prev != content and iteration < 20:
        prev = content
        content = re.sub(cmd_pattern, process_command, content)
        iteration += 1
    if iteration >= 20:
        print("Warning: command processing hit 20 iterations, some nesting may remain")

    # Convert LaTeX -- (en-dash) and --- (em-dash) to HTML equivalents
    content = content.replace(' -- ', ' – ')
    content = content.replace('---', '—')

    # Clean up unprocessed \href second args: {text} left after </a> when source has \href{URL} {text} with space
    content = re.sub(r'</a>\s*\{[^}]*\}', r'</a>', content)
    
    # Post-process: fix \emph{} artifacts that contain HTML tags from failed brace nesting
    emph_pattern = r'\\emph\{([^}]*(?:\{[^}]*\})?[^}]*)\}'
    def fix_emph(m):
        inner = m.group(1)
        # Strip any HTML tags
        inner = re.sub(r'<[^>]+>', '', inner)
        # Unescape LaTeX escapes
        inner = inner.replace('\\_', '_')
        return f'<em>{inner}</em>'
    content = re.sub(emph_pattern, fix_emph, content)
    
    # Post-process: fix remaining unprocessed nested brace patterns
    # These are LITERAL curly braces in the HTML (not backslash-escaped)
    # Strip tabular column specs like {l|c|c}, {r|p{11cm}}, {c}
    # Strip tabular column specs - both with and without inner braces
    content = re.sub(r'\{(?:[lrcLRCpP@\d\|\.]+(?:\{[^}]*\})?)*\}\s*', '', content)
    def fix_braces(m):
        text = m.group(0)
        # Unescape LaTeX escapes
        text = text.replace('\\_', '_').replace('\\#', '#').replace('\\$', '$')
        # Remove outer braces
        if text.startswith('{') and text.endswith('}'):
            text = text[1:-1]
        return text
    # Fix {begin{...}}, {end{...}} patterns (literal braces in HTML)
    content = re.sub(r'\{begin\{[^}]+\}\}', fix_braces, content)
    content = re.sub(r'\{end\{[^}]+\}\}', fix_braces, content)
    # Fix {texttt{...}}, {textbf{...}} etc.
    for cmd in ['texttt', 'textbf', 'textit', 'text', 'bf', 'it', 'tt']:
        content = re.sub(r'\{' + cmd + r'\{([^}]*)\}\}', fix_braces, content)
    # Fix {textgreater{}} patterns
    content = re.sub(r'\{textgreater\{\}\}', '>', content)
    # Fix twoImagesWithTwoCaptionsFullWidth{...} patterns
    content = re.sub(r'\{twoImagesWithTwoCaptionsFullWidth\{([^}]*)\}\}', lambda m: m.group(1), content)
    # Fix {[}...{]} literal bracket patterns
    content = re.sub(r'\{\[\}([^}]*)\{\]\}', r'[\1]', content)
    # Strip custom image markers {id}{H} and {id}{h} from makro.tex (images don't exist in repo)
    # Pattern: {id}{H} or {id}{h} where id is a non-space identifier
    content = re.sub(r'\{([^\s{}]+)\}\{[Hh]\}', r'', content)
    # Strip standalone {H} and {h} closing markers on their own lines
    content = re.sub(r'^\s*\{[Hh]\}\s*$', '', content, flags=re.MULTILINE)
    # Strip {img/...} remnants from unexpanded makro.tex macros (images don't exist in repo)
    content = re.sub(r'\{img/[^}]+\}', '', content)
    # Strip stray bare group delimiters ({ or } on their own line)
    content = re.sub(r'\n\s*\{\s*\n', '\n', content)
    # Strip stray closing braces/tabs that leak before content
    content = re.sub(r'\n\s*}\s*\n', '\n', content)
    
    # Strip bare {caption text} patterns left by makro.tex macro expansion
    content = re.sub(r'\{([^{}]+)\}\s*$', lambda m: m.group(1), content, flags=re.MULTILINE)
    # Strip {text} patterns anywhere in line (not just at end)
    content = re.sub(r'\{([^{}]+)\}', lambda m: m.group(1), content)
    
    # Convert remaining \item commands to <li></li> tags (both open and close)
    content = re.sub(r'\\item\s*(.*)', lambda m: '<li>' + m.group(1).rstrip() + '</li>', content, flags=re.MULTILINE)
    
    # Strip bare LaTeX commands that have no HTML equivalent
    for bare_cmd in ['nopagebreak', 'pagebreak', 'clearpage', 'bigskip', 'medskip', 'smallskip',
                     'normalsize', 'scriptsize', 'break', 'vfill', 'newpage', 'grid',
                     'linewidth', 'nolinebreak', 'large',
                     'baselinestretch']:
        content = re.sub(r'\\' + bare_cmd + r'\s*', '', content)

    # Document structure commands - strip (TOC already generated)
    for struct_cmd in ['tableofcontents', 'listoffigures', 'lstlistoflistings', 'printindex']:
        content = re.sub(r'\\' + struct_cmd + r'\s*', '', content)

    # Metadata macros - strip
#     for meta_cmd in ['mTitle', 'mSubtitle', 'mAuthor', 'mDateDocument', 'mVersionDocument']:
#         content = re.sub(r'\\' + meta_cmd + r'\s*', '', content)
# 
    # Huge - size command without args in output, strip
    content = re.sub(r'\\Huge\s*', '', content)

    # Program, Mandelbulber - custom macros, strip (skip inside <pre> blocks)
    for custom_cmd in ['Program', 'Mandelbulber']:
        def strip_outside_pre(m):
            before = m.string[:m.start()]
            in_pre = before.count('<pre') - before.count('</pre>')
            return '' if in_pre == 0 else m.group(0)
        content = re.sub(r'\\' + custom_cmd + r'\s*', strip_outside_pre, content)

    # hline - table horizontal line -> <hr>
    content = re.sub(r'\\hline', '<hr>', content)

    # Number all captions in document order (both \caption{} and manual figcaps)
    # Split by <h1> tags so each section gets its own figure counter
    def number_captions_in_section(section_content, sec_num):
        global _figure_counter
        fig_count = [0]
        def repl(m):
            fig_count[0] += 1
            _figure_counter[0] += 1
            fig_num = f"{sec_num}.{fig_count[0]}"
            if m.group(1) is not None:
                return f'<figcaption class="caption">Figure {fig_num}: {m.group(1)}</figcaption>'
            else:
                return f'<figcaption class="figcaption">Figure {fig_num}: {m.group(2)}</figcaption>'
        return re.sub(r'\\caption\{([^}]*)\}|<figcaption class="figcaption">__FIGNUM__ ([^<]*)</figcaption>', repl, section_content)
    # Split content into sections by <h1> tags
    parts = re.split(r'(<h1[^>]*>.*?</h1>)', content)
    # First part is before any <h1>
    sec_num = 1
    new_parts = []
    for j, part in enumerate(parts):
        if part.startswith('<h1'):
            # Extract section number from h1
            h1_m = re.search(r'>(\d+)\.\s', part)
            if h1_m:
                sec_num = int(h1_m.group(1))
            new_parts.append(part)
        else:
            new_parts.append(number_captions_in_section(part, sec_num))
    content = ''.join(new_parts)


    # Convert \\\\ (LaTeX line breaks) to <br> BEFORE stripping - this preserves row breaks
    # in tabular environments where the tabular handler is dead code
    content = re.sub(r'\\\\(?=$|\s)', '<br>', content, flags=re.MULTILINE)

    # Strip \\\\ (LaTeX line breaks) that leaked outside tabular
    content = re.sub(r'\\\\\\\\s*', '', content)
    


    # Process LaTeX escapes: \# -> #, \$ -> $, etc.
    content = content.replace('\\#', '#')
    content = content.replace('\\\\$', '$')
    content = content.replace('\\\\%', '%')
    content = content.replace('\\\\&', '&')
    content = content.replace('\\\\_', '_')
    # Fix remaining \\_ -> _ (double-backslash-underscore)
    content = content.replace('\\\_', '_')
    # Fix remaining \_ -> _ (single backslash-underscore)
    content = content.replace('\\_', '_')

    # Math symbols - map to HTML entities
    content = content.replace('\\ast', chr(8727))
    content = content.replace('\\cdot', chr(8901))
    content = content.replace('\\leq', chr(8804))
    content = content.replace('\\le', chr(8804))
    content = content.replace('\\lvert', '|')
    content = content.replace('\\rvert', '|')
    content = content.replace('\\textbackslash', '\\')
    # Remove space after backslash in paths (textbackslash often has space in tex)
    content = content.replace('\\ ', '\\')
    content = content.replace('\\textgreater', '&gt;')
    content = content.replace('\\times', chr(215))
    content = content.replace('\\space', ' ')
    content = content.replace('\\log', 'log')
    content = content.replace('\\max', 'max')
    content = content.replace('\\le ', 'le ')

    # ldots -> ellipsis
    content = content.replace('\\ldots', chr(8230))

    # tt - typewriter, already handled in process_command but appears as bare in output
    content = re.sub(r'\\tt', '', content)
    
    
    # Fix double-escaped entities: &amp;radic; -> &radic; etc.
    content = content.replace('&amp;radic;', '&radic;')
    content = content.replace('&amp;hellip;', '&hellip;')
    content = content.replace('&amp;mdash;', '&mdash;')
    content = content.replace('&amp;ndash;', '&ndash;')
    content = content.replace('&amp;bull;', '&bull;')
    content = content.replace('&amp;times;', '&times;')
    content = content.replace('&amp;laquo;', '&laquo;')
    content = content.replace('&amp;raquo;', '&raquo;')
    content = content.replace('&amp;copy;', '&copy;')
    content = content.replace('&amp;reg;', '&reg;')
    content = content.replace('&amp;trade;', '&trade;')
    content = content.replace('&amp;euro;', '&euro;')
    content = content.replace('&amp;pound;', '&pound;')

    # Strip orphaned numbers/fragments immediately before heading tags
    content = re.sub(r'\n\s*\d+\.\d+\s*(?=<h[1-6])', '\n', content)
    # Also strip orphaned baselinestretch values at content start
    content = re.sub(r'^\s*\d+\.\d+\s*', '', content)
    


    # Strip stray & (LaTeX tabular column separators) that leaked outside tabular environments
    # These appear in titlepage divs where & is used but not inside \begin{tabular}
    # First, fix double-escaped &&amp; -> remove the extra &
    content = content.replace('&&amp;', '&amp;')
    # Then strip standalone & that appear between content and links (column separators)
    # Pattern: & followed by <a or & preceded by </a> (column delimiters)
    content = re.sub(r'</a>\s*&\s*<span', '</a> <span', content)
    content = re.sub(r'</a>\s*&\s*<a', '</a> <a', content)
    content = re.sub(r'<span[^>]*>\s*&\s*<a', '<span> <a', content)
    # Strip any remaining standalone & between text and links
    content = re.sub(r'(?<=</a>)\s*&\s*(?=<span)', '', content)
    content = re.sub(r'(?<=</a>)\s*&\s*(?=<a)', '', content)
    content = re.sub(r'(?<=</a>)\s*&\s*(?=\s*$)', '', content, flags=re.MULTILINE)
    # Strip leading & from paragraphs (leftover column separator)
    content = re.sub(r'<p>\s*&\s*(&amp;)?\s*', '<p>', content)
    content = re.sub(r'<p>\s*(&amp;)\s*', '<p>', content)
    # Strip trailing & from paragraphs
    content = re.sub(r'\s*&\s*</p>', '</p>', content)
    content = re.sub(r'\s*(&amp;)\s*</p>', '</p>', content)
    # Clean up &&amp; -> just the email/link content
    content = re.sub(r'\s*&&amp;\s*', ' ', content)
    content = re.sub(r'\s*&&\s*', ' ', content)
    content = re.sub(r'\s*&\s*<a', ' <a', content)
    content = re.sub(r'</a>\s*&\s*', '</a> ', content)
    content = re.sub(r'(?<=:</span>)\s*&\s*', ' ', content)
    content = re.sub(r'(?<=:</span>)\s*&&amp;\s*', ' ', content)
    content = re.sub(r'(?<=:</span>)\s*&&\s*', ' ', content)

    # Strip trailing \\ (LaTeX line breaks) that leaked outside tabular
    content = re.sub(r'\\\\\s*(?=\n|<)', '', content)
    
    # =====================================================================
    # RESTORE MATH CONTENT - unwrap protected math and wrap for MathJax
    # =====================================================================
    for key, (math_type, math_content) in _math_registry.items():
        # Strip leading/trailing parens from math content (LaTeX grouping like ($ ... $))
        math_content = math_content.strip()
        if math_content.startswith('(') and math_content.endswith(')'):
            math_content = math_content[1:-1].strip()
        if math_type == "display":
            wrapped = '\n$$' + math_content.strip() + '$$\n'
        else:
            # Add space before $ if preceded by alphanumeric/punctuation, after $ if followed by such
            wrapped = ' $' + math_content.strip() + '$ '
        content = content.replace(key, wrapped)

    # Convert literal [a], [b], [c] etc. to HTML entities to prevent MathJax from treating them as math
    # These are common in mandelbulber source as references to variables
    content = re.sub(r'\[([a-zA-Z0-9_]+)\]', r'&#91;\1&#93;', content)

    
    # Balance unclosed list tags from nested enumerate/itemize
    ul_opens = len(re.findall(r'<ul', content))
    ul_closes = len(re.findall(r'</ul>', content))
    ol_opens = len(re.findall(r'<ol', content))
    ol_closes = len(re.findall(r'</ol>', content))
    li_opens = len(re.findall(r'<li>', content))
    li_closes = len(re.findall(r'</li>', content))
    div_opens = len(re.findall(r'<div[^/]', content))
    div_closes = len(re.findall(r'</div>', content))
    missing = ""
    if li_opens > li_closes:
        missing += "</li>" * (li_opens - li_closes)
    if ol_opens > ol_closes:
        missing += "</ol>" * (ol_opens - ol_closes)
    if ul_opens > ul_closes:
        missing += "</ul>" * (ul_opens - ul_closes)
    if missing:
        # Insert before </body> or at end
        if "</body>" in content:
            content = content.replace("</body>", missing + "</body>", 1)
        else:
            content = content + missing
    


    # =====================================================================
    # WRAP PARAGRAPHS - wrap unwrapped text in <p> tags
    # =====================================================================
    lines = content.split('\n')
    result = []
    paragraph_buffer = []
    block_depth = 0  # Track nesting inside <pre>, <table>
    
    def flush_paragraph():
        nonlocal paragraph_buffer
        if paragraph_buffer:
            text = ' '.join(t.strip() for t in paragraph_buffer if t.strip())
            if text:
                result.append('<p>' + text + '</p>')
            paragraph_buffer = []
    
    for line in lines:
        stripped = line.strip()
        # Skip empty lines
        if not stripped:
            if block_depth == 0:
                flush_paragraph()
            else:
                paragraph_buffer = []
            continue
        
        # Count ALL open/close tags on this line for block elements
        pre_opens = len(re.findall(r'<pre[^>]*>', stripped, re.IGNORECASE))
        pre_closes = len(re.findall(r'</pre>', stripped, re.IGNORECASE))
        table_opens = len(re.findall(r'<table[^>]*>', stripped, re.IGNORECASE))
        table_closes = len(re.findall(r'</table>', stripped, re.IGNORECASE))
        
        old_depth = block_depth
        block_depth += pre_opens + table_opens - pre_closes - table_closes
        block_depth = max(0, block_depth)
        
        # If entering, inside, or exiting a block element, don't wrap in <p>
        if block_depth > 0 or old_depth > 0 or pre_opens or pre_closes or table_opens or table_closes:
            if old_depth == 0 and (pre_opens or table_opens):
                flush_paragraph()  # flush before entering block
            else:
                paragraph_buffer = []
            result.append(line)
            continue

        # Skip lines that are already HTML block elements
        if re.match(r'^<(h[1-6]|ul|ol|li|table|tr|td|th|div|hr|pre|img|p|span|figcaption|br)', stripped, re.IGNORECASE):
            flush_paragraph()
            result.append(line)
            continue
        # Skip lines that are ONLY closing tags
        if re.match(r'^</?(h[1-6]|ul|ol|li|table|tr|td|th|div|pre|p|span|figcaption|br)[^>]*>$', stripped, re.IGNORECASE):
            flush_paragraph()
            result.append(line)
            continue
        # Skip lines that are ONLY HTML tags (no text content)
        if re.match(r'^<[^>]+>$', stripped, re.IGNORECASE):
            flush_paragraph()
            result.append(line)
            continue
        # This is text content - add to paragraph buffer
        if block_depth == 0:
            paragraph_buffer.append(stripped)
        else:
            result.append(line)
    
    # Flush any remaining paragraph
    flush_paragraph()
    
    content = '\n'.join(result)

    # =====================================================================

    # Cleanup: remove stray <p> tags inside <pre> blocks
    def remove_p_in_pre(match):
        pre_block = match.group(0)
        pre_block = re.sub(r'</?p\b[^>]*>', '', pre_block)
        return pre_block
    content = re.sub(r'<pre[^>]*>.*?</pre>', remove_p_in_pre, content, flags=re.DOTALL)


    # =====================================================================
    # BALANCE unclosed tags from nested enumerate/itemize and env processing
    # =====================================================================
    ul_opens = len(re.findall(r'<ul', content))
    ul_closes = len(re.findall(r'</ul>', content))
    ol_opens = len(re.findall(r'<ol', content))
    ol_closes = len(re.findall(r'</ol>', content))
    li_opens = len(re.findall(r'<li>', content))
    li_closes = len(re.findall(r'</li>', content))
    div_opens = len(re.findall(r'<div[^/]', content))
    div_closes = len(re.findall(r'</div>', content))
    missing = ""
    extra = ""
    if li_opens > li_closes:
        missing += "</li>" * (li_opens - li_closes)
    if ol_opens > ol_closes:
        missing += "</ol>" * (ol_opens - ol_closes)
    if ul_opens > ul_closes:
        missing += "</ul>" * (ul_opens - ul_closes)
    # Remove any extra </div> tags from content (titlepage/document wrappers)
    if div_closes > div_opens:
        extra_divs = div_closes - div_opens
        for _ in range(extra_divs):
            last_div = content.rfind("</div>")
            if last_div >= 0:
                content = content[:last_div] + content[last_div+7:]
    if missing:
        if "</body>" in content:
            content = content.replace("</body>", missing + "</body>", 1)
        else:
            content = content + missing


    # Fix: restore &amp; that lost its & prefix (e.g. in editors table)
    # Remove [fontsize=] from verbatim blocks
    content = re.sub(r'\[fontsize=\]', '', content)
    content = content.replace('amp;', '&amp;')
    # Strip leading &amp; from tabular cells (leaked cell separator)
    content = re.sub(r'<td>\s*&amp;\s*', '<td>', content)

    # Pair images with captions - section-aware, single pass per section
    sections = re.split(r'(<h1[^>]*>.*?</h1>)', content)
    paired = []
    sec_num = 1
    for part in sections:
        h1_match = re.match(r'<h1[^>]*>\s*(\d+)', part)
        if h1_match:
            paired.append(part)
            _figure_counter[0] = 0
            sec_num = int(h1_match.group(1))
        else:
            # Single pass: match all image+caption patterns in document order
            def pair_all(m, _sec=sec_num):
                img = m.group(1)
                # Check which group matched
                cap = (m.group(2) or m.group(3) or m.group(4) or '').strip()
                if cap:
                    _figure_counter[0] += 1
                    fn = f"{_sec}.{_figure_counter[0]}"
                    fig = f'<figure class="figure">{img}<figcaption class="caption">Figure {fn}: {cap}</figcaption></figure>'
                    # Return appropriate closing based on which pattern matched
                    if m.group(3):  # </li> pattern
                        return fig + '</li>'
                    elif m.group(4):  # bare text pattern
                        return fig + ' ' + m.group(5)
                    else:
                        return fig
                else:
                    # No caption - return as-is
                    if m.group(3):
                        return img + '</li>'
                    elif m.group(4):
                        return img + '  ' + m.group(5)
                    return img
            # Combined pattern: <img> followed by <p>cap</p>, bare cap before </li>, or bare cap + double-space
            part = re.sub(
                r'(<img[^>]+/>)(?:\s*<p>([^<]*)</p>|\s*([^<]*?)\s*</li>|\s*([^<]+?)\s{2,}([^<]))',
                pair_all,
                part
            )
            paired.append(part)
    content = ''.join(paired)


    # Restore verbatim content AFTER paragraph wrapping
    for key, body in _verbatim_registry.items():
        verbatim_html = '<pre class="verbatim">' + chr(10) + escape(body) + chr(10) + '</pre>'
        verbatim_html = re.sub(r'\[fontsize=\]', '', verbatim_html)
        content = content.replace(key, verbatim_html)

    # Convert [text] to <strong>text</strong> - skip <pre> blocks
    def convert_brackets(text):
        return re.sub(r'\[([^\]]+)\]', lambda m: f'<strong>{m.group(1)}</strong>', text)
    parts = re.split(r'(<pre[^>]*>.*?</pre>)', content, flags=re.DOTALL)
    content = ''.join(convert_brackets(p) if not p.startswith('<pre') else p for p in parts)
    return content


def generate_toc(content):
    """Generate sidebar TOC from headings in processed content."""
    # Extract all headings with their IDs
    headings = []
    heading_pattern = r'<h([1-6])[^>]*id=[\x27\x22]([^\x27\x22]+)[\x27\x22][^>]*>(.*?)</h\1>'
    for match in re.finditer(heading_pattern, content):
        level = int(match.group(1))
        anchor = match.group(2)
        text = re.sub(r'<[^>]+>', '', match.group(3)).strip()
        if text and anchor:
            headings.append((level, anchor, text))

    if not headings:
        return '<div class="sidebar">\n<h3>Table of Contents</h3><p>No sections found.</p></div>'

    # Build a tree from the headings
    root = {'children': []}
    stack = [(0, root)]  # (level, node)

    for level, anchor, text in headings:
        node = {'level': level, 'anchor': anchor, 'text': text, 'children': []}
        # Find the parent: pop stack until we find a node with level < current
        while stack and stack[-1][0] >= level:
            stack.pop()
        if stack:
            stack[-1][1]['children'].append(node)
        else:
            root['children'].append(node)
        stack.append((level, node))

    # Render the tree as HTML
    def render_tree(node):
        result = ''
        for child in node['children']:
            result += '<li>\n<a href="#' + child['anchor'] + '">' + escape(child['text']) + '</a>\n'
            if child['children']:
                result += '<ul>\n' + render_tree(child) + '</ul>\n'
            result += '</li>\n'
        return result

    toc_html = '<div class="sidebar">\n<h3>Table of Contents</h3>\n<ul class="toc">\n'
    toc_html += render_tree(root)
    toc_html += '\n</ul>\n</div>'
    return toc_html



def generate_html(title, content, toc):
    """Generate complete HTML document."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TITLE_PLACEHOLDER</title>
<style>
/* Mandelbulber Manual - Single Page Styles */
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    overflow-x: hidden;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    background: #fff;
}

/* Sidebar TOC */
.sidebar {
    position: fixed;
    top: 0;
    left: 0;
    width: 280px;
    height: 100vh;
    overflow-y: auto;
    background: #1e1e2e;
    color: #cdd6f4;
    padding: 0;
    z-index: 1000;
    display: flex;
    flex-direction: column;
    transition: transform 0.3s ease;
    transform: translateX(-100%);
}

.sidebar.open {
    transform: translateX(0);
}

.sidebar h3 {
    padding: 1em 1.2em;
    font-size: 1.1em;
    color: #f5c2e7;
    border-bottom: 1px solid #313244;
    background: #181825;
    position: sticky;
    top: 0;
    z-index: 1;
    margin: 0;
}

.sidebar ul {
    list-style: none;
    padding: 0.5em 0;
    margin: 0;
}

.sidebar li {
    padding: 0;
    margin: 0;
}

.sidebar a {
    display: block;
    padding: 0.35em 1.2em;
    color: #b4befe;
    text-decoration: none;
    font-size: 0.85em;
    border-left: 3px solid transparent;
    transition: all 0.15s ease;
}

.sidebar a:hover {
    background: #313244;
    color: #f5c2e7;
    border-left-color: #f5c2e7;
}

/* Content area */
#content {
    margin-left: 40px;
    padding: 2em 3em;
    max-width: 900px;
    transition: margin-left 0.3s ease;
}

#content.sidebar-open {
    margin-left: 288px !important;
}

#content h1, #content h2, #content h3, #content h4, #content h5 {
    margin-top: 1.8em;
    margin-bottom: 0.6em;
    color: #1e1e2e;
}

#content h1 { font-size: 1.8em; border-bottom: 2px solid #eee; padding-bottom: 0.3em; text-align: center; }

/* Title page styling */
.titlepage strong {
    font-size: 2.5em;
    display: block;
    text-align: center;
}
.titlepage p {
    text-align: center;
}
.titlepage p strong {
    font-size: 2em;
}
#content h2 { font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 0.2em; }
#content h3 { font-size: 1.3em; }
#content h4 { font-size: 1.1em; }

#content p {
    margin-bottom: 1em;
}

#content ul, #content ol {
    list-style: disc;
    margin: 0.5em 0 1em 2em;
    padding-left: 2em;
}

#content ol {
    list-style: decimal;
}

#content li {
    list-style: inherit;
    margin-bottom: 0.3em;
}

#code, #content code {
    background: #f5f5f5;
    padding: 0.1em 0.3em;
    border-radius: 3px;
    font-family: "Fira Code", "Consolas", monospace;
    font-size: 0.9em;
}

#content pre {
    background: #fff;
    color: #222;
    padding: 1em;
    border: 1px solid #ddd;
    border-radius: 6px;
    overflow-x: auto;
    margin: 1em 0;
}

#content pre.verbatim {
    background: #fff;
    color: #222;
    border: 1px solid #ddd;
}

#content pre.code-block {
    background: #fff;
    color: #222;
    border: 1px solid #ddd;
}

#content p.code-caption {
    font-size: 0.85em;
    color: #666;
    font-style: italic;
    margin: -0.5em 0 1em;
}

#content figcaption, #content .caption {
    text-align: center;
    font-size: 0.9em;
    color: #444;
    margin: 0.5em 0 1em;
    font-style: italic;
}

#content img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
}

#content figure {
    text-align: center;
    margin: 1.5em 0;
}

#content blockquote {
    border-left: 4px solid #d4d4d4;
    padding: 0.5em 1em;
    margin: 1em 0;
    background: #f9f9f9;
}

/* Collapsible toggle */
.sidebar-toggle {
    display: block;
    position: fixed;
    top: 0.8em;
    left: 0.8em;
    z-index: 1100;
    background: #1e1e2e;
    color: #f5c2e7;
    border: none;
    padding: 0.5em 0.8em;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1.2em;
}

.sidebar-toggle.shifted {
    left: 288px;
}

/* Responsive */
@media (max-width: 768px) {
    #content {
        padding: 2em 1.2em;
    }
}


/* Title page table styling - vertical separator */
.titlepage table.table {
    border-collapse: collapse;
}
.titlepage table.table td {
    padding: 0.15em 0.5em;
    vertical-align: top;
}
.titlepage table.table td:first-child {
    border-right: 1px solid #000;
    padding-right: 0.8em;
    white-space: nowrap;
}
.titlepage table.table td:last-child {
    padding-left: 0.8em;
}

</style>
<script>
window.MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
    displayMath: [['$$', '$$']],
    processEscapes: true,
    processEnvironments: false,
    packages: {'[+]': 'ams'}
  },
  options: {
    skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
  },
  startup: {
    ready: function() {
      MathJax.startup.defaultReady();
    }
  }
};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" async></script>
</head>
<body>
<button class="sidebar-toggle" onclick="document.querySelector('.sidebar').classList.toggle('open'); document.getElementById('content').classList.toggle('sidebar-open'); this.classList.toggle('shifted');">☰ TOC</button>
TOC_PLACEHOLDER
<div id="content">
CONTENT_PLACEHOLDER
</div>
</body>
</html>"""
    # Balance divs in content to prevent premature closing of #content wrapper
    # Tokenize into div tags and non-div text (preserves all content)
    tokens = re.split(r'(<div[^>]*>|</div>)', content)
    depth = 0
    filtered = []
    for token in tokens:
        if token.startswith('<div') and not token.startswith('</'):
            depth += 1
            filtered.append(token)
        elif token == '</div>':
            if depth > 0:
                depth -= 1
                filtered.append(token)
            # else: skip excess </div>
        else:
            filtered.append(token)
    content = ''.join(filtered)
    # Add any missing closing divs
    while depth > 0:
        content += '</div>'
        depth -= 1
    
    return (
        html.replace("TITLE_PLACEHOLDER", escape(title), 2)
        .replace("TOC_PLACEHOLDER", toc)
        .replace("CONTENT_PLACEHOLDER", content)
    )


def main():
    # Run from script directory - no arguments needed
    script_dir = Path(__file__).resolve().parent
    repo_root = str(script_dir)

    # Copy CSS to repo root (skip if already there)
    css_src = Path("css/style.css")
    css_dst = Path(repo_root) / "css" / "style.css"
    if css_src.exists():
        if css_src.resolve() != css_dst.resolve():
            css_dst.parent.mkdir(exist_ok=True)
            shutil.copy2(css_src, css_dst)

    main_file = Path(repo_root) / "handbook.tex"
    if not main_file.exists():
        print(f"Error: {main_file} not found")
        sys.exit(1)

    with open(main_file, "r", encoding="utf-8") as f:
        content = f.read()
    # Strip % comment lines from .tex files (lines that begin with %)
    content = '\n'.join(
        line for line in content.split('\n')
        if not line.lstrip().startswith('%')
    )
    # Strip \def macro definitions (they're already handled by process_image_macro)
    # Match \def\name#1#2...{...} and remove the entire definition
    def_cmd = '\\def'
    def_pattern = r'\\\\def\\\\[a-zA-Z]+#\\d(\\+[^{]*\\{[^}]*\\})+'
    content = re.sub(def_pattern, '', content)
    # Also strip any remaining \\def lines with their content
    content = re.sub(r'\\\\def\\[a-zA-Z]+', '', content)

    processed = process_content(content, repo_root, repo_root=repo_root)

    title = "Mandelbulber Manual"
    
    # Generate TOC from headings
    toc = generate_toc(processed)
    
    html = generate_html(title, processed, toc)

    output_file = Path(repo_root) / "index.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Generated {output_file}")


if __name__ == "__main__":
    main()
