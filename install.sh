#!/usr/bin/env bash
#
#  toolsite — сайт-журнал для маскировки ноды (selfsteal / CDN-заглушка)
#
#    bash <(curl -fsSL https://raw.githubusercontent.com/masterRaizer/toolsite/main/install.sh)
#
#  Сам находит, куда ставить:
#    • selfsteal из remnautility  (/opt/selfsteal/html — Caddy или nginx, в Docker или системный)
#    • заглушка CDN-ноды из install-4cdn.sh  (LANDING_DIR из /root/.multicdn.state)
#    • или любая папка: --dir /var/www/site
#
#  Ключи:
#    --dir PATH      поставить в эту папку (без автоопределения)
#    --seed TEXT     вариант сайта (по умолчанию — домен ноды: на разных доменах разные журналы)
#    --name TEXT     своё название журнала
#    --rollback      вернуть предыдущую версию из бэкапа
#    --branch NAME   ветка репозитория (по умолчанию main)
#
set -uo pipefail

REPO="masterRaizer/toolsite"
BRANCH="main"
RED='\033[0;31m'; GRN='\033[0;32m'; YLW='\033[1;33m'; CYA='\033[0;36m'; RST='\033[0m'
info() { echo -e "${GRN}[+]${RST} $*"; }
warn() { echo -e "${YLW}[!]${RST} $*"; }
die()  { echo -e "${RED}[x]${RST} $*" >&2; exit 1; }

DIR=""; SEED=""; NAME=""; ROLLBACK=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dir) DIR="${2:-}"; shift 2 ;;
        --seed) SEED="${2:-}"; shift 2 ;;
        --name) NAME="${2:-}"; shift 2 ;;
        --branch) BRANCH="${2:-main}"; shift 2 ;;
        --rollback) ROLLBACK=1; shift ;;
        -h|--help) sed -n '2,21p' "$0" 2>/dev/null | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) die "Неизвестный параметр: $1 (см. --help)" ;;
    esac
done
[[ $EUID -eq 0 ]] || die "Запускать от root."

# ── Куда ставим ──────────────────────────────────────────────────────────────
KIND="dir"; DOMAIN=""; PORT=""; WEBSERVER=""; NGINX_SITE=""; CADDYFILE=""
SS_ENV=/opt/selfsteal/selfsteal.env; CDN_STATE=/root/.multicdn.state
envval() { grep -E "^$2=" "$1" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"'; }

if [[ -n "$DIR" ]]; then
    TARGET="$DIR"
elif [[ -f "$SS_ENV" ]]; then
    KIND="selfsteal"; TARGET=/opt/selfsteal/html
    DOMAIN=$(envval "$SS_ENV" DOMAIN); PORT=$(envval "$SS_ENV" PORT); WEBSERVER=$(envval "$SS_ENV" WEBSERVER)
    NGINX_SITE=$(envval "$SS_ENV" NGINX_SITE); CADDYFILE=$(envval "$SS_ENV" CADDYFILE)
    info "Найден selfsteal: $DOMAIN ($WEBSERVER → 127.0.0.1:$PORT)"
elif [[ -f "$CDN_STATE" ]]; then
    KIND="cdn"; TARGET=$(envval "$CDN_STATE" LANDING_DIR); TARGET=${TARGET:-/var/www/hugedonate}
    for p in yandex vk beeline timeweb; do d=$(envval "$CDN_STATE" "DOM_$p"); [[ -n "$d" ]] && { DOMAIN="$d"; break; }; done
    SITES=$(envval "$CDN_STATE" SITE_LIST)
    info "Найдена CDN-нода (install-4cdn.sh), папка сайта: $TARGET"
    [[ -n "$SITES" ]] || warn "Сайт на «/» у этой ноды не включён ни для одного CDN (SITE_LIST пуст) — файлы лягут, но отдаваться не будут. Включается в install-4cdn.sh, шаг «2а»."
else
    die "Не нашёл ни selfsteal (/opt/selfsteal), ни CDN-ноды (/root/.multicdn.state). Укажи папку: --dir /путь"
fi
SEED=${SEED:-${DOMAIN:-$(hostname -f 2>/dev/null || hostname)}}

# ── Откат ───────────────────────────────────────────────────────────────────
if (( ROLLBACK )); then
    BK=$(ls -1d "$TARGET".bak-* 2>/dev/null | sort | tail -1)
    [[ -n "$BK" ]] || die "Бэкапов $TARGET.bak-* нет."
    rm -rf "$TARGET.rollback-tmp" && mv "$TARGET" "$TARGET.rollback-tmp" && mv "$BK" "$TARGET" && rm -rf "$TARGET.rollback-tmp"
    info "Вернул $BK → $TARGET"
    exit 0
fi

# ── Зависимости ─────────────────────────────────────────────────────────────
for c in python3 curl tar; do
    command -v "$c" >/dev/null 2>&1 || { info "Ставлю $c…"; DEBIAN_FRONTEND=noninteractive apt-get update -qq >/dev/null 2>&1; DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "$c" >/dev/null 2>&1 || die "Не поставился $c"; }
done

# ── Сборка ──────────────────────────────────────────────────────────────────
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
if [[ -n "${TOOLSITE_SRC:-}" ]]; then
    cp -a "$TOOLSITE_SRC/." "$TMP/"   # локальная копия репозитория (для проверки)
else
    info "Скачиваю $REPO ($BRANCH)…"
    curl -fsSL "https://codeload.github.com/$REPO/tar.gz/$BRANCH" | tar -xz -C "$TMP" --strip-components=1 || die "Не скачался репозиторий."
fi
ARGS=(--seed "$SEED" --out "$TMP/out"); [[ -n "$NAME" ]] && ARGS+=(--name "$NAME")
python3 -B "$TMP/site/build.py" "${ARGS[@]}" || die "Сборка сайта не удалась."
TITLE=$(grep -o '<b>[^<]*</b><small>' "$TMP/out/index.html" | head -1 | sed 's/<[^>]*>//g')

# ── Установка (с бэкапом, последние 3) ──────────────────────────────────────
TS=$(date +%Y%m%d-%H%M%S)
if [[ -d "$TARGET" ]] && [[ -n "$(ls -A "$TARGET" 2>/dev/null)" ]]; then
    cp -a "$TARGET" "$TARGET.bak-$TS" && info "Бэкап: $TARGET.bak-$TS"
    ls -1d "$TARGET".bak-* 2>/dev/null | sort | head -n -3 | xargs -r rm -rf
fi
mkdir -p "$TARGET"
find "$TARGET" -mindepth 1 -delete
cp -a "$TMP/out/." "$TARGET/"
chmod 755 "$TARGET"; chmod -R a+rX "$TARGET"
id www-data >/dev/null 2>&1 && [[ "$KIND" == "cdn" ]] && chown -R www-data:www-data "$TARGET"
info "Сайт «$TITLE» установлен в $TARGET"

# ── Своя страница 404 вместо пустого ответа ─────────────────────────────────
nginx_404() {  # $1 — файл конфига; добавляет error_page после «index index.html;»
    local f="$1"
    [[ -f "$f" ]] || return 1
    grep -q "error_page 404 /404.html" "$f" && return 0
    cp "$f" "$f.bak-toolsite-$TS"
    sed -i 's#^\(\s*\)index index.html;#\1index index.html;\n\1error_page 404 /404.html;#' "$f"
}
case "$KIND/$WEBSERVER" in
    selfsteal/caddy)
        CF=/opt/selfsteal/Caddyfile
        if [[ -f "$CF" ]] && ! grep -q handle_errors "$CF"; then
            cp "$CF" "$CF.bak-toolsite-$TS"
            python3 - "$CF" <<'PY'
