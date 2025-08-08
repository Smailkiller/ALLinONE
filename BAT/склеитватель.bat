@echo off
setlocal enabledelayedexpansion

set OUTPUT=merged.csv
if exist "%OUTPUT%" del "%OUTPUT%"

set headerWritten=false

for %%F in ("*.csv") do (
    set firstLine=true
    for /f "usebackq tokens=1-20 delims=, eol=" %%a in ("%%~F") do (
        if "!headerWritten!"=="false" (
            echo %%a,%%b,%%c,%%d,%%e,%%f,%%g,%%h,%%i,%%j,%%k,%%l,%%m,%%n,%%o,%%p,%%q,%%r,%%s,%%t>> "%OUTPUT%"
            set headerWritten=true
        ) else (
            if "!firstLine!"=="false" (
                echo %%a,%%b,%%c,%%d,%%e,%%f,%%g,%%h,%%i,%%j,%%k,%%l,%%m,%%n,%%o,%%p,%%q,%%r,%%s,%%t>> "%OUTPUT%"
            ) else (
                set firstLine=false
            )
        )
    )
)

echo Объединение завершено! Файл: %OUTPUT%
pause
