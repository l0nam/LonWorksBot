# 🤖 Telegram Order Bot

Бот для приёма заказов на Denizen Script, сайты и дизайн.

## Структура файлов

```
tg-order-bot/
├── bot.py            # основной код бота
├── requirements.txt  # зависимости Python
├── Procfile          # команда запуска для хостинга
├── railway.json      # конфиг Railway
└── README.md
```

## Переменные окружения

| Переменная | Описание |
|---|---|
| `BOT_TOKEN` | Токен бота от @BotFather |
| `ADMIN_ID` | Твой числовой Telegram ID |

## Локальный запуск (для теста)

```bash
pip install -r requirements.txt
export BOT_TOKEN="твой_токен"
export ADMIN_ID="твой_id"
python bot.py
```

## Деплой на Railway (бесплатно)

1. Залей папку на GitHub
2. Зайди на railway.app → New Project → Deploy from GitHub
3. Добавь переменные BOT_TOKEN и ADMIN_ID в настройках
4. Готово — бот работает 24/7