import re, sys
p = sys.argv[1]; s = open(p).read()
s = re.sub(r"(https://[^\n{]+\{\n(?:[^}]*\n)*?\s*file_server\n)", r"\1    handle_errors {\n        rewrite * /404.html\n        file_server\n    }\n", s, count=1)
open(p, "w").write(s)
PY
        fi
        docker exec selfsteal-caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile >/dev/null 2>&1 \
            && info "Caddy: страница 404 подключена" || warn "Caddy не перечитал конфиг — проверь: docker logs selfsteal-caddy" ;;
    selfsteal/nginx)
        nginx_404 /opt/selfsteal/nginx.conf && docker exec selfsteal-nginx nginx -s reload >/dev/null 2>&1 \
            && info "nginx (Docker): страница 404 подключена" || warn "nginx в Docker не перечитал конфиг" ;;
    selfsteal/nginx-system)
        if nginx_404 "$NGINX_SITE" && nginx -t >/dev/null 2>&1; then systemctl reload nginx && info "nginx: страница 404 подключена"
        else [[ -f "$NGINX_SITE.bak-toolsite-$TS" ]] && cp "$NGINX_SITE.bak-toolsite-$TS" "$NGINX_SITE"; warn "nginx -t не прошёл — 404 не трогал"; fi ;;
    cdn/*)
        if nginx_404 /etc/nginx/nginx.conf && nginx -t >/dev/null 2>&1; then systemctl reload nginx && info "nginx: страница 404 подключена"
        else [[ -f /etc/nginx/nginx.conf.bak-toolsite-$TS ]] && cp /etc/nginx/nginx.conf.bak-toolsite-$TS /etc/nginx/nginx.conf; warn "nginx -t не прошёл — 404 не трогал"; fi ;;
    *) [[ "$KIND" == "selfsteal" ]] && warn "Веб-сервер «$WEBSERVER» — 404 настрой вручную (error_page / handle_errors)." ;;
esac

# ── Проверка ────────────────────────────────────────────────────────────────
if [[ "$KIND" == "selfsteal" && -n "$DOMAIN" && -n "$PORT" ]]; then
    code=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 10 --resolve "$DOMAIN:$PORT:127.0.0.1" "https://$DOMAIN:$PORT/" || echo 000)
    c404=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 10 --resolve "$DOMAIN:$PORT:127.0.0.1" "https://$DOMAIN:$PORT/net-takoy-stranicy" || echo 000)
    [[ "$code" == 200 ]] && info "Проверка: главная 200, несуществующая страница $c404" || warn "Проверка: главная отвечает $code"
fi

echo -e "
${CYA}────────────────────────────────────────────────────────────${RST}
  Готово: «$TITLE»${DOMAIN:+  →  https://$DOMAIN}
  Папка   : $TARGET
  Вариант : $SEED  (на другом домене соберётся другой журнал)
  Откат   : bash <(curl -fsSL https://raw.githubusercontent.com/$REPO/main/install.sh) --rollback
${CYA}────────────────────────────────────────────────────────────${RST}"
