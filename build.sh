mkdir build
pdflatex -output-directory build handbook.tex
pdflatex -output-directory build handbook.tex
cd build
makeindex handbook.idx
cd ..
pdflatex -interaction nonstopmode -halt-on-error -file-line-error -output-directory build handbook.tex
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dNOPAUSE -dQUIET -dBATCH -sOutputFile=build/handbook-compressed.pdf build/handbook.pdf
