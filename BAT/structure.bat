@echo off
REM Этот скрипт сохраняет всю структуру текущей папки, включая файлы и подпапки, в файл folder_structure.txt

chcp 65001 >nul

REM Удаляем старый файл, если он есть
if exist folder_structure.txt del folder_structure.txt

REM Записываем структуру папки с файлами и подпапками в текстовый файл
tree /F /A > folder_structure.txt

echo Структура папки сохранена в файле folder_structure.txt
pause