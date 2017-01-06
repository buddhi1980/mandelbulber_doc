-   [Native Support for x100 Xeon Phi Co-Processor]
    -   [Purpose]
    -   [Introduction]
    -   [Experiment Description]
        -   [Null Hypothesis]
        -   [Alternative Hypothesis]
        -   [Deliverables]
            -   [README.md]
            -   [RESULTS.md]
            -   [REPORT]
    -   [Experiment Design]
        -   [Baseline]
        -   [Factor A]
        -   [Factor B]
        -   [Factor C]
    -   [Linux Operating System]
        -   [Local Machine Configuration]
            -   [local.sh]
        -   [Required Software Libraries]
            -   [build\_all.sh]
            -   [build.bot.sh]
            -   [build.bot.log.sh]
        -   [Configurations ]
        -   [Compilation]
            -   [white-space-v2.08-1.patch]
            -   [build\_patches.sh]
            -   [build\_patches.log.sh]
    -   [Analysis]
        -   [Floating Point Validation]
            -   [NaNtester.sh]
            -   [NaNtester.log.sh]
        -   [Amplifier Project]
            -   [mandelbulber2-vTune]
        -   [Advisor Project]
            -   [mandelbulber2-advisor]
    -   [Data Collection]
        -   [Settings Tested]
        -   [Automation of Experiment]
            -   [trial.sh]
            -   [trial.log.sh]
            -   [trial.log.Loop.10.sh]
            -   [trial-run-host.py]
        -   [Automation of Render]
            -   [render.bot.nodes.sh]
            -   [render.bot.sh]
            -   [host.py]
    -   [Windows Operating System]
        -   [For Reference Only]
            -   [build.batch.bat]
            -   [build.batch.log.bat]
            -   [trial.bat]
            -   [trial.log.bat]
    -   [Conclusion]
        -   [Results]
        -   [Release]

<span id="_Toc463615912" class="anchor"></span>TODO:

report.pdf

latex output required for PDf for app catalog

Factor Assignment

Main Effects

Interactions

Response Table (Data)

Replicates used to normalize the data

2 levels of 3 factors with up to 8 reps = (2^3) x 8 = 64 or
less data points; Change only yellow boxes

2^3 Full Factorial Array (Similar to the Taguchi L8
Orthogonal Array)

Quick Calculations

D=AB E=AC F=BC G=ABC

Reference Key to Factor Selection

Factor A = Your factor: ; B = ; C =

Factor D = Your factor: AB Interaction? ; E = AC
Interaction? ; F = BC Interaction? ; G = Error

Confounding Column Information (for alternative factor
assignment considerations)

The Taguchi L8 array is very similar to this arrray but has
slightly different columns that confound with each other.
This

array does not have confounding columns. Using the L8 array
requires an uderstanding of column confounding.

Calculating Confidence

ANOVA analysis is used to compare "within variation" with
"between variation".

Hypotheses: Ho= All means are equal; HA= They are not equal

Linear contrasts is a method used to test any two levels or
combinations of two levels against each other.

Degrees of freedom is always 1 for testing two items.

Additional Comments

Note \#1: If the data is known to be normally distributed,
analyzing the within run data as design replicates yields

higher confidence in the results. Unfortunately this matrix
is not set up to do that.

Note \#2: Error in the results increases as columns contain
greater amounts of partial data. For example, if two reps

are taken for each run, then columns R1 and R2 should be
fully filled out.

Calculating the Significance of Main Effects (Solving for
Means)

Factor A

Factor B

Factor C

Calculating the Significance of Main Effects (Solving for
Standard Deviation)

Factor A

Factor B

Factor C

Calculating the Significance of Main Effects (Solving for
Signal-to-Noise)

Factor A

Factor B

Factor C

Calc. the Sig. of 2nd Order Interaction Effects or Aliased
Effects (Solving for Means)

Factor D (AB)

Factor E (AC)

Factor F (BC)

Calc. the Sig. of 2nd Order Interaction Effects or Aliased
Effects (Solving for Std Dev.)

Factor D (AB)

Factor E (AC)

Factor F (BC)

Calc. the Sig. of 2nd Order Interaction Effects or Aliased
Effects (Solving for Sig-to-Noise)

Factor D (AB)

