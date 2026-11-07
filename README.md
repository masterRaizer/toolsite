# toolsite

Статический сайт-журнал о пиве для ноды: статьи, история, форум, «живой» чат, библиотека EPUB/FB2.
Ставится одной командой на сервер с selfsteal (remnautility) или на CDN-ноду (install-4cdn.sh).

## Установка

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/masterRaizer/toolsite/main/install.sh)
```

Скрипт сам найдёт, куда ставить:

| Что на сервере | Куда кладётся сайт |
|---|---|
| selfsteal из remnautility (Caddy / nginx, Docker или системный) | `/opt/selfsteal/html` |
| CDN-нода из install-4cdn.sh | `LANDING_DIR` из `/root/.multicdn.state` |
| другое | `--dir /путь` |

Прежний сайт сохраняется в `<папка>.bak-<дата>` (хранятся последние 3), подключается своя страница 404.

## Параметры

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/masterRaizer/toolsite/main/install.sh) --rollback       # вернуть прошлую версию
bash <(curl -fsSL https://raw.githubusercontent.com/masterRaizer/toolsite/main/install.sh) --name "Мой журнал"
bash <(curl -fsSL https://raw.githubusercontent.com/masterRaizer/toolsite/main/install.sh) --dir /var/www/site
```

`--seed` — вариант сайта. По умолчанию это домен ноды, поэтому на разных доменах получаются разные журналы
(название, цвет, набор статей и тем), а на одном домене при обновлении — тот же самый.

## Разработка

```
site/build.py               сборка → site/out (python3, без зависимостей)
site/content_articles.py    статьи и рубрики
site/content_community.py   форум, чат, хронология
site/static/                стили и скрипты
site/images/<ключ>.jpg      фото вместо SVG (ключ = слаг статьи, history, forum, library, about)
```

```bash
python3 site/build.py --seed example.com
```
