[![Build Status Linux / OSX](https://travis-ci.org/buddhi1980/mandelbulber_doc.svg?branch=master)](https://travis-ci.org/buddhi1980/mandelbulber_doc)

# Mandelbulber End User Manual
Documentation for Mandelbulber 3D Fractal Generation System.

# Latex Engine
Compile the documentation's root file, handbook.tex, with:
`pdflatex handbook.tex`

Tested on Windows 10 using miktex engine.

# Optimize size of PDF file
`gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dNOPAUSE -dQUIET -dBATCH -sOutputFile=handbook-compressed.pdf handbook.pdf`

# Create PDF Manual with Travis CI
To Release the PDF, create a new tag. Example commands:
``` 
git tag -a v2.11.0.6 -m "Mandelbulber doc v2.11.0.6"
git push -u origin --tags
```

# HTML Manual Converter (convert.py)
`convert.py` converts the LaTeX sources into a single-page HTML manual
(`index.html`) with a collapsible sidebar table of contents and inline CSS.
It requires Python 3 and standard library modules only (no LaTeX engine).

The set and order of chapters is defined in `mandelbulber2/manual/manual.tex`
(the converter resolves the `\input{}` chain, `%` comment lines and the LaTeX
environments itself).

Generate the HTML in the repository root:
```
python3 convert.py
```

Additionally copy `index.html` and only the referenced images to the
Mandelbulber2 application tree (the generated HTML is tracked in git there):
```
python3 convert.py --publish /path/to/mandelbulber2/mandelbulber2/deploy/doc
```

When editing the `.tex` sources, regenerate `index.html` and commit it
together with the source changes; run `--publish` to update the copy shipped
with the application.