Factor E (AC)

Factor F (BC)

Calc. the Sig. of 3rd Order Interaction Effects, Error, or
Aliased Effects (Solving for Means)

Factor G (ABC)

Calc. the Sig. of 3rd Order Interaction Effects, Error, or
Aliased Effects (Solving for Std.Dev.)

Factor G (ABC)

Calc. the Sig. of 3rd Order Interaction Effects, Error, or
Aliased Effects (Solving for Sig.-to-Noise)

Factor G (ABC)

Total Sum of Squares

ANOVA Table

Is there a statistically significant difference between
factors, rows, and error?

Df = Degrees of freedom

SS = Sum of Squares

Alpha = F-test probability

MS = Mean Sum of Squares

F = F-test characteristic

Native Support for x100 Xeon Phi Co-Processor
=============================================

Purpose
-------

This document exists to discuss relevant experimental
factors and data affecting the optimum completion time of a
particular computer algorithm that renders advanced
fractals. To supplement design efforts, this full factorial
experiment documents multiple enhancements of algorithm
productivity by means of an analysis of variance approach.
Utilization of Python distributes the experimentation across
multiple co-processors to expedite production of the
results. **The results provide documented data illustrating
the effects of increased performance and fidelity from
enhanced efficiency within Mandelbulber2.**

Introduction
------------

Multi-core processors are the modern approach to rendering
3D fractals. *Parallel Ray Marching* unites the innovative
essence for some 3D algorithms in modern computer science.
Mandelbulber2, a collection of open source software, exists
today exclusively for this purpose. The goal of this
experiment is to record optimal software configurations
using an x100 co-processor hardware system for rendering 3D
Mandelbrot fractals.

Experiment Description
----------------------

The experiment considers three key factors for affecting the
collective runtime of the algorithm under each experimental
configuration. These factors include a patch for random
number generation, a set of patches for the not-a-number
function, and a patch for the shade and lights functions.
Scripts and miscellaneous files have been prepared to
compile and execute the algorithm. The algorithm executes
eight times sequentially, once under each software
configuration. Python scripts track the timing metrics for
each experimental configuration. Each trial considers over
80 different examples that practice a majority of the code
base within the algorithm.

### Null Hypothesis

H0: µ1 = µ2 = µ3 = µ4 = µ5 = µ6 = µ7 = µ8

### Alternative Hypothesis

H1: µi ≠ µj for at least one configuration pair

### Deliverables

| **ITEM** | **FORMAT** |
|----------|------------|
| README   | Markdown   |
| RESULTS  | Markdown   |
| REPORT   | Latex      |

#### README.md

This file describes the objective.

#### RESULTS.md

This file contains the experimental data.

#### REPORT

This folder contains the latex formatted report.

Experiment Design
-----------------

At this time, the design reflects a two-level full factorial
experiment with k being three factors. The full combination
of factors, with their respective patches applied to the
baseline; compose test configurations compiled as
experimental binaries.

### Baseline

-   Mandelbulber v2.08-1 - Jul 3, 2016

-   https://github.com/buddhi1980/mandelbulber2/commit/daec61022499faf1f75a8fa9d3bf5e861635c503

### Factor A

-   Park-Miller Random Number Generator - Jul 31, 2016

-   https://github.com/buddhi1980/mandelbulber2/commit/898fd8a1db7ad789ebe6381a66046cf99ed1456a.patch

### Factor B

-   Eliminated Get Light Issue - Aug 1, 2016

-   https://github.com/buddhi1980/mandelbulber2/commit/c494aee5e9a7bccc8773437e775c96a43ec37e16.patch

### Factor C

-   Utilized GSL Finite for Not-a-Number - Sept 4, 2016

-   https://github.com/buddhi1980/mandelbulber2/commit/68cacbfbafe623030978d21b2e3ade36c1df7f3c.patch

-   https://github.com/buddhi1980/mandelbulber2/commit/56c6082db20fe2532d6b4b23c66b0149be58f81c.patch

Linux Operating System
----------------------

This experiment targets the Linux Operating System
environment.

### Local Machine Configuration

#### local.sh

This shell script contains the definitions of many variables
used throughout the experimental builds and throughout
execution of experimental trial runs.

