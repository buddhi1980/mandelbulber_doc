[![Build Status Linux / OSX](https://travis-ci.org/buddhi1980/mandelbulber_doc.svg?branch=master)](https://travis-ci.org/buddhi1980/mandelbulber_doc)

# Mandelbulber End User Manual
Documentation for Mandelbulber 3D Fractal Generation System.

# Latex Engine
The main file is handbook.tex
compile the program with:
`pdflatex handbook.tex`

Tested on Windows 10 using miktex engine.

# Reducing size of PDF file
`gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dNOPAUSE -dQUIET -dBATCH -sOutputFile=handbook-compressed.pdf handbook.pdf`
