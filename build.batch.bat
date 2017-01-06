REM @echo off

set INCREMENTDISABLE=true

REM # XEON x64 Build Vars #
set _SCRIPT_DRIVE=%~d0
set _SCRIPT_FOLDER=%~dp0
set SRC=%CD%
copy %SRC%\post-commit-git-diff.sh %SRC%\.git\hooks\post-commit

copy %SRC%\pre-commit-git-diff.sh %SRC%\.git\hooks\pre-commit

GOTO:eof
REM --- exit ----
GOTO:eof