| **VARIABLE** | **PATH**              | **DESCRIPTION**                   |
|--------------|-----------------------|-----------------------------------|
| DOE          | $PWD                  | The current directory of local.sh |
| SRC          | $PWD/../../../        | The source code root directory    |
| KNC\_LIB     | $SRC/../KNC-Lib       | x100 Co-Processor Library         |
| MPSSDIR      | $SRC/../mpss-3.7/k1om | x100 Co-Processor SDK             |
| build\_logs  | $SRC/../build\_logs   | Experimental logs directory       |
| BUILD        | $SRC/../build         | x64 build directory               |
| BUILDMIC     | $SRC/../build-mic     | k1om build directory              |
| BUILDNAN     | $SRC/../NaNtest       | Test build directory              |

### Required Software Libraries

#### build\_all.sh

This shell script targets k1om architecture for the x100
co-processor. It compiles libraries from the KNC-Lib
repository. The libraries used in this experiment include
FreeType2 to render fonts, GNU Scientific Library for common
mathematics, libjpeg for the application's JPEG support,
libpng for Portable Network Graphics support, Perl
Compatible Regular Expressions for pattern matching, and Qt5
as a development framework.

#### build.bot.sh

This experimental shell script uses the local Linux machine
variables to execute a full build for both x64 binaries and
Knights Corner binaries.

#### build.bot.log.sh

Log the Linux machine build process.

### Configurations 

| Factors   | NAN Patched | Light Patched | Random Patched |
|-----------|-------------|---------------|----------------|
| CONFIG000 | No          | No            | No             |
| CONFIG001 | No          | No            | Yes            |
| CONFIG010 | No          | Yes           | No             |
| CONFIG011 | No          | Yes           | Yes            |
| CONFIG100 | Yes         | No            | No             |
| CONFIG101 | Yes         | No            | Yes            |
| CONFIG110 | Yes         | Yes           | No             |
| CONFIG111 | Yes         | Yes           | Yes            |

### Compilation

#### white-space-v2.08-1.patch

Non-functional whitespace changes required for clean
application of patches to baseline source revision.

#### build\_patches.sh

This script builds all possible combinations of patches and
maintains separate binaries for each configuration.

#### build\_patches.log.sh

Logs the process of building all the patched binaries

Analysis
--------

### Floating Point Validation

#### NaNtester.sh

Test suite for k1om and x64 architectures

#### NaNtester.log.sh

Log the test suite process

### Amplifier Project

#### mandelbulber2-vTune

Investigate Algorithm Scalability

### Advisor Project

#### mandelbulber2-advisor

Investigate Algorithm Vectorization

Data Collection
---------------

### Settings Tested

