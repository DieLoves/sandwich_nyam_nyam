## IntegrityOS - системы визуализации, хранения и анализа данных обследований магистральных трубопроводов.

### Установка библиотек

```bash
pip install -r requirements.txt
```

### Если нет sqlite3 встроенного

```bash
pip install -r requirementsnosql.txt
```

### Запуск проекта

```bash
streamlit run app.py
```

---

## Архитектура проекта

```bash
IntegrityOS/
├── app.py
├── db.py
├── ml.py
├── map.py
├── cards.py
├── dashboard.py
├── report.py
├── constants.py
├── utils.py
└── requirements.txt
```
