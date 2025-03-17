# Prospekt Scraper

Скрапер для збору проспектів з різних магазинів. Скрипт автоматично збирає інформацію про акційні пропозиції та зберігає їх у форматі JSON та JavaScript.

## Функціональність

- Збір проспектів з різних магазинів (EDEKA, Norma, Lidl, Netto, тощо)
- Автоматичне визначення дат дії акцій
- Експорт даних у формати JSON та JavaScript
- Підтримка як простих HTTP-запитів, так і складних сценаріїв з використанням Playwright
- Детальне логування процесу збору даних

## Вимоги

- Python 3.11 або вище
- pip (менеджер пакетів Python)
- Доступ до інтернету

## Встановлення

1. Клонуйте репозиторій:
```bash
git clone https://github.com/your-username/prospekt_scraper.git
cd prospekt_scraper
```

2. Встановіть залежності:
```bash
pip install -r requirements.txt
```

3. Встановіть браузери для Playwright:
```bash
playwright install
```

## Використання

### Базове використання

```bash
python main.py
```

### Додаткові опції

- `-v` або `--verbose`: Увімкнути детальне логування
- `-o` або `--output`: Вказати шлях до вихідного файлу (за замовчуванням: ./output.json)

Приклад:
```bash
python main.py -v -o ./my_output.json
```

## Структура проекту

- `main.py` - головний скрипт
- `scraper.py` - логіка скрапінгу
- `exporters.py` - функції для експорту даних
- `utils.py` - допоміжні функції
- `models.py` - моделі даних
- `requirements.txt` - залежності проекту

## Формат вихідних даних

### JSON формат
```json
{
    "store_name": "EDEKA",
    "title": "Wochenangebote",
    "start_date": "2025-03-16",
    "end_date": "2025-03-22",
    "parsed_time": "2024-03-17 15:30:00"
}
```

### JavaScript формат
```javascript
const leaflets = [
    {
        store_name: "EDEKA",
        title: "Wochenangebote",
        start_date: "2025-03-16",
        end_date: "2025-03-22",
        parsed_time: "2024-03-17 15:30:00"
    }
];
```

## Логування

Скрипт веде логування наступних подій:
- Початок та завершення збору даних
- Успішне додавання проспектів
- Помилки при парсингу дат
- Помилки при зборі даних

## Вирішення проблем

### Помилка "No module named 'playwright'"
```bash
pip install -r requirements.txt
playwright install
```

### Помилки з датами
Якщо виникають попередження про нерозпізнані дати, перевірте формат дат у проспектах.

## Ліцензія

MIT License

## Автор

[Ваше ім'я]

## Внесок у проект

Будь ласка, створюйте issues та pull requests для покращення проекту. 