| File Names                                     |
|------------------------------------------------|
| aboxmod1\_001                                  |
| aboxmod2\_001                                  |
| aboxvsicen1\_001                               |
| aexion\_octopus\_001                           |
| amoxmodkali\_001                               |
| benesi\_t1\_pine\_tree\_001                    |
| bristorbrot001                                 |
| hybrid002                                      |
| hybrid004                                      |
| hybrid007                                      |
| IFS\_002                                       |
| iq\_bulb\_001                                  |
| keyframe\_anim\_mandelbox\_boxes               |
| Makin3D-Julia\_001                             |
| mandelbox001                                   |
| mandelbox002                                   |
| mandelbulb002                                  |
| menger-mod1\_001                               |
| msltoe\_julia\_bulb\_eiffie\_001               |
| primitives001                                  |
| quaternion\_001                                |
| riemann\_sphere\_msltoe\_001                   |
| KM/aexion01                                    |
| KM/benesi03                                    |
| KM/Bristorbrot                                 |
| KM/bristorbrot01                               |
| KM/constant factor 2.0 - mandelbox scale 2.0   |
| KM/equirectangular menger sponge               |
| KM/fish eye                                    |
| KM/folded mender sponge                        |
| KM/hybrid16                                    |
| KM/hybrid17                                    |
| KM/hybrid18\_2                                 |
| KM/hybrid19                                    |
| KM/hybrid20                                    |
| KM/hybrid22 - foldigIntPow v 2                 |
| KM/hybrid42                                    |
| KM/hypercomplex 03                             |
| KM/IFS 19 - maxiter                            |
| KM/IFS 20                                      |
| KM/IFS 21                                      |
| KM/IFS 25                                      |
| KM/IFS 29\_2                                   |
| KM/IFS 31                                      |
| KM/IFS 32                                      |
| KM/iter fog 002\_2                             |
| KM/iter fog 2                                  |
| KM/mandelbox 22                                |
| KM/mandelbox10                                 |
| KM/mandelbox11 - rotations                     |
| KM/mandelbox15 - rotations                     |
| KM/mandelbox17                                 |
| KM/mandelbox18                                 |
| KM/mandelbox19                                 |
| KM/mandelbox24                                 |
| KM/mandelbox25\_3                              |
| KM/mandelbox27                                 |
| KM/mandelbox28                                 |
| KM/mandelbox29                                 |
| KM/mandelbox30                                 |
| KM/mandelbox31                                 |
| KM/mandelbox36                                 |
| KM/mandelbox49                                 |
| KM/mandelbox52\_2                              |
| KM/mandelbox8 - maxiter                        |
| KM/mandelbulb powe 6 - circle                  |
| KM/mandelbulb power 2 - slice 4                |
| KM/mandelbulb power 2 - slice 5                |
| KM/mandelbulb power 4 - water                  |
| KM/mandelbulb power 8 - 4\_2                   |
| KM/mandelbulb power 8 - 7 - volmetric fog      |
| KM/menger sponge 004\_2                        |
| KM/modified mandelbulb 001                     |
| KM/orbitTraps 003                              |
| KM/orbitTraps 004                              |
| KM/orbitTraps 005                              |
| KM/orbitTraps 006                              |
| KM/primitive objects - water                   |
| KM/xenodreambuie2                              |
| KM/xenodreambuie3                              |
| SJ/hybrid 02 - rectangle hieroglyphs animation |
| SJ/hybrid 02 - rectangle hieroglyphs           |

### Automation of Experiment

#### trial.sh

Linux Machine Trial Run

#### trial.log.sh

Log the Linux Machine Trial Run

#### trial.log.Loop.10.sh

Logs 10 replications the Linux Machine Trial Run

#### trial-run-host.py

Executes experimental binaries and records the timing data
from numerous example settings.

### Automation of Render

#### render.bot.nodes.sh

#### render.bot.sh

#### host.py

Render sequential animation frames to collect timing data.

Windows Operating System
------------------------

### For Reference Only

Subsets of the experimental files enable partial Windows
support for experimentation. These results contain many
uncontrollable factors. Due to these nuisance factors, the
results from Windows based machines exist as reference only.

#### build.batch.bat

This experimental batch file generates x64 binaries for
Windows using MSBUILD.

#### build.batch.log.bat

Log the Windows machine build process.

#### trial.bat

Windows Machine Trial Run

#### trial.log.bat

Log the Windows Machine Trial Run.

Conclusion
----------

### Results

The entire experiment will replicate through multiple
iterations to reinforce a sound statistical conclusion. The
results, contained in a separate plain-text file, require
further review.

### Release

-   Mandelbulber v2.09 – Oct 4, 2016

-   https://github.com/buddhi1980/mandelbulber2/commit/013208e3ee969c498a01b4160f834ad20f2a2f13

-   Easily scales past 240 threads

| CONFIG | R1      | R2      | R3  | R4  | R5  | R6  | R7  | R8  | A   | B   | C   | D   | E   | F   | G   |
|--------|---------|---------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| 000    | 1080.65 | 1080.87 |     |     |     |     |     |     | -   | -   | -   | +   | +   | +   | -   |
| 001    | 414.60  | 421.76  |     |     |     |     |     |     | +   | -   | -   | -   | -   | +   | +   |
| 010    | 1091.43 | 1079.20 |     |     |     |     |     |     | -   | +   | -   | -   | +   | -   | +   |
| 011    | 391.31  | 392.96  |     |     |     |     |     |     | +   | +   | -   | +   | -   | -   | -   |
| 100    | 1067.08 | 1062.10 |     |     |     |     |     |     | -   | -   | +   | +   | -   | -   | +   |
| 101    | 371.63  | 378.36  |     |     |     |     |     |     | +   | -   | +   | -   | +   | -   | -   |
| 110    | 1060.88 | 1072.13 |     |     |     |     |     |     | -   | +   | +   | -   | -   | +   | -   |
| 111    | 350.08  | 350.69  |     |     |     |     |     |     | +   | +   | +   | +   | +   | +   | +   |

