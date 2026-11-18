# Скальпер Дашборд - MOEX FUTOI

Интерфейс для отслеживания открытых позиций физических и юридических лиц по фьючерсным контрактам MOEX в реальном времени.

## Возможности

- 📊 **Real-time данные** — обновление каждые 30 секунд
- 🌙 **Тёмная тема** — комфортная работа в любое время
- 🇷🇺 **Русский язык** — полный перевод интерфейса
- 👤 **Физические лица** — объёмы лонг/шорт позиций
- 🏢 **Юридические лица** — объёмы лонг/шорт позиций
- 📈 **OI График** — исторические данные, детекция дивергенции
- ⚖️ **Сравнение** — разница между категориями
- 🕐 **Московское время** — автоматическая синхронизация (UTC+3)
- 🔐 **Защита паролем** — доступ только по токену

## Быстрый старт (локально)

### 1. API ключ

Создайте файл `api_key.txt` и вставьте ваш MOEX Algopack JWT-токен:

```
ваш_api_ключ_сюда
```

### 2. Запуск

```bash
python server.py
```

### 3. Открыть

- **Дашборд**: http://localhost:8081/scalper-dashboard.html
- **Health-Check**: http://localhost:8081/health
- **Тест API**: http://localhost:8081/test-api.html

Или запустите `start.bat` (Windows).

---

## 🌐 Deployment (Render.com)

| Umgebung | URL | Branch | Назначение |
|----------|-----|--------|------------|
| **Production** | `moex-scalper-dashboard.onrender.com` | `main` | Для пользователей |
| **Staging** | `moex-staging.onrender.com` | `dev` | Тестирование |
| **Lokal** | `localhost:8081` | любой | Разработка |

### Health-Check (без авторизации)

```bash
# Production
curl https://moex-scalper-dashboard.onrender.com/health

# Staging
curl https://moex-staging.onrender.com/health
```

Ответ:
```json
{
  "status": "ok",
  "uptime": "2h 15m 30s",
  "api_key": "configured",
  "auth": "enabled",
  "port": 10000,
  "python": "3.14.10"
}
```

> ⚠️ Если `"api_key": "missing"` — значит `MOEX_API_KEY` не задана в настройках Render.

### Environment Variables (Render)

| Key | Описание |
|-----|----------|
| `MOEX_API_KEY` | MOEX Algopack JWT-токен |
| `ACCESS_TOKEN` | Пароль для доступа к дашборду |
| `SESSION_SECRET` | Автогенерируемый (Render) |

---

## 🔀 Branch-Стратегия

```
main        ← Production (стабильный, деплой на Render Production)
  └── dev   ← Staging (новые фичи сначала тестируются здесь)
```

| Branch | Когда использовать | Deploy |
|--------|-------------------|--------|
| `main` | Только стабильные, протестированные изменения | → Render Production |
| `dev` | Новые фичи, багфиксы — для тестирования | → Render Staging |

### Обычный рабочий процесс

```bash
# 1. Разрабатываем на dev
git checkout dev
# ... кодим ...
python server.py   # локально тестируем

# 2. Пушим → Staging деплоится автоматически
git push origin dev
# → Тестируем на https://moex-staging.onrender.com

# 3. Если всё OK → мерджим в main
git checkout main
git merge dev
git push origin main
# → Production деплоится автоматически
```

---

## 🔴 Rollback (если Production сломался)

### Быстрый rollback

```bash
# 1. Найти последний стабильный коммит
git log --oneline -10

# 2. Откатить проблемный коммит
git checkout main
git revert <проблемный-коммит>

# 3. Пушить → Render задеплоит автоматически
git push origin main
```

### Hard rollback (к определённому коммиту)

```bash
git checkout main
git reset --hard <стабильный-коммит>
git push origin main --force
```

---

## 📋 Чеклист перед деплоем

- [ ] `python server.py` запускается без ошибок
- [ ] `/health` возвращает `"api_key": "configured"`
- [ ] Дашборд загружается и показывает данные
- [ ] Логин работает (с `ACCESS_TOKEN`)
- [ ] Изменения протестированы на `dev` / Staging

---

## Структура файлов

```
moex-scalper-dashboard/
├── scalper-dashboard.html    # Основной дашборд
├── demo.html                 # Демо-версия
├── test-api.html             # Тест API для диагностики
├── server.py                 # Прокси-сервер (Python)
├── render.yaml               # Конфигурация Render (Production + Staging)
├── requirements.txt          # Python-зависимости
├── api_key.txt              # API ключ (не в git!)
├── start.bat                # Быстрый запуск (Windows)
├── ROLLBACK.md              # Подробная инструкция по деплою и роллбэку
└── README.md                # Этот файл
```

## Решение проблем

### Данные не отображаются

1. Проверьте, что сервер запущен (`python server.py`)
2. Убедитесь, что `api_key.txt` существует и содержит правильный ключ
3. Откройте консоль браузера (F12) и проверьте ошибки
4. Проверьте Health-Check: `http://localhost:8081/health`

### Ошибка "Failed to fetch"

Вы открываете HTML файл напрямую. Запустите `python server.py` и откройте через `http://localhost:8081/`.

### Render Free Tier

- Сервер **засыпает через 15 мин** бездействия
- Первый запрос после сна: **~30 секунд** (cold start)
- Для постоянного доступа: перейдите на платный тариф

## Технические детали

- **API**: MOEX Algopack FUTOI (Futures Open Interest) + ISS
- **Обновление данных MOEX**: каждые 5 минут
- **Обновление интерфейса**: каждые 30 секунд
- **Прокси-сервер**: решает проблему CORS и безопасно хранит API ключ
- **Авторизация**: токен с SHA-256 подписью, cookie 30 дней
