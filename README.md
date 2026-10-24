# NioHelper

Бот-помощник для управления контентом сообщества **PSA Union**.

У группы есть VK, Telegram-канал и собственный сайт с информацией и мерчем. NioHelper берёт на себя рутину: админы управляют группой прямо из Telegram, а бот сам собирает контент по ссылкам, формирует посты и публикует их.

## Возможности

- **Постинг по ссылкам.** Отправляешь боту список ссылок с тегами — он скрапит источники, достаёт картинки и описание и публикует пост.
- **Меню редактирования постов** (`/post_menu`). Посты хранятся в базе данных, их можно открыть, изменить описание, заменить картинку и т. д.
- **Отдельные топики Telegram** под разные задачи: публикации, события, переводы, логи.
- **Прокси** для сайтов, которые блокируют прямые запросы.
- **Автоповтор** при сбоях (настраиваемое число попыток и задержка).
- **Планировщик** задач на базе APScheduler.
- **Логирование** в файл с ротацией.

## Поддерживаемые источники

| Источник | Статус |
|---|---|
| x.com (Twitter) | ✅ работает |
| vk.com | ✅ работает |
| FurAffinity | ⚠️ не работает: защита от ботов |
| Reddit | ⚠️ не работает: защита от ботов |

> Скраперы FurAffinity и Reddit остаются в проекте, но сейчас упираются в антибот-защиту этих сайтов.

## Использование

### `/post`: опубликовать посты по ссылкам

Каждая ссылка идёт с новой строки, после неё через пробел указывается тег:

```
/post
https://x.com/user/status/123456789 тег
https://vk.com/wall-12345_678 тег
```

Бот обработает все ссылки по очереди, соберёт контент и опубликует его.

### `/post_menu`: редактирование постов

Открывает меню управления постами. Через него можно:

- выбрать пост из базы данных;
- изменить описание;
- заменить картинку;
- и другие действия редактирования.

<!-- TODO: добавить скриншоты меню -->

## Стек

- Python 3
- [aiogram](https://github.com/aiogram/aiogram) 3: Telegram-бот
- [vkbottle](https://github.com/vkbottle/vkbottle): работа с VK
- SQLAlchemy + aiosqlite: база данных (SQLite)
- httpx, requests, BeautifulSoup4, lxml: скрапинг
- aiohttp-socks: работа через прокси
- APScheduler: планировщик
- loguru: логирование
- PyYAML: конфигурация
- pytest: тесты

## Структура проекта

```
NioHelper/
├── src/                  # основной код бота
├── config.example.yaml   # пример конфигурации
├── config.py             # загрузка конфигурации
├── logger.py             # настройка логирования
├── run_tg.py             # запуск Telegram-бота
├── run_vk.py             # запуск VK-части
├── start.bat             # запуск под Windows
└── requirements.txt      # зависимости
```

## Установка и запуск

1. **Клонируй репозиторий**

   ```bash
   git clone https://github.com/morovec/NioHelper.git
   cd NioHelper
   ```

2. **Создай виртуальное окружение и установи зависимости**

   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Создай конфиг**

   ```bash
   cp config.example.yaml config.yaml   # Windows: copy config.example.yaml config.yaml
   ```

   Заполни `config.yaml` (см. раздел ниже).

4. **Запусти бота**

   ```bash
   python run_tg.py
   ```

   На Windows можно запустить через `start.bat`.

## Конфигурация

Все настройки лежат в `config.yaml` (шаблон: `config.example.yaml`).

```yaml
# Telegram
telegram:
  token: token                  # токен бота от @BotFather
  group_id: "@psa_union"        # группа/канал, которым управляет бот
  admin_chat_id: -id            # чат администраторов
  events_thread_id: None        # топик для событий
  posting_thread_id: None       # топик для постинга
  logs_thread_id: None          # топик для логов
  translation_thread_id: None   # топик для переводов
  owner_id: None                # Telegram ID владельца

# VK
vk:
  bot_token: token
  user_token: token
  group_id: id
  owner_id: id

# Логирование
logging:
  level: "INFO"
  file: "logs/bot.log"
  rotation: "10 MB"

# Повторные попытки
retries:
  max_attempts: 5
  delay_seconds: 10

# Прокси для заблокированных сайтов
proxy:
  https: http://user:password@ip:port

# Данные для парсинга FurAffinity
furaffinity:
  a: a
  b: b

# База данных
database:
  url: "sqlite:///bot.db"
```

| Секция | Назначение |
|---|---|
| `telegram` | Токен бота, группа и ID топиков, в которые бот пишет посты, события, переводы и логи |
| `vk` | Токены и ID группы VK |
| `logging` | Уровень логов, путь к файлу и размер для ротации |
| `retries` | Количество попыток и пауза между ними |
| `proxy` | Прокси для сайтов, недоступных напрямую |
| `furaffinity` | Данные авторизации для скрапинга FurAffinity |
| `database` | Строка подключения к БД (по умолчанию SQLite `bot.db`) |

> ⚠️ **Не коммить `config.yaml`**: в нём токены и пароли. Убедись, что он указан в `.gitignore`.

## Тесты

```bash
pytest
```

## Планы / известные проблемы

- [ ] Починить скрапинг FurAffinity и Reddit (обход антибот-защиты)
- [ ] Добавить новые источники

## О проекте

NioHelper создан для внутренних нужд **PSA Union**.

- Telegram: [@psa_union](https://t.me/psa_union)
- VK: [@psa_union](https://vk.ru/psa_union)
- Сайт: [psaunion.ru](https://psaunion.ru)

## Лицензия

<!-- TODO: указать лицензию -->
