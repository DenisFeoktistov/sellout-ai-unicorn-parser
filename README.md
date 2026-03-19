# sellout-ai-unicorn-parser

Простой API-сервер на FastAPI для парсинга карточек товаров `unicorngo`.

## Запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

## Эндпоинты

- `GET /health` - проверка состояния сервиса.
- `POST /parse` - парсинг товара.

Пример body:

```json
{
  "url": "https://unicorngo.ru/product/new-balance-530-white-silver-navy-1001819?sku=600012669&shop=false"
}
```