| CONFIG | AVG     | Std.Dev. | SNR  |
|--------|---------|----------|------|
| 000    | 1080.76 | 0.16     | 3.84 |
| 001    | 418.18  | 5.06     | 1.92 |
| 010    | 1085.32 | 8.65     | 2.10 |
| 011    | 392.13  | 1.17     | 2.53 |
| 100    | 1064.59 | 3.52     | 2.48 |
| 101    | 375.00  | 4.76     | 1.90 |
| 110    | 1066.50 | 7.95     | 2.13 |
| 111    | 350.39  | 0.43     | 2.91 |

| Grand Average | (GA) | 729.11 |
|---------------|------|--------|

| Total              | Factor | Value-i | Value-ii | Value-iii | Value-iv | Average |
|--------------------|--------|---------|----------|-----------|----------|---------|
| -690.37            | A+     | 418.18  | 392.13   | 375.00    | 350.39   | 383.92  |
| Effect on Mean     | A-     | 1080.76 | 1085.32  | 1064.59   | 1066.50  | 1074.29 |
| -11.05             | B+     | 1085.32 | 392.13   | 1066.50   | 350.39   | 723.59  |
| Effect on Mean     | B-     | 1080.76 | 418.18   | 1064.59   | 375.00   | 734.63  |
| -29.98             | C+     | 1064.59 | 375.00   | 1066.50   | 350.39   | 714.12  |
| Effect on Mean     | C-     | 1080.76 | 418.18   | 1085.32   | 392.13   | 744.10  |
| -14.28             | D+     | 1080.76 | 392.13   | 1064.59   | 350.39   | 721.97  |
| Effect on Mean     | D-     | 418.18  | 1085.32  | 375.00    | 1066.50  | 736.25  |
| -12.49             | E+     | 1080.76 | 1085.32  | 375.00    | 350.39   | 722.87  |
| Effect on Mean     | E-     | 418.18  | 392.13   | 1064.59   | 1066.50  | 735.35  |
| -0.30              | F+     | 1080.76 | 418.18   | 1066.50   | 350.39   | 728.96  |
| Effect on Mean     | F-     | 1085.32 | 392.13   | 1064.59   | 375.00   | 729.26  |
| 1.02               | G+     | 418.18  | 1085.32  | 1064.59   | 350.39   | 729.62  |
| Effect on Mean     | G-     | 1080.76 | 392.13   | 375.00    | 1066.50  | 728.60  |
| -2.21              | A+     | 5.06    | 1.17     | 4.76      | 0.43     | 2.86    |
| Effect on Std.Dev. | A-     | 0.16    | 8.65     | 3.52      | 7.95     | 5.07    |
| 1.18               | B+     | 8.65    | 1.17     | 7.95      | 0.43     | 4.55    |
| Effect on Std.Dev. | B-     | 0.16    | 5.06     | 3.52      | 4.76     | 3.37    |
| 0.41               | C+     | 3.52    | 4.76     | 7.95      | 0.43     | 4.17    |
| Effect on Std.Dev. | C-     | 0.16    | 5.06     | 8.65      | 1.17     | 3.76    |
| -5.29              | D+     | 0.16    | 1.17     | 3.52      | 0.43     | 1.32    |
| Effect on Std.Dev. | D-     | 5.06    | 8.65     | 4.76      | 7.95     | 6.61    |
| -0.93              | E+     | 0.16    | 8.65     | 4.76      | 0.43     | 3.50    |
| Effect on Std.Dev. | E-     | 5.06    | 1.17     | 3.52      | 7.95     | 4.43    |
| -1.12              | F+     | 0.16    | 5.06     | 7.95      | 0.43     | 3.40    |
| Effect on Std.Dev. | F-     | 8.65    | 1.17     | 3.52      | 4.76     | 4.52    |
| 0.01               | G+     | 5.06    | 5.06     | 3.52      | 0.43     | 3.52    |
| Effect on Std.Dev. | G-     | 0.16    | 1.17     | 4.76      | 7.95     | 3.51    |
| -0.32              | A+     | 1.92    | 2.53     | 1.90      | 2.91     | 2.31    |
| Effect on SNR      | A-     | 3.84    | 2.10     | 2.48      | 2.13     | 2.64    |
| -0.12              | B+     | 2.10    | 2.53     | 2.13      | 2.91     | 2.41    |
| Effect on SNR      | B-     | 3.84    | 1.92     | 2.48      | 1.90     | 2.53    |
| -0.24              | C+     | 2.48    | 1.90     | 2.13      | 2.91     | 2.35    |
| Effect on SNR      | C-     | 3.84    | 1.92     | 2.10      | 2.53     | 2.60    |
| 0.93               | D+     | 3.84    | 2.53     | 2.48      | 2.91     | 2.94    |
| Effect on SNR      | D-     | 1.92    | 2.10     | 1.90      | 2.13     | 2.01    |
| 0.42               | E+     | 3.84    | 2.10     | 1.90      | 2.91     | 2.69    |
| Effect on SNR      | E-     | 1.92    | 2.53     | 2.48      | 2.13     | 2.26    |
| 0.45               | F+     | 3.84    | 1.92     | 2.13      | 2.91     | 2.70    |
| Effect on SNR      | F-     | 2.10    | 2.53     | 2.48      | 1.90     | 2.25    |
| -0.25              | G+     | 1.92    | 2.10     | 2.48      | 2.91     | 2.35    |
| Effect on SNR      | G-     | 3.84    | 2.53     | 1.90      | 2.13     | 2.60    |

