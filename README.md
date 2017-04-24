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
git tag -a v2.11.0.6 -m "Mandelbulber doc v2.11.0.6"`
git push -u origin --tags
```
