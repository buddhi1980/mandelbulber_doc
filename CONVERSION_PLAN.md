# LaTeX to HTML Conversion Plan — Mandelbulber Manual

## 1. Project Overview

**Source**: LaTeX documentation for Mandelbulber 2, compiled from multiple `.tex` files.

**Structure**:
```
mandelbulber_doc/
├── img/
│   ├── mandelbulber_logo.png          (site branding)
│   ├── mandelbulber_background.jpg    (background / watermark)
│   └── manual/media/                  (200+ screenshot images)
├── mandelbulber2/
│   ├── preamble.tex                   (document class, packages, styles)
│   ├── makro.tex                      (custom macros — image helpers)
│   ├── manual/
│   │   ├── manual.tex                 (master file — \input{...} chains 15 chapters)
│   │   └── chapters/                  (15 chapter .tex files)
│   ├── introduction/
│   │   └── aboutHandbook.tex          (intro section)
│   └── outroduction/
│       └── exitHandbook.tex           (thanks / closing section)
```

**Total content**: ~3,000+ lines of LaTeX across 15 chapters + intro + outro + preamble + macros.

---

## 2. LaTeX Features Used — Conversion Mapping

| LaTeX Feature | Examples Found | HTML Equivalent |
|---|---|---|
| `\section{}`, `\subsection{}`, `\subsubsection{}` | All chapters | `<h2>`, `<h3>`, `<h4>` |
| `\label{...}` / `\ref{...}` | Cross-references | Named anchors + `<a href="#label">` |
| `\index{...}` | Index entries | **Drop** (no index needed in HTML) |
| `\emph{...}` / `\textbf{...}` | Emphasis | `<em>`, `<strong>` |
| `\texttt{...}` | Code/paths | `<code>` / `<pre>` |
| `\href{url}{text}` / `\url{url}` | Links | `<a href>`, auto-link URLs |
| `\[...\]` / `$...$` | Display / inline math | MathJax / KaTeX `<span class="math">` |
| `\begin{itemize}...\end{itemize}` | Bullet lists | `<ul><li>` |
| `\begin{description}...\end{description}` | Definition lists | `<dl><dt><dd>` |
| `\begin{verbatim}...\end{verbatim}` | Code blocks | `<pre><code>` |
| `\begin{center}...\end{center}` | Centered content | `<div class="center">` |
| `\begin{tabular}...\end{tabular}` | Tables | `<table>` |
| `\begin{figure}...\end{figure}` | Figures (via macros) | `<figure><figcaption>` |
| `\includegraphics{...}` | Images | `<img src="...">` |
| `\nopagebreak` / `\pagebreak` | Page breaks | **Drop** (not needed in HTML) |
| Custom macros | `simpleImageWithCaption*`, `twoImagesWithTwoCaptionsFullWidth`, `threeImagesWithTwoCaptionsFullWidth` | See §3 |

---

## 3. Custom Macro Handling

The `makro.tex` defines 6 custom macros that wrap images with captions. These must be detected and converted to proper HTML `<figure>` elements.

### Macro inventory:

| Macro | Params | Image Width |
|---|---|---|
| `simpleImageWithCaptionFullWidth` | `{path}{caption}{label}{pos}` | 100% |
| `simpleImageWithCaptionHalfWidth` | `{path}{caption}{label}{pos}` | 50% |
| `simpleImageWithCaptionThirdWidth` | `{path}{caption}{label}{pos}` | 35% |
| `simpleImageWithCaption75Width` | `{path}{caption}{label}{pos}` | 75% |
| `simpleImageWithCaptionSmallWidth` | `{path}{caption}{label}{pos}` | 25% |
| `twoImagesWithTwoCaptionsFullWidth` | `{path1}{cap1}{lab1}{path2}{cap2}{lab2}{pos}` | side-by-side |
| `threeImagesWithTwoCaptionsFullWidth` | `{path1}{cap1}{lab1}{path2}{cap2}{lab2}{path3}{cap3}{lab3}` | 3-column |

### Conversion strategy:

Each macro invocation like:
```latex
\simpleImageWithCaptionHalfWidth{img/manual/media/qsg_cpu.png}
{Settings for number of CPU cores and program priority}
{qsg-cpu-preferences}{H}
```
becomes:
```html
<figure class="screenshot half-width" id="qsg-cpu-preferences">
  <img src="img/manual/media/qsg_cpu.png" alt="Settings for number of CPU cores and program priority">
  <figcaption>Settings for number of CPU cores and program priority</figcaption>
</figure>
```

