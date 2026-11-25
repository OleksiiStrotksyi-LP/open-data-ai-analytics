# Дані

- `raw/` — сирі дані з порталу [data.gov.ua](https://data.gov.ua/), завантажуються скриптом `src/data_load.py`.
- `processed/` — очищені дані після `src/data_quality_analysis.py`.

Обидві папки не зберігаються в Git (див. `.gitignore`), бо містять великі файли.
Щоб отримати дані локально, запустіть:

```bash
python src/data_load.py
```
