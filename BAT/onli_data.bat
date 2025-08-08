@echo off
setlocal enabledelayedexpansion

set "TEMPFILE=merged_temp.csv"
set "OUTPUT=merged_data.csv"

if exist "%TEMPFILE%" del "%TEMPFILE%"
if exist "%OUTPUT%" del "%OUTPUT%"

for %%F in (*.csv) do (
    set "firstLine=true"
    for /f "usebackq tokens=1-25 delims=; eol=" %%a in ("%%~F") do (
        if "!firstLine!"=="true" (
            set "firstLine=false"
        ) else (
            echo %%p | findstr ".2025" >nul
            if !errorlevel! == 0 (
                set "percent=%%s"
                set "percent=!percent:%%=!"
                set "percent=!percent:,=!"     :: Убираем запятую на случай, если она есть
                set "percent=!percent:.=!"     :: Убираем точку на случай, если она есть
                rem Добавим 0, перед значением вручную
                if defined percent (
                    set "formatted=0,!percent!"
                    echo !formatted!;%%a>> "%TEMPFILE%"
                )
            )
        )
    )
)

move /Y "%TEMPFILE%" "%OUTPUT%" >nul
echo ✅ Готово: %OUTPUT%
pause