- The 4th param (`H`, `h`) maps to CSS width class (`full-width`, `half-width`, `third-width`, `small-width`).
- The label param becomes the `id` attribute for cross-reference targeting.
- Captions become `<figcaption>`.
- `twoImages...` → `<figure class="two-images">` with two `<img>` side by side.
- `threeImages...` → `<figure class="three-images">` with three `<img>` in a row.

---

## 4. Output Architecture

### Option A: Single-page HTML (recommended for readability)

One large HTML file with a sticky sidebar TOC. Best for:
- Quick reference / reading
- No server needed — just open the file
- Searchable within the browser

### Option B: Multi-page HTML site

One HTML file per chapter + a main index. Best for:
- Large documents that benefit from pagination
- Linking between chapters from external docs

### Recommendation: **Option A** (single-page) with a collapsible sidebar TOC.

This is the most practical for a user manual that people read linearly or search within.

---

## 5. Conversion Pipeline

### Phase 1: Preprocessing (Python)

```
raw .tex files
    │
    ▼
Step 1: Resolve \input{} → inline content
        Merge: preamble.tex + makro.tex + aboutHandbook.tex
        + each chapter in order (manual.tex defines order)
        + exitHandbook.tex
    │
    ▼
Step 2: Extract all \label{} definitions → label map
        Store: label_name → (file, line) for cross-ref resolution
    │
    ▼
Step 3: Convert custom macros → HTML figure elements
        Regex-match each macro invocation, extract params,
        emit <figure> with proper id/caption/img
    │
    ▼
Step 4: Convert remaining LaTeX → HTML
        \section{X}\label{y}       → <h2 id="y">X</h2>
        \subsection{X}\label{y}    → <h3 id="y">X</h3>
        \emph{X}                    → <em>X</em>
        \textbf{X}                  → <strong>X</strong>
        \texttt{X}                  → <code>X</code>
        \href{url}{text}            → <a href="url">text</a>
        \url{url}                   → <a href="url">url</a>
        \index{X}                   → (drop)
        \nopagebreak / \pagebreak  → (drop)
        \vspace{...}               → (drop — CSS handles spacing)
        \\[...\\] (display math)   → <div class="math-display">...</div>
        $...$ (inline math)        → <span class="math-inline">...</span>
        \begin{itemize}            → <ul>
        \begin{description}        → <dl>
        \begin{verbatim}           → <pre><code>
        \begin{center}             → <div class="center">
        \begin{tabular}            → <table>
        \hline                      → (drop — CSS borders)
        \label{...} (standalone)   → (already captured in label map)
        \caption{...}              → (handled by macro converter)
        \ref{...}                  → <a href="#...">...</a>
        \footnotesize, \small,     → (drop — CSS handles)
        \sfdefault font family     → (CSS font-family)
```

### Phase 2: HTML Assembly

```
Converted HTML fragments
    │
    ▼
Step 5: Assemble into single HTML document
        - <head> with meta, title, CSS, MathJax config
        - Sidebar TOC generated from <h2>/<h3>/<h4> headings
        - Body with all content sections in order
        - Footer with thanks
    │
    ▼
Step 6: Write output
        output/
        ├── index.html              (main document)
        ├── css/
        │   └── style.css           (all styles)
        ├── js/
        │   └── toc.js              (sidebar TOC toggle)
        └── img/
            └── manual/
                └── media/        (copy of all 200+ images)
```

---

## 6. CSS / Styling Strategy

- **Font**: Sans-serif (matching `renewcommand{\familydefault}{\sfdefault}` from preamble)
- **Layout**: Fixed sidebar TOC (250px) + scrollable content area
- **Typography**: 16px base, 1.6 line-height, max-width 900px for content
- **Code blocks**: Dark background, monospace, left border accent
- **Figures**: Responsive images, centered captions, width classes
- **Math**: MathJax 3 — renders LaTeX in-browser (no pre-processing needed)
- **Links**: Blue, underlined on hover
- **Tables**: Border-collapse, striped rows, responsive scroll
- **Description lists**: Bold `<dt>`, indented `<dd>`
- **Responsive**: Sidebar collapses to hamburger on mobile

---

## 7. Tooling Recommendation

### Primary: **Custom Python script** (recommended)

