# Mandelbulber End User Manual
Documentation for Mandelbulber program.

Scripts enable Word Processor for spelling/grammar/style checks.
Scripts export to plaintext formats using PANDOC.
Easy integration for concurrent version control systems.

# Latex Engine
The main file is handbook.tex
compile the program with:
`pdflatex handbook.tex`

Tested on Windows 10 using miktex engine.

# To Make edits in DOCX and convert to Latex

`pandoc mandelbulber2\manual\manual.docx -o mandelbulber2\manual\manual.tex --extract-media=img\manual --latex-engine=pdflatex`

`pandoc mandelbulber2\sound\sound.docx -o mandelbulber2\sound\sound.tex --extract-media=img\sound --latex-engine=pdflatex`

