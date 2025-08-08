@echo off
setlocal enabledelayedexpansion

:: Проверка аргумента
if "%~1"=="" (
    echo Перетащи CSV-файл на этот bat-файл.
    pause
    exit /b
)

:: Пути и имена
set "INPUT=%~1"
set "FILENAME=%~n1"
set "EXT=%~x1"
set "DIR=%~dp1"
set "OUTPUT=%DIR%%FILENAME%_fixed%EXT%"

:: Заменяем сломанные разделители на ;
:: Сохраняем как UTF-8 с BOM
powershell -Command ^
    "$text = Get-Content -Path '%INPUT%' -Encoding UTF8; " ^
    "$fixed = $text -replace '\s{2,}', ';' -replace '\t', ';' -replace '\|', ';' -replace ',', ';'; " ^
    "[System.IO.File]::WriteAllLines('%OUTPUT%', $fixed, [System.Text.Encoding]::UTF8)"

echo [✓] Файл сохранён как:
echo %OUTPUT%
pause
