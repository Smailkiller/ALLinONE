# 🔧 ALLinONE Scripts

<p align="left">
    <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/BAT%20Scripts-4EAA25?style=for-the-badge&logo=windows&logoColor=white" alt="BAT"/>
</p>

📦 Сборник моих **скриптов и утилит для автоматизации** на Python и BAT.  
Применяются для обработки файлов, отчётов, работы с платформами и вспомогательных задач.

---

## 📂 Структура проекта

```bash
.
├── 📁 BAT/                # BAT-скрипты для Windows
│   ├── 📝 Fix_csv.bat
│   ├── 🎞️ compressvideo.bat
│   ├── 📝 onli_data.bat
│   └── 📝 склеиватель.bat
│
├── 📁 PYTHONE/
│   ├── 📁 SMLT_курсы/
│   │   ├── 📜 SMLT_result_data.py
│   │   └── 📜 kyrsi_load.py
│   │
│   └── 📁 TG_BOT/
│       ├── 🤖 TG_Bot_HABITTICA.py
│       ├── 🎙️ TavernGuestBot.py
│       └── 🎲 очко.py
└── 📄 README.md
```

---

## ⚡ Скрипты

### 🖥️ BAT

| Файл | Описание |
|------|-----------|
| **📝 onli_data.bat** | Сбор всех CSV файлов и фильтрация по столбцу с датой. |
| **📝 склеиватель.bat** | Склейка всех CSV файлов в папке. |
| **📝 Fix_csv.bat** | Чистка и фиксы CSV для корректного импорта (табуляция, разделители). |
| **🎞️ compressvideo.bat** | Сжатие видео с использованием FFMPEG. |

---

### 🐍 Python

#### 📊 SMLT_курсы
| Файл | Описание |
|------|-----------|
| **📜 kyrsi_load.py** | Пакетная загрузка результатов курсов с платформы. |
| **📜 SMLT_result_data.py** | Создание отчётного документа для рассылки по неверным ответам. |

#### 🤖 TG_BOT
| Файл | Описание |
|------|-----------|
| **🎙️ TavernGuestBot.py** | Бот для отправки аудио в формате голосовых. |
| **🤖 TG_Bot_HABITTICA.py** | Бот для фиксации привычек и генерации статистики. |
| **🎲 очко.py** | Многофункциональный бот для чата: рейтинги, донат, ограничения. |


---

## 🛠️ Стек
| Технология | Применение |
|------------|------------|
| 🐍 **Python** | Обработка данных, боты |
| 🖥️ **BAT** | Автоматизация на Windows |
| 🎞️ **FFMPEG** | Работа с видео |
| 📊 **CSV/Excel** | Отчёты и аналитика |



---

## 📜 Лицензия
Проект распространяется под лицензией [MIT](LICENSE).
