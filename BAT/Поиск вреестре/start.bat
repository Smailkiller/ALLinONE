@echo off
setlocal ENABLEDELAYEDEXPANSION
chcp 65001 >nul

set "ScriptDir=%~dp0"
set "PSFile=%ScriptDir%Search_and_pin.ps1"
set "LogFile=%ScriptDir%run.log"

echo [*] Папка: %ScriptDir%
echo [*] Скрипт: %PSFile%
echo [*] Лог:    %LogFile%
echo.

if not exist "%PSFile%" (
  echo [!] Не найден PowerShell-скрипт: "%PSFile%"
  pause
  exit /b 1
)

REM Пишем вывод в консоль и в лог одним проходом
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -Command ^
  "& { & '%PSFile%' *>&1 | Tee-Object -FilePath '%LogFile%' -Append }"

echo.
echo [*] Готово. Проверьте index.txt и run.log.
pause