| Factor A       |     | =   | -690.37 | ^2 / (1/2) = | 953221.45 |
|----------------|-----|-----|---------|--------------|-----------|
| Factor B       |     | =   | -11.05  | ^2 / (1/2) = | 244.01    |
| Factor C       |     | =   | -29.98  | ^2 / (1/2) = | 1797.43   |
| Factor D (AB)  |     | =   | -14.28  | ^2 / (1/2) = | 407.90    |
| Factor E (AC)  |     | =   | -12.49  | ^2 / (1/2) = | 311.81    |
| Factor F (BC)  |     | =   | -0.30   | ^2 / (1/2) = | 0.18      |
| Factor G (ABC) |     | =   | 1.02    | ^2 / (1/2) = | 2.08      |

| Row Number:               | 1.00      | 2.00      | 3.00      | 4.00      | 5.00      | 6.00      | 7.00      | 8.00      |
|---------------------------|-----------|-----------|-----------|-----------|-----------|-----------|-----------|-----------|
| Row Averages:             | 1080.76   | 418.18    | 1085.32   | 392.13    | 1064.59   | 375.00    | 1066.50   | 350.39    |
| GA - Row Average:         | -351.65   | 310.93    | -356.21   | 336.97    | -335.48   | 354.11    | -337.40   | 378.72    |
| (GA - Row Average)^2:     | 123659.79 | 96677.74  | 126885.15 | 113552.05 | 112547.87 | 125395.90 | 113836.11 | 143430.24 |
| Total SS Groups           |           |           |           |           |           |           |           |           |
| Sum of (GA - Row Ave)^2 = |           | 955984.85 |           |           |           |           |           |           |

|                | SS        | Df   | MS        | F         | Alpha | Conf. |
|----------------|-----------|------|-----------|-----------|-------|-------|
| Factor A       | 953221.45 | 1.00 | 953221.45 | 458698.73 | 0.00  | 1.00  |
| Factor B       | 244.01    | 1.00 | 244.01    | 117.42    | 0.06  | 0.94  |
| Factor C       | 1797.43   | 1.00 | 1797.43   | 864.94    | 0.02  | 0.98  |
| Factor D (AB)  | 407.90    | 1.00 | 407.90    | 196.28    | 0.05  | 0.95  |
| Factor E (AC)  | 311.81    | 1.00 | 311.81    | 150.05    | 0.05  | 0.95  |
| Factor F (BC)  | 0.18      | 1.00 | 0.18      | 0.09      | 0.82  | 0.18  |
| Factor G (ABC) | 2.08      | 1.00 | 2.08      |           |       |       |
| Total          | 955984.85 | 7.00 |           |           |       |       |
