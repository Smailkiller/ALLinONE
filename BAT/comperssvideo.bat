@echo off
chcp 65001 >nul
setlocal EnableExtensions

REM === Проверка аргумента ===
if "%~1"=="" (
  echo Перетащите видеофайл на этот BAT-файл.
  pause
  exit /b
)

REM === Вход/выход ===
set "infile=%~1"
set "outfile=%~dpn1_compressed.mp4"

REM === Значения по умолчанию ===
set "CRF=22"       REM 18-20 почти без потерь, 22-24 оптимум, 25-27 сильнее сжимает
set "PRESET=slow"  REM slower/slow/medium/fast/faster

echo Исходный файл: "%infile%"
echo Выходной файл: "%outfile%"
echo Текущее качество: CRF=%CRF%, Preset=%PRESET%
echo.

REM === (Необязательно) спросить у пользователя значения ===
set /p CRF=Введите CRF (Enter=%CRF%): 
if "%CRF%"=="" set "CRF=22"
set /p PRESET=Введите preset [slower/slow/medium/fast] (Enter=%PRESET%): 
if "%PRESET%"=="" set "PRESET=slow"

echo.
echo Использую параметры: CRF=%CRF%  ^|  Preset=%PRESET%
echo.

REM === Запуск ffmpeg с прогрессом ===
ffmpeg -hide_banner -v warning -stats -i "%infile%" ^
  -map 0:v:0 -map 0:a:0? ^
  -vf "scale=-2:720,format=yuv420p" ^
  -c:v libx264 -preset %PRESET% -crf %CRF% ^
  -c:a aac -b:a 128k ^
  -movflags +faststart ^
  -y "%outfile%"

echo.
echo ✅ Готово! Файл сохранён как: "%outfile%"
pause