**Why not pandoc?**
- Pandoc handles ~80% of LaTeX natively, BUT:
  - Custom macros (`simpleImageWithCaption*`, etc.) are **not** understood — would need pre-processing anyway
  - Multi-file `\input{}` resolution requires preprocessing
  - `\hyperref` with custom label resolution works but cross-chapter refs break
  - Pandoc's `--to html` is great for single files; this is a 15-file project
  - Pandoc would still need a custom filter for the image macros

**Why custom Python?**
- Full control over every macro → HTML mapping
- Can resolve `\label`/`\ref` cross-references accurately
- Can copy/symlink images in the right structure
- Can generate the TOC programmatically from headings
- No heavy dependency on LaTeX installation
- Fast — pure text processing

### Dependencies:
- **Python 3.11+** (already available)
- **No external libraries needed** — regex + stdlib is sufficient
- **MathJax 3** — loaded from CDN in `<head>`, no install needed

---

## 8. Implementation Steps

| Step | Task | Complexity |
|---|---|---|
| 1 | Write `convert.py` — core LaTeX-to-HTML converter | Medium |
| 2 | Handle macro expansion (6 macros → HTML figures) | Medium |
| 3 | Handle math (display + inline → MathJax spans) | Low |
| 4 | Handle cross-references (\label + \ref) | Medium |
| 5 | Assemble single-page HTML with sidebar TOC | Low |
| 6 | Write CSS (responsive, dark code blocks, typography) | Medium |
| 7 | Copy images to output directory | Low |
| 8 | Verify output — check all images, links, math render | Medium |

---

## 9. Known Challenges & Mitigations

| Challenge | Mitigation |
|---|---|
| `utf8x` encoding (non-standard) | Python reads UTF-8 directly; source files are likely already UTF-8 |
| `tikz` packages (diagrams) | Rarely used in this doc; if present, convert to images or drop |
| `draftwatermark` (watermark) | Drop — not needed in HTML |
| `makeidx` (index generation) | Drop — HTML search replaces index |
| `longtable` / `supertabular` | Convert to `<table>`; pagination not needed in HTML |
| `wrapfig` (text wrapping around images) | Use CSS `float` or `column-span` |
| `booktabs` (table styling) | CSS `border-collapse`, `th` styling |
| `lstset` (code listing style) | Convert to `<pre><code>` with CSS matching the blue/red/green color scheme |
| 200+ images — file copy | Use `shutil.copy2` or symlinks in one pass |
| `\pagebreak` between sections | Drop — HTML flows naturally |
| `\nopagebreak` | Drop |
| `\footnotesize`, `\small`, `\scriptsize` | Drop — CSS handles font sizing |
| `\setlength{\parskip}{0.5em}` | Set in CSS as `margin-bottom` or `padding` |
| `\newcommand{\sectionbreak}{\clearpage}` | Drop — each section is a natural page break in HTML |

---

## 10. File Structure of Output

```
output/
├── index.html              (main HTML document, ~self-contained)
├── css/
│   └── style.css           (all styling)
├── js/
│   └── toc.js              (sidebar toggle, scroll spy)
└── img/
    └── manual/
        └── media/          (200+ screenshot images, copied from source)
        mandelbulber_logo.png
        mandelbulber_background.jpg
```

---

## 11. Recommended Approach Summary

**Go with a custom Python converter script** rather than pandoc. Here's why:

1. The 6 custom image macros are the biggest hurdle — they encode layout info (width, caption, label) that pandoc can't interpret. A Python regex-based converter handles these cleanly.
2. Cross-reference resolution (`\ref{label}` → `<a href="#label">`) requires a two-pass approach (collect labels, then resolve refs) — trivial in Python, awkward in pandoc.
3. The multi-file `\input{}` structure needs a preprocessor to merge everything into one document — again, simple in Python.
4. Math rendering via MathJax CDN means no preprocessing of equations needed — just wrap them in span/div tags.
5. Image copying is straightforward with `shutil`.

**Alternative**: If you want to go the pandoc route, you'd still need a Python preprocessor step to convert the custom macros to standard LaTeX figure environments, then run pandoc. This adds complexity without clear benefit over a pure Python approach.

---

## 12. Next Steps

1. **Approve this plan** — confirm single-page vs multi-page output, styling preferences
2. **Write the converter script** (`convert.py`)
3. **Run it** and verify output
4. **Iterate** on styling and edge cases
