# DROPVERSE

Стартовый проект Telegram-игры: FastAPI API, SQLAlchemy, Telegram-бот aiogram 3, React/Vite Mini App, PostgreSQL/Docker и базовые тесты.

**Честный статус:** это работающая основа основных сценариев, но не завершённая реализация каждой подсистемы из большого ТЗ. Реализованы профиль, Telegram initData HMAC-проверка, коллекционные предметы, инвентарь, контейнеры, ежедневная награда, задания, магазин, рейтинг и минимальная админ-статистика. Друзья, кланы, обмены, почта, полноценная админ-панель, сезонная система и другие крупные подсистемы требуют дальнейшей разработки.

## Docker запуск
1. Скопируй `.env.example` в `.env`.
2. Заполни `BOT_TOKEN` токеном от @BotFather и `ADMIN_TELEGRAM_IDS` своим числовым Telegram ID.
3. `docker compose up --build`
4. API: http://localhost:8000/docs, frontend: http://localhost:5173.

## Запуск без Docker
Backend: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000`
Bot: `cd bot && pip install -r requirements.txt && python main.py`
Frontend: `cd frontend && npm install && npm run dev`

Локально используется SQLite, если `DATABASE_URL` не задан. В Docker используется PostgreSQL. Для production обязательно выключить demo mode (`VITE_DEMO_MODE=false`), установить `ENVIRONMENT=production`, указать HTTPS URL Mini App и постоянную PostgreSQL базу.

## Render
Создай PostgreSQL, Web Service для backend (`Root Directory=backend`, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`), Background Worker для bot (`Root Directory=bot`, build `pip install -r requirements.txt`, start `python main.py`) и Static Site для frontend (`Root Directory=frontend`, build `npm install && npm run build`, publish `dist`). Настрой переменные окружения из `.env.example`.

## Важное
Игровые монеты и предметы виртуальные, денежных ставок и вывода денег нет. Не публикуй `.env` или BOT_TOKEN. Прежде чем считать проект production-ready, реализуй пункты из `docs/IMPLEMENTATION_STATUS.md` и проведи полный аудит.
