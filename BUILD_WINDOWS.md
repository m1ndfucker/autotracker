# Building BB Death Detector for Windows

## Quick Build (без встроенного Tesseract)

```batch
build.bat
```

Пользователям нужно будет установить Tesseract отдельно.

## Full Build (с встроенным Tesseract)

### Шаг 1: Скачать Tesseract

1. Скачай Tesseract installer с:
   https://github.com/UB-Mannheim/tesseract/wiki

2. Установи (запомни путь, например `C:\Program Files\Tesseract-OCR`)

### Шаг 2: Скопировать файлы Tesseract

Скопируй эти файлы в `assets/tesseract/`:

```
assets/tesseract/
├── tesseract.exe
├── *.dll (все DLL файлы)
└── tessdata/
    └── eng.traineddata
```

Из установленного Tesseract тебе нужны:
- `tesseract.exe`
- Все `.dll` файлы из папки установки
- Папка `tessdata` с `eng.traineddata`

### Шаг 3: Собрать

```batch
build_full.bat
```

Готовый exe будет в `dist/BB Death Detector.exe`

## Структура проекта

```
bb-detector/
├── assets/
│   ├── icon.ico          # Иконка приложения
│   └── tesseract/        # Portable Tesseract (опционально)
│       ├── tesseract.exe
│       ├── *.dll
│       └── tessdata/
│           └── eng.traineddata
├── bb_detector/          # Исходный код
├── requirements/
│   ├── base.txt          # Общие зависимости
│   └── windows.txt       # Windows-специфичные
├── build.bat             # Быстрая сборка
├── build_full.bat        # Полная сборка с Tesseract
├── run.bat               # Запуск для разработки
└── bb_detector.spec      # PyInstaller конфиг
```

## Troubleshooting

### "Tesseract not found"

Если Tesseract не забандлен, пользователь увидит ошибку.
Решение: установить Tesseract и добавить в PATH.

### DLL ошибки

Убедись что скопировал ВСЕ dll файлы из папки Tesseract.

### Антивирус

PyInstaller exe иногда помечается антивирусами как подозрительный.
Это ложное срабатывание. Можно добавить в исключения.
